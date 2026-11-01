import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";
import App from "../App";

const project = {
  id: "p-adaptive",
  client_name: "Synthetic Lab",
  engagement_name: "Adaptive test",
};
const target = {
  id: "t-adaptive",
  project_id: "p-adaptive",
  name: "Branching agent",
  target_type: "agent_lab",
  endpoint: "http://127.0.0.1:9999/chat",
  configuration: {},
  remote_authorized: false,
};
const audit = {
  id: "a-adaptive",
  project_id: project.id,
  target_id: target.id,
  audit_type: "adaptive_red_team",
  status: "queued",
  passive: false,
  configuration: {},
  summary: {},
  error: null,
  created_at: "2026-10-31T00:00:00Z",
  started_at: null,
  finished_at: null,
};

function json(value: unknown, status = 200) {
  return new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

beforeEach(() => {
  localStorage.setItem("agentsec-api-token", "test-token");
  localStorage.setItem("agentsec-language", "en");
});

it("previews, starts and cancels an evidence-driven adaptive assessment", async () => {
  const fetchMock = vi.fn(
    async (input: RequestInfo | URL, options?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/health"))
        return json({
          status: "ok",
          service: "agentsec-backend",
          version: "1.5.0",
        });
      if (url.includes("/projects")) return json([project]);
      if (url.includes("/targets")) return json([target]);
      if (url.endsWith("/audits/adaptive/preview"))
        return json({
          method: "POST",
          payload: { message: "exact adaptive payload" },
          messages: [{ role: "user", content: "exact adaptive payload" }],
        });
      if (url.endsWith("/audits/adaptive") && options?.method === "POST")
        return json(audit, 202);
      if (url.endsWith("/audits/a-adaptive/cancel"))
        return json({ ...audit, status: "cancelled" });
      if (url.includes("/audits")) return json([]);
      return json([]);
    },
  );
  vi.stubGlobal("fetch", fetchMock);
  render(
    <MemoryRouter initialEntries={["/adaptive-red-team"]}>
      <App />
    </MemoryRouter>,
  );
  expect(
    await screen.findByRole("heading", { name: "Adaptive Red Team", level: 2 }),
  ).toBeInTheDocument();
  await screen.findByRole("option", { name: /Synthetic Lab/ });
  fireEvent.change(screen.getByLabelText("Project"), {
    target: { value: project.id },
  });
  await screen.findByRole("option", { name: "Branching agent" });
  fireEvent.change(screen.getByLabelText("Target"), {
    target: { value: target.id },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Preview first request" }),
  );
  expect(await screen.findByRole("dialog")).toHaveTextContent(
    "exact adaptive payload",
  );
  fireEvent.click(screen.getByRole("button", { name: "Close" }));
  fireEvent.click(
    screen
      .getByText(/I authorise the configured adaptive payload sequence/)
      .closest("label")!
      .querySelector("input")!,
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Run adaptive assessment" }),
  );
  await waitFor(() =>
    expect(
      fetchMock.mock.calls.some(
        ([url, options]) =>
          String(url).endsWith("/audits/adaptive") &&
          options?.method === "POST",
      ),
    ).toBe(true),
  );
  const start = fetchMock.mock.calls.find(
    ([url, options]) =>
      String(url).endsWith("/audits/adaptive") && options?.method === "POST",
  );
  expect(JSON.parse(String(start?.[1]?.body))).toMatchObject({
    test_mode: "black_box",
    entry_step: "initial-injection",
    confirm_active_test: true,
  });
  fireEvent.click(await screen.findByRole("button", { name: "Cancel" }));
  await waitFor(() =>
    expect(screen.getByText("cancelled")).toBeInTheDocument(),
  );
});
