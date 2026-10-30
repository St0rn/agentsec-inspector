[CmdletBinding()]
param([switch]$SkipTests)
. (Join-Path $PSScriptRoot 'lib\Common.ps1')
$log=Initialize-AgentSecLog -Category 'build' -ScriptName $MyInvocation.MyCommand.Name
try {
    Assert-Windows
    & (Join-Path $PSScriptRoot 'check-prerequisites.ps1') -ForBuild
    if($LASTEXITCODE){throw 'Build prerequisites are incomplete or the native compiler probe failed.'}
    $msvcPath=Get-MsvcInstallation
    [void](Import-MsvcEnvironment $msvcPath)

    $python=Join-Path $script:RepoRoot '.venv\Scripts\python.exe'
    if(-not(Test-Path -LiteralPath $python)){throw 'Backend virtual environment is missing. Run install-dev.ps1.'}
    $tauri=Join-Path $script:RepoRoot 'frontend\node_modules\.bin\tauri.cmd'
    if(-not(Test-Path -LiteralPath $tauri)){throw 'Local Tauri CLI is missing. Run setup-frontend.ps1.'}

    if(-not $SkipTests){
        & (Join-Path $PSScriptRoot 'test-all.ps1')
        if($LASTEXITCODE){throw 'Quality gates failed.'}
    }

    [void](Invoke-Checked npm @('run','build') (Join-Path $script:RepoRoot 'frontend'))
    [void](Invoke-Checked $python @('-m','PyInstaller','--clean','--noconfirm','agentsec-backend.spec') (Join-Path $script:RepoRoot 'backend'))
    $builtBackend=Join-Path $script:RepoRoot 'backend\dist\agentsec-backend.exe'
    if(-not(Test-Path -LiteralPath $builtBackend -PathType Leaf)){throw 'PyInstaller backend executable is missing.'}
    if((Get-Item -LiteralPath $builtBackend).Length -lt 1MB){throw 'PyInstaller backend executable is unexpectedly small.'}

    $binaryDir=Join-Path $script:RepoRoot 'src-tauri\binaries'
    New-Item -ItemType Directory -Force -Path $binaryDir|Out-Null
    $sidecar=Join-Path $binaryDir 'agentsec-backend-x86_64-pc-windows-msvc.exe'
    Copy-Item -LiteralPath $builtBackend -Destination $sidecar -Force
    if((Get-FileHash -LiteralPath $builtBackend -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $sidecar -Algorithm SHA256).Hash){
        throw 'Bundled backend sidecar checksum does not match the PyInstaller output.'
    }

    [void](Invoke-Checked cargo @('test','--locked','--manifest-path',(Join-Path $script:RepoRoot 'src-tauri\Cargo.toml'),'--target','x86_64-pc-windows-msvc') $script:RepoRoot)

    $icon=Join-Path $script:RepoRoot 'assets\icon.svg'
    [void](Invoke-Checked $tauri @('icon',$icon) $script:RepoRoot)
    [void](Invoke-Checked $tauri @('build','--target','x86_64-pc-windows-msvc') $script:RepoRoot)

    $bundle=Join-Path $script:RepoRoot 'src-tauri\target\x86_64-pc-windows-msvc\release\bundle'
    $msiDirectory=Join-Path $bundle 'msi'
    $nsisDirectory=Join-Path $bundle 'nsis'
    $msiArtifacts=@(Get-ChildItem -LiteralPath $msiDirectory -File -Filter '*.msi' -ErrorAction SilentlyContinue)
    $nsisArtifacts=@(Get-ChildItem -LiteralPath $nsisDirectory -File -Filter '*.exe' -ErrorAction SilentlyContinue)
    if($msiArtifacts.Count -eq 0){throw "MSI installer was not generated in $msiDirectory"}
    if($nsisArtifacts.Count -eq 0){throw "NSIS installer was not generated in $nsisDirectory"}
    $artifacts=@($msiArtifacts+$nsisArtifacts)
    foreach($artifact in $artifacts){
        if($artifact.Length -lt 1MB){throw "Installer is unexpectedly small: $($artifact.FullName)"}
    }

    $report=[ordered]@{
        timestamp=(Get-Date -Format o)
        version=$script:AgentSecVersion
        target='x86_64-pc-windows-msvc'
        backend=[ordered]@{path=$sidecar;bytes=(Get-Item -LiteralPath $sidecar).Length;sha256=(Get-FileHash -LiteralPath $sidecar -Algorithm SHA256).Hash}
        msvc_installation=$msvcPath
        artifacts=@($artifacts|ForEach-Object{$kind=if($_.Extension -eq '.msi'){'msi'}else{'nsis'};[ordered]@{kind=$kind;path=$_.FullName;bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}})
        success=$true
    }
    $reportPath=Join-Path $script:RepoRoot 'logs\build\windows-build-report.json'
    $report|ConvertTo-Json -Depth 6|Set-Content -Encoding UTF8 -LiteralPath $reportPath
    Write-Step "MSI: $($msiArtifacts[0].FullName)" 'OK'
    Write-Step "NSIS: $($nsisArtifacts[0].FullName)" 'OK'
    Complete-AgentSecLog 0
    exit 0
}catch{
    Write-Step $_.Exception.Message 'ERROR'
    Complete-AgentSecLog 1
    exit 1
}
