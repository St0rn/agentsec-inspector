# Installation Validation Matrix

État au 2026-10-29. « Statique » signifie présence et relecture de structure, pas analyse par PowerShell. Les résultats Linux CI cités proviennent du run GitHub Actions `40916996042`; Windows reste non validé.

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
