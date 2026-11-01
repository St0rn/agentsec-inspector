import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";
import App from "../App";

const project = {
  id: "p-settings",
  client_name: "Synthetic Lab",
  engagement_name: "Connector assessment",
};

function json(value: unknown, status = 200) {
  return new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

beforeEach(() => localStorage.setItem("agentsec-api-token", "test-token"));

it("stores the development token and creates then removes a connector", async () => {
  let connectors: Array<Record<string, unknown>> = [];
  const fetchMock = vi.fn(
    async (input: RequestInfo | URL, options?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/health"))
        return json({ status: "ok", service: "agentsec-backend", version: "1.5.0" });
      if (url.endsWith("/projects")) return json([project]);
      if (url.endsWith("/connectors") && options?.method === "POST") {
        connectors = [
          {
            id: "connector-1",
            project_id: project.id,
            name: "Local Ollama",
            connector_type: "ollama",
            has_secret: true,
            last_status: "untested",
          },
        ];
        return json(connectors[0], 201);
      }
      if (url.endsWith("/connectors/connector-1") && options?.method === "DELETE") {
        connectors = [];
        return new Response(null, { status: 204 });
      }
      if (url.endsWith("/connectors")) return json(connectors);
      return json([]);
    },
  );
  vi.stubGlobal("fetch", fetchMock);
  render(
    <MemoryRouter initialEntries={["/settings"]}>
      <App />
    </MemoryRouter>,
  );
  await screen.findByRole("option", { name: /Synthetic Lab/ });
  fireEvent.change(screen.getByLabelText("Jeton local"), {
    target: { value: "local-development-token" },
  });
  fireEvent.click(screen.getByRole("button", { name: /Enregistrer dans le navigateur/ }));
  expect(await screen.findByText("Enregistré. Rechargez les données.")).toBeInTheDocument();
  expect(localStorage.getItem("agentsec-api-token")).toBe("local-development-token");

  const form = screen.getByText("Nouveau connecteur").closest("form")!;
  const selects = within(form).getAllByRole("combobox");
  fireEvent.change(selects[0], { target: { value: project.id } });
  fireEvent.change(within(form).getByPlaceholderText("Nom"), {
    target: { value: "Local Ollama" },
  });
  fireEvent.change(selects[1], { target: { value: "ollama" } });
  fireEvent.change(within(form).getByLabelText("Secret (chiffré au repos)"), {
    target: { value: "test-only-secret" },
  });
  fireEvent.submit(form);
  const connectorName = await screen.findByText("Local Ollama");
  const createCall = fetchMock.mock.calls.find(
    ([url, options]) =>
      String(url).endsWith("/connectors") && options?.method === "POST",
  );
  expect(JSON.parse(String(createCall?.[1]?.body))).toMatchObject({
    project_id: project.id,
    connector_type: "ollama",
    secret: "test-only-secret",
  });
  fireEvent.click(within(connectorName.closest("tr")!).getByRole("button"));
  await waitFor(() => expect(screen.queryByText("Local Ollama")).not.toBeInTheDocument());
  expect(fetchMock.mock.calls.some(([url, options]) =>
    String(url).endsWith("/connectors/connector-1") && options?.method === "DELETE",
  )).toBe(true);
});
