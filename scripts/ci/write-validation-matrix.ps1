[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$scripts=@(
    'install.ps1','install-dev.ps1','check-prerequisites.ps1','setup-backend.ps1',
    'setup-frontend.ps1','setup-database.ps1','start-dev.ps1','start-production.ps1',
    'build-windows.ps1','test-all.ps1','verify-installation.ps1','update.ps1',
    'backup.ps1','restore.ps1','uninstall.ps1','clean.ps1'
)

function Test-Evidence {
    param([string]$RelativePath)
    return Test-Path -LiteralPath (Join-Path $root $RelativePath)
}

$syntaxOk=Test-Evidence 'logs\tests\powershell-static.ok'
$pesterOk=(Test-Evidence 'logs\tests\pester-pwsh.ok') -and (Test-Evidence 'logs\tests\pester-windows-powershell.ok')
$buildOk=Test-Evidence 'logs\build\windows-build-report.json'
$verifyOk=Test-Evidence 'logs\tests\installation-verification.json'
$msiOk=Test-Evidence 'logs\tests\msi-install-twice.ok'
$nsisOk=Test-Evidence 'logs\tests\nsis-install-twice.ok'
$msiUninstallOk=Test-Evidence 'logs\tests\msi-uninstall.ok'
$nsisUninstallOk=Test-Evidence 'logs\tests\nsis-uninstall.ok'

$rows=@(
    '# Installation Validation Matrix',
    '',
    "Generated from Windows CI evidence at $(Get-Date -Format o). A missing evidence file remains non-validated.",
    '',
    "| Script | Syntaxe | Exécution | Tests d'erreur | Résultat | Statut |",
    '|---|---|---|---|---|---|'
)
foreach($name in $scripts){
    $syntax=if($syntaxOk){'PowerShell 5.1/7 + PSScriptAnalyzer réussis'}else{'Preuve absente'}
    $execution='Non exécutée dans ce job'
    $errors=if($pesterOk){'Régressions Pester réussies'}else{'Preuve Pester absente'}
    $result='—'
    $status='Non validé par ce job'

    if($name -eq 'check-prerequisites.ps1' -and (Test-Evidence 'logs\installation\prerequisites.json')){
        $execution='Exécutée avec -ForBuild'
        $result='MSVC/SDK et compilation C++ minimale réussis'
        $status='Validé CI Windows'
    }
    elseif($name -eq 'setup-database.ps1' -and $pesterOk){
        $execution='Exécutée deux fois en répertoire isolé'
        $result='Migration SQLite idempotente'
        $status='Validé CI Windows'
    }
    elseif($name -eq 'build-windows.ps1' -and $buildOk){
        $execution='Exécutée'
        $result='Backend, MSI et NSIS produits avec SHA-256'
        $status='Validé CI Windows'
    }
    elseif($name -eq 'test-all.ps1' -and $buildOk){
        $execution='Exécutée par build-windows.ps1'
        $result='Quality gates bloquants réussis'
        $status='Validé CI Windows'
    }
    elseif($name -eq 'verify-installation.ps1' -and $verifyOk -and $msiOk -and $nsisOk){
        $execution='Exécutée après MSI et NSIS, deux fois chacun'
        $result='API, SQLite, auth, logs, desktop et sidecar vérifiés'
        $status='Validé CI Windows'
    }
    elseif($name -eq 'install.ps1' -and $msiOk -and $nsisOk){
        $execution='MSI et NSIS installés deux fois'
        $result='Réexécution sans corruption'
        $status='Validé CI Windows'
    }
    elseif($name -eq 'uninstall.ps1' -and $msiUninstallOk -and $nsisUninstallOk){
        $execution='Exécutée pour MSI et NSIS'
        $result='Données utilisateur préservées'
        $status='Validé CI Windows'
    }
    elseif($pesterOk -and $name -eq 'restore.ps1'){
        $execution='Chemin de refus exécuté'
        $result='Confirmation obligatoire vérifiée'
        $status='Partiel'
    }
    elseif($syntaxOk){
        $status='Statique uniquement'
    }
    $rows+="| $name | $syntax | $execution | $errors | $result | $status |"
}
$rows|Set-Content -Encoding UTF8 (Join-Path $root 'INSTALLATION_VALIDATION_MATRIX.md')
