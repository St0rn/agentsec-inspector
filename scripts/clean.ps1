[CmdletBinding(SupportsShouldProcess)]
param([switch]$IncludeDependencies)
. (Join-Path $PSScriptRoot 'lib\Common.ps1')
$log=Initialize-AgentSecLog -Category 'build' -ScriptName $MyInvocation.MyCommand.Name
try {
    $targets=@('frontend\dist','backend\build','backend\dist','src-tauri\target','.pytest_cache','backend\.pytest_cache','backend\.coverage')
    if($IncludeDependencies){$targets+=@('frontend\node_modules','.venv')}
    foreach($relative in $targets){$path=Join-Path $script:RepoRoot $relative;if((Test-Path $path)-and $PSCmdlet.ShouldProcess($path,'Remove generated content')){Remove-Item -Recurse -Force $path;Write-Step "Removed $path"}}
    Complete-AgentSecLog 0;exit 0
}catch{Write-Step $_.Exception.Message 'ERROR';Complete-AgentSecLog 1;exit 1}
