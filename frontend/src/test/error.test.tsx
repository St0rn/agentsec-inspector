import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { expect, it, vi } from "vitest";
import App from "../App";

it("shows API failures instead of fabricated content", async () => {
  localStorage.setItem("agentsec-api-token", "test-token");
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ detail: "backend unavailable" }), { status: 503, headers: { "Content-Type": "application/json" } })));
  render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);
  expect(await screen.findByRole("alert")).toHaveTextContent(/backend local ne répond pas/i);
  expect(await screen.findByText("Backend Offline")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Reconnecter" })).toBeInTheDocument();
});
