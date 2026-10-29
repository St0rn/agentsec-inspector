# AgentSec Inspector — état d’implémentation V1.0

Date : 2026-10-29. Ce document distingue livraison de code, exécution locale Linux et validation Windows.

## Terminé et exécuté sous Linux

- Architecture FastAPI/Pydantic/SQLAlchemy/SQLite, API REST locale et authentification par jeton.
- Schéma relationnel avec projets, cibles, connecteurs, scénarios versionnés, audits, exécutions, findings, preuves, événements, rapports, paramètres et données RAG.
- CRUD projets/cibles/findings; isolation et intégrité référentielle; historique des findings.
- Dashboard calculé à partir de la base, sans données fictives.
- MCP Streamable HTTP et stdio passif : initialisation, capacités, outils, ressources et prompts; aucune invocation d’outil.
- Analyse MCP conservatrice avec Observation / Risk potential / Confirmed vulnerability.
- Connecteurs LLM OpenAI-compatible, Ollama et HTTP de chat; timeout, limite de réponse, redirections désactivées, credentials via variable d’environnement.
- Dix scénarios de prompt injection versionnés, marqueur fictif, statuts PASS/FAIL/INCONCLUSIVE/ERROR et preuves.
- RAG : import de document, inspection d’instructions, import de trace, respect du drapeau de télémétrie, comparaison obtenu/attendu.
- Événements observables d’agent, timeline et graphe d’interactions observées.
- Findings complets et modifiables.
- Rapports HTML, JSON et PDF, français/anglais, technique/exécutif.
- Sauvegarde SQLite en ligne via API; scripts archive/restauration hors ligne.
- Frontend React/TypeScript/Tailwind sombre avec les 12 menus demandés et états vides.
- Laboratoire distinct : endpoint chat déterministe, MCP et corpus RAG contrôlé.
- 19 tests backend réussis (70 %); 4 tests frontend réussis; Ruff, mypy, ESLint et build web réussis.
- Intégration loopback réelle MCP + LLM réussie contre le laboratoire.
- Backend autonome Linux PyInstaller vérifié sur base neuve : migration, santé, rejet sans jeton, CORS authentifié, CRUD, intégrité et génération/téléchargement PDF.
- Audits de dépendances `pip-audit` et `npm audit` réussis sans vulnérabilité connue; Bandit sans finding moyen ou élevé.
- Capture réelle du dashboard produite depuis le frontend connecté au backend distribué et aux résultats du laboratoire contrôlé.

## Fourni mais non validé sur Windows

- Sidecar PyInstaller et cycle de vie Tauri 2.
- Build MSI/NSIS Windows x64.
- Scripts PowerShell d’installation, développement, configuration, base, lancement, build, tests, vérification, update, backup, restore, uninstall et nettoyage.
- Workflow Windows avec analyse PowerShell, Pester, build, installation MSI et smoke test.

Raison : l’environnement courant ne contient ni Windows ni PowerShell. Rust/Cargo a été installé pour les contrôles statiques, mais la vérification de la cible MSVC est bloquée sous Linux par l’absence de `llvm-rc`. Ces éléments ne portent donc pas le statut « validé Windows ».

## Partiel

- Isolation MCP stdio : allowlist, absence de shell, environnement réduit, limites et timeout sont implémentés; pas de sandbox OS intégrée.
- Agent Behavior : collecte et visualisation des événements produits par AgentSec; import de formats de trace tiers non fourni.
- Attack Chains : graphe des relations observées; création manuelle de chemins théoriques non fournie.
- RAG : import et analyse de télémétrie réelle fournie; adaptateurs automatiques propres à chaque fournisseur RAG non fournis.
- Frameworks : modèle de correspondance et OWASP LLM01 basé sur preuve; pas de catalogue automatique complet, afin d’éviter les correspondances artificielles.
- Modèles de rapports : modèle livré et champ `template_name`; édition visuelle, logo client et chargement de modèles personnalisés non fournis.
- Plugin API : modèle de scénario versionné extensible; chargement dynamique de code tiers volontairement non fourni en V1 pour des raisons de sécurité.
- Gestion de secrets : chiffrement local Fernet et ACL utilisateur; intégration Windows Credential Manager/DPAPI non fournie.

## Non implémenté

- Signature de code Windows et certificat éditeur.
- Exécution de serveurs non fiables dans une VM/Windows Sandbox créée automatiquement.
- Automatisation UI end-to-end WebView2.
- Import de logo client et éditeur de template.

## Scripts fournis

Tous les scripts obligatoires sont présents dans `scripts/`, plus `start-demo.ps1`, les tests Pester et la génération CI de matrice.

## Scripts réellement exécutés

Aucun script `.ps1` n’a été exécuté, PowerShell étant absent. Les commandes Python/npm équivalentes ont été exécutées directement. Voir `docs/VALIDATION_REPORT.md` et `INSTALLATION_VALIDATION_MATRIX.md`.

## Résultats de tests

- Backend : 19/19 réussis; couverture 70 %; Ruff et mypy réussis.
- Frontend : 4/4 réussis; lint réussi; build réussi.
- Intégration laboratoire : MCP et LLM réussis.
- Dépendances : `pip-audit` et `npm audit` sans vulnérabilité connue.
- PyInstaller Linux : binaire autonome construit et smoke-testé, rapports PDF inclus.
- Tauri : `cargo fmt --check` et `cargo metadata --locked --no-deps` réussis; compilation Windows non réalisée.
- Windows/PowerShell : non exécutés, donc non validés.
