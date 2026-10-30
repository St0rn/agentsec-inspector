$discoveryRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$scriptCases = Get-ChildItem (Join-Path $discoveryRepoRoot 'scripts') -Recurse -Filter *.ps1 |
    Where-Object { $_.FullName -notlike '*Scripts.Tests.ps1' } |
    ForEach-Object { @{ Path = $_.FullName; Name = $_.Name } }

BeforeAll {
    $script:RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
    . (Join-Path $script:RepoRoot 'scripts\lib\Common.ps1')
    $script:NativeTestDirectory = Join-Path $TestDrive 'native command with spaces'
    New-Item -ItemType Directory -Path $script:NativeTestDirectory | Out-Null
    $script:NativeHelper = Join-Path $script:NativeTestDirectory 'argument helper.py'
    @'
import json
import sys
sys.stderr.write("npm warn deprecated: controlled warning\n")
print(json.dumps(sys.argv[1:]))
'@ | Set-Content -LiteralPath $script:NativeHelper -Encoding UTF8
    $script:FailureHelper = Join-Path $script:NativeTestDirectory 'failure helper.py'
    'import sys; sys.stderr.write("controlled failure\n"); raise SystemExit(23)' | Set-Content -LiteralPath $script:FailureHelper -Encoding UTF8
    $script:BatchWrapper = Join-Path $script:NativeTestDirectory 'native wrapper.cmd'
    @'
@echo off
python "%~dp0argument helper.py" %*
'@ | Set-Content -LiteralPath $script:BatchWrapper -Encoding ASCII
}

Describe 'PowerShell delivery scripts' {
    $required = @(
        'install.ps1','install-dev.ps1','check-prerequisites.ps1','setup-backend.ps1',
        'setup-frontend.ps1','setup-database.ps1','start-dev.ps1','start-production.ps1',
        'build-windows.ps1','test-all.ps1','verify-installation.ps1','update.ps1',
        'backup.ps1','restore.ps1','uninstall.ps1','clean.ps1'
    ) | ForEach-Object { @{ Name = $_ } }
    It 'contains mandatory script <Name>' -ForEach $required {
        Test-Path (Join-Path $script:RepoRoot "scripts\$Name") | Should -BeTrue
    }

    It 'parses <Name> without syntax errors' -ForEach $scriptCases {
        $errors = $null
        [void][System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$null, [ref]$errors)
        $errors | Should -BeNullOrEmpty
    }

    It 'does not read the unavailable Win32_OperatingSystem.OSArchitecture property' {
        Get-Content -Raw (Join-Path $script:RepoRoot 'scripts\check-prerequisites.ps1') | Should -Not -Match '\.OSArchitecture'
    }

    It 'creates uniform prerequisite records under strict mode' {
        $check = New-PrerequisiteCheck -Name 'example' -Value '1.0' -Ok $true -Required $true -Details 'test'
        (@($check.PSObject.Properties.Name) -join ',') | Should -Be 'name,value,ok,required,details'
        $check.value | Should -Be '1.0'
        $check.ok | Should -BeTrue
    }

    It 'ignores unrelated uninstall registry entries under strict mode' {
        $entries = @(
            [pscustomobject]@{ PSPath = 'entry-without-display-name' },
            [pscustomobject]@{ DisplayName = 'Unrelated application' },
            [pscustomobject]@{ DisplayName = 'AgentSec Inspector'; UninstallString = 'controlled' }
        )
        $entry = Find-AgentSecUninstallEntry $entries
        $entry.DisplayName | Should -Be 'AgentSec Inspector'
        $entry.UninstallString | Should -Be 'controlled'
    }

    It 'finds the packaged desktop binary by its Cargo executable name' {
        $installRoot = Join-Path $TestDrive 'AgentSec Inspector'
        New-Item -ItemType Directory -Path $installRoot | Out-Null
        New-Item -ItemType File -Path (Join-Path $installRoot 'agentsec-inspector.exe') | Out-Null
        Find-AgentSecDesktopExecutable @($installRoot) | Should -Be (Join-Path $installRoot 'agentsec-inspector.exe')
    }

    It 'stops the standalone backend before launching the desktop sidecar' {
        $source = Get-Content -Raw (Join-Path $script:RepoRoot 'scripts\verify-installation.ps1')
        $stopIndex = $source.IndexOf('Remove-Item Env:AGENTSEC_PORT')
        $desktopIndex = $source.IndexOf('$desktop=Start-Process')
        $stopIndex | Should -BeGreaterThan -1
        $desktopIndex | Should -BeGreaterThan $stopIndex
        $source | Should -Match 'Wait-Process'
        $source | Should -Match '\$backendIdsInitial -notcontains \$_\.Id'
        $source | Should -Match '\$attempt -le 10'
    }

    It 'checks the desktop dynamic port, health endpoint, and Windows Tauri origin' {
        $source = Get-Content -Raw (Join-Path $script:RepoRoot 'scripts\verify-installation.ps1')
        $source | Should -Match 'Get-NetTCPConnection'
        $source | Should -Match 'desktop_dynamic_port'
        $source | Should -Match 'desktop_backend_health'
        $source | Should -Match 'http://tauri\.localhost'
        $source | Should -Match 'desktop_tauri_cors'
    }

    It 'returns a WebView2 result with stable properties' {
        $runtime = Get-WebView2Runtime
        @($runtime.PSObject.Properties.Name) | Should -Contain 'installed'
        @($runtime.PSObject.Properties.Name) | Should -Contain 'version'
        @($runtime.PSObject.Properties.Name) | Should -Contain 'registry_path'
    }

    It 'checks official WebView2 user and system registrations and reads the version' {
        $source = Get-Content -Raw (Join-Path $script:RepoRoot 'scripts\lib\Common.ps1')
        $source | Should -Match ([regex]::Escape('{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}'))
        $source | Should -Match 'HKLM:'
        $source | Should -Match 'HKCU:'
        $source | Should -Match "Properties\['pv'\]"
    }

    It 'preserves native arguments, spaces, quotes, and trailing slashes' {
        $expected = @('space value','embedded"quote','C:\Program Files\AgentSec\')
        $result = Invoke-Checked python (@($script:NativeHelper) + $expected)
        $actual = $result.StdOut | ConvertFrom-Json
        $actual[0] | Should -Be $expected[0]
        $actual[1] | Should -Be $expected[1]
        $actual[2] | Should -Be $expected[2]
        $result.ExitCode | Should -Be 0
    }

    It 'logs native stderr warnings without treating them as failure' {
        $result = Invoke-Checked python @($script:NativeHelper,'ok')
        $result.ExitCode | Should -Be 0
        $result.StdErr | Should -Match 'npm warn deprecated'
    }

    It 'can consume sensitive command output without copying it to logs' {
        Mock Write-Step {}
        $result = Invoke-Checked python @($script:NativeHelper,'controlled-secret') -SuppressOutputLogging
        $result.StdOut | Should -Match 'controlled-secret'
        Should -Invoke Write-Step -ParameterFilter { $Message -match 'stdout|stderr|controlled-secret' } -Times 0
    }

    It 'runs a batch command from a path containing spaces' {
        $result = Invoke-Checked $script:BatchWrapper @('space value')
        $result.StdOut.Trim() | Should -Be '["space value"]'
    }

    It 'blocks on the real nonzero native exit code' {
        { Invoke-Checked python @($script:FailureHelper) } | Should -Throw '*exited with code 23*'
    }

    It 'accepts only explicitly allowed nonzero native exit codes' {
        $result = Invoke-Checked python @($script:FailureHelper) -AllowedExitCodes @(0,23)
        $result.ExitCode | Should -Be 23
    }

    It 'requires distinct MSI and NSIS artifact directories' {
        $source = Get-Content -Raw (Join-Path $script:RepoRoot 'scripts\build-windows.ps1')
        $source | Should -Match 'msiDirectory=Join-Path \$bundle'
        $source | Should -Match 'nsisDirectory=Join-Path \$bundle'
        $source | Should -Match 'MSI installer was not generated'
        $source | Should -Match 'NSIS installer was not generated'
    }

    It '<Name> uses strict error handling' -ForEach $scriptCases {
        if ($Path -notmatch '\\(tests|ci|lib)\\') { Get-Content -Raw $Path | Should -Match 'try\s*\{' }
    }

    It 'rejects restore without explicit confirmation' {
        $hostExecutable=(Get-Process -Id $PID).Path
        $restoreScript=Join-Path $script:RepoRoot 'scripts\restore.ps1'
        $result=Invoke-Checked $hostExecutable @('-NoLogo','-NoProfile','-ExecutionPolicy','Bypass','-File',$restoreScript,'-BackupPath','missing.zip') -AllowedExitCodes @(0,1)
        $result.ExitCode | Should -Be 1
    }

    It 'initializes the database idempotently' {
        $testData = Join-Path $TestDrive 'data'
        $hostExecutable=(Get-Process -Id $PID).Path
        $databaseScript=Join-Path $script:RepoRoot 'scripts\setup-database.ps1'
        $arguments=@('-NoLogo','-NoProfile','-ExecutionPolicy','Bypass','-File',$databaseScript,'-DataDir',$testData)
        (Invoke-Checked $hostExecutable $arguments).ExitCode | Should -Be 0
        (Invoke-Checked $hostExecutable $arguments).ExitCode | Should -Be 0
        Test-Path (Join-Path $testData 'agentsec.db') | Should -BeTrue
    }
}
