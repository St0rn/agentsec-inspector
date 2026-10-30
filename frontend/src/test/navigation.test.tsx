import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "../App";

const emptyDashboard = { projects: 0, audits: 0, findings: 0, severity: {}, audit_status: {}, connector_status: {}, recent_audits: [] };

describe("navigation", () => {
  beforeEach(() => {
    localStorage.setItem("agentsec-api-token", "test-token");
    vi.stubGlobal("fetch", vi.fn(async (url: string) => {
      const value = url.endsWith("/health") ? { status: "ok", service: "agentsec-backend", version: "1.0.1" } : url.includes("/dashboard") ? emptyDashboard : [];
      return new Response(JSON.stringify(value), { status: 200, headers: { "Content-Type": "application/json" } });
    }));
  });

  it("shows every primary security module", async () => {
    render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);
    expect(await screen.findByText("Vue d’ensemble")).toBeInTheDocument();
    for (const label of ["Projects", "Targets", "MCP Security", "Prompt Injection", "Jailbreak", "RAG Security", "Agent Behavior", "LLM Security", "Attack Chains", "Findings", "Reports", "Settings"]) {
      expect(screen.getByRole("link", { name: new RegExp(label) })).toBeInTheDocument();
    }
  });

  it("renders an explicit empty projects state", async () => {
    render(<MemoryRouter initialEntries={["/projects"]}><App /></MemoryRouter>);
    expect(await screen.findByText("Aucun projet")).toBeInTheDocument();
  });
});
