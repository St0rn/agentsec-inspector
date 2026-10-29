# Mise à jour

Vérifier l’empreinte et exécuter :

```powershell
Get-FileHash .\AgentSec-Inspector-1.1.0-setup.exe -Algorithm SHA256
.\scripts\update.ps1 -InstallerPath .\AgentSec-Inspector-1.1.0-setup.exe -TargetVersion 1.1.0
```

Le script refuse une version non supérieure, arrête en cas d’échec de sauvegarde, demande confirmation, installe, vérifie puis tente une restauration des données si la vérification échoue. Les migrations de schéma sont appliquées au démarrage par la couche de migration livrée avec la version.

Restauration manuelle :

```powershell
$backup = Get-ChildItem "$env:LOCALAPPDATA\AgentSec\backups\agentsec-backup-*.zip" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
.\scripts\restore.ps1 -BackupPath $backup.FullName -Confirmed
```
