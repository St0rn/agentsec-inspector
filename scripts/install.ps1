[CmdletBinding()]
param([string]$InstallerPath,[switch]$AllowDependencyInstall)
. (Join-Path $PSScriptRoot 'lib\Common.ps1')
$log=Initialize-AgentSecLog -Category 'installation' -ScriptName $MyInvocation.MyCommand.Name
try {
    Assert-Windows
    & (Join-Path $PSScriptRoot 'check-prerequisites.ps1');if($LASTEXITCODE){throw 'Unsupported Windows environment.'}
    if(-not $InstallerPath){$InstallerPath=(Get-ChildItem -Recurse -File (Join-Path $script:RepoRoot 'src-tauri\target') -ErrorAction SilentlyContinue|Where-Object{$_.Name -match 'agentsec.*(setup.*\.exe|\.msi)$'}|Sort-Object LastWriteTime -Descending|Select-Object -First 1).FullName}
    if(-not $InstallerPath -or -not(Test-Path $InstallerPath)){throw 'No installer found. Supply -InstallerPath or run build-windows.ps1.'}
    $extension=[IO.Path]::GetExtension($InstallerPath)
    Write-Step "Installer: $InstallerPath";Write-Step "SHA256: $((Get-FileHash $InstallerPath -Algorithm SHA256).Hash)"
    $answer=Read-Host 'Install this signed/verified package now? [y/N]'
    if($answer -notmatch '^(y|yes|o|oui)$'){throw 'Installation cancelled; no third-party software was installed.'}
    if($extension -eq '.msi'){Invoke-Checked msiexec @('/i',$InstallerPath)}else{Invoke-Checked $InstallerPath @()}
    & (Join-Path $PSScriptRoot 'verify-installation.ps1');if($LASTEXITCODE){throw 'Installation completed but verification failed.'}
    Complete-AgentSecLog 0;exit 0
}catch{Write-Step $_.Exception.Message 'ERROR';Complete-AgentSecLog 1;exit 1}
