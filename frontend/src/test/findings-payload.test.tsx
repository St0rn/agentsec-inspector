import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";
import App from "../App";

beforeEach(() => {
  localStorage.setItem("agentsec-api-token", "test-token");
});

it("shows the stored Payload in the finding details", async () => {
  const finding = {
    id: "finding-1", project_id: "project-1", title: "Injection confirmée", description: "Description",
    component: "Chatbot", classification: "Confirmed vulnerability", severity: "high", confidence: "high",
    impact: "Impact", exploitation_conditions: "Accès", reproduction_steps: "Envoyer le test",
    observed_result: "Marqueur divulgué", expected_result: "Refus", recommendation: "Filtrer",
    status: "Confirmed", frameworks: [], created_at: "2026-10-31T10:00:00Z", updated_at: "2026-10-31T10:00:00Z",
  };
  const project = {
    id: "project-1", client_name: "Acme", engagement_name: "Audit chatbot", description: "",
    authorized_scope: "Chatbot", start_date: null, end_date: null,
    created_at: "2026-10-31T10:00:00Z", updated_at: "2026-10-31T10:00:00Z",
  };
  const detail = {
    finding, audit: { id: "audit-1" }, evidence: [],
    executions: [{
      id: "execution-1", scenario_id: "pi.direct", status: "FAIL",
      request_data: { turns: [{ step: 1, exact_payload_sent: { message: "PAYLOAD_CANARY" } }] },
      response_data: { text: "marker" }, analysis: { verdict: "FAIL" },
    }],
  };
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith("/health")) return new Response(JSON.stringify({ status: "ok", service: "agentsec-backend", version: "1.2.0" }), { status: 200 });
    const value = url.endsWith("/findings/finding-1/detail") ? detail : url.endsWith("/projects") ? [project] : [finding];
    return new Response(JSON.stringify(value), { status: 200, headers: { "Content-Type": "application/json" } });
  }));

  render(<MemoryRouter initialEntries={["/findings"]}><App /></MemoryRouter>);
  const projectTitle = await screen.findByText("Audit chatbot");
  const projectGroup = projectTitle.closest("details");
  expect(projectGroup).toHaveAttribute("open");
  fireEvent.click(projectTitle.closest("summary")!);
  await waitFor(() => expect(projectGroup).not.toHaveAttribute("open"));
  fireEvent.click(projectTitle.closest("summary")!);
  await waitFor(() => expect(projectGroup).toHaveAttribute("open"));
  fireEvent.click(await screen.findByText("Injection confirmée"));
  expect(await screen.findByText("Payload")).toBeInTheDocument();
  expect(await screen.findByText(/PAYLOAD_CANARY/)).toBeInTheDocument();
});
