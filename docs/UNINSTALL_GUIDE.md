# Désinstallation

Par défaut, les projets, preuves et rapports sont conservés :

```powershell
.\scripts\uninstall.ps1
```

Pour supprimer aussi les données, deux confirmations sont exigées :

```powershell
.\scripts\uninstall.ps1 -DeleteUserData -Confirmed
```

PowerShell affiche une confirmation à impact élevé. Cette suppression est irréversible hors sauvegarde. Créer une archive avant :

```powershell
.\scripts\backup.ps1
```
