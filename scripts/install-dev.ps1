[CmdletBinding()]
param([switch]$SkipBuildCheck)
. (Join-Path $PSScriptRoot 'lib\Common.ps1')
$log=Initialize-AgentSecLog -Category 'installation' -ScriptName $MyInvocation.MyCommand.Name
try {
    if(-not $SkipBuildCheck){& (Join-Path $PSScriptRoot 'check-prerequisites.ps1') -ForBuild;if($LASTEXITCODE){throw 'Prerequisite check failed.'}}
    foreach($name in @('setup-backend.ps1','setup-frontend.ps1','setup-database.ps1')){& (Join-Path $PSScriptRoot $name);if($LASTEXITCODE){throw "$name failed."}}
    Write-Step 'Development installation completed.' 'OK';Complete-AgentSecLog 0;exit 0
}catch{Write-Step $_.Exception.Message 'ERROR';Complete-AgentSecLog 1;exit 1}
