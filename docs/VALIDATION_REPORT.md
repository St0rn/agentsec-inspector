# Rapport de validation — 2026-10-29

## Environnement observé

- Linux x86_64, noyau 6.18.55
- Python 3.12.14
- Node.js 24.19.0, npm 11.9.0
- Rust 1.99.1 et Cargo installés dans un répertoire temporaire de validation
- PowerShell absent
- Aucun dépôt initial : implémentation créée dans `/workspace`

## Exécutions réussies

Backend :

```text
ruff check agentsec tests ../demo
All checks passed!

pytest --cov=agentsec --cov-report=term-missing
19 passed
Couverture totale : 70 %

mypy agentsec
0 erreur
```

Frontend :

```text
npm run lint
0 erreur

npm run test
3 fichiers, 4 tests réussis

npm run build
TypeScript + Vite réussis, 2404 modules transformés; chunks inférieurs à 500 ko

npm audit --audit-level=high
0 vulnérabilité

pip-audit -r backend/requirements.lock
0 vulnérabilité connue

bandit -r backend/agentsec -x backend/tests -ll
0 finding moyen ou élevé
```

Intégration réseau locale contrôlée :

```text
MCP Streamable HTTP : 2 outils, 1 ressource, 1 prompt réellement découverts
OpenAI-compatible : réponse réelle reçue du laboratoire déterministe
```

La connexion a été exécutée dans le même environnement réseau isolé avec permission loopback. Le laboratoire est dans `demo/` et ses données ne sont pas injectées dans la base de production.

Backend distribué Linux :

```text
PyInstaller 6.13 : binaire autonome x86_64 construit
Migration Alembic sur base SQLite neuve : réussie
GET /health : 200
API sans jeton : 401
Pré-vérification CORS autorisée : 200
Création et lecture de projet : réussies
Contrôle d’intégrité : database=ok, répertoire accessible
Rapport PDF : signature %PDF, téléchargement réussi
```

Tauri/Rust :

```text
cargo fmt --check : réussi
cargo metadata --locked --no-deps : réussi
cargo check --target x86_64-pc-windows-msvc : tenté, bloqué par llvm-rc absent sous Linux
```

Une capture du dashboard réellement connecté aux données du laboratoire est conservée dans `docs/images/dashboard.png`.

## Non exécuté dans cet environnement

- Analyse syntaxique PowerShell avec le parseur PowerShell
- Exécution nominale ou erreur des scripts `.ps1`
- Build complet Rust/Tauri Windows (seuls formatage et métadonnées ont été validés localement)
- PyInstaller Windows
- MSI/NSIS
- Installation, mise à jour, restauration et désinstallation Windows
- Lancement WebView2 sur Windows propre

Ces éléments sont donc **non validés Windows**, même si leurs scripts et workflows sont présents. `.github/workflows/windows-build.yml` exécute les validations manquantes sur `windows-2022`, génère les artefacts et publie les journaux. Aucun run CI n’a été observé dans cet environnement local.

## Limites constatées

- La couverture des transports MCP/LLM est surtout assurée par l’intégration contrôlée; les branches d’erreur restent moins couvertes.
- Le processus MCP stdio est restreint, mais son isolation forte dépend d’une VM ou Windows Sandbox externe.
