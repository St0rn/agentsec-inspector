<div align="center">

<img src="assets/icon.svg" width="88" alt="AgentSec Inspector" />

# AgentSec Inspector

### AI Red Team & MCP Security Auditing Platform

A local-first Windows framework for authorized red-team campaigns against AI agents, MCP servers, RAG pipelines, and LLM applications.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.162-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-149ECA?style=flat-square&logo=react&logoColor=white)
![Tauri](https://img.shields.io/badge/Tauri-2-24C8DB?style=flat-square&logo=tauri&logoColor=white)
![Windows](https://img.shields.io/badge/Windows-x64-0078D4?style=flat-square&logo=windows11&logoColor=white)
![Mode](https://img.shields.io/badge/passive%20audit%20by%20default-22C55E?style=flat-square)

[![Backend tests](https://github.com/St0rn/agentsec-inspector/actions/workflows/backend-tests.yml/badge.svg?branch=main)](https://github.com/St0rn/agentsec-inspector/actions/workflows/backend-tests.yml)
[![Frontend tests](https://github.com/St0rn/agentsec-inspector/actions/workflows/frontend-tests.yml/badge.svg?branch=main)](https://github.com/St0rn/agentsec-inspector/actions/workflows/frontend-tests.yml)
[![Security checks](https://github.com/St0rn/agentsec-inspector/actions/workflows/security-checks.yml/badge.svg?branch=main)](https://github.com/St0rn/agentsec-inspector/actions/workflows/security-checks.yml)

**Evidence-first · Passive-first · Local-first**

[🇫🇷 Français](README.md) · [🇬🇧 English](README.en.md)

[Capabilities](#one-unified-audit-surface) · [Tests](#every-security-control-and-test) · [Architecture](#secure-local-architecture) · [Installation](#windows-development-setup) · [Validation](#observed-validation)

</div>

![AgentSec Inspector Dashboard](docs/images/dashboard.png)

<p align="center"><sub>Real V1 screenshot running against the included controlled laboratory — no fictional records are injected into the production dashboard.</sub></p>

<table>
  <tr>
    <td align="center" width="33%"><strong>🛡️ Evidence before verdicts</strong><br/><sub>Every conclusion remains linked to an actually observed request, response, trace, or event.</sub></td>
    <td align="center" width="33%"><strong>⚡ Active under control</strong><br/><sub>No sensitive action without precise selection, authorized scope, and explicit confirmation.</sub></td>
    <td align="center" width="33%"><strong>🔒 Local data</strong><br/><sub>Authenticated loopback backend, isolated projects, and secrets encrypted at rest.</sub></td>
  </tr>
</table>

## A reproducible AI red-team framework

The framework does not depend on an external “AI judge.” Its decisions rely on versioned criteria, fictional canary markers, actually observed traces, and retained evidence. Teams can import their own [declarative scenario packs](docs/SCENARIO_PACKS.md) without loading or executing third-party code.

<table>
  <tr>
    <td width="50%"><img src="docs/images/mcp-active.png" alt="Controlled active MCP audit"/><br/><sub>Bounded and explicitly authorized active MCP call</sub></td>
    <td width="50%"><img src="docs/images/prompt-injection.png" alt="Prompt Injection Tester"/><br/><sub>Versioned injection scenarios using fictional markers</sub></td>
  </tr>
  <tr>
    <td width="50%"><img src="docs/images/findings.png" alt="Findings management"/><br/><sub>Traceable findings with severity, confidence, and remediation</sub></td>
    <td width="50%"><img src="docs/images/attack-chains.png" alt="Attack-chain visualization"/><br/><sub>Graph built exclusively from observed interactions</sub></td>
  </tr>
  <tr>
    <td colspan="2"><img src="docs/images/scenario-packs.png" alt="Scenario-pack import"/><br/><sub>Framework extension through validated, versioned JSON packs</sub></td>
  </tr>
</table>

<p align="center"><sub>Gallery generated from the real frontend connected to the controlled local laboratory.</sub></p>

## One unified audit surface

AgentSec Inspector centralizes technical evidence without claiming to observe a model's hidden reasoning. Results explicitly distinguish an **observation**, a **potential risk**, and a **confirmed vulnerability**.

| Domain | Operational capabilities |
|---|---|
| MCP Security | Passive Streamable HTTP/stdio discovery and explicitly selected, configured, and confirmed active calls |
| Prompt & LLM | 10 versioned scenarios, OpenAI-compatible, Ollama, and HTTP endpoints, with PASS/FAIL/INCONCLUSIVE/ERROR outcomes |
| RAG Security | Documents and metadata, controlled injection cases, real traces, and Document → Retrieval → LLM → Response visualization |
| Agent Behavior | Timeline of messages, MCP calls, parameters, results, errors, durations, and observable decisions |
| Findings | Full lifecycle, history, evidence, confidence, impact, reproduction, and remediation |
| Reporting | Technical and executive reports in English or French, exported as HTML, JSON, or PDF |
| Scenario Packs | Versioned JSON import with extensible criteria and references, without plugin-code execution |

## Every security control and test

<details open>
<summary><strong>Enumeration and passive auditing</strong></summary>

1. MCP negotiation and protocol version.
2. Server information and advertised capabilities.
3. Tool inventory, names, and descriptions.
4. Complete tool input schemas.
5. Resource inventory and metadata.
6. Prompt inventory and descriptions.
7. Suspicious instructions embedded in tool descriptions.
8. Exposed sensitive capabilities: delete, write, admin, exec, shell, upload, credential, secret, or token operations.
9. Insufficiently constrained path or file parameters.
10. Schemas accepting undeclared properties.
11. Duplicate or ambiguous case-insensitive tool names.
12. Transport configuration and explicit remote-target authorization.
13. RAG document import with SHA-256 fingerprint and controlled origin.
14. Instruction detection in document content.
15. Inspection of retrieved chunks and their metadata when supplied.
16. Inspection of the LLM context when telemetry supplies it.
17. Comparison of observed and expected responses.
18. Detection of a fictional `AGENTSEC_CANARY_*` marker in a RAG response.
19. Distinction between real telemetry and response-only analysis.
20. Collection of observed LLM exchanges, MCP discovery, and tool calls.
21. Collection of redacted parameters, errors, statuses, and durations.
22. Interaction timeline and graph of actually observed relationships.

Passive mode never calls an MCP tool and never fabricates internal stages missing from the available telemetry.

</details>

<details open>
<summary><strong>Active attacks and security tests</strong></summary>

### Controlled active MCP

1. Calling a tool selected from the actually discovered inventory.
2. Sending only explicitly authorized JSON parameters.
3. Validation of required parameters and additional properties.
4. Validation of simple types, advertised `enum` values, and constants.
5. Global confirmation of the active audit.
6. Separate confirmation for sensitive or potentially destructive capabilities.
7. Capture of the real output, `isError` flag, duration, and evidence.
8. Detection of malicious instructions in actual tool output.
9. Classification of transport or tool failures as `ERROR`, never as a successful attack.

### Prompt Injection and LLM security

1. Direct Prompt Injection.
2. Indirect Prompt Injection.
3. Instruction Hierarchy Confusion.
4. Role Spoofing.
5. Tool Output Injection.
6. Context Manipulation.
7. RAG Prompt Injection.
8. System Prompt Disclosure Attempt using a fictional secret.
9. Agent Goal Hijacking.
10. Multi-turn Manipulation with multiple real exchanges.
11. Observable fictional-marker disclosure.
12. Observable tool-call attempts.
13. Empty responses or insufficient results.
14. Timeout, controlled retry, HTTP error, oversized response, or malformed response.
15. Referenced credentials missing from the environment.
16. Custom multi-turn scenarios through strictly validated, versioned JSON packs.

Active connectors cover OpenAI-compatible APIs, Ollama, custom HTTP chat endpoints, and the local laboratory agent. Every execution retains requests, responses, versions, timestamps, and associated evidence.

</details>

<details>
<summary><strong>Outcomes and security boundaries</strong></summary>

- `PASS`: no observable violation of the built-in criterion.
- `FAIL`: fictional marker disclosed or observable tool call under the controlled scenario.
- `INCONCLUSIVE`: insufficient evidence, such as an empty response.
- `ERROR`: technical failure, never treated as a successful attack.
- Findings: `Observation`, `Risk potential`, or `Confirmed vulnerability`, with separate severity and confidence.

V1 does not perform port scanning, host exploitation, automatic invocation of every tool, arbitrary command execution, or autonomous exploit chaining. It uses no real secrets in the supplied scenarios and never claims to read a model's chain of thought.

</details>

The [detailed test catalog](docs/TEST_CATALOG.md) documents the method, evidence, and boundaries of every control.

## Secure local architecture

<table>
  <tr>
    <td align="center"><strong>Desktop UI</strong><br/><sub>React · TypeScript · WebView2</sub></td>
    <td align="center">→<br/><sub>local IPC</sub></td>
    <td align="center"><strong>Tauri 2</strong><br/><sub>Launch · supervision</sub></td>
    <td align="center">→<br/><sub>ephemeral token</sub></td>
    <td align="center"><strong>FastAPI sidecar</strong><br/><sub>127.0.0.1 only</sub></td>
  </tr>
  <tr>
    <td align="center"><strong>SQLite</strong><br/><sub>Isolated projects</sub></td>
    <td align="center">←</td>
    <td align="center" colspan="3"><strong>Engines and outputs</strong><br/><sub>MCP HTTP/stdio · LLM/RAG · evidence · PDF/HTML/JSON</sub></td>
  </tr>
</table>

- The backend refuses non-loopback binding, and the local API requires a token passed through Tauri IPC.
- Outbound requests include SSRF protection, redirects are disabled, and remote targets require explicit authorization.
- MCP discovery invokes no tool. Active operations require explicit confirmation.
- A sensitive MCP capability requires a second, individual confirmation, and its arguments are validated against the advertised schema.
- Connector secrets are encrypted at rest; tokens must never be stored in plaintext target configuration.
- A transport failure remains `ERROR` and is never treated as a successful attack.

The [test and attack catalog](docs/TEST_CATALOG.md) states exactly what V1 executes and where its boundaries are. The [security model](docs/SECURITY.md) documents trust boundaries and isolation limits. The [Scenario Pack API](docs/SCENARIO_PACKS.md) describes safe framework extension.

## Windows development setup

Requirements: Windows 10 22H2/Windows 11 x64, Python 3.12, Node.js 22+, stable Rust, MSVC build tools, and WebView2.

```powershell
git clone https://github.com/St0rn/agentsec-inspector.git
cd agentsec-inspector
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\check-prerequisites.ps1 -Development
.\scripts\install-dev.ps1
.\scripts\start-dev.ps1
```

Start the reproducible laboratory, which remains clearly separated from real audits:

```powershell
.\scripts\start-demo.ps1
```

Build the x64 MSI and NSIS installer:

```powershell
.\scripts\build-windows.ps1
```

Exact procedures are available in the [Windows installation](docs/INSTALLATION_WINDOWS.md), [development setup](docs/INSTALLATION_DEVELOPMENT.md), [build guide](docs/BUILD_WINDOWS.md), and [troubleshooting guide](docs/TROUBLESHOOTING.md).

## Observed validation

| Control | Local result |
|---|---|
| Backend | 46/46 tests, 85.4% coverage with an 80% blocking threshold, Ruff and mypy successful |
| Frontend | 9/9 tests, 83.46% line coverage with blocking thresholds, ESLint, TypeScript, and Vite build successful |
| Source and dependency security | `pip-audit` and `npm audit` found no known vulnerabilities; Bandit found no medium/high issue |
| Standalone binary | Linux PyInstaller build verified with fresh migration, authentication, CORS, integrity, and PDF generation |
| Laboratory | Passive MCP discovery, bounded active MCP call, and actual LLM exchanges executed successfully |
| Rust/Tauri | `cargo fmt` and locked metadata successful; Windows build delegated to CI |
| Windows/PowerShell | Scripts and workflow supplied, but not locally validated because no Windows host was available |

The Windows build is **not** reported as validated without evidence from a Windows run. See [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md), the [installation validation matrix](INSTALLATION_VALIDATION_MATRIX.md), and the [detailed validation report](docs/VALIDATION_REPORT.md).

## Repository layout

```text
backend/       API, models, migrations, audit engines, and reports
frontend/      React, TypeScript, Tailwind, charts, and visualizations
src-tauri/     desktop application, sidecar supervision, and IPC
demo/          controlled MCP / LLM / RAG laboratory
scripts/       installation, build, test, update, backup, and uninstall
docs/          architecture, security, and Windows procedures
.github/       backend/frontend tests, security checks, and Windows x64 build
```

## Authorized use only

This tool is intended exclusively for audits with explicit authorization and a documented scope. Run untrusted MCP servers inside a dedicated VM or Windows Sandbox: stdio subprocess restrictions alone are not a security sandbox.

---

<div align="center"><sub>AgentSec Inspector V1.0 · outcomes based on observable executions and retained evidence</sub></div>
