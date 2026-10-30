import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";
import App from "../App";

beforeEach(() => {
  localStorage.setItem("agentsec-api-token", "test-token");
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
    const value = String(input).endsWith("/health") ? { status: "ok", service: "agentsec-backend", version: "1.0.1" } : [];
    return new Response(JSON.stringify(value), { status: 200, headers: { "Content-Type": "application/json" } });
  }));
});

it("opens the validated project form", async () => {
  render(<MemoryRouter initialEntries={["/projects"]}><App /></MemoryRouter>);
  fireEvent.click(await screen.findByRole("button", { name: /Nouveau projet/i }));
  expect(screen.getByText("Nouvelle mission")).toBeInTheDocument();
  expect(screen.getByLabelText("Périmètre autorisé")).toBeRequired();
});

it("creates, updates, and deletes a project through the local API", async () => {
  const project = {
    id: "project-1",
    client_name: "Acme",
    engagement_name: "Audit chatbot",
    description: "Initial scope",
    authorized_scope: "Chatbot de test",
    start_date: "2026-10-30",
    end_date: "2026-10-31",
    created_at: "2026-10-30T08:00:00Z",
    updated_at: "2026-10-30T08:00:00Z",
  };
  let projects: typeof project[] = [];
  const fetchMock = vi.fn(async (input: RequestInfo | URL, options?: RequestInit) => {
    const url = String(input);
    if (url.endsWith("/health")) return new Response(JSON.stringify({ status: "ok", service: "agentsec-backend", version: "1.0.1" }), { status: 200 });
    if (options?.method === "POST") {
      projects = [{ ...project, ...JSON.parse(String(options.body)) }];
      return new Response(JSON.stringify(projects[0]), { status: 201, headers: { "Content-Type": "application/json" } });
    }
    if (options?.method === "PUT") {
      projects = [{ ...projects[0], ...JSON.parse(String(options.body)), engagement_name: "Audit chatbot corrigé" }];
      return new Response(JSON.stringify(projects[0]), { status: 200, headers: { "Content-Type": "application/json" } });
    }
    if (options?.method === "DELETE") {
      projects = [];
      return new Response(null, { status: 204 });
    }
    return new Response(JSON.stringify(projects), { status: 200, headers: { "Content-Type": "application/json" } });
  });
  vi.stubGlobal("fetch", fetchMock);
  vi.stubGlobal("confirm", vi.fn(() => true));

  render(<MemoryRouter initialEntries={["/projects"]}><App /></MemoryRouter>);
  fireEvent.click(await screen.findByRole("button", { name: /Nouveau projet/i }));
  fireEvent.change(screen.getByLabelText("Client"), { target: { value: "Acme" } });
  fireEvent.change(screen.getByLabelText("Mission"), { target: { value: "Audit chatbot" } });
  fireEvent.change(screen.getByLabelText("Début"), { target: { value: "2026-10-30" } });
  fireEvent.change(screen.getByLabelText("Fin"), { target: { value: "2026-10-31" } });
  fireEvent.change(screen.getByLabelText("Description"), { target: { value: "Initial scope" } });
  fireEvent.change(screen.getByLabelText("Périmètre autorisé"), { target: { value: "Chatbot de test" } });
  fireEvent.click(screen.getByRole("button", { name: "Créer le projet" }));

  expect(await screen.findByText("Audit chatbot")).toBeInTheDocument();
  const post = fetchMock.mock.calls.find(([, options]) => options?.method === "POST");
  expect(JSON.parse(String(post?.[1]?.body))).toMatchObject({ client_name: "Acme", authorized_scope: "Chatbot de test" });

  fireEvent.click(screen.getByRole("button", { name: "Modifier Audit chatbot" }));
  fireEvent.change(screen.getByLabelText("Mission"), { target: { value: "Audit chatbot corrigé" } });
  fireEvent.click(screen.getByRole("button", { name: "Enregistrer les modifications" }));
  expect(await screen.findByText("Audit chatbot corrigé")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "Supprimer Audit chatbot corrigé" }));
  await waitFor(() => expect(fetchMock.mock.calls.some(([, options]) => options?.method === "DELETE")).toBe(true));
  expect(await screen.findByText("Aucun projet")).toBeInTheDocument();
});
