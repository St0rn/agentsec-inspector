[CmdletBinding()]
param([switch]$ForBuild, [string]$ReportPath)
. (Join-Path $PSScriptRoot 'lib\Common.ps1')
$log = Initialize-AgentSecLog -Category 'installation' -ScriptName $MyInvocation.MyCommand.Name
try {
    Assert-Windows
    $os = Get-CimInstance Win32_OperatingSystem
    $arch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()
    $checks = [ordered]@{
        windows = [ordered]@{ caption=$os.Caption; version=$os.Version; build=$os.BuildNumber; ok=([version]$os.Version -ge [version]'10.0') }
        architecture = [ordered]@{ value=$arch; ok=($arch -eq 'X64') }
        powershell = [ordered]@{ value=$PSVersionTable.PSVersion.ToString(); ok=($PSVersionTable.PSVersion -ge [version]'5.1') }
        python = [ordered]@{ value=(Get-CommandVersion python); ok=$false }
        node = [ordered]@{ value=(Get-CommandVersion node); ok=$false }
        npm = [ordered]@{ value=(Get-CommandVersion npm); ok=$false }
        rust = [ordered]@{ value=(Get-CommandVersion rustc); ok=$false }
        cargo = [ordered]@{ value=(Get-CommandVersion cargo); ok=$false }
        webview2 = [ordered]@{ value='registry'; ok=$false }
        vs_build_tools = [ordered]@{ value='vswhere'; ok=$false }
    }
    if ($checks.python.value -match 'Python (3\.1[2-9]|[4-9]\.)') { $checks.python.ok=$true }
    if ($checks.node.value -match 'v(20|22|24)\.') { $checks.node.ok=$true }
    $checks.npm.ok = [bool]$checks.npm.value; $checks.rust.ok=[bool]$checks.rust.value; $checks.cargo.ok=[bool]$checks.cargo.value
    $wvKeys=@('HKLM:\SOFTWARE\Microsoft\EdgeUpdate\Clients\{F1E7E7D1-9A4B-4E8A-BE7A-4A476B48FC48}','HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F1E7E7D1-9A4B-4E8A-BE7A-4A476B48FC48}')
    $checks.webview2.ok = [bool]($wvKeys | Where-Object { Test-Path $_ } | Select-Object -First 1)
    $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
    if (Test-Path $vswhere) { $install=& $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath; $checks.vs_build_tools.ok=[bool]$install; $checks.vs_build_tools.value=$install }
    $required = if($ForBuild){@('windows','architecture','powershell','python','node','npm','rust','cargo','webview2','vs_build_tools')}else{@('windows','architecture','powershell')}
    $missing=@($required | Where-Object {-not $checks[$_].ok})
    $result=[ordered]@{timestamp=(Get-Date -Format o); version=$script:AgentSecVersion; for_build=[bool]$ForBuild; checks=$checks; missing=$missing; success=($missing.Count -eq 0)}
    if(-not $ReportPath){$ReportPath=Join-Path $script:RepoRoot 'logs\installation\prerequisites.json'}
    $result | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $ReportPath
    foreach($item in $checks.Keys){Write-Step "$item = $($checks[$item].value); ok=$($checks[$item].ok)" $(if($checks[$item].ok){'OK'}else{'WARN'})}
    if($missing.Count){throw "Missing prerequisites: $($missing -join ', ')"}
    Complete-AgentSecLog 0; exit 0
} catch { Write-Step $_.Exception.Message 'ERROR'; Complete-AgentSecLog 1; exit 1 }
