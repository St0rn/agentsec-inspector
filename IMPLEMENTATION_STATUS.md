# AgentSec Inspector — implementation status v1.5.0

Status date: 2026-11-01. This document deliberately separates implemented code, tests executed in the current Linux workspace, and package validation performed by GitHub Actions. A package is not described as validated until its platform workflow has completed successfully.

## Completed in v1.5.0

- Black-Box Red Team is the default for Prompt Injection, Jailbreak, LLM Security, Custom Payload, and Adaptive Red Team. The backend sends only auditor-defined attack messages and keeps the security objective and evaluation rules local.
- Controlled Lab is explicit and confirmed. Its artificial policy is shown before execution, and its protected synthetic marker is placed in that policy rather than repeated in the user payload.
- Exact effective-request previews are available without exposing authentication values. Audit history, findings, evidence, and reports retain the exact payload sent when it exists.
- Verdicts are deterministic and rule-based: `PASS`, `FAIL`, `INCONCLUSIVE`, and `ERROR` are separated. A transport failure is never treated as a successful attack, and an echoed user-supplied marker is not treated as secret disclosure.
- Marker provenance, criteria provenance, test mode, evaluator version, rule outcomes, observed evidence, tool calls, and technical errors are persisted.
- Adaptive Red Team uses a bounded deterministic state machine with observable transitions, explicit authorization, cancellation, turn/token budgets, and evidence for every request and response.
- MCP passive discovery supports paginated tools, resources, prompts, and capabilities without invoking tools. Active calls remain explicitly selected, schema-validated, bounded, and confirmed.
- MCP vulnerability analysis compares only auditor-configured identities, recursively validates input schemas, records permission differences, and creates conservative attack-chain correlations without claiming exploitability from an indicator alone.
- RAG Security imports TXT, Markdown, and PDF test documents with size/page/encryption controls, supports indirect document and metadata injection cases, and requires actual retrieval/context telemetry before confirming a retrieval-dependent violation.
- OpenAI-compatible, Ollama, custom HTTP, JSON, NDJSON, and SSE responses pass through a shared normalization layer that preserves tokens, status events, tool calls, completion data, and transport errors.
- English is the default application language; Settings switches the interface immediately to French. Report language remains independent.
- HTML, PDF, and JSON reports include the real project data, findings, exact payloads, evidence, tool calls, and module-specific results. HTML preview and the desktop save dialog are retained.
- Targets, Findings, and Reports remain grouped by project in collapsible sections. Attack-chain node placement, zoom, pan, centering, layout, and persistence are retained.
- Real screenshots were regenerated from the running FastAPI application and the controlled local MCP/LLM/RAG laboratory.

## Completed and executed in the current Linux workspace

- Backend: 101 tests passed; total coverage 85.19% with an 80% blocking threshold; Ruff lint/format and mypy passed.
- Frontend: 56 tests passed; line coverage 80.15% with blocking thresholds; ESLint, TypeScript, and the production Vite build passed.
- Security: `pip-audit` found no known Python vulnerability; Bandit found no medium/high issue; `npm audit --audit-level=high` passed.
- npm reports 12 moderate `minimatch` advisories in the development lint dependency tree. They do not ship in the desktop runtime, but remain documented until the upstream lint stack can be updated without a forced breaking downgrade.
- Screenshot capture completed against real local services and rejected browser page errors or suspiciously small output files.
- Bash syntax checks passed. The isolated Linux script lifecycle suite passed its nominal and principal error paths, including repeated installation, backup/restore, update checks, invalid artifacts, and uninstall with preserved or explicitly deleted data.

## Platform package validation

The v1.5.0 MSI, NSIS Setup executable, AppImage, and DEB are not considered validated by the local source tests. Their status is established by the Windows and Linux workflows for the exact release tag and by the published `SHA256SUMS.txt`.

The exact-tag v1.5.0 platform validations completed successfully for commit `a5a694a3ca37232790affa17e700a64b29b5dd11`:

- Windows x64 MSI/NSIS build, repeated installation, runtime verification, and data-preserving uninstall: [run 41293107640](https://github.com/St0rn/agentsec-inspector/actions/runs/41293107640).
- Linux x86_64 AppImage/DEB build and repeated AppImage installation/runtime verification: [run 41293107481](https://github.com/St0rn/agentsec-inspector/actions/runs/41293107481).
- Clean-environment screenshot regeneration: [run 41293107465](https://github.com/St0rn/agentsec-inspector/actions/runs/41293107465).
- Release assembly and publication from those validated artifacts: [run 41294325538](https://github.com/St0rn/agentsec-inspector/actions/runs/41294325538).
- Published packages and checksums: [AgentSec Inspector v1.5.0](https://github.com/St0rn/agentsec-inspector/releases/tag/v1.5.0).

Published SHA-256 values:

```text
d32977790b825a7592e90a8130b96df21c01f8773fa83e7ded422c2ec83d287f  AgentSec-Inspector_1.5.0_amd64.AppImage
ed4f146883ecbad07f3caef066f3a699d65d6b8d17b37da431a1bda61f44672f  AgentSec-Inspector_1.5.0_amd64.deb
0830eac08171faa6ad94f91db9e31a93cc4ef5a8a52cac0212f048093b95ee88  AgentSec-Inspector_1.5.0_x64-setup.exe
2a201fd497102db5a3c25f6c592e114c2a907c33db2474d16e2367af256b6656  AgentSec-Inspector_1.5.0_x64_en-US.msi
```

## Partial capabilities and explicit limits

- MCP stdio uses an executable allowlist, no shell, a reduced environment, timeout, and resource controls. It is not an operating-system sandbox; untrusted servers still belong in a dedicated VM or sandbox.
- Identity comparison tests configured credentials and discovery visibility. It does not guess identities, bypass authentication, or automatically invoke sensitive tools to prove privilege escalation.
- Adaptive Red Team is deterministic and evidence-driven. It does not use a second LLM to invent attacks or judge another model.
- RAG supports supplied retrieval traces and the documented generic target mapping. Vendor-specific ingestion and observability adapters are not bundled.
- Agent Behavior visualizes events observable to AgentSec. It does not claim access to hidden chain-of-thought or internal model reasoning.
- Scenario extensions are declarative JSON packs. Loading arbitrary third-party executable plugin code is intentionally excluded.
- Interface translation uses a controlled application dictionary and English fallback. User content, payloads, evidence, and code blocks are never translated.
- Framework mappings are added only where evidence supports them; the tool does not manufacture comprehensive OWASP/MITRE mappings.

## Not implemented

- Automatic creation of a VM or Windows Sandbox for an untrusted MCP process.
- Windows code signing and an organization-issued publisher certificate.
- Vendor-specific RAG connectors for every commercial platform.
- Dynamic execution of third-party plugin code.
- Access to hidden model reasoning.

## Scripts supplied

All required PowerShell lifecycle scripts are present in `scripts/`: prerequisite checks, development and production installation, backend/frontend/database setup, development and production startup, Windows build, complete tests, installation verification, update, backup, restore, uninstall, and clean. Pester regression tests and shared logging helpers are included.

The equivalent Linux lifecycle is present in `scripts/linux/`, including prerequisite checks, development install, database setup, startup, tests, AppImage/DEB build, install, verification, update, backup, restore, uninstall, and clean.

## Execution evidence for scripts

- Current workspace: Bash syntax and `scripts/linux/test-scripts.sh` passed. The application test suites, lint, typing, security scans, and production frontend build were executed directly.
- Windows: PowerShell syntax, PSScriptAnalyzer, Pester under PowerShell 7 and Windows PowerShell 5.1, compilation, installation, repeat installation, runtime smoke tests, and uninstall are executed by `windows-build.yml`.
- Linux packaging: ShellCheck, lifecycle regression tests, locked installation, AppImage/DEB build, two AppImage installations, and two runtime verifications are executed by `linux-build.yml`.
- PowerShell was not available in the current Linux workspace; no local Windows execution is claimed.

See [INSTALLATION_VALIDATION_MATRIX.md](INSTALLATION_VALIDATION_MATRIX.md) and [docs/VALIDATION_REPORT.md](docs/VALIDATION_REPORT.md) for command-level evidence and the distinction between current and historical platform results.
