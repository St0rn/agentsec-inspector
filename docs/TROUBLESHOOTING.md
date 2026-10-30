# Dépannage

## Le backend ne démarre pas

```powershell
Get-Content "$env:LOCALAPPDATA\AgentSec\logs\agentsec.jsonl" -Tail 100
Get-NetTCPConnection -LocalAddress 127.0.0.1 -State Listen
.\scripts\verify-installation.ps1
```

Ne pas ouvrir le port dans le pare-feu : l’API doit rester locale. Si le port sélectionné est occupé, fermer l’autre instance avant de relancer.

## L’interface affiche « Backend Offline » ou une erreur de connexion

L’application attend le démarrage du sidecar et de la base avant d’envoyer ses requêtes. Si le statut reste hors ligne :

1. cliquer sur **Reconnecter** dans le panneau **Local Mode** ;
2. consulter `%LOCALAPPDATA%\AgentSec\logs\agentsec.jsonl` ;
3. fermer les autres instances d’AgentSec Inspector ;
4. lancer `scripts\verify-installation.ps1` depuis le dépôt de livraison.

Le backend doit écouter sur un port aléatoire de `127.0.0.1`. Il ne faut ni ouvrir ce port dans le pare-feu ni remplacer les restrictions CORS par un joker. Sous Windows, l’origine WebView2 attendue est `http://tauri.localhost`.

## Échec PyInstaller / WeasyPrint

Réexécuter la préparation verrouillée, puis le build :

```powershell
.\scripts\setup-backend.ps1 -ForceRecreate
.\scripts\build-windows.ps1
```

## Build Rust MSVC

Vérifier la cible et les outils C++ :

```powershell
rustup show
rustup target add x86_64-pc-windows-msvc
.\scripts\check-prerequisites.ps1 -ForBuild
```

Le rapport détaillé se trouve dans `logs\installation\prerequisites.json`. Les contrôles `windows_sdk_headers`, `windows_sdk_tools`, `build_environment` et `compiler_probe` doivent tous être à `ok: true`.

### `specstrings_strict.h` absent ou erreur C1083

Cette erreur indique généralement un Windows SDK incomplet ou endommagé. AgentSec ne modifie pas le registre et ne tente aucune réparation silencieuse.

1. Ouvrir **Visual Studio Installer**.
2. Modifier **Build Tools for Visual Studio 2022**.
3. Activer **Développement Desktop en C++**.
4. Vérifier **MSVC v143 x64/x86** et un **Windows 10/11 SDK** pris en charge.
5. Appliquer la réparation, ouvrir un nouveau terminal PowerShell x64 et relancer :

```powershell
.\scripts\check-prerequisites.ps1 -ForBuild
```

Si plusieurs installations Visual Studio coexistent, vérifier le chemin `vs_build_tools.value` dans le rapport. Le compilateur, les headers et les bibliothèques doivent provenir d’un environnement cohérent chargé par `vcvars64.bat`.

## WebView2 non détecté

Le contrôle lit les clés Microsoft EdgeUpdate utilisateur et système et exige une version réelle différente de `0.0.0.0`. Installer le runtime Evergreen depuis Microsoft avec le consentement de l’administrateur, puis ouvrir un nouveau terminal. AgentSec ne désactive aucune protection Windows et n’installe pas le runtime silencieusement.

## Avertissements npm sous PowerShell 5.1

`npm warn deprecated` ou `npm warn allow-scripts` sont enregistrés comme `stderr`, mais seul le code de sortie natif détermine le succès. Si le script s’arrête, consulter la fin du journal : un code non nul ou une erreur réelle doit rester bloquant.

## Cible distante bloquée

Le projet doit autoriser la cible et la case d’autorisation distante doit être cochée. Les adresses link-local, non spécifiées et réservées restent bloquées. Les réseaux privés distants exigent en plus `AGENTSEC_ALLOW_PRIVATE_REMOTE_TARGETS=true` au démarrage contrôlé.

## MCP stdio refusé

Définir une liste exacte, sans shell :

```powershell
$env:AGENTSEC_ALLOWED_MCP_EXECUTABLES='C:\Program Files\nodejs\node.exe'
```

Le processus est lancé sans shell avec un environnement réduit. Pour un serveur non fiable, utiliser une VM ou Windows Sandbox : la V1 ne fournit pas elle-même une frontière de virtualisation.

## Journaux

Les scripts écrivent dans `logs\installation`, `logs\build`, `logs\tests`, `logs\updates` et `logs\errors`. Les tokens et clés ne doivent jamais y apparaître. Les journaux applicatifs sont dans `%LOCALAPPDATA%\AgentSec\logs`.
