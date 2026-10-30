# Cibles chatbot génériques / Generic chatbot targets

## Français

Le type **Chatbot générique** permet d’auditer une API de conversation qui n’utilise ni le format OpenAI Chat Completions ni le format Ollama. AgentSec envoie une requête JSON à l’**URL cible** exacte et extrait la réponse au moyen de chemins déclaratifs. Il n’exécute aucun script d’adaptation.

### Choisir le bon type

| API auditée | Type de cible |
|---|---|
| OpenAI ou API compatible Chat Completions | API compatible OpenAI |
| Ollama | Ollama |
| API JSON de chatbot propre à une application | Chatbot générique |
| Serveur MCP Streamable | MCP distant |

### Attributs de configuration

| Attribut | Type | Défaut | Fonction |
|---|---|---|---|
| `message_path` | chaîne | `message` | Emplacement du dernier message utilisateur dans le JSON envoyé |
| `history_path` | chaîne | absent | Emplacement facultatif de l’historique complet `[{role, content}]` |
| `response_path` | chaîne | `response` | Emplacement du texte dans la réponse JSON |
| `tool_calls_path` | chaîne | absent | Emplacement facultatif de la liste des appels/actions exposés |
| `max_tokens_path` | chaîne | absent | Emplacement facultatif de la limite de génération |
| `static_payload` | objet | `{}` | Valeurs ajoutées à chaque requête ; ne pas y placer d’identifiant ni de clé |
| `headers` | objet | `{}` | En-têtes ajoutés à la requête ; n’y placez ni clé ni jeton |
| `api_key_env` | chaîne | absent | Nom de la variable d’environnement contenant l’identifiant |
| `api_key_header` | chaîne | `Authorization` | En-tête recevant l’identifiant lu dans l’environnement |
| `api_key_prefix` | chaîne | `Bearer` | Préfixe placé avant l’identifiant ; utiliser `""` pour aucun préfixe |
| `retries` | entier | valeur applicative | Nombre borné de nouvelles tentatives sur une erreur transitoire |

Les chemins utilisent une notation pointée, comme `request.input.message` ou `result.items.0.text`. Les chemins de requête créent des objets imbriqués. Les chemins de réponse peuvent également lire un index de tableau.

### Exemple complet

Configuration enregistrée dans la cible :

```json
{
  "message_path": "request.input.message",
  "history_path": "request.input.history",
  "max_tokens_path": "request.generation.limit",
  "response_path": "result.answer.text",
  "tool_calls_path": "result.actions",
  "static_payload": {
    "tenant": "audit-lab",
    "channel": "agentsec"
  },
  "api_key_env": "CHATBOT_API_KEY",
  "api_key_header": "X-API-Key",
  "api_key_prefix": ""
}
```

Pour un message `Bonjour`, AgentSec envoie notamment :

```json
{
  "tenant": "audit-lab",
  "channel": "agentsec",
  "request": {
    "input": {
      "message": "Bonjour",
      "history": [
        {"role": "user", "content": "Bonjour"}
      ]
    },
    "generation": {"limit": 512}
  }
}
```

Une réponse compatible peut être :

```json
{
  "result": {
    "answer": {"text": "Bonjour, comment puis-je vous aider ?"},
    "actions": []
  }
}
```

### Identifiants et sécurité réseau

Définissez l’identifiant dans l’environnement qui lance AgentSec :

```powershell
$env:CHATBOT_API_KEY = 'valeur-fournie-pour-la-mission'
.\scripts\start-dev.ps1
```

Ne placez jamais une clé dans l’URL, `static_payload` ou `headers`. Les en-têtes de transport sensibles (`Host`, `Content-Length`, `Authorization`, cookies, etc.) sont refusés dans `headers`; l’authentification doit utiliser `api_key_env`. Les redirections sont désactivées, la taille de réponse est bornée et une cible distante doit être explicitement autorisée dans le périmètre.

La V1 prend en charge les API JSON accessibles par requête POST. Un widget web nécessitant un navigateur, des cookies de session interactifs, WebSocket ou un protocole propriétaire nécessite un adaptateur futur ; AgentSec ne simule pas ces échanges.

---

## English

The **Generic chatbot** target audits conversational JSON APIs that do not implement OpenAI Chat Completions or Ollama. AgentSec posts JSON to the exact **target URL** and maps the request and response through declarative dot paths; it never runs adapter code supplied by a target.

Use `message_path`, optional `history_path`, `response_path`, optional `tool_calls_path`, `max_tokens_path`, and `static_payload` as documented in the table above. Reference credentials through `api_key_env`; `api_key_header` and `api_key_prefix` control how that environment value is sent.

Dot paths such as `request.input.message` create nested request objects. Response paths such as `result.items.0.text` may read array indexes. The V1 connector supports JSON POST APIs. Browser widgets, interactive session cookies, WebSocket transports, and proprietary protocols require a future adapter and are not simulated.

Remote access still requires explicit authorization. Redirects are disabled, response size is bounded, embedded URL credentials and sensitive static headers are rejected, and transport errors remain `ERROR` rather than successful attacks.
