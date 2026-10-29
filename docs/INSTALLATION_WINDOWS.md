# Installation Windows

## Compatibilité

- Windows 10 22H2 ou Windows 11, x64
- WebView2 Runtime (l’installateur Tauri peut proposer le bootstrapper Microsoft avec consentement)
- 500 Mo d’espace libre minimum, davantage pour les preuves et rapports
- Aucun Python, Node.js ou Rust requis sur le poste final

## Installation par paquet

1. Télécharger le `.msi` ou le programme `-setup.exe` depuis une release approuvée.
2. Vérifier son empreinte publiée :

```powershell
Get-FileHash .\AgentSec-Inspector_1.0.0_x64_en-US.msi -Algorithm SHA256
```

3. Depuis la racine du dépôt de livraison :

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install.ps1 -InstallerPath .\AgentSec-Inspector_1.0.0_x64_en-US.msi
```

Le script demande une confirmation, installe le paquet puis exécute un contrôle fonctionnel. Il ne désactive aucune protection Windows et n’installe aucun logiciel tiers silencieusement.

## Données

Les projets, preuves, rapports, sauvegardes, journaux et secrets chiffrés sont placés sous `%LOCALAPPDATA%\AgentSec`. Le backend n’écoute que sur une adresse de bouclage et utilise un jeton éphémère fourni à l’interface par IPC Tauri.

## Vérification autonome

```powershell
.\scripts\verify-installation.ps1
if ($LASTEXITCODE -ne 0) { throw 'AgentSec installation invalid' }
Get-Content .\logs\tests\installation-verification.json
```

La vérification crée un répertoire temporaire et un projet temporaire, teste l’authentification, la base, l’API, les journaux et le démarrage desktop, puis supprime les données temporaires.
