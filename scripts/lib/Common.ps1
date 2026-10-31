Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:AgentSecVersion = '1.2.0'
$script:RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$script:LogPath = $null

function Initialize-AgentSecLog {
    param([Parameter(Mandatory)][string]$Category, [Parameter(Mandatory)][string]$ScriptName)
    $directory = Join-Path $script:RepoRoot "logs\$Category"
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $script:LogPath = Join-Path $directory "$($ScriptName.Replace('.ps1',''))-$stamp.log"
    "$(Get-Date -Format o) | START | $ScriptName | AgentSec $script:AgentSecVersion" | Set-Content -Encoding UTF8 $script:LogPath
    return $script:LogPath
}

function Write-Step {
    param([string]$Message, [ValidateSet('INFO','OK','WARN','ERROR')][string]$Level = 'INFO')
    $line = "$(Get-Date -Format o) | $Level | $Message"
    Write-Host $line
    if ($script:LogPath) { Add-Content -Encoding UTF8 -Path $script:LogPath -Value $line }
}

function ConvertTo-NativeArgument {
    param([AllowEmptyString()][string]$Argument)
    if ($Argument.Length -gt 0 -and $Argument -notmatch '[\s"]') { return $Argument }

    $builder = New-Object System.Text.StringBuilder
    [void]$builder.Append('"')
    $slashes = 0
    foreach ($character in $Argument.ToCharArray()) {
        if ($character -eq '\') {
            $slashes++
            continue
        }
        if ($character -eq '"') {
            if ($slashes -gt 0) { [void]$builder.Append(('\' * ($slashes * 2))) }
            [void]$builder.Append('\"')
        } else {
            if ($slashes -gt 0) { [void]$builder.Append(('\' * $slashes)) }
            [void]$builder.Append($character)
        }
        $slashes = 0
    }
    if ($slashes -gt 0) { [void]$builder.Append(('\' * ($slashes * 2))) }
    [void]$builder.Append('"')
    return $builder.ToString()
}

function Resolve-NativeCommand {
    param([Parameter(Mandatory)][string]$FilePath)
    if (Test-Path -LiteralPath $FilePath -PathType Leaf) {
        return (Resolve-Path -LiteralPath $FilePath).Path
    }
    $command = Get-Command $FilePath -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $command) { throw "Native command not found: $FilePath" }
    return $command.Source
}

function Invoke-Checked {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = $script:RepoRoot,
        [int[]]$AllowedExitCodes = @(0),
        [switch]$SuppressOutputLogging
    )

    $resolved = Resolve-NativeCommand $FilePath
    $displayArguments = @($Arguments | ForEach-Object { ConvertTo-NativeArgument ([string]$_) })
    if ($SuppressOutputLogging) {
        Write-Step "Execute: $resolved [arguments and output logging suppressed]"
    } else {
        Write-Step "Execute: $resolved $($displayArguments -join ' ')"
    }

    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $extension = [IO.Path]::GetExtension($resolved).ToLowerInvariant()
    if ($extension -in @('.cmd', '.bat')) {
        if (-not $env:ComSpec) { throw 'The Windows command processor is unavailable.' }
        $startInfo.FileName = $env:ComSpec
        $batchLine = @((ConvertTo-NativeArgument $resolved)) + $displayArguments
        $startInfo.Arguments = '/d /s /c "' + ($batchLine -join ' ') + '"'
    } else {
        $startInfo.FileName = $resolved
        $startInfo.Arguments = $displayArguments -join ' '
    }
    $startInfo.WorkingDirectory = (Resolve-Path -LiteralPath $WorkingDirectory).Path
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    try {
        if (-not $process.Start()) { throw "Unable to start native command: $resolved" }
        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()
        $process.WaitForExit()
        $stdout = $stdoutTask.GetAwaiter().GetResult()
        $stderr = $stderrTask.GetAwaiter().GetResult()
        $exitCode = $process.ExitCode
    } finally {
        $process.Dispose()
    }

    if (-not $SuppressOutputLogging) {
        foreach ($line in @($stdout -split "`r?`n" | Where-Object { $_ })) { Write-Step "  stdout | $line" }
        foreach ($line in @($stderr -split "`r?`n" | Where-Object { $_ })) { Write-Step "  stderr | $line" 'WARN' }
    }

    $result = [pscustomobject][ordered]@{
        FilePath = $resolved
        ExitCode = $exitCode
        StdOut = $stdout
        StdErr = $stderr
    }
    if ($AllowedExitCodes -notcontains $exitCode) {
        $message = "$resolved exited with code $exitCode"
        if ($stderr) { $message += ": $($stderr.Trim())" }
        throw $message
    }
    return $result
}

function Assert-Windows {
    if ($PSVersionTable.PSEdition -eq 'Core' -and -not $IsWindows) { throw 'This operation requires Windows.' }
}

function Get-WindowsArchitecture {
    if (-not [Environment]::Is64BitOperatingSystem) { return 'X86' }
    $reported = [string]$env:PROCESSOR_ARCHITEW6432
    if (-not $reported) { $reported = [string]$env:PROCESSOR_ARCHITECTURE }
    if ($reported -match 'ARM64') { return 'Arm64' }
    return 'X64'
}

function New-PrerequisiteCheck {
    param(
        [Parameter(Mandatory)][string]$Name,
        [AllowNull()][object]$Value,
        [Parameter(Mandatory)][bool]$Ok,
        [bool]$Required = $false,
        [string]$Details = ''
    )
    return [pscustomobject][ordered]@{
        name = $Name
        value = $Value
        ok = $Ok
        required = $Required
        details = $Details
    }
}

function Get-WebView2Runtime {
    # Microsoft WebView2 Evergreen Runtime product identifier documented at:
    # https://learn.microsoft.com/microsoft-edge/webview2/concepts/distribution
    $clientId = '{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}'
    $keys = @(
        "HKLM:\SOFTWARE\Microsoft\EdgeUpdate\Clients\$clientId",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\$clientId",
        "HKCU:\SOFTWARE\Microsoft\EdgeUpdate\Clients\$clientId",
        "HKCU:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\$clientId"
    )
    foreach ($key in $keys) {
        if (-not (Test-Path -LiteralPath $key)) { continue }
        $item = Get-ItemProperty -LiteralPath $key -ErrorAction SilentlyContinue
        if (-not $item) { continue }
        $versionProperty = $item.PSObject.Properties['pv']
        if (-not $versionProperty) { $versionProperty = $item.PSObject.Properties['version'] }
        $version = if ($versionProperty) { [string]$versionProperty.Value } else { '' }
        if ($version -and $version -ne '0.0.0.0') {
            return [pscustomobject]@{ installed = $true; version = $version; registry_path = $key }
        }
    }
    return [pscustomobject]@{ installed = $false; version = $null; registry_path = $null }
}

function Get-VsWherePath {
    $candidate = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
    if (Test-Path -LiteralPath $candidate) { return $candidate }
    $command = Get-Command vswhere.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($command) { return $command.Source }
    return $null
}

function Get-MsvcInstallation {
    $vswhere = Get-VsWherePath
    if (-not $vswhere) { return $null }
    $result = Invoke-Checked $vswhere @(
        '-latest', '-products', '*',
        '-requires', 'Microsoft.VisualStudio.Component.VC.Tools.x86.x64',
        '-property', 'installationPath'
    )
    $path = $result.StdOut.Trim()
    if (-not $path) { return $null }
    return $path
}

function Import-MsvcEnvironment {
    param([string]$InstallationPath)
    if (-not $InstallationPath) { $InstallationPath = Get-MsvcInstallation }
    if (-not $InstallationPath) { throw 'Visual Studio C++ Build Tools were not found.' }
    $vcvars = Join-Path $InstallationPath 'VC\Auxiliary\Build\vcvars64.bat'
    if (-not (Test-Path -LiteralPath $vcvars)) { throw "MSVC x64 environment script is missing: $vcvars" }
    $bootstrap = Join-Path $env:TEMP ("agentsec-vcvars-" + [guid]::NewGuid().ToString('N') + '.cmd')
    try {
        @(
            '@echo off',
            "call `"$vcvars`" >nul",
            'if errorlevel 1 exit /b %errorlevel%',
            'set'
        ) | Set-Content -LiteralPath $bootstrap -Encoding ASCII
        # `set` returns the complete process environment, which can contain CI
        # credentials. Consume it in memory without copying it to logs.
        $result = Invoke-Checked $bootstrap -SuppressOutputLogging
        foreach ($line in $result.StdOut -split "`r?`n") {
            if ($line -notmatch '^([^=]+)=(.*)$') { continue }
            [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], 'Process')
        }
    } finally {
        if (Test-Path -LiteralPath $bootstrap) { Remove-Item -LiteralPath $bootstrap -Force }
    }
    if (-not $env:INCLUDE -or -not $env:LIB) {
        throw 'vcvars64.bat completed but did not provide INCLUDE and LIB.'
    }
    return $InstallationPath
}

function Get-AgentSecDataDir {
    if ($env:AGENTSEC_DATA_DIR) { return $env:AGENTSEC_DATA_DIR }
    return (Join-Path $env:LOCALAPPDATA 'AgentSec')
}

function Find-AgentSecUninstallEntry {
    param([AllowEmptyCollection()][object[]]$Entries = @())
    return $Entries |
        Where-Object {
            $displayName = $_.PSObject.Properties['DisplayName']
            $displayName -and [string]$displayName.Value -eq 'AgentSec Inspector'
        } |
        Select-Object -First 1
}

function Find-AgentSecDesktopExecutable {
    param([AllowEmptyCollection()][string[]]$Roots = @())
    $binaryNames = @('agentsec-inspector.exe', 'AgentSec Inspector.exe')
    foreach ($root in @($Roots | Where-Object { $_ } | Select-Object -Unique)) {
        if (-not (Test-Path -LiteralPath $root -PathType Container)) { continue }
        foreach ($binaryName in $binaryNames) {
            $candidate = Get-ChildItem -LiteralPath $root -Recurse -File -Filter $binaryName -ErrorAction SilentlyContinue |
                Select-Object -First 1
            if ($candidate) { return $candidate.FullName }
        }
    }
    return $null
}

function Get-CommandVersion {
    param([string]$Name, [string[]]$Arguments = @('--version'))
    try {
        $result = Invoke-Checked $Name $Arguments
        $firstLine = @($result.StdOut -split "`r?`n" | Where-Object { $_ } | Select-Object -First 1)
        if ($firstLine.Count) { return ([string]$firstLine[0]).Trim() }
        $firstError = @($result.StdErr -split "`r?`n" | Where-Object { $_ } | Select-Object -First 1)
        if ($firstError.Count) { return ([string]$firstError[0]).Trim() }
        return 'present (version unavailable)'
    } catch {
        return $null
    }
}

function Stop-AgentSecProcesses {
    $processes = Get-Process 'AgentSec Inspector','agentsec-backend*' -ErrorAction SilentlyContinue
    foreach ($process in $processes) { if ($process.MainWindowHandle -ne 0) { [void]$process.CloseMainWindow() } }
    if ($processes) { Start-Sleep -Seconds 3 }
    foreach ($process in $processes) { if (-not $process.HasExited) { Stop-Process -Id $process.Id -Force } }
}

function Complete-AgentSecLog {
    param([int]$ExitCode)
    Write-Step "END | exit_code=$ExitCode" $(if ($ExitCode -eq 0) {'OK'} else {'ERROR'})
}
