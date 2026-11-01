# AgentSec Inspector v1.5.0 — Evidence-driven Black-Box Red Team

AgentSec Inspector 1.5.0 separates the payload sent to a target from the auditor's local objective and evaluation rules. Black-Box Red Team is now the default; Controlled Lab remains available for deliberately artificial policies and protected markers.

## Highlights

- Exact request preview for Prompt Injection, Jailbreak, LLM Security, and Custom Payload.
- Marker provenance and deterministic, rule-by-rule verdicts; a user-supplied marker echoed by the target is not treated as a protected-secret disclosure. Controlled Lab places its synthetic protected marker only in the explicitly displayed artificial system policy, never in the user payload.
- Adaptive Red Team state machine with observable transitions, exact multi-turn evidence, cancellation, and token/turn budgets.
- Advanced MCP analysis with explicitly configured identities, permission differences, conservative attack-chain correlation, and recursive input-schema validation.
- RAG document import for TXT, Markdown, and PDF, strict size limits, extraction metadata, and evidence requirements for adversarial verdicts.
- English interface by default with an immediate French switch in Settings. Report language remains independent.
- Historical audit notices when older records do not contain fields that cannot be reconstructed safely.
- Every README and user-manual screenshot was regenerated from the v1.5.0 application connected to the controlled local laboratory, including the A4 report cover, finding, and exact payload views.

## Security boundaries

- Passive MCP discovery never invokes a tool.
- Active operations still require explicit, scoped confirmation.
- Security objectives, local rules, and credentials are not sent in Black-Box mode.
- Missing telemetry is not invented and normally produces `INCONCLUSIVE`.
- Technical failures remain `ERROR` and do not create confirmed-vulnerability findings.
- MCP identity comparison uses only identities explicitly configured by the auditor; AgentSec does not enumerate or guess credentials.

## Local validation before publication

- Backend: 101 tests passed; total coverage reached 85.19% with the 80% threshold enforced; Ruff and mypy passed.
- Frontend: 56 tests passed; ESLint, TypeScript, and the production Vite build passed; line coverage reached 80.15% with the 80% threshold enforced.
- Dependencies: `pip-audit` found no known Python vulnerability; Bandit found no medium/high issue. The high-severity npm gate passed. Twelve moderate `minimatch` advisories remain in the development-only lint dependency tree and are documented rather than hidden behind a breaking forced downgrade.
- Screenshot workflow: executed locally against the real FastAPI backend and the controlled MCP/LLM/RAG laboratory; all expected images were generated and checked for browser errors.

Windows x64 MSI/NSIS and Linux x86_64 AppImage/DEB validation links and SHA-256 values are added to the GitHub release after the platform workflows complete successfully. A source commit or local test run alone is not presented as installer validation.
