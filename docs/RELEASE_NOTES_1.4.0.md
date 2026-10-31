# AgentSec Inspector v1.4.0 — MCP Security & Findings UX

## What's new

- **Three MCP Security modes:** passive capability discovery, explicitly authorized active tool calls, and a separate non-destructive vulnerability assessment tab. The vulnerability assessment evaluates tool annotations, JSON input schemas, sensitive operations, resource URI exposure and instruction-like prompt metadata. These are potential risks, not proven exploits; no unsafe tool is automatically invoked.
- **Interactive MCP discovery:** click Tools, Resources, Prompts or Observations to open a searchable detail window with descriptions, input parameters, allowed enum values, required fields, evidence and remediation. Original JSON stays available.
- **Schema-driven active MCP forms:** discovered `inputSchema` produces typed fields, enum selectors, booleans, nested JSON parameter editors and default values. Raw JSON editing remains available.
- **Findings management:** explicitly confirmed per-finding deletion from the table or detail view, with associated finding history cleanup.
- **Custom Payload history:** delete individual audit runs, clear one project's history, or explicitly clear all Custom Payload audit history across projects. Findings attached to other work remain preserved.
- **Dashboard:** severity tooltip text is white for dark-mode readability.
- **Version consistency:** backend, Python package, frontend, Tauri/Rust and MCP client are synchronized to 1.4.0.

## Limitations and interpretation

A successful MCP call shows that the specified tool executed, **not that it is secure**. The non-destructive vulnerability scan examines the advertised surface; it cannot prove authorization bypass or arbitrary code execution without separate authorized tests. MCP metadata annotations are not a trust boundary. Keep the scope authorized, use a controlled lab before invoking destructive tools, and verify all findings manually.

## Platforms and installation

Windows x64: MSI or NSIS EXE. Linux x64: AppImage or DEB. The final GitHub release bundles the backend and includes `SHA256SUMS.txt` for integrity checks. See the French and English README for current links and the workflow runs for exact build validation.

## Notes en français

- Trois onglets MCP : **Découverte passive**, **Appel actif contrôlé**, **Audit de vulnérabilités** non destructif.
- Inventaire MCP cliquable avec fenêtres de détail et recherche, paramètres dynamiques déduits des schémas JSON des outils.
- Suppression individuelle des findings avec confirmation.
- Purge ligne par ligne, par projet et globale des historiques Custom Payload.
- Texte blanc dans les infobulles de criticité du tableau de bord.
- Résultats et preuves conservés ; les observations MCP ne doivent pas être confondues avec des vulnérabilités confirmées.

License: MIT · Copyright (c) 2026 Fabien Dromas (St0rn).
