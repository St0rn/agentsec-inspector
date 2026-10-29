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
46 passed
Couverture totale : 85,40 % (seuil bloquant : 80 %)

mypy agentsec
0 erreur
```

Frontend :

```text
npm run lint
0 erreur

npm run test
5 fichiers, 9 tests réussis
Couverture : 66,4 % statements, 61,37 % branches, 55,31 % fonctions, 83,46 % lignes
Seuils bloquants : 65 % statements, 60 % branches, 55 % fonctions, 80 % lignes

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
MCP Streamable HTTP passif : 2 outils, 1 ressource, 1 prompt réellement découverts, 0 appel d’outil
MCP Streamable HTTP actif : read_lab_note appelé avec le paramètre exact note_id=welcome, statut SUCCESS
Protection active : capacité delete_demo_record refusée sans confirmation sensible individuelle (HTTP 409)
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
Rebuild après extension active : 53 123 616 octets
Smoke test final : MCP passif completed, appel actif SUCCESS, scénario multi-tour 2 échanges PASS
```

Tauri/Rust :

```text
cargo fmt --check : réussi
cargo metadata --locked --no-deps : réussi
cargo check --target x86_64-pc-windows-msvc : tenté, bloqué par llvm-rc absent sous Linux
```

Six captures du frontend réellement connecté au laboratoire sont conservées dans `docs/images/` : dashboard, MCP actif, prompt injection, findings, graphe observé et packs de scénarios.

Scripts Linux :

```text
check-prerequisites.sh : succès sur Linux x86_64, Python 3.12.14 et Node.js 24.19.0
check-prerequisites.sh --build : échec attendu, dépendances WebKitGTK/Rust absentes correctement signalées
install-dev.sh : deux exécutions successives, base SQLite intègre
setup-database.sh : migration et scénarios réussis
start-dev.sh : backend /health=200, API sans jeton=401, frontend=200
test-all.sh : backend, frontend, lint, typage et build réussis
test-scripts.sh : syntaxe, backup/restore, idempotence, downgrade, artefact invalide et uninstall réussis
backup.sh / restore.sh : archive SHA-256, integrity_check=ok, ancienne donnée préservée
```

Packaging et installation Linux sur GitHub Actions Ubuntu x64 :

```text
Run : https://github.com/St0rn/agentsec-inspector/actions/runs/40916996042
build-linux.sh : AppImage et DEB Tauri générés
install.sh : AppImage 1.0.0 installée deux fois
verify-installation.sh : deux exécutions réussies
Contrôles : checksum, sidecar PyInstaller, /health, rejet 401 sans jeton, migration SQLite,
création/lecture d’un projet et événement backend_started JSON valide
Artefact publié : agentsec-linux-x64 (archive CI 206 041 396 octets)
```

Les captures du manuel utilisateur (`manual-project`, `manual-target`, `mcp-passive`, `rag-security`, `agent-behavior`, `reports`) ont été générées depuis le frontend réel connecté au laboratoire contrôlé.

## Non exécuté dans cet environnement

- Analyse syntaxique PowerShell avec le parseur PowerShell
- Exécution nominale ou erreur des scripts `.ps1`
- Build complet Rust/Tauri Windows (seuls formatage et métadonnées ont été validés localement)
- PyInstaller Windows
- MSI/NSIS
- Installation, mise à jour, restauration et désinstallation Windows
- Lancement WebView2 sur Windows propre
- Build Tauri AppImage/DEB local, bloqué avant compilation par les bibliothèques système absentes; build et installation validés séparément sur le runner Ubuntu du run `40916996042`

Les éléments Windows sont donc **non validés Windows**, même si leurs scripts et workflows sont présents. `.github/workflows/windows-build.yml` exécute les validations manquantes sur `windows-2022`, génère les artefacts et publie les journaux. La réussite Linux ne constitue pas une preuve de fonctionnement Windows.

## Limites constatées

- Les clients MCP/LLM couvrent les chemins nominaux, retries, réponses invalides, limites de taille, allowlist stdio et credentials manquants; les particularités de fournisseurs tiers restent à valider sur chaque mission.
- Le processus MCP stdio est restreint, mais son isolation forte dépend d’une VM ou Windows Sandbox externe.
