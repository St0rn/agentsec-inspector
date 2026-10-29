# Installation Validation Matrix

État au 2026-10-29. « Syntaxe PS7 » signifie que le fichier a été chargé sans erreur par le parseur PowerShell 7 dans un conteneur Linux; cela ne constitue pas une exécution Windows. Les résultats Linux CI cités proviennent du run GitHub Actions `40916996042`; PowerShell 5.1, MSVC et les installateurs Windows restent non validés tant qu’un run Windows réussi n’est pas disponible.

| Script | Syntaxe | Exécution | Tests d’erreur | Résultat | Statut |
|---|---|---|---|---|---|
| install.ps1 | Syntaxe PS7 réussie | Non exécutée | Cas prévus par Pester, non exécutés localement | Environnement sans Windows | Non validé Windows |
| install-dev.ps1 | Syntaxe PS7 réussie | Non exécutée | Venv incomplet traité dans le code | Environnement sans Windows | Non validé Windows |
| check-prerequisites.ps1 | Syntaxe PS7 réussie | Non exécutée | Tests Pester fournis | Sonde MSVC/SDK non exécutable sous Linux | Non validé Windows |
| setup-backend.ps1 | Syntaxe PS7 réussie | Non exécutée | Venv absent/incomplet couvert | Équivalent Python exécuté | Non validé Windows |
| setup-frontend.ps1 | Syntaxe PS7 réussie | Non exécutée | `stderr` natif couvert par Pester fourni | Équivalent npm exécuté | Non validé Windows |
| setup-database.ps1 | Syntaxe PS7 réussie | Non exécutée | Idempotence Pester fournie | Initialisation Python exécutée directement | Non validé Windows |
| start-dev.ps1 | Syntaxe PS7 réussie | Non exécutée | Non exécutés | — | Non validé Windows |
| start-production.ps1 | Syntaxe PS7 réussie | Non exécutée | Installation absente couverte dans le code | — | Non validé Windows |
| build-windows.ps1 | Syntaxe PS7 réussie | Non exécutée | MSI/NSIS manquants bloquants | Rust/MSVC Windows absents | Non validé Windows |
| test-all.ps1 | Syntaxe PS7 réussie | Non exécutée | Seuils bloquants | Tests appelés directement, réussis | Non validé Windows |
| verify-installation.ps1 | Syntaxe PS7 réussie | Non exécutée | Rapport d’échec prévu | — | Non validé Windows |
| update.ps1 | Syntaxe PS7 réussie | Non exécutée | Backup/rollback prévus | — | Non validé Windows |
| backup.ps1 | Syntaxe PS7 réussie | Non exécutée | Données absentes couvertes | API backup testée | Non validé Windows |
| restore.ps1 | Syntaxe PS7 réussie | Non exécutée | Confirmation obligatoire fournie | Opération destructive non lancée | Non validé Windows |
| uninstall.ps1 | Syntaxe PS7 réussie | Non exécutée | Suppression des données doublement confirmée | Opération destructive non lancée | Non validé Windows |
| clean.ps1 | Syntaxe PS7 réussie | Non exécutée | Cibles bornées au dépôt | — | Non validé Windows |

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
| update.sh | Bash `-n` réussi | Chemins sans changement/downgrade testés | Downgrade refusé | Contrôles de version réussis | Partiel — AppImage CI attendue |
| uninstall.sh | Bash `-n` réussi | Exécutée en environnement isolé | Confirmation suppression testée | Conservation/suppression explicite réussies | Validé localement |
| build-linux.sh | Bash `-n` et ShellCheck réussis | AppImage et DEB construits en CI | Dépendances locales absentes | Artefacts `agentsec-linux-x64` publiés | Validé Linux CI |
| start-production.sh | Bash `-n` réussi | Non exécutée avec AppImage réelle | Installation absente couverte | — | Non validé jusqu’à la CI |
| clean.sh | Bash `-n` réussi | Non exécutée | Cibles bornées au dépôt | — | Statique uniquement |
