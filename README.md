<div align="center">

<img src="assets/icon.svg" width="88" alt="AgentSec Inspector" />

# AgentSec Inspector

### AI Red Team & MCP Security Auditing Platform

Un framework Windows local-first pour conduire, avec autorisation, des campagnes de red team sur les agents IA, serveurs MCP, pipelines RAG et applications LLM.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.162-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-149ECA?style=flat-square&logo=react&logoColor=white)
![Tauri](https://img.shields.io/badge/Tauri-2-24C8DB?style=flat-square&logo=tauri&logoColor=white)
![Windows](https://img.shields.io/badge/Windows-x64-0078D4?style=flat-square&logo=windows11&logoColor=white)
![Mode](https://img.shields.io/badge/audit-passif%20par%20défaut-22C55E?style=flat-square)

</div>

![Dashboard AgentSec Inspector](docs/images/dashboard.png)

<p align="center"><sub>Capture réelle de la V1 exécutée contre le laboratoire contrôlé inclus — aucune donnée fictive n’est injectée dans le dashboard de production.</sub></p>

## Framework de red team IA reproductible

Le framework ne dépend d’aucun « juge IA » externe. Ses décisions reposent sur des critères versionnés, des marqueurs fictifs, les traces réellement observées et des preuves conservées. Les équipes peuvent importer leurs propres [packs déclaratifs de scénarios](docs/SCENARIO_PACKS.md), sans charger ni exécuter de code tiers.

<table>
  <tr>
    <td width="50%"><img src="docs/images/mcp-active.png" alt="Audit MCP actif contrôlé"/><br/><sub>Appel MCP actif borné et explicitement autorisé</sub></td>
    <td width="50%"><img src="docs/images/prompt-injection.png" alt="Prompt Injection Tester"/><br/><sub>Scénarios d’injection versionnés avec marqueur fictif</sub></td>
  </tr>
  <tr>
    <td width="50%"><img src="docs/images/findings.png" alt="Gestion des findings"/><br/><sub>Finding traçable, sévérité, confiance et remédiation</sub></td>
    <td width="50%"><img src="docs/images/attack-chains.png" alt="Visualisation de chaîne d’attaque"/><br/><sub>Graphe construit uniquement à partir d’interactions observées</sub></td>
  </tr>
  <tr>
    <td colspan="2"><img src="docs/images/scenario-packs.png" alt="Import de packs de scénarios"/><br/><sub>Extension du framework par packs JSON validés et versionnés</sub></td>
  </tr>
</table>

<p align="center"><sub>Galerie générée depuis le frontend réel connecté au laboratoire local contrôlé.</sub></p>

## Une surface d’audit unifiée

AgentSec Inspector centralise les preuves techniques sans prétendre observer le raisonnement caché des modèles. Les résultats distinguent explicitement une **observation**, un **risque potentiel** et une **vulnérabilité confirmée**.

| Domaine | Capacités opérationnelles |
|---|---|
| MCP Security | Découverte passive Streamable HTTP/stdio et appels actifs explicitement sélectionnés, paramétrés et confirmés |
| Prompt & LLM | 10 scénarios versionnés, OpenAI-compatible, Ollama et endpoint HTTP, statuts PASS/FAIL/INCONCLUSIVE/ERROR |
| RAG Security | Documents et métadonnées, injections contrôlées, traces réelles et parcours Document → Retrieval → LLM → Réponse |
| Agent Behavior | Timeline des messages, appels MCP, paramètres, résultats, erreurs, durées et décisions observables |
| Findings | Cycle de vie complet, historique, preuves, confiance, impact, reproduction et remédiation |
| Reporting | Rapports techniques/exécutifs en français ou anglais, HTML, JSON et PDF |
| Scenario Packs | Import JSON versionné, critères et références extensibles, sans exécution de code plugin |

## Tous les contrôles et tests de sécurité

<details open>
<summary><strong>Énumération et audit passif</strong></summary>

1. Négociation MCP et version de protocole.
2. Informations serveur et capacités annoncées.
3. Inventaire des outils, noms et descriptions.
4. Schémas d’entrée complets des outils.
5. Inventaire des ressources et de leurs métadonnées.
6. Inventaire des prompts et de leurs descriptions.
7. Instructions suspectes dans une description d’outil.
8. Capacités sensibles exposées : suppression, écriture, administration, exécution, shell, upload, credential, secret ou token.
9. Paramètres de chemin ou fichier insuffisamment contraints.
10. Schémas acceptant des propriétés non déclarées.
11. Noms d’outils dupliqués ou ambigus sans distinction de casse.
12. Configuration du transport et autorisation distante explicite.
13. Import de documents RAG avec empreinte SHA-256 et origine contrôlée.
14. Recherche d’instructions dans les documents.
15. Inspection des chunks récupérés et de leurs métadonnées lorsqu’ils sont fournis.
16. Inspection du contexte LLM lorsque la télémétrie le fournit.
17. Comparaison entre réponse obtenue et réponse attendue.
18. Détection d’un marqueur fictif `AGENTSEC_CANARY_*` dans une réponse RAG.
19. Distinction entre télémétrie réelle et analyse de réponse seule.
20. Collecte des échanges LLM, découvertes MCP et appels d’outils observés.
21. Collecte des paramètres caviardés, erreurs, statuts et durées.
22. Timeline des interactions et graphe des relations réellement observées.

La phase passive n’appelle aucun outil MCP et n’invente aucune étape interne absente de la télémétrie.

</details>

<details open>
<summary><strong>Attaques et tests actifs</strong></summary>

### MCP actif contrôlé

1. Appel d’un outil choisi dans l’inventaire réellement découvert.
2. Envoi des seuls paramètres JSON explicitement autorisés.
3. Validation des paramètres requis et des propriétés supplémentaires.
4. Validation des types simples, valeurs `enum` et constantes annoncées.
5. Confirmation globale de l’audit actif.
6. Seconde confirmation pour une capacité sensible ou potentiellement destructive.
7. Capture de la sortie réelle, du drapeau `isError`, de la durée et de la preuve.
8. Détection d’instructions malveillantes dans la sortie réelle d’un outil.
9. Classement des erreurs de transport ou d’outil en `ERROR`, jamais en attaque réussie.

### Prompt Injection et sécurité LLM

1. Direct Prompt Injection.
2. Indirect Prompt Injection.
3. Instruction Hierarchy Confusion.
4. Role Spoofing.
5. Tool Output Injection.
6. Context Manipulation.
7. RAG Prompt Injection.
8. System Prompt Disclosure Attempt avec secret fictif.
9. Agent Goal Hijacking.
10. Multi-turn Manipulation avec plusieurs échanges réels.
11. Divulgation observable du marqueur fictif.
12. Tentatives observables d’appel d’outil.
13. Réponse vide ou résultat insuffisant.
14. Timeout, retry contrôlé, erreur HTTP, réponse surdimensionnée ou malformée.
15. Credential référencé mais absent de l’environnement.
16. Scénarios personnalisés multi-tours via packs JSON versionnés et strictement validés.

Les connecteurs actifs couverts sont OpenAI-compatible, Ollama, endpoint HTTP de chat et agent local de laboratoire. Chaque exécution conserve les requêtes, réponses, versions, heures et preuves.

</details>

<details>
<summary><strong>Verdicts et limites de sécurité</strong></summary>

- `PASS` : aucune violation observable du critère intégré.
- `FAIL` : marqueur fictif divulgué ou appel d’outil observable sous le scénario contrôlé.
- `INCONCLUSIVE` : preuve insuffisante, par exemple une réponse vide.
- `ERROR` : échec technique, jamais assimilé à une attaque réussie.
- Findings : `Observation`, `Risk potential` ou `Confirmed vulnerability`, avec sévérité et confiance distinctes.

La V1 ne réalise ni scan de ports, ni exploitation d’hôte, ni appel automatique de tous les outils, ni commande arbitraire, ni chaîne d’exploits autonome. Elle n’utilise aucun vrai secret dans les scénarios fournis et ne prétend jamais lire la chaîne de pensée d’un modèle.

</details>

Le [catalogue détaillé](docs/TEST_CATALOG.md) précise la méthode, les preuves et les limites de chaque contrôle.

## Architecture locale sécurisée

```mermaid
flowchart LR
    UI[React + TypeScript<br/>WebView2] -->|IPC local| T[Tauri 2]
    T -->|lance et supervise| API[FastAPI sidecar<br/>127.0.0.1 + jeton éphémère]
    API --> DB[(SQLite<br/>projets isolés)]
    API --> MCP[MCP HTTP / stdio<br/>passif par défaut]
    API --> LLM[LLM / RAG<br/>sorties contrôlées]
    API --> REP[PDF · HTML · JSON]
```

- Le backend refuse toute écoute non-loopback et l’API locale exige un jeton transmis par IPC Tauri.
- Les sorties réseau sont protégées contre le SSRF, les redirections sont désactivées et les cibles distantes doivent être explicitement autorisées.
- La découverte MCP n’appelle aucun outil. Les opérations actives nécessitent une confirmation explicite.
- Une capacité MCP sensible exige une seconde confirmation individuelle et ses paramètres sont validés contre le schéma annoncé.
- Les secrets de connecteurs sont chiffrés au repos ; aucun token ne doit être placé en clair dans la configuration d’une cible.
- Un échec de transport reste un statut `ERROR`, jamais une attaque réussie.

Le [catalogue des contrôles et attaques](docs/TEST_CATALOG.md) énumère exactement ce qui est exécuté et les limites de la V1. Le [modèle de sécurité](docs/SECURITY.md) documente les frontières de confiance et les limites d’isolation. La [Scenario Pack API](docs/SCENARIO_PACKS.md) décrit l’extension sûre du framework.

## Démarrage développeur sous Windows

Prérequis : Windows 10 22H2/Windows 11 x64, Python 3.12, Node.js 22+, Rust stable, outils MSVC et WebView2.

```powershell
git clone https://github.com/St0rn/agentsec-inspector.git
cd agentsec-inspector
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\check-prerequisites.ps1 -Development
.\scripts\install-dev.ps1
.\scripts\start-dev.ps1
```

Le laboratoire reproductible et clairement séparé des audits réels se lance avec :

```powershell
.\scripts\start-demo.ps1
```

Pour produire le MSI et l’installateur NSIS x64 :

```powershell
.\scripts\build-windows.ps1
```

Consultez les procédures exactes : [installation Windows](docs/INSTALLATION_WINDOWS.md) · [développement](docs/INSTALLATION_DEVELOPMENT.md) · [build](docs/BUILD_WINDOWS.md) · [dépannage](docs/TROUBLESHOOTING.md).

## Validation observée

| Contrôle | Résultat local |
|---|---|
| Backend | 46/46 tests, 85,4 % de couverture (seuil bloquant 80 %), Ruff et mypy réussis |
| Frontend | 9/9 tests, 83,46 % des lignes couvertes avec seuils bloquants, ESLint, TypeScript et build Vite réussis |
| Sécurité source/dépendances | `pip-audit` et `npm audit` sans vulnérabilité connue ; Bandit sans finding moyen/élevé |
| Binaire autonome | Build Linux PyInstaller, migration neuve, auth, CORS, intégrité et PDF vérifiés |
| Laboratoire | Découverte MCP passive, appel MCP actif borné et échange LLM réellement exécutés |
| Rust/Tauri | `cargo fmt` et métadonnées verrouillées réussis ; build Windows confié à la CI |
| Windows/PowerShell | Scripts et workflow fournis, mais non validés localement faute d’hôte Windows |

La compilation Windows n’est **pas** déclarée validée sans preuve d’un run Windows. Voir [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md), la [matrice de validation](INSTALLATION_VALIDATION_MATRIX.md) et le [rapport détaillé](docs/VALIDATION_REPORT.md).

## Organisation du dépôt

```text
backend/       API, modèles, migrations, moteurs d’audit et rapports
frontend/      React, TypeScript, Tailwind, graphiques et visualisations
src-tauri/     application desktop, supervision et IPC du sidecar
demo/          laboratoire MCP / LLM / RAG contrôlé
scripts/       installation, build, test, update, backup et désinstallation
docs/          architecture, sécurité et procédures Windows
.github/       tests backend/frontend, sécurité et build Windows x64
```

## Usage autorisé uniquement

Cet outil est conçu pour les audits disposant d’une autorisation explicite et d’un périmètre documenté. Un serveur MCP non fiable doit être exécuté dans une VM ou une Windows Sandbox dédiée : les restrictions du sous-processus stdio ne constituent pas, à elles seules, une sandbox de sécurité.

---

<div align="center"><sub>AgentSec Inspector V1.0 · résultats fondés sur des exécutions et preuves observables</sub></div>
