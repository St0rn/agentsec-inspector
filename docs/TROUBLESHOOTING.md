# Dépannage

## Le backend ne démarre pas

```powershell
Get-Content "$env:LOCALAPPDATA\AgentSec\logs\agentsec.jsonl" -Tail 100
Get-NetTCPConnection -LocalAddress 127.0.0.1 -State Listen
.\scripts\verify-installation.ps1
```

Ne pas ouvrir le port dans le pare-feu : l’API doit rester locale. Si le port sélectionné est occupé, fermer l’autre instance avant de relancer.

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
