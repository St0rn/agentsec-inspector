import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";
import App from "../App";

function response(value: unknown) {
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
    vi.fn(async (input: RequestInfo | URL) =>
      String(input).endsWith("/health")
        ? response({ status: "ok", service: "agentsec-backend", version: "1.5.0" })
        : response([]),
    ),
  );
});

it("uses English by default and persists an immediate French selection", async () => {
  render(
    <MemoryRouter initialEntries={["/settings"]}>
      <App />
    </MemoryRouter>,
  );
  expect(await screen.findByText("Local configuration, encrypted connectors, and declarative red-team scenario packs.")).toBeInTheDocument();
  expect(document.documentElement.lang).toBe("en");
  fireEvent.click(screen.getByRole("button", { name: "Français" }));
  await waitFor(() =>
    expect(
      screen.getByText(
        "Configuration locale, connecteurs chiffrés et packs déclaratifs du framework red team.",
      ),
    ).toBeInTheDocument(),
  );
  expect(document.documentElement.lang).toBe("fr");
  expect(localStorage.getItem("agentsec-language")).toBe("fr");
});

it("falls back to English when the stored language is unsupported", async () => {
  localStorage.setItem("agentsec-language", "de");
  render(
    <MemoryRouter initialEntries={["/settings"]}>
      <App />
    </MemoryRouter>,
  );
  expect(await screen.findByText("API token — development only")).toBeInTheDocument();
  expect(document.documentElement.lang).toBe("en");
});

it("localises the adaptive and RAG additions when French is selected", async () => {
  localStorage.setItem("agentsec-language", "fr");
  const { unmount } = render(
    <MemoryRouter initialEntries={["/adaptive-red-team"]}>
      <App />
    </MemoryRouter>,
  );
  expect(await screen.findByText("Nom de l’audit")).toBeInTheDocument();
  expect(screen.getByText("Exécution observée")).toBeInTheDocument();
  expect(screen.getByText("Budget total de jetons")).toBeInTheDocument();
  expect(document.documentElement.lang).toBe("fr");
  unmount();

  render(
    <MemoryRouter initialEntries={["/rag"]}>
      <App />
    </MemoryRouter>,
  );
  expect(await screen.findByText("Fichier TXT, Markdown ou PDF")).toBeInTheDocument();
  expect(
    screen.getByText("Marqueurs fictifs (séparés par des virgules)"),
  ).toBeInTheDocument();
});
