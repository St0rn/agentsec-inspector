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

Validations de plateforme :

- [Windows x64 — MSI/NSIS, installations répétées et smoke tests](https://github.com/St0rn/agentsec-inspector/actions/runs/41108334253) ;
- [Linux x64 — AppImage/DEB et installation répétée](https://github.com/St0rn/agentsec-inspector/actions/runs/41108334280) ;
- [publication contrôlée de la release](https://github.com/St0rn/agentsec-inspector/actions/runs/41110672480).

Les quatre paquets et leur fichier `SHA256SUMS.txt` sont disponibles dans cette release. Empreintes SHA-256 :

```text
1b3640f77316b7a5290942cb095c61be65a117dae9b4314a028250e1503687a7  AgentSec-Inspector_1.1.0_amd64.AppImage
1863921b3aa008cac2281a93006ef6c2e43e0faf48edb450bdad21b433516739  AgentSec-Inspector_1.1.0_amd64.deb
a99cd189cb06d3ebf9e9c06782b7013ed8a2ac14fae4c4455906dc08cc98aa51  AgentSec-Inspector_1.1.0_x64-setup.exe
359ce23388102612758a945243f403ba487ce4b47879295842ce02b7e2a3638d  AgentSec-Inspector_1.1.0_x64_en-US.msi
```
