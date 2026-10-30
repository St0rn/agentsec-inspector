# AgentSec Inspector v1.0.1

Cette version corrige la communication entre l’interface Tauri sous Windows et le backend FastAPI intégré.

## Corrections

- ajout de l’origine Windows `http://tauri.localhost` à la liste CORS, sans autorisation générique ;
- attente du démarrage du backend et des migrations avant le premier appel API ;
- délais d’attente bornés, erreurs réseau explicites et bouton de reconnexion ;
- état de connexion dynamique : `Connecting...`, `Backend Online` ou `Backend Offline` ;
- création, affichage, modification et suppression des projets depuis l’interface ;
- conservation du port dynamique, du jeton transmis par IPC et de l’écoute sur `127.0.0.1` uniquement.

## Validation Windows x64

Le workflow Windows a exécuté :

- 60 tests backend, Ruff et mypy ;
- 17 tests frontend, ESLint, TypeScript et le build Vite ;
- 71 tests Pester sous PowerShell 7 et 71 sous Windows PowerShell 5.1 ;
- un test Rust de la configuration IPC ;
- la compilation PyInstaller, Tauri, MSI et NSIS ;
- deux installations et vérifications du MSI ;
- deux installations et vérifications du Setup NSIS ;
- les contrôles du port dynamique, de la santé du sidecar, de CORS, de l’authentification, de SQLite, du CRUD projets et des journaux.

Preuve : [workflow Windows x64 `41059965105`](https://github.com/St0rn/agentsec-inspector/actions/runs/41059965105).

## Fichiers

- `AgentSec-Inspector_1.0.1_x64_en-US.msi`
- `AgentSec-Inspector_1.0.1_x64-setup.exe`
- `SHA256SUMS-windows.txt`

Les binaires ne sont pas signés numériquement dans cette version. Vérifiez leur empreinte SHA-256 avant installation.
