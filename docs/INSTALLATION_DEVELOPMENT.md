# Installation de développement

## Prérequis verrouillés

- Windows 10/11 x64
- Python 3.12
- Node.js 20, 22 ou 24 et npm
- Rust stable MSVC et Cargo
- Visual Studio 2022 Build Tools avec **Développement Desktop en C++**, MSVC v143 x64/x86 et un Windows 10/11 SDK complet
- WebView2 Runtime

## Commandes

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\check-prerequisites.ps1 -ForBuild
.\scripts\install-dev.ps1
.\scripts\start-dev.ps1
```

`install-dev.ps1` crée `.venv`, installe `backend\requirements.lock`, exécute `npm ci`, compile le frontend et initialise `%LOCALAPPDATA%\AgentSec\agentsec.db`. Il est réexécutable.

`check-prerequisites.ps1 -ForBuild` ne se limite pas à détecter Visual Studio : il charge l’environnement x64, vérifie les principaux outils et headers puis compile un programme C++ minimal. En cas d’échec, consulter `logs\installation\prerequisites.json` avant de lancer le build complet.

## Démonstration isolée

Dans un second terminal :

```powershell
.\scripts\start-demo.ps1 -Port 8877
```

Créer ensuite des cibles loopback `http://127.0.0.1:8877/mcp` et `http://127.0.0.1:8877`. Le projet de démonstration doit être nommé explicitement et ne doit pas contenir de données client.

## Tests

```powershell
.\scripts\test-all.ps1
```

Les versions Python sont gelées dans `backend\requirements.lock`; les versions npm et l’arbre résolu sont gelés dans `frontend\package-lock.json`.
