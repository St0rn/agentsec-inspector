# AgentSec controlled laboratory

This directory is **demo data**, never production audit data. It provides reproducible loopback-only endpoints:

- OpenAI-compatible deterministic chat (`/v1/chat/completions`)
- MCP Streamable HTTP discovery (`/mcp`)
- a small RAG endpoint with explicit retrieval telemetry (`/rag/query`)

Start with `python -m uvicorn server:app --app-dir demo --host 127.0.0.1 --port 8877`.
