[CmdletBinding()]
param([switch]$ForBuild, [string]$ReportPath)
. (Join-Path $PSScriptRoot 'lib\Common.ps1')
$log = Initialize-AgentSecLog -Category 'installation' -ScriptName $MyInvocation.MyCommand.Name

function Find-IncludeHeader {
    param([Parameter(Mandatory)][string]$Name)
    foreach ($directory in @($env:INCLUDE -split ';' | Where-Object { $_ })) {
        $candidate = Join-Path $directory $Name
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { return $candidate }
    }
    return $null
}

try {
    Assert-Windows
    try { $os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop }
    catch { $os = Get-WmiObject Win32_OperatingSystem -ErrorAction Stop }

    $architecture = Get-WindowsArchitecture
    $pythonVersion = Get-CommandVersion python
    $nodeVersion = Get-CommandVersion node
    $npmVersion = Get-CommandVersion npm
    $rustVersion = Get-CommandVersion rustc
    $cargoVersion = Get-CommandVersion cargo
    $webView = Get-WebView2Runtime

    $checks = [ordered]@{}
    $checks.windows = New-PrerequisiteCheck 'windows' "$($os.Caption) $($os.Version) build $($os.BuildNumber)" ([version]$os.Version -ge [version]'10.0') $true
    $checks.architecture = New-PrerequisiteCheck 'architecture' $architecture ($architecture -eq 'X64') $true 'Windows x64 is required.'
    $checks.powershell = New-PrerequisiteCheck 'powershell' $PSVersionTable.PSVersion.ToString() ($PSVersionTable.PSVersion -ge [version]'5.1') $true
    $checks.python = New-PrerequisiteCheck 'python' $pythonVersion ([bool]($pythonVersion -match 'Python (3\.1[2-9]|[4-9]\.)')) ([bool]$ForBuild) 'Python 3.12 or newer is required for source builds.'
    $checks.node = New-PrerequisiteCheck 'node' $nodeVersion ([bool]($nodeVersion -match '^v(20|22|24)\.')) ([bool]$ForBuild) 'Node.js 20, 22, or 24 is supported.'
    $checks.npm = New-PrerequisiteCheck 'npm' $npmVersion ([bool]$npmVersion) ([bool]$ForBuild)
    $checks.rust = New-PrerequisiteCheck 'rust' $rustVersion ([bool]$rustVersion) ([bool]$ForBuild)
    $checks.cargo = New-PrerequisiteCheck 'cargo' $cargoVersion ([bool]$cargoVersion) ([bool]$ForBuild)
    $checks.webview2 = New-PrerequisiteCheck 'webview2' $webView.version ([bool]$webView.installed) ([bool]$ForBuild) $webView.registry_path

    $msvcError = ''
    $msvcPath = $null
    if ($ForBuild) {
        try {
            $msvcPath = Get-MsvcInstallation
            if (-not $msvcPath) { throw 'Visual Studio C++ Build Tools were not found by vswhere.' }
            [void](Import-MsvcEnvironment $msvcPath)
        } catch {
            $msvcError = $_.Exception.Message
        }
    }
    $checks.vs_build_tools = New-PrerequisiteCheck 'vs_build_tools' $msvcPath ([bool]$msvcPath) ([bool]$ForBuild) $msvcError

    $clPath = $null
    $linkPath = $null
    $rcPath = $null
    $mtPath = $null
    $windowsHeader = $null
    $strictHeader = $null
    $runtimeHeader = $null
    if ($ForBuild -and $msvcPath -and -not $msvcError) {
        $clCommand = Get-Command cl.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        $linkCommand = Get-Command link.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        $rcCommand = Get-Command rc.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        $mtCommand = Get-Command mt.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($clCommand) { $clPath = $clCommand.Source }
        if ($linkCommand) { $linkPath = $linkCommand.Source }
        if ($rcCommand) { $rcPath = $rcCommand.Source }
        if ($mtCommand) { $mtPath = $mtCommand.Source }
        $windowsHeader = Find-IncludeHeader 'windows.h'
        $strictHeader = Find-IncludeHeader 'specstrings_strict.h'
        $runtimeHeader = Find-IncludeHeader 'vcruntime.h'
    }

    $environmentReady = [bool]($env:INCLUDE -and $env:LIB -and $env:PATH)
    $checks.msvc_x64 = New-PrerequisiteCheck 'msvc_x64' $clPath ([bool]$clPath) ([bool]$ForBuild) 'cl.exe must come from the x64 MSVC developer environment.'
    $checks.linker = New-PrerequisiteCheck 'linker' $linkPath ([bool]$linkPath) ([bool]$ForBuild) 'link.exe is required.'
    $checks.windows_sdk_tools = New-PrerequisiteCheck 'windows_sdk_tools' "rc=$rcPath; mt=$mtPath" ([bool]($rcPath -and $mtPath)) ([bool]$ForBuild) 'Install or repair a Windows 10/11 SDK with Desktop C++ tools.'
    $checks.build_environment = New-PrerequisiteCheck 'build_environment' "INCLUDE=$([bool]$env:INCLUDE); LIB=$([bool]$env:LIB)" $environmentReady ([bool]$ForBuild) 'vcvars64.bat must define INCLUDE, LIB, and PATH.'
    $headersReady = [bool]($windowsHeader -and $strictHeader -and $runtimeHeader)
    $checks.windows_sdk_headers = New-PrerequisiteCheck 'windows_sdk_headers' "windows.h=$windowsHeader; specstrings_strict.h=$strictHeader; vcruntime.h=$runtimeHeader" $headersReady ([bool]$ForBuild) 'A missing specstrings_strict.h indicates an incomplete or damaged Windows SDK.'

    $probeOk = $false
    $probeDetails = 'Compiler probe is only run for -ForBuild.'
    if ($ForBuild -and $clPath -and $linkPath -and $headersReady -and $environmentReady) {
        $probeDirectory = Join-Path $env:TEMP ("AgentSec Compiler Probe " + [guid]::NewGuid().ToString('N'))
        try {
            New-Item -ItemType Directory -Path $probeDirectory | Out-Null
            $source = Join-Path $probeDirectory 'agentsec compiler probe.cpp'
            $binary = Join-Path $probeDirectory 'agentsec-compiler-probe.exe'
            @'
#include <windows.h>
#include <specstrings_strict.h>
int main() { return GetCurrentProcessId() == 0 ? 1 : 0; }
'@ | Set-Content -LiteralPath $source -Encoding ASCII
            $probe = Invoke-Checked $clPath @('/nologo', '/EHsc', '/W4', $source, "/Fe:$binary") $probeDirectory
            $probeOk = (Test-Path -LiteralPath $binary -PathType Leaf) -and $probe.ExitCode -eq 0
            $probeDetails = "Compiled and linked a minimal C++ program in a path containing spaces."
        } catch {
            $probeDetails = $_.Exception.Message
        } finally {
            if (Test-Path -LiteralPath $probeDirectory) { Remove-Item -LiteralPath $probeDirectory -Recurse -Force }
        }
    }
    $checks.compiler_probe = New-PrerequisiteCheck 'compiler_probe' $probeOk $probeOk ([bool]$ForBuild) $probeDetails

    $missing = @($checks.Keys | Where-Object { $checks[$_].required -and -not $checks[$_].ok })
    $result = [ordered]@{
        timestamp = Get-Date -Format o
        version = $script:AgentSecVersion
        for_build = [bool]$ForBuild
        checks = $checks
        missing = $missing
        success = ($missing.Count -eq 0)
    }
    if (-not $ReportPath) { $ReportPath = Join-Path $script:RepoRoot 'logs\installation\prerequisites.json' }
    $reportDirectory = Split-Path -Parent $ReportPath
    if ($reportDirectory) { New-Item -ItemType Directory -Force -Path $reportDirectory | Out-Null }
    $result | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -LiteralPath $ReportPath

    foreach ($item in $checks.Keys) {
        $check = $checks[$item]
        $level = if ($check.ok) { 'OK' } elseif ($check.required) { 'ERROR' } else { 'WARN' }
        Write-Step "$item = $($check.value); required=$($check.required); ok=$($check.ok); $($check.details)" $level
    }
    if ($missing.Count) {
        throw "Missing or unusable prerequisites: $($missing -join ', '). Repair Visual Studio Build Tools/Windows SDK if compiler checks fail; no system setting was modified."
    }
    Complete-AgentSecLog 0
    exit 0
} catch {
    Write-Step $_.Exception.Message 'ERROR'
    Complete-AgentSecLog 1
    exit 1
}
