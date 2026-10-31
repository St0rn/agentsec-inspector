import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";
import App from "../App";

const project = {
  id: "project-report",
  client_name: "Acme Europe",
  engagement_name: "Audit IA",
  description: "Mission contrôlée",
  authorized_scope: "Chatbot de qualification",
  start_date: "2026-10-01",
  end_date: "2026-10-31",
  created_at: "2026-10-01T00:00:00Z",
  updated_at: "2026-10-01T00:00:00Z",
};

const report = {
  id: "report-1",
  project_id: project.id,
  report_type: "technical",
  language: "fr",
  format: "pdf",
  template_name: "default",
  filename: "agentsec-technical-fr.pdf",
  size_bytes: 4096,
  sha256: "a".repeat(64),
  created_at: "2026-10-31T10:00:00Z",
};

beforeEach(() => {
  localStorage.setItem("agentsec-api-token", "test-token");
});

it("previews the A4 report before generating it", async () => {
  let reports: typeof report[] = [];
  const fetchMock = vi.fn(async (input: RequestInfo | URL, options?: RequestInit) => {
    const url = String(input);
    if (url.endsWith("/health")) return new Response(JSON.stringify({ status: "ok", service: "agentsec-backend", version: "1.2.0" }), { status: 200 });
    if (url.endsWith("/projects")) return new Response(JSON.stringify([project]), { status: 200, headers: { "Content-Type": "application/json" } });
    if (url.endsWith("/reports/preview")) return new Response("<!doctype html><html><body>APERÇU A4</body></html>", { status: 200, headers: { "Content-Type": "text/html" } });
    if (url.endsWith("/reports") && options?.method === "POST") { reports = [report]; return new Response(JSON.stringify(report), { status: 201, headers: { "Content-Type": "application/json" } }); }
    if (url.endsWith("/reports")) return new Response(JSON.stringify(reports), { status: 200, headers: { "Content-Type": "application/json" } });
    return new Response(null, { status: 404 });
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<MemoryRouter initialEntries={["/reports"]}><App /></MemoryRouter>);
  await screen.findByRole("option", { name: "Acme Europe — Audit IA" });
  fireEvent.change(await screen.findByLabelText("Projet"), { target: { value: project.id } });
  const previewButton = screen.getByRole("button", { name: "Prévisualiser" });
  await waitFor(() => expect(previewButton).not.toBeDisabled());
  fireEvent.click(previewButton);
  await waitFor(() => expect(fetchMock.mock.calls.some(([input]) => String(input).endsWith("/reports/preview"))).toBe(true));
  const frame = await screen.findByTitle("Prévisualisation du rapport");
  expect(frame).toHaveAttribute("srcdoc", expect.stringContaining("APERÇU A4"));
  fireEvent.click(screen.getByRole("button", { name: "Fermer" }));
  fireEvent.click(screen.getByRole("button", { name: "Générer" }));
  expect(await screen.findByText(/Rapport PDF généré/)).toBeInTheDocument();
  expect(await screen.findByText("agentsec-technical-fr.pdf")).toBeInTheDocument();
});

it("uses the native save picker when Enregistrer sous is available", async () => {
  const write = vi.fn(async () => undefined);
  const close = vi.fn(async () => undefined);
  const picker = vi.fn(async () => ({ createWritable: async () => ({ write, close }) }));
  vi.stubGlobal("showSaveFilePicker", picker);
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith("/health")) return new Response(JSON.stringify({ status: "ok", service: "agentsec-backend", version: "1.2.0" }), { status: 200 });
    if (url.endsWith("/projects")) return new Response(JSON.stringify([project]), { status: 200, headers: { "Content-Type": "application/json" } });
    if (url.endsWith(`/reports/${report.id}/download`)) return new Response(new Blob(["%PDF fixture"]), { status: 200, headers: { "Content-Type": "application/pdf" } });
    if (url.endsWith("/reports")) return new Response(JSON.stringify([report]), { status: 200, headers: { "Content-Type": "application/json" } });
    return new Response(null, { status: 404 });
  }));

  render(<MemoryRouter initialEntries={["/reports"]}><App /></MemoryRouter>);
  fireEvent.click(await screen.findByRole("button", { name: "Enregistrer sous" }));
  await waitFor(() => expect(picker).toHaveBeenCalledWith(expect.objectContaining({ suggestedName: report.filename })));
  expect(write).toHaveBeenCalledOnce();
  expect(close).toHaveBeenCalledOnce();
  expect(await screen.findByText(`Rapport enregistré : ${report.filename}`)).toBeInTheDocument();
});
