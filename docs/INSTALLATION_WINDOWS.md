# Installation Windows

## Compatibilité

- Windows 10 22H2 ou Windows 11, x64
- WebView2 Runtime (l’installateur Tauri peut proposer le bootstrapper Microsoft avec consentement)
- 500 Mo d’espace libre minimum, davantage pour les preuves et rapports
- Aucun Python, Node.js ou Rust requis sur le poste final

## Installation par paquet

1. Télécharger le [MSI x64](https://github.com/St0rn/agentsec-inspector/releases/download/v1.0.1/AgentSec-Inspector_1.0.1_x64_en-US.msi) ou le [programme NSIS x64](https://github.com/St0rn/agentsec-inspector/releases/download/v1.0.1/AgentSec-Inspector_1.0.1_x64-setup.exe) de la version 1.0.1.
2. Vérifier son empreinte publiée :

```powershell
Get-FileHash '.\AgentSec-Inspector_1.0.1_x64_en-US.msi' -Algorithm SHA256
```

3. Depuis la racine du dépôt de livraison :

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install.ps1 -InstallerPath '.\AgentSec-Inspector_1.0.1_x64_en-US.msi'
```

Le script demande une confirmation, installe le paquet puis exécute un contrôle fonctionnel. Il ne désactive aucune protection Windows et n’installe aucun logiciel tiers silencieusement.

Pour le programme NSIS :

```powershell
.\scripts\install.ps1 -InstallerPath '.\AgentSec-Inspector_1.0.1_x64-setup.exe'
```

Dans une CI ou un environnement de test isolé, l’installation sans interface reste explicite :

```powershell
.\scripts\install.ps1 -InstallerPath '.\AgentSec-Inspector_1.0.1_x64_en-US.msi' -Confirmed -Quiet
```

Les codes MSI `1641` et `3010` signifient qu’un redémarrage est demandé. Le script les reconnaît sans masquer les autres erreurs.

## Données

Les projets, preuves, rapports, sauvegardes, journaux et secrets chiffrés sont placés sous `%LOCALAPPDATA%\AgentSec`. Le backend n’écoute que sur une adresse de bouclage et utilise un jeton éphémère fourni à l’interface par IPC Tauri.

## Vérification autonome

```powershell
.\scripts\verify-installation.ps1
if ($LASTEXITCODE -ne 0) { throw 'AgentSec installation invalid' }
Get-Content .\logs\tests\installation-verification.json
```

La vérification crée un répertoire temporaire et un projet temporaire, teste l’authentification, la base, l’API, les journaux et le démarrage desktop, puis supprime les données temporaires.

## Désinstallation

La désinstallation conserve les projets, preuves et rapports :

```powershell
.\scripts\uninstall.ps1
```

La suppression des données nécessite deux options et la confirmation PowerShell :

```powershell
.\scripts\backup.ps1
.\scripts\uninstall.ps1 -DeleteUserData -Confirmed
```

## Récupérer les installateurs de la CI

Le run de référence pour la version 1.0.1 est [`41059965105`](https://github.com/St0rn/agentsec-inspector/actions/runs/41059965105), terminé avec succès le 30 octobre 2026. Son artefact `agentsec-windows-x64` contient :

- le MSI sous `bundle\msi` ;
- le setup NSIS sous `bundle\nsis` ;
- `SHA256SUMS-windows.txt` ;
- les rapports JSON et journaux de validation.

Une compilation seule n’est pas une preuve d’installation. Vérifier que les étapes MSI, NSIS, vérification du sidecar et désinstallation sont toutes vertes.
