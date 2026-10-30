import { beforeEach, expect, it, vi } from "vitest";
import {
  api,
  getBackendConnectionState,
  reconnectBackend,
  setDevelopmentToken,
} from "../lib/api";

function json(value: unknown, status = 200) {
  return new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

beforeEach(() => {
  setDevelopmentToken("desktop-token");
});

it("waits for a valid backend health response before calling the API", async () => {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, options?: RequestInit) => {
    void options;
    const url = String(input);
    return url.endsWith("/health")
      ? json({ status: "ok", service: "agentsec-backend", version: "1.0.1" })
      : json([{ id: "project-1" }]);
  });
  vi.stubGlobal("fetch", fetchMock);

  const result = await api<Array<{ id: string }>>("/projects");

  expect(result[0].id).toBe("project-1");
  expect(String(fetchMock.mock.calls[0][0])).toBe("http://127.0.0.1:8765/health");
  expect(String(fetchMock.mock.calls[1][0])).toBe("http://127.0.0.1:8765/api/v1/projects");
  const headers = fetchMock.mock.calls[1][1]?.headers as Headers;
  expect(headers.get("Authorization")).toBe("Bearer desktop-token");
  expect(getBackendConnectionState()).toBe("online");
});

it("reports an unavailable backend and reconnects without fabricating data", async () => {
  let available = false;
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (!available) throw new TypeError("Failed to fetch");
    return url.endsWith("/health")
      ? json({ status: "ok", service: "agentsec-backend", version: "1.0.1" })
      : json([]);
  }));

  await expect(api("/projects")).rejects.toThrow(/backend local ne répond pas/i);
  expect(getBackendConnectionState()).toBe("offline");

  available = true;
  await expect(reconnectBackend()).resolves.toMatchObject({ baseUrl: "http://127.0.0.1:8765" });
  await expect(api("/projects")).resolves.toEqual([]);
  expect(getBackendConnectionState()).toBe("online");
});

it("turns a lost API connection into an actionable error", async () => {
  let calls = 0;
  vi.stubGlobal("fetch", vi.fn(async () => {
    calls += 1;
    if (calls === 1) return json({ status: "ok", service: "agentsec-backend", version: "1.0.1" });
    throw new TypeError("Failed to fetch");
  }));

  await expect(api("/projects")).rejects.toThrow(/connexion au backend local a été interrompue/i);
  expect(getBackendConnectionState()).toBe("offline");
});
