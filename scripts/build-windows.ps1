[CmdletBinding()]
param([switch]$SkipTests)
. (Join-Path $PSScriptRoot 'lib\Common.ps1')
$log=Initialize-AgentSecLog -Category 'build' -ScriptName $MyInvocation.MyCommand.Name
try {
    Assert-Windows
    & (Join-Path $PSScriptRoot 'check-prerequisites.ps1') -ForBuild;if($LASTEXITCODE){throw 'Build prerequisites are incomplete.'}
    if(-not $SkipTests){& (Join-Path $PSScriptRoot 'test-all.ps1');if($LASTEXITCODE){throw 'Quality gates failed.'}}
    Invoke-Checked npm @('run','build') (Join-Path $script:RepoRoot 'frontend')
    $python=Join-Path $script:RepoRoot '.venv\Scripts\python.exe'
    Invoke-Checked $python @('-m','PyInstaller','--clean','--noconfirm','agentsec-backend.spec') (Join-Path $script:RepoRoot 'backend')
    $builtBackend=Join-Path $script:RepoRoot 'backend\dist\agentsec-backend.exe';if(-not(Test-Path $builtBackend)){throw 'PyInstaller backend executable missing.'}
    $binaryDir=Join-Path $script:RepoRoot 'src-tauri\binaries';New-Item -ItemType Directory -Force -Path $binaryDir|Out-Null
    Copy-Item -Force $builtBackend (Join-Path $binaryDir 'agentsec-backend-x86_64-pc-windows-msvc.exe')
    $tauri=Join-Path $script:RepoRoot 'frontend\node_modules\.bin\tauri.cmd';if(-not(Test-Path $tauri)){throw 'Local Tauri CLI is missing; run setup-frontend.ps1.'}
    $icon=Join-Path $script:RepoRoot 'assets\icon.svg';Invoke-Checked $tauri @('icon',$icon) $script:RepoRoot
    Invoke-Checked $tauri @('build','--target','x86_64-pc-windows-msvc') $script:RepoRoot
    $bundle=Join-Path $script:RepoRoot 'src-tauri\target\x86_64-pc-windows-msvc\release\bundle'
    $artifacts=@(Get-ChildItem -Recurse -File $bundle -ErrorAction Stop|Where-Object{$_.Extension -in @('.msi','.exe')})
    if(-not $artifacts.Count){throw 'No MSI or NSIS installer was generated.'}
    $report=[ordered]@{timestamp=(Get-Date -Format o);version=$script:AgentSecVersion;target='x86_64-pc-windows-msvc';artifacts=@($artifacts|ForEach-Object{[ordered]@{path=$_.FullName;bytes=$_.Length;sha256=(Get-FileHash $_.FullName -Algorithm SHA256).Hash}});success=$true}
    $report|ConvertTo-Json -Depth 5|Set-Content -Encoding UTF8 (Join-Path $script:RepoRoot 'logs\build\windows-build-report.json')
    Complete-AgentSecLog 0;exit 0
}catch{Write-Step $_.Exception.Message 'ERROR';Complete-AgentSecLog 1;exit 1}
