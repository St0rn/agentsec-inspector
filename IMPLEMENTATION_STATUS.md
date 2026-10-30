# AgentSec Inspector — état d’implémentation v1.0.1

Date : 2026-10-30. Ce document distingue livraison de code, exécution locale Linux et validation Windows CI.

## Terminé et exécuté sous Linux

- Architecture FastAPI/Pydantic/SQLAlchemy/SQLite, API REST locale et authentification par jeton.
- Schéma relationnel avec projets, cibles, connecteurs, scénarios versionnés, audits, exécutions, findings, preuves, événements, rapports, paramètres et données RAG.
- CRUD projets/cibles/findings; isolation et intégrité référentielle; historique des findings.
- Dashboard calculé à partir de la base, sans données fictives.
- MCP Streamable HTTP et stdio : découverte passive sans invocation, plus appels actifs explicitement sélectionnés et confirmés.
- Mode actif MCP borné : validation des arguments contre le schéma annoncé, seconde confirmation des capacités sensibles, redaction des secrets, preuves et événements observables.
- Analyse MCP conservatrice avec Observation / Risk potential / Confirmed vulnerability.
- Connecteurs LLM OpenAI-compatible, Ollama, HTTP Chat Completions et chatbot JSON générique; mapping déclaratif requête/réponse, timeout, limite de réponse, redirections désactivées et identifiants via variable d’environnement.
- Dix scénarios de prompt injection et neuf scénarios de jailbreak versionnés, marqueur fictif, statuts PASS/FAIL/INCONCLUSIVE/ERROR et preuves.
- API de packs de scénarios JSON déclaratifs, versionnés et strictement validés; aucun code plugin n’est exécuté.
- RAG : import de document, inspection d’instructions, import de trace, respect du drapeau de télémétrie, comparaison obtenu/attendu.
- Événements observables d’agent, timeline et graphe d’interactions observées.
- Findings complets et modifiables.
- Rapports HTML, JSON et PDF, français/anglais, technique/exécutif.
- Sauvegarde SQLite en ligne via API; scripts archive/restauration hors ligne.
- Frontend React/TypeScript/Tailwind sombre avec les 12 menus demandés, un module Jailbreak dédié supplémentaire et des états vides explicites.
- Communication desktop corrigée pour l’origine WebView2 Windows, avec attente du backend, délais bornés, reconnexion et état de connexion dynamique.
- CRUD projets complet dans l’interface : création, affichage, modification et suppression, sans données de remplacement en cas d’erreur.
- Laboratoire distinct : endpoint chat déterministe, MCP et corpus RAG contrôlé.
- 60 tests backend réussis (86,85 %, seuil bloquant 80 %); 17 tests frontend réussis (87,86 % des lignes et seuils bloquants); Ruff, mypy, ESLint et build web réussis.
- Intégration loopback réelle : découverte MCP passive, appel actif autorisé et test LLM réussis contre le laboratoire.
- Backend autonome Linux PyInstaller vérifié sur base neuve : migration, santé, rejet sans jeton, CORS authentifié, CRUD, intégrité et génération/téléchargement PDF.
- Audits de dépendances `pip-audit` et `npm audit` réussis sans vulnérabilité connue; Bandit sans finding moyen ou élevé.
- Six captures réelles produites depuis le frontend connecté aux résultats du laboratoire contrôlé : dashboard, MCP actif, prompt injection, findings, attack chains et packs de scénarios.
- Sept captures supplémentaires produites pour le manuel utilisateur : projet, cible, MCP passif, jailbreak, RAG, comportement agent et rapports.

## Terminé et exécuté sous Linux — cycle d’installation

- Scripts Bash pour prérequis, installation développeur, base de données, démarrage, tests, build, installation AppImage, vérification, mise à jour, sauvegarde, restauration, désinstallation et nettoyage.
- Vérification des prérequis standard réussie; erreur de build contrôlée et dépendances système manquantes correctement détaillées sans installation automatique.
- `install-dev.sh` exécuté deux fois sur le même environnement; base SQLite restée intègre.
- `start-dev.sh` vérifié avec backend sain, API protégée (401 sans jeton) et frontend disponible.
- `test-all.sh` exécuté ; la validation directe actuelle couvre 60 tests backend, 17 tests frontend, lint, typage et build.
- Tests isolés des scripts réussis : syntaxe Bash, sauvegarde, restauration avec confirmation, idempotence, refus de downgrade, rejet d’un artefact invalide, préservation et suppression confirmée des données.
- Sauvegarde et restauration réelles exécutées sur une base SQLite; empreinte et intégrité vérifiées, ancienne arborescence préservée.
- Workflow `linux-build.yml` exécuté avec succès sur Ubuntu x64 : AppImage et DEB construits, AppImage installée et vérifiée deux fois, artefact CI `agentsec-linux-x64` publié (run `40916996042`).

## Validé sur Windows x64 par CI

Preuve : [GitHub Actions run `41059965105`](https://github.com/St0rn/agentsec-inspector/actions/runs/41059965105), runner `windows-2022`, commit `cd429d769e66862aef731980934b80d8ab854307`, succès le 30 octobre 2026.

- Analyse syntaxique des 20 scripts et PSScriptAnalyzer réussis.
- 71 tests Pester réussis sous PowerShell 7 et les mêmes 71 sous Windows PowerShell 5.1.
- Détection WebView2 sur les clés officielles et installation contrôlée du runtime sur le runner.
- Environnement MSVC x64 et Windows SDK chargé via `vswhere`/`vcvars64.bat`; compilation et édition de liens d’un programme C++ minimal dans un chemin contenant des espaces.
- Backend autonome PyInstaller Windows, application Tauri 2, MSI et NSIS x64 construits avec sommes SHA-256.
- MSI installé et smoke-testé deux fois, puis désinstallé en préservant les données utilisateur.
- NSIS installé et smoke-testé deux fois, puis désinstallé en préservant les données utilisateur.
- Chaque smoke test a vérifié les fichiers packagés, le backend loopback, son port dynamique, l’origine CORS de Tauri, le rejet 401 sans jeton, le CRUD projets, SQLite, la journalisation, le lancement desktop et la création du sidecar.
- Artefact `agentsec-windows-x64` publié : [MSI, NSIS, sommes et journaux](https://github.com/St0rn/agentsec-inspector/actions/runs/41059965105/artifacts/12982170057).

Cette preuve CI ne signifie pas que tous les scripts de maintenance ont été exécutés nominalement : la matrice indique séparément les scripts validés dynamiquement, partiellement ou seulement statiquement.

## Construit en CI Linux, non construit sur l’hôte local

- Paquets desktop AppImage et DEB Tauri : build CI réussi et artefacts publiés par le run `40916996042`.

L’hôte local ne contient pas WebKitGTK/GTK/libsoup ni Rust dans le `PATH` système : le build local s’arrête donc proprement au contrôle des prérequis. La preuve de build et d’installation provient du runner GitHub Actions Ubuntu, pas de cet hôte local.

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

Sur Windows CI, `check-prerequisites.ps1 -ForBuild`, `setup-database.ps1` (deux fois par moteur PowerShell), `build-windows.ps1`, `test-all.ps1`, `install.ps1`, `verify-installation.ps1` et `uninstall.ps1` ont été exécutés. Les installations et vérifications ont été répétées deux fois pour le MSI puis deux fois pour NSIS. Le chemin de refus de `restore.ps1` a été exécuté par Pester. Les autres scripts PowerShell restent contrôlés statiquement ou par régression ciblée, sans prétention d’exécution nominale. Les scripts Bash Linux de prérequis, installation développeur, base, démarrage, tests, build, installation, vérification, sauvegarde, restauration et cycle de vie ont été exécutés localement ou sur le runner Ubuntu documenté. Voir `docs/VALIDATION_REPORT.md` et `INSTALLATION_VALIDATION_MATRIX.md`.

## Résultats de tests

- Backend : 60/60 réussis; couverture 86,85 % (minimum imposé 80 %); Ruff et mypy réussis.
- Frontend : 17/17 réussis; 87,86 % des lignes avec seuils minimums; lint et build réussis.
- Intégration laboratoire : MCP passif, MCP actif contrôlé et LLM réussis.
- Dépendances : `pip-audit` et `npm audit` sans vulnérabilité connue.
- PyInstaller Linux : binaire autonome construit et smoke-testé, rapports PDF inclus.
- Tauri : test Rust de la configuration IPC réussi, puis compilation Tauri Windows x64, MSI et NSIS réussis dans le run Windows.
- Windows/PowerShell : 71/71 tests réussis sous PowerShell 7 et 71/71 sous Windows PowerShell 5.1; MSVC/SDK, MSI/NSIS, installations répétées, smoke tests et désinstallations validés dans le run `41059965105`.
- Linux/Bash : scripts principaux exécutés; AppImage/DEB construits et AppImage installée/vérifiée deux fois dans le run CI `40916996042`.
