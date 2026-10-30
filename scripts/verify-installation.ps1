[CmdletBinding()]
param([string]$ApplicationPath,[string]$BackendPath,[int]$Port=18765)
. (Join-Path $PSScriptRoot 'lib\Common.ps1')
$log=Initialize-AgentSecLog -Category 'tests' -ScriptName $MyInvocation.MyCommand.Name
$checks=[ordered]@{}
$process=$null
$desktop=$null
$desktopBackend=@()
$testDir=$null
try {
    Assert-Windows
    $installRoots=@(
        (Join-Path $env:LOCALAPPDATA 'Programs\AgentSec Inspector'),
        (Join-Path $env:LOCALAPPDATA 'AgentSec Inspector'),
        (Join-Path $env:ProgramFiles 'AgentSec Inspector')
    )
    $registryRoots=@(
        'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*'
    )
    $installedEntry=Find-AgentSecUninstallEntry @(Get-ItemProperty $registryRoots -ErrorAction SilentlyContinue)
    if($installedEntry -and $installedEntry.PSObject.Properties['InstallLocation'] -and $installedEntry.InstallLocation){
        $installRoots=@([string]$installedEntry.InstallLocation)+$installRoots
    }
    $installRoots=@($installRoots|Where-Object{$_}|Select-Object -Unique)

    if(-not $ApplicationPath){
        $ApplicationPath=Find-AgentSecDesktopExecutable $installRoots
    }
    if(-not $BackendPath){
        $backendCandidates=@()
        foreach($root in $installRoots){
            if(Test-Path -LiteralPath $root){
                $backendCandidates+=@(Get-ChildItem -LiteralPath $root -Recurse -File -Filter 'agentsec-backend*.exe' -ErrorAction SilentlyContinue)
            }
        }
        if($backendCandidates.Count){$BackendPath=$backendCandidates[0].FullName}
    }
    if(-not $BackendPath){
        $sourceBackend=Join-Path $script:RepoRoot 'src-tauri\binaries\agentsec-backend-x86_64-pc-windows-msvc.exe'
        if(Test-Path -LiteralPath $sourceBackend){$BackendPath=$sourceBackend}
    }

    $checks.application_file=[bool]($ApplicationPath -and (Test-Path -LiteralPath $ApplicationPath -PathType Leaf))
    $checks.backend_file=[bool]($BackendPath -and (Test-Path -LiteralPath $BackendPath -PathType Leaf))
    if(-not $checks.application_file){throw 'Installed desktop executable was not found.'}
    if(-not $checks.backend_file){throw 'Packaged backend executable was not found.'}
    $checks.backend_sha256=(Get-FileHash -LiteralPath $BackendPath -Algorithm SHA256).Hash

    $testDir=Join-Path $env:TEMP ("agentsec-verification-"+[guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $testDir|Out-Null
    $token=[guid]::NewGuid().ToString('N')+[guid]::NewGuid().ToString('N')
    $env:AGENTSEC_API_TOKEN=$token
    $env:AGENTSEC_DATA_DIR=$testDir
    $env:AGENTSEC_PORT=$Port
    $process=Start-Process -FilePath $BackendPath -PassThru

    $ready=$false
    for($i=0;$i -lt 40;$i++){
        Start-Sleep -Milliseconds 500
        try{
            $health=Invoke-RestMethod "http://127.0.0.1:$Port/health" -TimeoutSec 2
            if($health.status -eq 'ok'){$ready=$true;break}
        }catch{}
    }
    $checks.backend_health=$ready
    if(-not $ready){throw 'Backend did not become healthy on loopback.'}

    $unauthorisedBlocked=$false
    try{
        Invoke-RestMethod "http://127.0.0.1:$Port/api/v1/projects" -TimeoutSec 3|Out-Null
    }catch{
        $response=$_.Exception.Response
        if($response){
            $statusProperty=$response.PSObject.Properties['StatusCode']
            if($statusProperty -and [int]$statusProperty.Value -eq 401){$unauthorisedBlocked=$true}
        }
    }
    $checks.unauthorised_blocked=$unauthorisedBlocked
    if(-not $unauthorisedBlocked){throw 'Unauthenticated API request was not rejected with HTTP 401.'}

    $headers=@{Authorization="Bearer $token"}
    $body=@{client_name='Verification';engagement_name='Installation smoke test';description='Temporary';authorized_scope='Local verification only';start_date=$null;end_date=$null}|ConvertTo-Json
    $created=Invoke-RestMethod "http://127.0.0.1:$Port/api/v1/projects" -Method Post -Headers $headers -ContentType 'application/json' -Body $body
    $read=Invoke-RestMethod "http://127.0.0.1:$Port/api/v1/projects/$($created.id)" -Headers $headers
    $checks.project_roundtrip=($read.client_name -eq 'Verification')
    Invoke-RestMethod "http://127.0.0.1:$Port/api/v1/projects/$($created.id)" -Method Delete -Headers $headers|Out-Null
    $integrity=Invoke-RestMethod "http://127.0.0.1:$Port/api/v1/integrity" -Headers $headers
    $checks.database_integrity=($integrity.database -eq 'ok')
    $checks.database_created=Test-Path -LiteralPath (Join-Path $testDir 'agentsec.db')
    $checks.log_created=Test-Path -LiteralPath (Join-Path $testDir 'logs\agentsec.jsonl')
    $checks.directory_permissions=[bool]$integrity.data_directory_writable

    # Complete the standalone API phase before starting the desktop sidecar.
    # This prevents inherited AGENTSEC_* values and the fixed smoke-test port
    # from conflicting with the random port selected by the Tauri process.
    if($process -and -not $process.HasExited){
        Stop-Process -Id $process.Id -Force
        Wait-Process -Id $process.Id -Timeout 10 -ErrorAction SilentlyContinue
    }
    $process=$null
    Remove-Item Env:AGENTSEC_API_TOKEN -ErrorAction SilentlyContinue
    Remove-Item Env:AGENTSEC_DATA_DIR -ErrorAction SilentlyContinue
    Remove-Item Env:AGENTSEC_PORT -ErrorAction SilentlyContinue

    $backendIdsBefore=@(Get-Process -ErrorAction SilentlyContinue|Where-Object{$_.ProcessName -like 'agentsec-backend*'}|ForEach-Object{$_.Id})
    $desktop=Start-Process -FilePath $ApplicationPath -PassThru
    for($i=0;$i -lt 30;$i++){
        Start-Sleep -Milliseconds 500
        if($desktop.HasExited){break}
        $desktopBackend=@(Get-Process -ErrorAction SilentlyContinue|Where-Object{$_.ProcessName -like 'agentsec-backend*' -and $backendIdsBefore -notcontains $_.Id})
        if($desktopBackend.Count){break}
    }
    $checks.desktop_launch=(-not $desktop.HasExited)
    if(-not $checks.desktop_launch){throw "Desktop application exited during smoke test with code $($desktop.ExitCode)."}
    $checks.desktop_backend_spawned=($desktopBackend.Count -gt 0)
    if(-not $checks.desktop_backend_spawned){throw 'Desktop application did not spawn its bundled backend sidecar.'}

    $success=@($checks.Values|Where-Object{$_ -is [bool] -and -not $_}).Count -eq 0
    $report=[ordered]@{
        timestamp=(Get-Date -Format o)
        version=$script:AgentSecVersion
        application_path=$ApplicationPath
        backend_path=$BackendPath
        checks=$checks
        success=$success
        limitations=@('The smoke test verifies process startup and the packaged local API; it does not automate every WebView UI interaction.')
    }
    $reportPath=Join-Path $script:RepoRoot 'logs\tests\installation-verification.json'
    $report|ConvertTo-Json -Depth 6|Set-Content -Encoding UTF8 -LiteralPath $reportPath
    if(-not $success){throw 'One or more installation verification checks failed.'}
    Complete-AgentSecLog 0
    exit 0
}catch{
    $checks.error=$_.Exception.Message
    $report=[ordered]@{timestamp=(Get-Date -Format o);version=$script:AgentSecVersion;checks=$checks;success=$false}
    $report|ConvertTo-Json -Depth 6|Set-Content -Encoding UTF8 (Join-Path $script:RepoRoot 'logs\tests\installation-verification.json')
    Write-Step $_.Exception.Message 'ERROR'
    Complete-AgentSecLog 1
    exit 1
}finally{
    if($desktop -and -not $desktop.HasExited){Stop-Process -Id $desktop.Id -Force;Wait-Process -Id $desktop.Id -Timeout 10 -ErrorAction SilentlyContinue}
    foreach($child in $desktopBackend){if(-not $child.HasExited){Stop-Process -Id $child.Id -Force;Wait-Process -Id $child.Id -Timeout 10 -ErrorAction SilentlyContinue}}
    if($process -and -not $process.HasExited){Stop-Process -Id $process.Id -Force;Wait-Process -Id $process.Id -Timeout 10 -ErrorAction SilentlyContinue}
    if($testDir -and(Test-Path -LiteralPath $testDir)){Remove-Item -LiteralPath $testDir -Recurse -Force}
}
