BeforeAll {
    $script:RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
    $script:Files = Get-ChildItem (Join-Path $script:RepoRoot 'scripts') -Recurse -Filter *.ps1 | Where-Object { $_.FullName -notlike '*Scripts.Tests.ps1' }
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

    $scriptCases = $script:Files | ForEach-Object { @{ Path = $_.FullName; Name = $_.Name } }
    It 'parses <Name> without syntax errors' -ForEach $scriptCases {
        $errors = $null
        [void][System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$null, [ref]$errors)
        $errors | Should -BeNullOrEmpty
    }

    It '<Name> uses strict error handling' -ForEach $scriptCases {
        if ($Path -notmatch '\\(tests|ci|lib)\\') { Get-Content -Raw $Path | Should -Match 'try\s*\{' }
    }

    It 'rejects restore without explicit confirmation' {
        & (Join-Path $script:RepoRoot 'scripts\restore.ps1') -BackupPath 'missing.zip'
        $LASTEXITCODE | Should -Not -Be 0
    }

    It 'initializes the database idempotently' {
        $testData = Join-Path $TestDrive 'data'
        & (Join-Path $script:RepoRoot 'scripts\setup-database.ps1') -DataDir $testData
        $LASTEXITCODE | Should -Be 0
        & (Join-Path $script:RepoRoot 'scripts\setup-database.ps1') -DataDir $testData
        $LASTEXITCODE | Should -Be 0
        Test-Path (Join-Path $testData 'agentsec.db') | Should -BeTrue
    }
}
