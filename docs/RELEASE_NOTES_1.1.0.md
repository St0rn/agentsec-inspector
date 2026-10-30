# AgentSec Inspector v1.1.0

Cette version étend AgentSec Inspector aux laboratoires et applications qui diffusent leurs réponses en streaming, tout en renforçant la traçabilité des verdicts.

## Principales évolutions

- prise en charge native des réponses JSON, NDJSON, SSE, OpenAI-compatible et Ollama ;
- reconstitution des tokens NDJSON, conservation des événements `status`, `token`, `tool` et `done`, déduplication des outils et suivi de `completed` ;
- aucun nouvel envoi automatique d’un POST après un échec réseau ou HTTP ;
- écran Custom Payload pour les tests multi-tours Prompt Injection, Jailbreak, RAG et Tool Abuse ;
- règles de sécurité structurées et champ `expected_marker` dans les scénarios ;
- les outils autorisés ne sont plus classés automatiquement comme vulnérabilités ;
- modification et test des cibles, détection du protocole et proposition de configuration ;
- historique détaillé, recherche, tri, filtres et exports JSON/PDF ;
- graphe Attack Chains déplaçable, zoomable et sauvegardé par projet ;
- migration additive des preuves d’audit sans suppression des données existantes.

## Validation

Les tests locaux utilisent des transports contrôlés et reproductibles. Le service AI Red Team Range situé sur le poste de l’utilisateur n’était pas accessible depuis l’environnement de build ; aucune validation réelle contre ce service local n’est donc revendiquée.

Les liens des workflows Windows et Linux, les empreintes SHA-256 et les artefacts exacts sont publiés après la réussite des deux validations de plateforme.
