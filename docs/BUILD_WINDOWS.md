# Compilation Windows x64

## Build reproductible

Dans un terminal PowerShell x64 :

```powershell
.\scripts\check-prerequisites.ps1 -ForBuild
.\scripts\install-dev.ps1
.\scripts\build-windows.ps1
```

Le premier contrôle charge `vcvars64.bat`, vérifie `cl.exe`, `link.exe`, `rc.exe`, `mt.exe`, `INCLUDE`, `LIB`, les headers MSVC/Windows SDK et compile réellement un programme C++ minimal. Il détecte ainsi une installation SDK incomplète avant le build Rust.

Le build exécute lint et tests, compile React, génère le backend PyInstaller autonome, compare l’empreinte du sidecar copié, crée les icônes et lance Tauri pour produire **les deux** installateurs. Les artefacts attendus se trouvent exactement sous :

```text
src-tauri\target\x86_64-pc-windows-msvc\release\bundle\msi\
src-tauri\target\x86_64-pc-windows-msvc\release\bundle\nsis\
```

Le rapport avec empreintes est `logs\build\windows-build-report.json`.

Pour construire sans relancer les tests uniquement après un passage réussi dans la même session contrôlée :

```powershell
.\scripts\build-windows.ps1 -SkipTests
```

Ne pas utiliser cette option pour une release.

## Validation après build

```powershell
$msi = Get-ChildItem .\src-tauri\target\x86_64-pc-windows-msvc\release\bundle -Recurse -Filter *.msi | Select-Object -First 1
Start-Process msiexec -ArgumentList @('/i', $msi.FullName) -Wait
.\scripts\verify-installation.ps1
```

Une compilation réussie ne vaut pas validation d’installation. Seul le rapport de `verify-installation.ps1` avec `success: true` constitue le smoke test Windows.

Le workflow `.github\workflows\windows-build.yml` effectue en plus l’analyse PowerShell, les tests Pester sous PowerShell 5.1 et 7, deux installations successives du MSI, sa désinstallation, deux installations successives du NSIS, sa désinstallation et la génération des SHA-256.

Preuve de référence pour la version 1.1.0 : [run Windows x64 `41108334253`](https://github.com/St0rn/agentsec-inspector/actions/runs/41108334253), succès complet sur `windows-2022`, avec [artefact MSI/NSIS et journaux](https://github.com/St0rn/agentsec-inspector/actions/runs/41108334253/artifacts/13001844123).
