<div align="center">

<img src="assets/icon.svg" width="88" alt="AgentSec Inspector" />

# AgentSec Inspector

### AI Red Team & MCP Security Auditing Platform

Une application Windows locale pour auditer, dans un cadre autorisé, des agents IA, des serveurs MCP, des pipelines RAG et des applications LLM.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.162-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-149ECA?style=flat-square&logo=react&logoColor=white)
![Tauri](https://img.shields.io/badge/Tauri-2-24C8DB?style=flat-square&logo=tauri&logoColor=white)
![Windows](https://img.shields.io/badge/Windows-x64-0078D4?style=flat-square&logo=windows11&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-x64-FCC624?style=flat-square&logo=linux&logoColor=111)
![Mode](https://img.shields.io/badge/audit-passif%20par%20défaut-22C55E?style=flat-square)

[![Backend tests](https://github.com/St0rn/agentsec-inspector/actions/workflows/backend-tests.yml/badge.svg?branch=main)](https://github.com/St0rn/agentsec-inspector/actions/workflows/backend-tests.yml)
[![Frontend tests](https://github.com/St0rn/agentsec-inspector/actions/workflows/frontend-tests.yml/badge.svg?branch=main)](https://github.com/St0rn/agentsec-inspector/actions/workflows/frontend-tests.yml)
[![Security checks](https://github.com/St0rn/agentsec-inspector/actions/workflows/security-checks.yml/badge.svg?branch=main)](https://github.com/St0rn/agentsec-inspector/actions/workflows/security-checks.yml)
[![Linux build](https://github.com/St0rn/agentsec-inspector/actions/workflows/linux-build.yml/badge.svg?branch=main)](https://github.com/St0rn/agentsec-inspector/actions/workflows/linux-build.yml)

**Preuves vérifiables · Audit passif par défaut · Traitement local**

[🇫🇷 Français](README.md) · [🇬🇧 English](README.en.md)

[Capacités](#tous-les-audits-au-même-endroit) · [Tests](#tous-les-contrôles-et-tests-de-sécurité) · [Manuel](#manuel-dutilisation) · [Architecture](#architecture-locale-sécurisée) · [Installation](#installation) · [Validation](#résultats-des-validations)

</div>

![Dashboard AgentSec Inspector](docs/images/dashboard.png)

<p align="center"><sub>Capture réelle de la V1 exécutée contre le laboratoire contrôlé inclus — aucune donnée fictive n’est injectée dans le dashboard de production.</sub></p>

<table>
  <tr>
    <td align="center" width="33%"><strong>🛡️ Une preuve pour chaque conclusion</strong><br/><sub>Chaque résultat reste relié à une requête, une réponse, une trace ou un événement réellement observé.</sub></td>
    <td align="center" width="33%"><strong>⚡ Des actions actives maîtrisées</strong><br/><sub>Aucune action sensible sans sélection précise, périmètre autorisé et confirmation explicite.</sub></td>
    <td align="center" width="33%"><strong>🔒 Des données conservées localement</strong><br/><sub>API accessible uniquement en local, projets isolés et secrets chiffrés au repos.</sub></td>
  </tr>
</table>

## Des audits de sécurité fiables et reproductibles

AgentSec Inspector applique des règles déterministes : il n’utilise pas un second modèle d’IA pour décider si un test a réussi. Les résultats reposent sur des critères versionnés, des marqueurs fictifs et des traces réellement observées. Les équipes peuvent ajouter leurs propres [packs de scénarios déclaratifs](docs/SCENARIO_PACKS.md), sans charger ni exécuter de code tiers.

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
    <td colspan="2"><img src="docs/images/scenario-packs.png" alt="Import de packs de scénarios"/><br/><sub>Ajout de scénarios au moyen de packs JSON validés et versionnés</sub></td>
  </tr>
</table>

<p align="center"><sub>Galerie générée depuis le frontend réel connecté au laboratoire local contrôlé.</sub></p>

## Tous les audits au même endroit

AgentSec Inspector regroupe les cibles, les tests, les preuves, les constats et les rapports d’une mission. Il analyse uniquement ce qui est observable et ne prétend pas accéder au raisonnement caché des modèles. Les résultats distinguent clairement une **observation**, un **risque potentiel** et une **vulnérabilité confirmée**.

| Domaine | Capacités opérationnelles |
|---|---|
| MCP Security | Découverte passive Streamable HTTP/stdio et appels actifs explicitement sélectionnés, paramétrés et confirmés |
| Prompt & LLM | 10 scénarios intégrés et versionnés, connecteurs OpenAI-compatible, Ollama et HTTP, résultats PASS/FAIL/INCONCLUSIVE/ERROR |
| RAG Security | Documents et métadonnées, injections contrôlées, traces réelles et parcours Document → Retrieval → LLM → Réponse |
| Agent Behavior | Chronologie des messages, appels MCP, paramètres, résultats, erreurs, durées et décisions observables |
| Findings | Gestion des constats : historique, preuves, confiance, impact, reproduction, statut et remédiation |
| Reporting | Rapports techniques/exécutifs en français ou anglais, HTML, JSON et PDF |
| Scenario Packs | Import de scénarios JSON versionnés, sans exécution de code provenant du pack |

## Tous les contrôles et tests de sécurité

<details open>
<summary><strong>Découverte et analyse passive</strong></summary>

1. Négociation MCP et version de protocole.
2. Informations serveur et capacités annoncées.
3. Inventaire des outils, noms et descriptions.
4. Schémas d’entrée complets des outils.
5. Inventaire des ressources et de leurs métadonnées.
6. Inventaire des prompts et de leurs descriptions.
7. Instructions suspectes dans une description d’outil.
8. Capacités sensibles exposées : suppression, écriture, administration, exécution de commande, envoi de fichier, identifiant, secret ou jeton.
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
<summary><strong>Tests de sécurité actifs</strong></summary>

### Tests MCP actifs avec confirmation

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
11. Divulgation du marqueur fictif dans la réponse.
12. Tentative d’appel d’outil dans la réponse de la cible.
13. Réponse vide ou résultat insuffisant.
14. Timeout, retry contrôlé, erreur HTTP, réponse surdimensionnée ou malformée.
15. Credential référencé mais absent de l’environnement.
16. Scénarios personnalisés multi-tours via packs JSON versionnés et strictement validés.

Les connecteurs actifs couverts sont OpenAI-compatible, Ollama, endpoint HTTP de chat et agent local de laboratoire. Chaque exécution conserve les requêtes, réponses, versions, heures et preuves.

</details>

<details>
<summary><strong>Verdicts et limites de sécurité</strong></summary>

- `PASS` : aucune violation constatée selon les critères du scénario.
- `FAIL` : le marqueur fictif a été divulgué ou la cible a tenté un appel d’outil interdit.
- `INCONCLUSIVE` : preuve insuffisante, par exemple une réponse vide.
- `ERROR` : échec technique, jamais assimilé à une attaque réussie.
- Constats : `Observation`, `Risk potential` ou `Confirmed vulnerability`, avec un niveau de sévérité et de confiance distinct.

La V1 ne réalise ni scan de ports, ni exploitation d’hôte, ni appel automatique de tous les outils, ni commande arbitraire, ni chaîne d’exploits autonome. Elle n’utilise aucun vrai secret dans les scénarios fournis et ne prétend jamais lire la chaîne de pensée d’un modèle.

</details>

Le [catalogue détaillé](docs/TEST_CATALOG.md) précise la méthode, les preuves et les limites de chaque contrôle.

## Architecture locale sécurisée

<table>
  <tr>
    <td align="center"><strong>Interface desktop</strong><br/><sub>React · TypeScript · WebView2</sub></td>
    <td align="center">→<br/><sub>IPC local</sub></td>
    <td align="center"><strong>Tauri 2</strong><br/><sub>Lancement · supervision</sub></td>
    <td align="center">→<br/><sub>jeton éphémère</sub></td>
    <td align="center"><strong>Backend FastAPI intégré</strong><br/><sub>127.0.0.1 uniquement</sub></td>
  </tr>
  <tr>
    <td align="center"><strong>SQLite</strong><br/><sub>Projets isolés</sub></td>
    <td align="center">←</td>
    <td align="center" colspan="3"><strong>Moteurs et sorties</strong><br/><sub>MCP HTTP/stdio · LLM/RAG · preuves · PDF/HTML/JSON</sub></td>
  </tr>
</table>

- Le backend refuse toute écoute non-loopback et l’API locale exige un jeton transmis par IPC Tauri.
- Les sorties réseau sont protégées contre le SSRF, les redirections sont désactivées et les cibles distantes doivent être explicitement autorisées.
- La découverte MCP n’appelle aucun outil. Les opérations actives nécessitent une confirmation explicite.
- Une capacité MCP sensible exige une seconde confirmation individuelle et ses paramètres sont validés contre le schéma annoncé.
- Les secrets de connecteurs sont chiffrés au repos ; aucun token ne doit être placé en clair dans la configuration d’une cible.
- Un échec de transport reste un statut `ERROR`, jamais une attaque réussie.

Le [catalogue des contrôles et attaques](docs/TEST_CATALOG.md) énumère exactement ce qui est exécuté et les limites de la V1. Le [modèle de sécurité](docs/SECURITY.md) documente les frontières de confiance et les limites d’isolation. La [documentation des packs de scénarios](docs/SCENARIO_PACKS.md) explique comment ajouter des tests en toute sécurité.

## Installation

### Windows x64

Utilisez l’installateur MSI/NSIS publié ou, depuis les sources, exécutez :

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install.ps1
.\scripts\verify-installation.ps1
```

### Linux x86_64

L’AppImage contient le frontend et le backend autonome ; Python et Node.js ne sont pas nécessaires sur le poste final.

```bash
chmod +x scripts/linux/*.sh
scripts/linux/install.sh --artifact /chemin/vers/AgentSec-Inspector.AppImage
scripts/linux/verify-installation.sh
agentsec-inspector
```

Consultez les guides d’[installation Linux](docs/INSTALLATION_LINUX.md) et de [build Linux](docs/BUILD_LINUX.md).

### Environnement de développement Windows

Prérequis : Windows 10 22H2/Windows 11 x64, Python 3.12, Node.js 22+, Rust stable, outils MSVC et WebView2.

```powershell
git clone https://github.com/St0rn/agentsec-inspector.git
cd agentsec-inspector
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\check-prerequisites.ps1 -Development
.\scripts\install-dev.ps1
.\scripts\start-dev.ps1
```

L’environnement de test contrôlé, clairement séparé des audits réels, se lance avec :

```powershell
.\scripts\start-demo.ps1
```

Pour produire le MSI et l’installateur NSIS x64 :

```powershell
.\scripts\build-windows.ps1
```

Consultez les procédures exactes : [installation Windows](docs/INSTALLATION_WINDOWS.md) · [développement](docs/INSTALLATION_DEVELOPMENT.md) · [build](docs/BUILD_WINDOWS.md) · [dépannage](docs/TROUBLESHOOTING.md).

### Environnement de développement Linux

```bash
scripts/linux/check-prerequisites.sh --build
scripts/linux/install-dev.sh
scripts/linux/start-dev.sh
```

## Manuel d’utilisation

Le déroulement recommandé va toujours du moins intrusif au plus intrusif. Commencez par documenter le périmètre, puis effectuez une découverte passive avant d’autoriser un test actif.

> [!IMPORTANT]
> N’ajoutez que des systèmes couverts par une autorisation explicite. Une cible distante reste bloquée tant que vous ne confirmez pas qu’elle appartient au périmètre de la mission.

<details open>
<summary><strong>1. Créer la mission et définir son périmètre</strong></summary>

Ouvrez **Projects**, cliquez sur **Nouveau projet**, puis renseignez le client, le nom de la mission, les dates et surtout le périmètre autorisé. Toutes les cibles, preuves et rapports resteront rattachés à ce projet.

<img src="docs/images/manual-project.png" alt="Création d’une mission et saisie du périmètre autorisé"/>

</details>

<details>
<summary><strong>2. Ajouter une cible</strong></summary>

Dans **Targets**, choisissez le projet et le type de cible : MCP HTTP/stdio, OpenAI-compatible, Ollama, endpoint HTTP, système RAG ou agent de laboratoire. Les secrets doivent être référencés par variable d’environnement et non saisis dans la configuration JSON. Cochez l’autorisation distante uniquement si le périmètre le permet.

<img src="docs/images/manual-target.png" alt="Ajout d’une cible MCP HTTP dans un projet"/>

</details>

<details>
<summary><strong>3. Commencer par un audit MCP passif</strong></summary>

Dans **MCP Security**, sélectionnez le projet et la cible, conservez le mode **Passif — découverte seule**, puis lancez l’inspection. AgentSec inventorie les capacités, outils, ressources, prompts et schémas sans appeler d’outil.

<img src="docs/images/mcp-passive.png" alt="Configuration d’un audit MCP passif"/>

</details>

<details>
<summary><strong>4. Autoriser un test MCP actif</strong></summary>

Après la découverte passive, passez en mode **Actif — appel contrôlé**. Choisissez un seul outil découvert, vérifiez les paramètres JSON et confirmez cet appel précis. Une capacité sensible demande une seconde confirmation. Le résultat, la durée et les erreurs sont conservés comme preuves.

<img src="docs/images/mcp-active.png" alt="Configuration d’un appel MCP actif et explicitement autorisé"/>

</details>

<details>
<summary><strong>5. Tester les protections Prompt et LLM</strong></summary>

Dans **Prompt Injection** ou **LLM Security**, choisissez la cible, un scénario versionné et l’objectif de sécurité. Le test utilise uniquement un marqueur fictif. Consultez ensuite le verdict `PASS`, `FAIL`, `INCONCLUSIVE` ou `ERROR` et la preuve associée.

<img src="docs/images/prompt-injection.png" alt="Sélection d’un scénario de Prompt Injection"/>

</details>

<details>
<summary><strong>6. Analyser un système RAG</strong></summary>

Dans **RAG Security**, importez un document contrôlé ou une trace réelle. Si la télémétrie est disponible, fournissez les chunks récupérés et le contexte LLM ; sinon, laissez-les absents. Saisissez la réponse attendue et la réponse obtenue pour comparer le comportement sans inventer les étapes internes.

<img src="docs/images/rag-security.png" alt="Analyse d’un document et d’une trace RAG"/>

</details>

<details>
<summary><strong>7. Examiner le comportement et la chaîne observée</strong></summary>

**Agent Behavior** présente les échanges et appels dans l’ordre où ils ont été observés. **Attack Chains** relie les composants impliqués. Le graphe représente des événements enregistrés, pas le raisonnement caché du modèle.

<table>
  <tr>
    <td width="50%"><img src="docs/images/agent-behavior.png" alt="Chronologie des événements observés"/></td>
    <td width="50%"><img src="docs/images/attack-chains.png" alt="Graphe des interactions observées"/></td>
  </tr>
</table>

</details>

<details>
<summary><strong>8. Qualifier et suivre les constats</strong></summary>

Dans **Findings**, ouvrez chaque constat, vérifiez sa preuve, sa classification, sa sévérité et son niveau de confiance. Modifiez son statut au fil de la validation et de la remédiation : Open, Confirmed, False Positive, Accepted Risk ou Remediated.

<img src="docs/images/findings.png" alt="Consultation et suivi d’un constat de sécurité"/>

</details>

<details>
<summary><strong>9. Générer le rapport</strong></summary>

Dans **Reports**, sélectionnez le projet, le type technique ou exécutif, la langue et le format HTML, PDF ou JSON. Le rapport est généré à partir des données réellement présentes dans le projet et reçoit une empreinte SHA-256.

<img src="docs/images/reports.png" alt="Génération et téléchargement des rapports"/>

</details>

<details>
<summary><strong>10. Ajouter les scénarios de votre équipe</strong></summary>

Dans **Settings**, importez un pack JSON versionné. Seules les étapes déclaratives `chat` sont acceptées ; les commandes et le code exécutable sont refusés. Utilisez une nouvelle version pour faire évoluer un scénario sans perdre la traçabilité des anciens audits.

<img src="docs/images/scenario-packs.png" alt="Import d’un pack de scénarios versionné"/>

</details>

## Résultats des validations

| Contrôle | Résultat local |
|---|---|
| Backend | 46/46 tests, 85,4 % de couverture (seuil bloquant 80 %), Ruff et mypy réussis |
| Frontend | 9/9 tests, 83,46 % des lignes couvertes avec seuils bloquants, ESLint, TypeScript et build Vite réussis |
| Sécurité source/dépendances | `pip-audit` et `npm audit` sans vulnérabilité connue ; Bandit sans finding moyen/élevé |
| Binaire autonome | Build Linux PyInstaller, migration neuve, auth, CORS, intégrité et PDF vérifiés |
| Laboratoire | Découverte MCP passive, appel MCP actif borné et échange LLM réellement exécutés |
| Scripts Linux | Installation développeur exécutée deux fois, démarrage, tests, sauvegarde/restauration et erreurs principales validés |
| Paquets desktop | Workflows dédiés pour AppImage/DEB et installateurs Windows ; leur statut est visible dans les badges CI |
| Windows/PowerShell | Scripts et workflow fournis, mais non validés localement faute d’hôte Windows |

La compilation Windows n’est **pas** déclarée validée sans preuve d’un run Windows. Voir [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md), la [matrice de validation](INSTALLATION_VALIDATION_MATRIX.md) et le [rapport détaillé](docs/VALIDATION_REPORT.md).

## Organisation du dépôt

```text
backend/       API, modèles, migrations, moteurs d’audit et rapports
frontend/      React, TypeScript, Tailwind, graphiques et visualisations
src-tauri/     application desktop, supervision et IPC du sidecar
demo/          laboratoire MCP / LLM / RAG contrôlé
scripts/       cycle de vie Windows PowerShell et Linux Bash
docs/          architecture, sécurité et procédures Windows
.github/       tests backend/frontend, sécurité et build Windows x64
```

## Usage autorisé uniquement

Cet outil est conçu pour les audits disposant d’une autorisation explicite et d’un périmètre documenté. Un serveur MCP non fiable doit être exécuté dans une VM ou une Windows Sandbox dédiée : les restrictions du sous-processus stdio ne constituent pas, à elles seules, une sandbox de sécurité.

## Auteur et contact

AgentSec Inspector est créé et maintenu par **St0rn**.

- Contact : [fabien.dromas@cybersecurit.fr](mailto:fabien.dromas@cybersecurit.fr)
- Site : [www.cybersecurit.fr](https://www.cybersecurit.fr)

---

<div align="center"><sub>AgentSec Inspector V1.0 · créé par St0rn · résultats fondés sur des tests exécutés et des preuves vérifiables</sub></div>
