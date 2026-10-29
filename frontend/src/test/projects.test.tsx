import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";
import App from "../App";

beforeEach(() => {
  localStorage.setItem("agentsec-api-token", "test-token");
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify([]), { status: 200, headers: { "Content-Type": "application/json" } })));
});

it("opens the validated project form", async () => {
  render(<MemoryRouter initialEntries={["/projects"]}><App /></MemoryRouter>);
  fireEvent.click(await screen.findByRole("button", { name: /Nouveau projet/i }));
  expect(screen.getByText("Nouvelle mission")).toBeInTheDocument();
  expect(screen.getByLabelText("Périmètre autorisé")).toBeRequired();
});
