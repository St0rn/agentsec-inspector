# Rapport de validation

## Candidat v1.5.0 — 2026-11-01

### Validation locale Linux réellement exécutée

- Backend : 101 tests réussis, couverture totale 85,19 % avec seuil bloquant à 80 %, Ruff et mypy réussis.
- Frontend : 56 tests réussis, couverture des lignes 80,15 % avec seuils bloquants, ESLint, TypeScript et build Vite de production réussis.
- Sécurité : `pip-audit` ne détecte aucune vulnérabilité Python connue ; Bandit ne relève aucun problème moyen/élevé ; le contrôle `npm audit --audit-level=high` réussit.
- Dépendances frontend : npm signale 12 alertes modérées `minimatch` dans la chaîne de lint de développement. Aucune alerte haute ou critique n’est masquée ; aucune correction forcée avec changement cassant n’a été appliquée.
- Captures : génération exécutée contre le backend FastAPI et le laboratoire MCP/LLM/RAG locaux réels. Le script vérifie les erreurs JavaScript et la présence de fichiers non triviaux.
- Scripts Linux : syntaxe Bash réussie et suite `scripts/linux/test-scripts.sh` réussie pour les chemins nominaux et les principales erreurs.

### Validation de plateforme

Les tests locaux ne valident ni MSI/NSIS ni AppImage/DEB. Les identifiants des runs Windows/Linux v1.5.0 et les empreintes des quatre paquets seront inscrits après réussite des workflows sur le tag exact. Jusqu’à cette étape, la dernière preuve publiée reste la v1.4.0 : [Windows 41224219837](https://github.com/St0rn/agentsec-inspector/actions/runs/41224219837), [Linux 41224219868](https://github.com/St0rn/agentsec-inspector/actions/runs/41224219868) et [release v1.4.0](https://github.com/St0rn/agentsec-inspector/releases/tag/v1.4.0).

PowerShell, WebView2 et la chaîne MSVC ne sont pas disponibles dans cet environnement Linux. Aucune exécution Windows locale n’est revendiquée.

---

## Historique de validation v1.1.0/v1.2.0 — 2026-10-31

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
71 passed
Couverture totale : 87,23 % (seuil bloquant : 80 %)

mypy agentsec
0 erreur
```

Frontend :

```text
npm run lint
0 erreur

npm run test
12 fichiers, 23 tests réussis
Couverture : 76,56 % statements, 67,69 % branches, 72,76 % fonctions, 85,68 % lignes
Seuils bloquants : 65 % statements, 60 % branches, 55 % fonctions, 80 % lignes

npm run build
TypeScript + Vite réussis, 2408 modules transformés; chunks inférieurs à 500 ko

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

Le Reporting Engine 1.2 a également été vérifié avec un projet vide et un projet détaillé contenant un finding critique, le payload exact, un appel d’outil, des caractères spéciaux et une preuve de 12 000 caractères. Les exports JSON, HTML et PDF utilisent les mêmes données. Le PDF obtenu comporte 12 pages A4 sans JavaScript embarqué; la couverture, la fiche finding et la page payload ont été contrôlées visuellement et conservées dans `docs/images/`.

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
Run : https://github.com/St0rn/agentsec-inspector/actions/runs/41108334280
Commit : 791cb580dee5fda3308e564c7882b8c233463195
build-linux.sh : AppImage et DEB Tauri générés
install.sh : AppImage 1.1.0 installée deux fois
verify-installation.sh : deux exécutions réussies
Contrôles : checksum, sidecar PyInstaller, /health, rejet 401 sans jeton, migration SQLite,
création/lecture d’un projet et événement backend_started JSON valide
Artefact publié : agentsec-linux-x64, ID 13001809139, 206 105 153 octets
```

Packaging et installation Windows sur GitHub Actions Windows Server 2022 x64 :

```text
Run : https://github.com/St0rn/agentsec-inspector/actions/runs/41108334253
Commit : 791cb580dee5fda3308e564c7882b8c233463195
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
Artefact : agentsec-windows-x64, ID 13001844123, 81 279 026 octets
```

Sommes publiées avec la release `v1.1.0` :

```text
AppImage  1b3640f77316b7a5290942cb095c61be65a117dae9b4314a028250e1503687a7
DEB       1863921b3aa008cac2281a93006ef6c2e43e0faf48edb450bdad21b433516739
NSIS      a99cd189cb06d3ebf9e9c06782b7013ed8a2ac14fae4c4455906dc08cc98aa51
MSI       359ce23388102612758a945243f403ba487ce4b47879295842ce02b7e2a3638d
```

Artefacts de validation : [MSI, NSIS et journaux Windows](https://github.com/St0rn/agentsec-inspector/actions/runs/41108334253/artifacts/13001844123) ; [AppImage, DEB et journaux Linux](https://github.com/St0rn/agentsec-inspector/actions/runs/41108334280/artifacts/13001809139). La [release `v1.1.0`](https://github.com/St0rn/agentsec-inspector/releases/tag/v1.1.0) a été créée par le [workflow `41110672480`](https://github.com/St0rn/agentsec-inspector/actions/runs/41110672480) uniquement après la réussite des deux validations.

Les captures du manuel utilisateur (`manual-project`, `manual-target`, `mcp-passive`, `jailbreak`, `rag-security`, `agent-behavior`, `reports`) ont été générées depuis le frontend réel connecté au laboratoire contrôlé. La capture `jailbreak.png` montre un scénario `jb.authority-impersonation` réellement exécuté avec un verdict `PASS` fondé sur la réponse observée.

## Non exécuté sur l’hôte Linux local

- Analyse et exécution sous Windows PowerShell 5.1
- Exécution nominale ou erreur des scripts `.ps1`
- Build complet Rust/Tauri Windows (seuls formatage et métadonnées ont été validés localement)
- PyInstaller Windows
- MSI/NSIS
- Installation, mise à jour, restauration et désinstallation Windows
- Lancement WebView2 sur Windows propre
- Build Tauri AppImage/DEB local, bloqué avant compilation par les bibliothèques système absentes; build et installation validés séparément sur le runner Ubuntu du run `41108334280`

Ces limites décrivent uniquement l’hôte Linux local. Les éléments Windows listés dans la section précédente sont validés par le runner `windows-2022` du run `41108334253`. Les scripts `install-dev.ps1`, `start-dev.ps1`, `update.ps1`, `backup.ps1` et `clean.ps1` n’ont toutefois pas été exécutés nominalement par ce run et conservent le statut indiqué dans `INSTALLATION_VALIDATION_MATRIX.md`.

## Limites constatées

- L’instance AI Red Team Range de l’utilisateur sur `127.0.0.1:8789` n’était pas accessible depuis l’environnement de validation. Le protocole fourni a été reproduit par des échanges HTTP contrôlés, sans présenter ce test comme un échange avec le service réel.
- Les clients MCP/LLM couvrent JSON, NDJSON, SSE, fragments de tokens, outils, réponses invalides, flux interrompus, limites de taille, absence de répétition automatique des POST, allowlist stdio et identifiants manquants; les particularités de fournisseurs tiers restent à valider sur chaque mission.
- Le processus MCP stdio est restreint, mais son isolation forte dépend d’une VM ou Windows Sandbox externe.
