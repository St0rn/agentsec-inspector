import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, it, vi } from "vitest";
import App from "../App";

function json(value: unknown) {
  return new Response(JSON.stringify(value), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

beforeEach(() => {
  localStorage.removeItem("agentsec-language");
  localStorage.setItem("agentsec-api-token", "test-token");
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/health"))
        return json({ status: "ok", service: "agentsec-backend", version: "1.5.0" });
      if (url.includes("/dashboard"))
        return json({
          projects: 0,
          audits: 0,
          findings: 0,
          severity: {},
          audit_status: {},
          connector_status: {},
          recent_audits: [],
        });
      return json([]);
    }),
  );
});

const routes = [
  "/",
  "/projects",
  "/targets",
  "/mcp",
  "/prompt-injection",
  "/jailbreak",
  "/custom-payload",
  "/adaptive-red-team",
  "/rag",
  "/agent-behavior",
  "/llm",
  "/attack-chains",
  "/findings",
  "/reports",
  "/settings",
];

it.each(routes)("renders %s without untranslated accented French UI", async (route) => {
  render(
    <MemoryRouter initialEntries={[route]}>
      <App />
    </MemoryRouter>,
  );
  await screen.findByText("Local Mode");
  await waitFor(() => {
    if ((document.body.textContent || "").includes("Loading local data"))
      throw new Error("Route is still loading");
  });
  await new Promise((resolve) => window.setTimeout(resolve, 25));
  await waitFor(() => {
    const text = (document.body.textContent || "").replaceAll("Français", "");
    const untranslated = text.match(/.{0,50}[àâçéèêëîïôùûüÿœ].{0,100}/i)?.[0];
    if (untranslated) throw new Error(`Untranslated UI: ${untranslated}`);
  });
});
