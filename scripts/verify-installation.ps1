[CmdletBinding()]
param([string]$ApplicationPath,[string]$BackendPath,[int]$Port=18765)
. (Join-Path $PSScriptRoot 'lib\Common.ps1')
$log=Initialize-AgentSecLog -Category 'tests' -ScriptName $MyInvocation.MyCommand.Name
$checks=[ordered]@{}
$process=$null;$desktop=$null
$testDir=$null
try {
    Assert-Windows
    $installRoots=@((Join-Path $env:LOCALAPPDATA 'Programs\AgentSec Inspector'),(Join-Path $env:ProgramFiles 'AgentSec Inspector'))
    if(-not $ApplicationPath){$ApplicationPath=@($installRoots|ForEach-Object{Join-Path $_ 'AgentSec Inspector.exe'}|Where-Object{Test-Path $_})|Select-Object -First 1}
    if(-not $BackendPath){$BackendPath=@($installRoots|Where-Object{Test-Path $_}|ForEach-Object{Get-ChildItem -File $_ -Filter 'agentsec-backend*.exe'}|Select-Object -First 1).FullName}
    if(-not $BackendPath){$sourceBackend=Join-Path $script:RepoRoot 'src-tauri\binaries\agentsec-backend-x86_64-pc-windows-msvc.exe';if(Test-Path $sourceBackend){$BackendPath=$sourceBackend}}
    $checks.application_file=[bool]($ApplicationPath -and (Test-Path $ApplicationPath));$checks.backend_file=[bool]($BackendPath -and (Test-Path $BackendPath))
    if(-not $checks.backend_file){throw 'Packaged backend executable not found.'}
    $checks.backend_sha256=(Get-FileHash $BackendPath -Algorithm SHA256).Hash
    $testDir=Join-Path $env:TEMP ("agentsec-verification-"+[guid]::NewGuid().ToString('N'));New-Item -ItemType Directory $testDir|Out-Null
    $token=[guid]::NewGuid().ToString('N')+[guid]::NewGuid().ToString('N');$env:AGENTSEC_API_TOKEN=$token;$env:AGENTSEC_DATA_DIR=$testDir;$env:AGENTSEC_PORT=$Port
    $process=Start-Process -FilePath $BackendPath -PassThru
    $ready=$false;for($i=0;$i -lt 30;$i++){Start-Sleep -Milliseconds 500;try{$health=Invoke-RestMethod "http://127.0.0.1:$Port/health" -TimeoutSec 2;if($health.status -eq 'ok'){$ready=$true;break}}catch{}}
    $checks.backend_health=$ready;if(-not $ready){throw 'Backend did not become healthy.'}
    try{Invoke-RestMethod "http://127.0.0.1:$Port/api/v1/projects" -TimeoutSec 3;throw 'Unauthenticated request unexpectedly succeeded.'}catch{if($_.Exception.Response.StatusCode.value__ -eq 401){$checks.unauthorised_blocked=$true}else{throw}}
    $headers=@{Authorization="Bearer $token"}
    $body=@{client_name='Verification';engagement_name='Installation smoke test';description='Temporary';authorized_scope='Local verification only';start_date=$null;end_date=$null}|ConvertTo-Json
    $created=Invoke-RestMethod "http://127.0.0.1:$Port/api/v1/projects" -Method Post -Headers $headers -ContentType 'application/json' -Body $body
    $read=Invoke-RestMethod "http://127.0.0.1:$Port/api/v1/projects/$($created.id)" -Headers $headers
    $checks.project_roundtrip=($read.client_name -eq 'Verification')
    Invoke-RestMethod "http://127.0.0.1:$Port/api/v1/projects/$($created.id)" -Method Delete -Headers $headers|Out-Null
    $integrity=Invoke-RestMethod "http://127.0.0.1:$Port/api/v1/integrity" -Headers $headers;$checks.database_integrity=($integrity.database -eq 'ok')
    $checks.database_created=Test-Path (Join-Path $testDir 'agentsec.db');$checks.log_created=Test-Path (Join-Path $testDir 'logs\agentsec.jsonl');$checks.directory_permissions=$integrity.data_directory_writable
    if($checks.application_file){$desktop=Start-Process -FilePath $ApplicationPath -PassThru;Start-Sleep -Seconds 4;$checks.desktop_launch=(-not $desktop.HasExited);if(-not $checks.desktop_launch){throw 'Desktop application exited during smoke test.'}}
    $success=@($checks.Values|Where-Object{$_ -is [bool] -and -not $_}).Count -eq 0
    $report=[ordered]@{timestamp=(Get-Date -Format o);version=$script:AgentSecVersion;checks=$checks;success=$success;limitations=@('UI automation is not included in this smoke test.')}
    $report|ConvertTo-Json -Depth 6|Set-Content -Encoding UTF8 (Join-Path $script:RepoRoot 'logs\tests\installation-verification.json')
    if(-not $success){throw 'One or more verification checks failed.'}
    Complete-AgentSecLog 0;exit 0
}catch{$checks.error=$_.Exception.Message;$report=[ordered]@{timestamp=(Get-Date -Format o);version=$script:AgentSecVersion;checks=$checks;success=$false};$report|ConvertTo-Json -Depth 6|Set-Content -Encoding UTF8 (Join-Path $script:RepoRoot 'logs\tests\installation-verification.json');Write-Step $_.Exception.Message 'ERROR';Complete-AgentSecLog 1;exit 1}
finally{if($desktop -and -not $desktop.HasExited){Stop-Process -Id $desktop.Id -Force};if($process -and -not $process.HasExited){Stop-Process -Id $process.Id -Force};if($testDir -and(Test-Path $testDir)){Remove-Item -Recurse -Force $testDir}}
