from __future__ import annotations

import uvicorn

from agentsec.config import get_settings
from agentsec.main import app

if __name__ == "__main__":
    settings = get_settings()
    if settings.host not in {"127.0.0.1", "::1", "localhost"}:
        raise SystemExit("AgentSec backend refuses to bind to a non-loopback address")
    uvicorn.run(app, host="127.0.0.1", port=settings.port, log_config=None, access_log=False)
