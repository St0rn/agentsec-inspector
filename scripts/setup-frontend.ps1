[CmdletBinding()]
param()
. (Join-Path $PSScriptRoot 'lib\Common.ps1')
$log=Initialize-AgentSecLog -Category 'installation' -ScriptName $MyInvocation.MyCommand.Name
try {Invoke-Checked npm @('ci','--no-audit','--no-fund') (Join-Path $script:RepoRoot 'frontend');Invoke-Checked npm @('run','build') (Join-Path $script:RepoRoot 'frontend');Complete-AgentSecLog 0;exit 0}catch{Write-Step $_.Exception.Message 'ERROR';Complete-AgentSecLog 1;exit 1}
