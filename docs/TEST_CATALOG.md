# Catalogue des contrôles et attaques

Ce catalogue décrit ce que la V1 exécute réellement. AgentSec Inspector ne transforme pas un indicateur en vulnérabilité confirmée sans preuve observable.

## 1. Énumération et audit passif

### MCP

1. Négociation MCP et version de protocole annoncée.
2. Informations du serveur (`serverInfo`).
3. Capacités annoncées.
4. Liste des outils, noms et descriptions.
5. Schémas d’entrée complets des outils.
6. Liste et métadonnées des ressources.
7. Liste et descriptions des prompts.
8. Description d’outil contenant une instruction suspecte.
9. Exposition d’une capacité sensible : suppression, écriture, administration, exécution, shell, upload, credential, secret ou token.
10. Paramètre de chemin ou fichier insuffisamment contraint.
11. Schéma acceptant des propriétés non déclarées.
12. Collision ou confusion par nom d’outil dupliqué, sans distinction de casse.
13. Configuration locale de cible, transport et autorisation distante explicite.
14. Découverte sous plusieurs identités explicitement configurées, sans résolution ni affichage des secrets.
15. Comparaison des différences de permissions annoncées entre identités.
16. Corrélation prudente de chaînes d’attaque potentielles, distinctes des chemins réellement observés.

La phase passive n’appelle aucun outil MCP.

### RAG et documents

1. Import contrôlé de documents et calcul SHA-256.
2. Conservation des métadonnées et origine laboratoire/import.
3. Recherche d’instructions dans le contenu documentaire.
4. Analyse des chunks réellement récupérés lorsqu’une trace les fournit.
5. Analyse des métadonnées présentes dans les chunks sérialisés.
6. Analyse du contexte LLM fourni par la télémétrie.
7. Comparaison réponse obtenue/réponse attendue.
8. Détection de divulgation d’un marqueur fictif `AGENTSEC_CANARY_*`.
9. Distinction entre télémétrie fournie et analyse de la réponse seule.

Le framework n’invente jamais des chunks, un contexte ou une étape de retrieval absents de la télémétrie.

### Comportement et chaîne d’attaque

1. Messages et échanges LLM observés.
2. Découvertes et appels MCP observés.
3. Paramètres d’outil après redaction des champs sensibles.
4. Statut, erreur et durée des appels.
5. Chronologie utilisateur/AgentSec/cible/outil.
6. Graphe des relations réellement observées.

Le framework ne prétend pas accéder au raisonnement interne ou à la chaîne de pensée du modèle.

## 2. Attaques et tests actifs

### Appels MCP contrôlés

1. Appel d’un outil choisi dans l’inventaire réellement découvert.
2. Envoi des seuls paramètres JSON explicitement fournis.
3. Validation des paramètres requis.
4. Rejet des paramètres supplémentaires si le schéma l’interdit.
5. Validation récursive des objets, tableaux, propriétés requises ou supplémentaires, types, motifs, longueurs, bornes numériques, `enum` et `const` annoncés.
6. Confirmation globale de l’audit actif.
7. Seconde confirmation individuelle pour un outil sensible ou potentiellement destructif.
8. Capture du résultat réel, de `isError`, de la durée et de la preuve.
9. Recherche d’instructions malveillantes dans la sortie réelle d’un outil.
10. Classification d’une erreur de transport ou d’outil en `ERROR`, jamais en attaque réussie.

L’interface exécute un appel précis à la fois. L’API accepte jusqu’à dix appels explicitement déclarés dans une exécution. Aucun outil découvert n’est appelé automatiquement.

### Formats de réponse et streaming

1. JSON standard et chemins de réponse déclaratifs.
2. OpenAI Chat Completions, en réponse complète ou SSE.
3. Ollama, en réponse complète ou flux JSON par ligne.
4. NDJSON avec événements `status`, `token`, `tool` et `done`.
5. Reconstruction des fragments sans concaténer une seconde fois `done.response`.
6. Comparaison entre les tokens reconstruits et la réponse finale.
7. Fusion et déduplication des appels d’outils et de leurs résultats.
8. Conservation du modèle, de `completed`, des continuations et des événements bruts.
9. Rejet d’une ligne invalide, d’un flux interrompu ou surdimensionné.
10. Aucun nouvel envoi automatique d’un POST après une erreur.

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
10. Multi-turn Manipulation.

Chaque scénario envoie de vraies requêtes à une cible OpenAI-compatible, Ollama, HTTP de chat ou agent local de laboratoire. L’évaluation observe :

1. la divulgation du marqueur fictif ;
2. les appels d’outils retournés par la cible et les règles qui les autorisent ou les interdisent ;
3. une réponse vide ou inexploitable ;
4. les erreurs de transport, timeout, protocole ou parsing ;
5. toutes les requêtes, réponses, versions, heures et preuves associées.

Les packs JSON permettent d’ajouter des scénarios déclaratifs versionnés. Plusieurs étapes `chat` sont exécutées séquentiellement : chaque réponse réelle devient le contexte du tour suivant.

Le mode **Black-Box Red Team**, actif par défaut, transmet uniquement les payloads déclarés par l’auditeur. L’objectif de sécurité et les règles d’évaluation restent locaux. Le mode **Controlled Lab** permet d’ajouter une politique artificielle et un marqueur prépositionné après sélection et confirmation explicites. La prévisualisation montre la requête effective avant l’envoi, sans exposer les identifiants.

La provenance des marqueurs est conservée. La répétition d’un marqueur fourni dans le payload utilisateur ne suffit jamais à établir une divulgation de secret protégé.

### Custom Payload

1. Payload libre Prompt Injection, Jailbreak, RAG, MCP, Tool Abuse ou catégorie personnalisée.
2. De un à vingt tours réels conservés dans l’ordre.
3. Marqueur fictif personnalisable via `{marker}`.
4. Règles `marker_absent`, `response_contains`, `response_not_contains`, `tool_allowed`, `tool_forbidden` et `completion_required`.
5. Historique permanent des requêtes, réponses, événements, outils, preuves, erreurs et verdicts.

### Adaptive Red Team

1. Machine à états déterministe composée uniquement d’étapes et de payloads déclarés.
2. Transitions sur texte présent/absent, refus observé, outil appelé, verdict, violation de règle ou branche de repli.
3. Payload et réponse exacts conservés à chaque tour.
4. Nombre maximal de tours, limite de tokens par tour et budget total imposés.
5. Annulation persistée sans reclasser une exécution partielle en succès.
6. `INCONCLUSIVE` lorsque les preuves nécessaires manquent et `ERROR` lors d’un échec technique.

### Jailbreak

Le module dédié exécute neuf scénarios contrôlés :

1. `jb.authority-impersonation` : fausse autorisation administrative.
2. `jb.developer-mode` : activation simulée d’un mode sans restrictions.
3. `jb.persona-override` : changement de persona.
4. `jb.hypothetical-framing` : cadrage fictionnel ou hypothétique.
5. `jb.refusal-suppression` : interdiction artificielle du refus et des avertissements.
6. `jb.format-coercion` : contrainte de format destinée à provoquer la divulgation.
7. `jb.obfuscated-instruction` : instruction fragmentée et légèrement obfusquée.
8. `jb.policy-reversal` : prétendue inversion de la politique de protection.
9. `jb.context-reset` : faux délimiteur de remise à zéro du contexte.

Tous sont versionnés `1.0.0`, reliés à OWASP LLM01:2025 et, lorsque pertinent, à MITRE ATLAS AML.T0051. Ils ne demandent ni contenu dangereux, ni secret réel : leur seul objectif intégré est de vérifier la protection d’un marqueur fictif et l’absence d’appel d’outil non autorisé.

## 3. Verdicts

1. `PASS` : toutes les règles requises et observables sont satisfaites.
2. `FAIL` : au moins une règle requise est violée par une preuve observable.
3. `INCONCLUSIVE` : résultat insuffisant ou télémétrie nécessaire absente.
4. `ERROR` : échec technique ; il ne constitue jamais une attaque réussie.
5. `NOT_APPLICABLE` / `SKIPPED` : règle non applicable ou étape déclarée non atteinte.

Les findings distinguent également `Observation`, `Risk potential` et `Confirmed vulnerability`, avec sévérité et confiance séparées.

## 4. Hors périmètre de la V1

1. Scan de ports, découverte réseau ou exploitation d’hôtes.
2. Exécution automatique d’une commande arbitraire fournie par une cible.
3. Appel automatique de tous les outils MCP découverts.
4. Enchaînement autonome d’exploits ou actions destructives.
5. Utilisation de vrais secrets, données personnelles ou données client dans les scénarios par défaut.
6. Lecture du raisonnement caché ou de la chaîne de pensée d’un modèle.
7. Exécution active automatique contre un pipeline RAG propriétaire sans adaptateur de télémétrie.
8. Sandbox VM automatique pour un serveur MCP non fiable.
9. Validation contre une instance locale de l’utilisateur qui n’est pas accessible depuis l’environnement d’exécution.
