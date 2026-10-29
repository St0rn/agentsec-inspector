# Architecture

```text
React/TypeScript (WebView2)
        │ IPC: configuration locale
        ▼
Tauri 2 ── lance/arrête ── PyInstaller/FastAPI 127.0.0.1:port aléatoire
                                   │
                ┌──────────────────┼──────────────────┐
                ▼                  ▼                  ▼
             SQLite          MCP/LLM clients      Reports
       projets et preuves   sorties contrôlées   HTML/PDF/JSON
```

Le backend suit les couches `routers`, `schemas`, `models`, `services` et `security`. Les tables dépendantes portent une clé `project_id` et les routes vérifient l’appartenance de la cible au projet. SQLAlchemy active les clés étrangères SQLite et WAL.

Les scénarios sont versionnés par clé composite `(id, version)`. L’ajout futur se fait dans le registre et via le modèle `Scenario`; aucune exécution arbitraire de code plugin n’est autorisée.
