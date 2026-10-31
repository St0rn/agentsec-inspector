# AgentSec Inspector v1.3.0 — MCP & RAG Security

This release extends the local Windows and Linux desktop application with evidence-based RAG testing, MCP result visualization, and finding deduplication.

## Highlights

- **Active RAG Security** — authorized real-endpoint campaigns with baseline and indirect-injection test cases; optional explicitly approved ingestion of controlled laboratory documents; recorded retrieval chunks and LLM context where the API supplies them; PASS / FAIL / INCONCLUSIVE / ERROR verdicts with observed evidence.
- **MCP Security** — pagination-aware tools/resources/prompts discovery, cursor-loop protection, fewer false positives from benign tool descriptions, and structured active-call results with a raw JSON evidence view.
- **Findings** — persistent target- and rule-scoped fingerprints, recurrence counts, first/last seen timestamps, and audit-linked occurrence history.
- **History** — individual and project-scoped audit-history deletion with explicit confirmation and safeguards for shared findings.
- **Desktop** — consistent `1.3.0` identity in the Tauri application, Python backend, Rust package, frontend, and MCP client.
- **License** — MIT, copyright (c) 2026 Fabien Dromas (St0rn).

## Supported platforms

- Windows x64: MSI and NSIS setup executable.
- Linux x86_64: AppImage and DEB.
- The desktop installers bundle the local Python backend.

## Security and limitations

The backend is loopback-only and uses a local bearer token. Active tests require confirmation and authorized scope. MCP tool capability observations are not proof of an exploitable vulnerability. RAG findings depend on retrieval telemetry and explicit test oracles; missing telemetry results in an inconclusive verdict, not a fabricated finding. Keep unfamiliar MCP stdio servers inside a disposable VM or sandbox.

## Validation

The release publication workflow only accepts verified Windows and Linux build runs for the exact tag SHA and generates `SHA256SUMS.txt`. Source, frontend and backend tests as well as dependency checks run through GitHub Actions. Inspect the linked actions for the final version-specific status.

## Install and update

Download the package appropriate for your OS, check the SHA-256 checksum, and use the installation instructions in `README.md`, `README.en.md`, and `docs/INSTALLATION_*.md`. Back up existing engagement data before upgrading.

---

**Changes are intended for professional, explicitly authorized security assessments.**

## Notes en français

La v1.3.0 apporte l’audit RAG actif avec verdicts fondés sur des preuves, la découverte MCP paginée et un meilleur affichage des résultats, la déduplication des constats avec occurrences, ainsi que la suppression contrôlée des historiques. Les tests actifs doivent être réalisés uniquement dans un périmètre autorisé.
