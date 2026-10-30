# Installation Validation Matrix

État au 2026-10-30. Preuve Windows 1.1.0 : [run GitHub Actions `41108334253`](https://github.com/St0rn/agentsec-inspector/actions/runs/41108334253), runner `windows-2022`, succès sur le commit `791cb580dee5fda3308e564c7882b8c233463195`. « Statique uniquement » signifie que le script a été analysé sous PowerShell 5.1/7 et PSScriptAnalyzer, mais que son chemin nominal complet n’a pas été exécuté dans ce job. Les résultats Linux CI proviennent du [run `41108334280`](https://github.com/St0rn/agentsec-inspector/actions/runs/41108334280).

| Script | Syntaxe | Exécution | Tests d’erreur | Résultat | Statut |
|---|---|---|---|---|---|
| install.ps1 | PowerShell 5.1/7 + PSScriptAnalyzer réussis | MSI ×2 et NSIS ×2 | Réexécution/idempotence vérifiée | Quatre installations avec vérification réussies | Validé CI Windows |
| install-dev.ps1 | PowerShell 5.1/7 + PSScriptAnalyzer réussis | Non exécutée dans ce job | Venv incomplet couvert par Pester | — | Statique + régression ciblée |
| check-prerequisites.ps1 | PowerShell 5.1/7 + PSScriptAnalyzer réussis | Exécutée avec `-ForBuild` | Détections strictes couvertes par Pester | WebView2, MSVC x64, SDK, headers et probe C++ réussis | Validé CI Windows |
| setup-backend.ps1 | PowerShell 5.1/7 + PSScriptAnalyzer réussis | Non exécutée séparément | Venv absent/incomplet couvert | Backend verrouillé construit par PyInstaller | Statique + intégration build |
| setup-frontend.ps1 | PowerShell 5.1/7 + PSScriptAnalyzer réussis | Non exécutée séparément | `stderr`/codes natifs couverts | Frontend construit dans `build-windows.ps1` | Statique + intégration build |
| setup-database.ps1 | PowerShell 5.1/7 + PSScriptAnalyzer réussis | Exécutée deux fois sous PS7 et deux fois sous PS5.1 | Idempotence et intégrité SQLite | Migration idempotente réussie | Validé CI Windows |
| start-dev.ps1 | PowerShell 5.1/7 + PSScriptAnalyzer réussis | Non exécutée dans ce job | Contrôle statique | — | Statique uniquement |
| start-production.ps1 | PowerShell 5.1/7 + PSScriptAnalyzer réussis | Non exécutée directement | Découverte du vrai binaire packagé couverte | Desktop lancé par `verify-installation.ps1` | Statique + intégration install |
| build-windows.ps1 | PowerShell 5.1/7 + PSScriptAnalyzer réussis | Exécutée | Absence MSI/NSIS bloquante | Backend, MSI et NSIS produits avec SHA-256 | Validé CI Windows |
| test-all.ps1 | PowerShell 5.1/7 + PSScriptAnalyzer réussis | Exécutée par le build | Seuils qualité bloquants | Backend/frontend/lint/typage réussis | Validé CI Windows |
| verify-installation.ps1 | PowerShell 5.1/7 + PSScriptAnalyzer réussis | MSI ×2 et NSIS ×2 | Auth 401, processus et nettoyage contrôlés | Fichiers, API, port dynamique, CORS Tauri, SQLite, CRUD, logs, desktop et sidecar réussis | Validé CI Windows |
| update.ps1 | PowerShell 5.1/7 + PSScriptAnalyzer réussis | Non exécutée dans ce job | Backup/migration/rollback analysés | — | Statique uniquement |
| backup.ps1 | PowerShell 5.1/7 + PSScriptAnalyzer réussis | Non exécutée dans ce job | Données absentes analysées | API backup couverte séparément | Statique uniquement Windows |
| restore.ps1 | PowerShell 5.1/7 + PSScriptAnalyzer réussis | Chemin de refus exécuté | Confirmation obligatoire vérifiée | Restauration nominale non lancée sur Windows | Partiel |
| uninstall.ps1 | PowerShell 5.1/7 + PSScriptAnalyzer réussis | Exécutée après MSI et NSIS | Données utilisateur préservées par défaut | Deux désinstallations réussies | Validé CI Windows |
| clean.ps1 | PowerShell 5.1/7 + PSScriptAnalyzer réussis | Non exécutée dans ce job | Cibles bornées au dépôt | — | Statique uniquement |

## Scripts Linux

| Script | Syntaxe | Exécution | Tests d’erreur | Résultat | Statut |
|---|---|---|---|---|---|
| check-prerequisites.sh | Bash `-n` réussi | Exécutée | Dépendances build absentes | Prérequis standard OK, message build exploitable | Validé localement |
| install-dev.sh | Bash `-n` réussi | Exécutée deux fois | Prérequis séparés | Dépendances verrouillées, DB intègre | Validé localement |
| setup-database.sh | Bash `-n` réussi | Exécutée plusieurs fois | Venv absent couvert | Migration idempotente | Validé localement |
| start-dev.sh | Bash `-n` réussi | Exécutée | Auth sans jeton testée | Backend, frontend et arrêt propre OK | Validé localement |
| test-all.sh | Bash `-n` réussi | Exécutée | Seuils bloquants | Tous les contrôles réussis | Validé localement |
| test-scripts.sh | Bash `-n` réussi | Exécutée | Confirmation, downgrade, artefact invalide | Tous les cas isolés réussis | Validé localement |
| backup.sh | Bash `-n` réussi | Exécutée | Données absentes couvertes | Archive et SHA-256 créés | Validé localement |
| restore.sh | Bash `-n` réussi | Exécutée | Confirmation obligatoire | SQLite intègre, ancienne donnée préservée | Validé localement |
| install.sh | Bash `-n` et ShellCheck réussis | AppImage réelle installée deux fois en CI | Artefact manquant/invalide | Copie atomique, checksum et idempotence vérifiés | Validé Linux CI |
| verify-installation.sh | Bash `-n` et ShellCheck réussis | AppImage réelle vérifiée deux fois en CI | Rejet d’artefact invalide | Backend embarqué, auth, DB, CRUD et JSONL vérifiés | Validé Linux CI |
| update.sh | Bash `-n` réussi | Chemins sans changement/downgrade testés | Downgrade refusé | Contrôles de version réussis | Partiel |
| uninstall.sh | Bash `-n` réussi | Exécutée en environnement isolé | Confirmation suppression testée | Conservation/suppression explicite réussies | Validé localement |
| build-linux.sh | Bash `-n` et ShellCheck réussis | AppImage et DEB construits en CI | Dépendances locales absentes | Artefacts `agentsec-linux-x64` publiés | Validé Linux CI |
| start-production.sh | Bash `-n` réussi | AppImage lancée par la vérification CI | Installation absente couverte | Backend embarqué observé | Validé par intégration CI |
| clean.sh | Bash `-n` réussi | Non exécutée | Cibles bornées au dépôt | — | Statique uniquement |
