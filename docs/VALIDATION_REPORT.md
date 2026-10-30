# Rapport de validation — 2026-10-30

## Environnement observé

- Linux x86_64, noyau 6.18.55
- Python 3.12.14
- Node.js 24.19.0, npm 11.9.0
- Rust 1.99.1 et Cargo installés dans un répertoire temporaire de validation
- PowerShell absent de l’hôte; PowerShell 7 utilisé dans un conteneur isolé pour le contrôle syntaxique
- Aucun dépôt initial : implémentation créée dans `/workspace`

## Exécutions réussies

Backend :

```text
ruff check agentsec tests ../demo
All checks passed!

pytest --cov=agentsec --cov-report=term-missing
69 passed
Couverture totale : 85,79 % (seuil bloquant : 80 %)

mypy agentsec
0 erreur
```

Frontend :

```text
npm run lint
0 erreur

npm run test
10 fichiers, 20 tests réussis
Couverture : 75,28 % statements, 68,67 % branches, 68,15 % fonctions, 86,87 % lignes
Seuils bloquants : 65 % statements, 60 % branches, 55 % fonctions, 80 % lignes

npm run build
TypeScript + Vite réussis, 2405 modules transformés; chunks inférieurs à 500 ko

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

Scripts PowerShell :

```text
Parseur PowerShell 7 conteneurisé : 20 fichiers .ps1 chargés sans erreur de syntaxe
Invoke-Checked sous PowerShell 7 : avertissement stderr + code 0 accepté; stderr + code 23 bloqué
PowerShell 5.1, MSVC et installateurs : non disponibles sur l’hôte Linux, validés séparément par le runner Windows ci-dessous
```

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

Packaging et installation Windows sur GitHub Actions Windows Server 2022 x64 :

```text
Run : https://github.com/St0rn/agentsec-inspector/actions/runs/41063236427
Commit : dcd74018817c23f8af6962dbd646145bf620f292
PowerShell 7 : 71 tests Pester réussis, 0 échec
Windows PowerShell 5.1 : 71 tests Pester réussis, 0 échec
PSScriptAnalyzer et parsing des 20 scripts : réussis
WebView2 : runtime 131.0.2903.86 détecté via la clé Microsoft officielle
MSVC/Windows SDK : cl.exe, link.exe, rc.exe, mt.exe et headers vérifiés
Probe compilateur : programme C++ compilé et lié dans un chemin contenant des espaces
Build : backend PyInstaller, application Tauri, MSI et NSIS x64 réussis
Rust : test de la configuration IPC réussi
MSI : installation + smoke test effectués deux fois, puis désinstallation réussie
NSIS : installation + smoke test effectués deux fois, puis désinstallation réussie
Smoke test : fichiers packagés, /health, port dynamique, origine CORS Tauri, rejet 401,
CRUD projets, SQLite, logs, lancement du desktop et création du sidecar vérifiés
Préservation des données utilisateur : réussie pour les deux désinstallations
Artefact : agentsec-windows-x64, ID 12983200265, 81 213 676 octets
```

Sommes observées dans le run :

```text
MSI  569C9FBB7FC9F8AFE68B3B462C45A178973D80A5AEDF23E23038C47533CE9C07
NSIS F13E6D7EB41803198F1428FB16BB996AC9891D71CD6ED1F51B83549B00006B61
ZIP  73FBF5F2AC8FDF83B8D16ACB383ABC6697E573CB775FC741FF17B5E7B86FD9E3
```

Artefact de validation : [MSI, NSIS et journaux Windows](https://github.com/St0rn/agentsec-inspector/actions/runs/41063236427/artifacts/12983200265).

Les captures du manuel utilisateur (`manual-project`, `manual-target`, `mcp-passive`, `jailbreak`, `rag-security`, `agent-behavior`, `reports`) ont été générées depuis le frontend réel connecté au laboratoire contrôlé. La capture `jailbreak.png` montre un scénario `jb.authority-impersonation` réellement exécuté avec un verdict `PASS` fondé sur la réponse observée.

## Non exécuté sur l’hôte Linux local

- Analyse et exécution sous Windows PowerShell 5.1
- Exécution nominale ou erreur des scripts `.ps1`
- Build complet Rust/Tauri Windows (seuls formatage et métadonnées ont été validés localement)
- PyInstaller Windows
- MSI/NSIS
- Installation, mise à jour, restauration et désinstallation Windows
- Lancement WebView2 sur Windows propre
- Build Tauri AppImage/DEB local, bloqué avant compilation par les bibliothèques système absentes; build et installation validés séparément sur le runner Ubuntu du run `40916996042`

Ces limites décrivent uniquement l’hôte Linux local. Les éléments Windows listés dans la section précédente sont validés par le runner `windows-2022` du run `41063236427`. Les scripts `install-dev.ps1`, `start-dev.ps1`, `update.ps1`, `backup.ps1` et `clean.ps1` n’ont toutefois pas été exécutés nominalement par ce run et conservent le statut indiqué dans `INSTALLATION_VALIDATION_MATRIX.md`.

## Limites constatées

- L’instance AI Red Team Range de l’utilisateur sur `127.0.0.1:8789` n’était pas accessible depuis l’environnement de validation. Le protocole fourni a été reproduit par des échanges HTTP contrôlés, sans présenter ce test comme un échange avec le service réel.
- Les clients MCP/LLM couvrent JSON, NDJSON, SSE, fragments de tokens, outils, réponses invalides, flux interrompus, limites de taille, absence de répétition automatique des POST, allowlist stdio et identifiants manquants; les particularités de fournisseurs tiers restent à valider sur chaque mission.
- Le processus MCP stdio est restreint, mais son isolation forte dépend d’une VM ou Windows Sandbox externe.
