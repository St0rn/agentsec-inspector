# Installation Validation Matrix

État local au 2026-10-29. « Statique » signifie présence et relecture de structure, pas analyse par PowerShell. La CI Windows remplace cette matrice par des résultats d’exécution lors d’un run réussi.

| Script | Syntaxe | Exécution | Tests d’erreur | Résultat | Statut |
|---|---|---|---|---|---|
| install.ps1 | À vérifier sous PowerShell | Non exécutée | Non exécutés | Environnement sans Windows | Non validé |
| install-dev.ps1 | À vérifier sous PowerShell | Non exécutée | Non exécutés | Environnement sans Windows | Non validé |
| check-prerequisites.ps1 | À vérifier sous PowerShell | Non exécutée | Non exécutés | Environnement sans Windows | Non validé |
| setup-backend.ps1 | À vérifier sous PowerShell | Non exécutée | Non exécutés | Équivalent Python exécuté | Non validé Windows |
| setup-frontend.ps1 | À vérifier sous PowerShell | Non exécutée | Non exécutés | Équivalent npm exécuté | Non validé Windows |
| setup-database.ps1 | À vérifier sous PowerShell | Non exécutée | Non exécutés | Initialisation Python exécutée | Non validé Windows |
| start-dev.ps1 | À vérifier sous PowerShell | Non exécutée | Non exécutés | — | Non validé |
| start-production.ps1 | À vérifier sous PowerShell | Non exécutée | Non exécutés | — | Non validé |
| build-windows.ps1 | À vérifier sous PowerShell | Non exécutée | Non exécutés | Rust/Windows absents | Non validé |
| test-all.ps1 | À vérifier sous PowerShell | Non exécutée | Non exécutés | Tests appelés directement, réussis | Non validé Windows |
| verify-installation.ps1 | À vérifier sous PowerShell | Non exécutée | Non exécutés | — | Non validé |
| update.ps1 | À vérifier sous PowerShell | Non exécutée | Non exécutés | — | Non validé |
| backup.ps1 | À vérifier sous PowerShell | Non exécutée | Non exécutés | API backup testée | Non validé Windows |
| restore.ps1 | À vérifier sous PowerShell | Non exécutée | Non exécutés | Opération destructive non lancée | Non validé |
| uninstall.ps1 | À vérifier sous PowerShell | Non exécutée | Non exécutés | Opération destructive non lancée | Non validé |
| clean.ps1 | À vérifier sous PowerShell | Non exécutée | Non exécutés | — | Non validé |
