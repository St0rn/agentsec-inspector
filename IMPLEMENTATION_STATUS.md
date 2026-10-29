# AgentSec Inspector — état d’implémentation V1.0

Date : 2026-10-29. Ce document distingue livraison de code, exécution locale Linux et validation Windows.

## Terminé et exécuté sous Linux

- Architecture FastAPI/Pydantic/SQLAlchemy/SQLite, API REST locale et authentification par jeton.
- Schéma relationnel avec projets, cibles, connecteurs, scénarios versionnés, audits, exécutions, findings, preuves, événements, rapports, paramètres et données RAG.
- CRUD projets/cibles/findings; isolation et intégrité référentielle; historique des findings.
- Dashboard calculé à partir de la base, sans données fictives.
- MCP Streamable HTTP et stdio : découverte passive sans invocation, plus appels actifs explicitement sélectionnés et confirmés.
- Mode actif MCP borné : validation des arguments contre le schéma annoncé, seconde confirmation des capacités sensibles, redaction des secrets, preuves et événements observables.
- Analyse MCP conservatrice avec Observation / Risk potential / Confirmed vulnerability.
- Connecteurs LLM OpenAI-compatible, Ollama et HTTP de chat; timeout, limite de réponse, redirections désactivées, credentials via variable d’environnement.
- Dix scénarios de prompt injection versionnés, marqueur fictif, statuts PASS/FAIL/INCONCLUSIVE/ERROR et preuves.
- API de packs de scénarios JSON déclaratifs, versionnés et strictement validés; aucun code plugin n’est exécuté.
- RAG : import de document, inspection d’instructions, import de trace, respect du drapeau de télémétrie, comparaison obtenu/attendu.
- Événements observables d’agent, timeline et graphe d’interactions observées.
- Findings complets et modifiables.
- Rapports HTML, JSON et PDF, français/anglais, technique/exécutif.
- Sauvegarde SQLite en ligne via API; scripts archive/restauration hors ligne.
- Frontend React/TypeScript/Tailwind sombre avec les 12 menus demandés et états vides.
- Laboratoire distinct : endpoint chat déterministe, MCP et corpus RAG contrôlé.
- 46 tests backend réussis (85,4 %, seuil bloquant 80 %); 9 tests frontend réussis (83,46 % des lignes et seuils bloquants); Ruff, mypy, ESLint et build web réussis.
- Intégration loopback réelle : découverte MCP passive, appel actif autorisé et test LLM réussis contre le laboratoire.
- Backend autonome Linux PyInstaller vérifié sur base neuve : migration, santé, rejet sans jeton, CORS authentifié, CRUD, intégrité et génération/téléchargement PDF.
- Audits de dépendances `pip-audit` et `npm audit` réussis sans vulnérabilité connue; Bandit sans finding moyen ou élevé.
- Six captures réelles produites depuis le frontend connecté aux résultats du laboratoire contrôlé : dashboard, MCP actif, prompt injection, findings, attack chains et packs de scénarios.
- Six captures supplémentaires produites pour le manuel utilisateur : projet, cible, MCP passif, RAG, comportement agent et rapports.

## Terminé et exécuté sous Linux — cycle d’installation

- Scripts Bash pour prérequis, installation développeur, base de données, démarrage, tests, build, installation AppImage, vérification, mise à jour, sauvegarde, restauration, désinstallation et nettoyage.
- Vérification des prérequis standard réussie; erreur de build contrôlée et dépendances système manquantes correctement détaillées sans installation automatique.
- `install-dev.sh` exécuté deux fois sur le même environnement; base SQLite restée intègre.
- `start-dev.sh` vérifié avec backend sain, API protégée (401 sans jeton) et frontend disponible.
- `test-all.sh` exécuté avec les 46 tests backend, 9 tests frontend, lint, typage et build.
- Tests isolés des scripts réussis : syntaxe Bash, sauvegarde, restauration avec confirmation, idempotence, refus de downgrade, rejet d’un artefact invalide, préservation et suppression confirmée des données.
- Sauvegarde et restauration réelles exécutées sur une base SQLite; empreinte et intégrité vérifiées, ancienne arborescence préservée.
- Workflow `linux-build.yml` fourni pour construire et installer réellement les paquets AppImage et DEB sur Ubuntu.

## Fourni mais non validé sur Windows

- Sidecar PyInstaller et cycle de vie Tauri 2.
- Build MSI/NSIS Windows x64.
- Scripts PowerShell d’installation, développement, configuration, base, lancement, build, tests, vérification, update, backup, restore, uninstall et nettoyage.
- Workflow Windows avec analyse PowerShell, Pester, build, installation MSI et smoke test.

Raison : l’environnement courant ne contient ni Windows ni PowerShell. Rust/Cargo a été installé pour les contrôles statiques, mais la vérification de la cible MSVC est bloquée sous Linux par l’absence de `llvm-rc`. Ces éléments ne portent donc pas le statut « validé Windows ».

## Fourni mais non construit localement sous Linux

- Paquets desktop AppImage et DEB Tauri.

Raison : l’environnement Linux courant ne contient pas WebKitGTK/GTK/libsoup ni Rust dans le `PATH` système. Le script refuse proprement le build et indique les paquets nécessaires. Le workflow Linux installe ces dépendances de manière explicite et produit les preuves manquantes. Aucun paquet AppImage/DEB n’est déclaré validé avant la réussite de ce workflow.

## Partiel

- Isolation MCP stdio : allowlist, absence de shell, environnement réduit, limites et timeout sont implémentés; pas de sandbox OS intégrée.
- Agent Behavior : collecte et visualisation des événements produits par AgentSec; import de formats de trace tiers non fourni.
- Attack Chains : graphe des relations observées; création manuelle de chemins théoriques non fournie.
- RAG : import et analyse de télémétrie réelle fournie; adaptateurs automatiques propres à chaque fournisseur RAG non fournis.
- Frameworks : modèle de correspondance et OWASP LLM01 basé sur preuve; pas de catalogue automatique complet, afin d’éviter les correspondances artificielles.
- Modèles de rapports : modèle livré et champ `template_name`; édition visuelle, logo client et chargement de modèles personnalisés non fournis.
- Plugin API : packs de scénarios déclaratifs opérationnels; chargement dynamique de code tiers volontairement non fourni en V1 pour des raisons de sécurité.
- Gestion de secrets : chiffrement local Fernet et ACL utilisateur; intégration Windows Credential Manager/DPAPI non fournie.

## Non implémenté

- Signature de code Windows et certificat éditeur.
- Exécution de serveurs non fiables dans une VM/Windows Sandbox créée automatiquement.
- Automatisation UI end-to-end WebView2.
- Import de logo client et éditeur de template.

## Scripts fournis

Tous les scripts PowerShell obligatoires sont présents dans `scripts/`, plus `start-demo.ps1`, les tests Pester et la génération CI de matrice. Le cycle Linux équivalent est présent dans `scripts/linux/` avec ses tests isolés.

## Scripts réellement exécutés

Aucun script `.ps1` n’a été exécuté, PowerShell étant absent. Les scripts Bash Linux de prérequis, installation développeur, base, démarrage, tests, sauvegarde, restauration et tests de cycle de vie ont été exécutés. Voir `docs/VALIDATION_REPORT.md` et `INSTALLATION_VALIDATION_MATRIX.md`.

## Résultats de tests

- Backend : 46/46 réussis; couverture 85,4 % (minimum imposé 80 %); Ruff et mypy réussis.
- Frontend : 9/9 réussis; 83,46 % des lignes avec seuils minimums; lint et build réussis.
- Intégration laboratoire : MCP passif, MCP actif contrôlé et LLM réussis.
- Dépendances : `pip-audit` et `npm audit` sans vulnérabilité connue.
- PyInstaller Linux : binaire autonome construit et smoke-testé, rapports PDF inclus.
- Tauri : `cargo fmt --check` et `cargo metadata --locked --no-deps` réussis; compilation Windows non réalisée.
- Windows/PowerShell : non exécutés, donc non validés.
- Linux/Bash : scripts principaux exécutés; AppImage/DEB en attente de la preuve du workflow Linux.
