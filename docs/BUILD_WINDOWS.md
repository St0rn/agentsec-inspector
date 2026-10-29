# Compilation Windows x64

## Build reproductible

Dans un terminal PowerShell x64 :

```powershell
.\scripts\check-prerequisites.ps1 -ForBuild
.\scripts\install-dev.ps1
.\scripts\build-windows.ps1
```

Le script exécute lint et tests, compile React, génère le backend PyInstaller autonome, crée les icônes, intègre le sidecar et lance Tauri pour produire MSI et NSIS. Les artefacts attendus se trouvent sous :

```text
src-tauri\target\x86_64-pc-windows-msvc\release\bundle\msi\
src-tauri\target\x86_64-pc-windows-msvc\release\bundle\nsis\
```

Le rapport avec empreintes est `logs\build\windows-build-report.json`.

## Validation après build

```powershell
$msi = Get-ChildItem .\src-tauri\target\x86_64-pc-windows-msvc\release\bundle -Recurse -Filter *.msi | Select-Object -First 1
Start-Process msiexec -ArgumentList @('/i', $msi.FullName) -Wait
.\scripts\verify-installation.ps1
```

Une compilation réussie ne vaut pas validation d’installation. Seul le rapport de `verify-installation.ps1` avec `success: true` constitue le smoke test Windows.
