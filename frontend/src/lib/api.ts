const FALLBACK_URL = "http://127.0.0.1:8765";
const REQUEST_TIMEOUT_MS = 30_000;
const HEALTH_TIMEOUT_MS = 1_500;
const STARTUP_ATTEMPTS = import.meta.env.MODE === "test" ? 1 : 24;
const STARTUP_RETRY_MS = 250;

type BackendConfig = { baseUrl: string; token: string };
export type BackendConnectionState = "connecting" | "online" | "offline";

let configPromise: Promise<BackendConfig> | undefined;
let readinessPromise: Promise<BackendConfig> | undefined;
let connectionState: BackendConnectionState = "connecting";
const connectionListeners = new Set<(state: BackendConnectionState) => void>();

function updateConnectionState(state: BackendConnectionState) {
  if (connectionState === state) return;
  connectionState = state;
  connectionListeners.forEach((listener) => listener(state));
}

export function getBackendConnectionState() {
  return connectionState;
}

export function subscribeBackendConnection(listener: (state: BackendConnectionState) => void) {
  connectionListeners.add(listener);
  return () => {
    connectionListeners.delete(listener);
  };
}

function delay(milliseconds: number) {
  return new Promise<void>((resolve) => window.setTimeout(resolve, milliseconds));
}

async function backendConfig(): Promise<BackendConfig> {
  if (!configPromise) {
    configPromise = (async () => {
      const envToken = import.meta.env.VITE_API_TOKEN || localStorage.getItem("agentsec-api-token") || "";
      try {
        const { invoke } = await import("@tauri-apps/api/core");
        return await invoke<BackendConfig>("backend_config");
      } catch {
        return { baseUrl: import.meta.env.VITE_API_URL || FALLBACK_URL, token: envToken };
      }
    })();
  }
  return configPromise;
}

async function fetchWithTimeout(input: RequestInfo | URL, init: RequestInit, timeoutMs: number) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } finally {
    window.clearTimeout(timeout);
  }
}

async function checkHealth(config: BackendConfig) {
  try {
    const response = await fetchWithTimeout(`${config.baseUrl}/health`, {
      cache: "no-store",
      headers: { Accept: "application/json" },
    }, HEALTH_TIMEOUT_MS);
    if (!response.ok) return false;
    const body = await response.json() as { status?: string; service?: string };
    return body.status === "ok" && body.service === "agentsec-backend";
  } catch {
    return false;
  }
}

async function waitForBackend(): Promise<BackendConfig> {
  updateConnectionState("connecting");
  const currentConfig = await backendConfig();
  for (let attempt = 0; attempt < STARTUP_ATTEMPTS; attempt += 1) {
    if (await checkHealth(currentConfig)) {
      updateConnectionState("online");
      return currentConfig;
    }
    if (attempt + 1 < STARTUP_ATTEMPTS) await delay(STARTUP_RETRY_MS);
  }
  updateConnectionState("offline");
  throw new Error("Le backend local ne répond pas. Vérifiez que l’application est démarrée, puis réessayez.");
}

async function readyBackend(): Promise<BackendConfig> {
  if (!readinessPromise) {
    readinessPromise = waitForBackend().catch((error) => {
      readinessPromise = undefined;
      throw error;
    });
  }
  return readinessPromise;
}

export async function reconnectBackend() {
  readinessPromise = undefined;
  return readyBackend();
}

function requestHeaders(config: BackendConfig, options: RequestInit) {
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body !== undefined) headers.set("Content-Type", "application/json");
  if (config.token) headers.set("Authorization", `Bearer ${config.token}`);
  return headers;
}

function readableNetworkError(error: unknown) {
  if (error instanceof DOMException && error.name === "AbortError") {
    return new Error("Le backend local n’a pas répondu dans le délai prévu.");
  }
  return new Error("La connexion au backend local a été interrompue. Utilisez « Reconnecter » pour réessayer.");
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const currentConfig = await readyBackend();
  let response: Response;
  try {
    response = await fetchWithTimeout(`${currentConfig.baseUrl}/api/v1${path}`, {
      ...options,
      headers: requestHeaders(currentConfig, options),
    }, REQUEST_TIMEOUT_MS);
  } catch (error) {
    updateConnectionState("offline");
    readinessPromise = undefined;
    throw readableNetworkError(error);
  }
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json() as { detail?: string };
      message = body.detail || message;
    } catch {
      // Keep the HTTP status when the backend did not return JSON.
    }
    throw new Error(message);
  }
  updateConnectionState("online");
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function downloadApi(path: string): Promise<Blob> {
  const currentConfig = await readyBackend();
  let response: Response;
  try {
    response = await fetchWithTimeout(`${currentConfig.baseUrl}/api/v1${path}`, {
      headers: requestHeaders(currentConfig, {}),
    }, REQUEST_TIMEOUT_MS);
  } catch (error) {
    updateConnectionState("offline");
    readinessPromise = undefined;
    throw readableNetworkError(error);
  }
  if (!response.ok) throw new Error(`Téléchargement impossible (${response.status}).`);
  return response.blob();
}

export async function textApi(path: string, options: RequestInit = {}): Promise<string> {
  const currentConfig = await readyBackend();
  let response: Response;
  try {
    response = await fetchWithTimeout(`${currentConfig.baseUrl}/api/v1${path}`, {
      ...options,
      headers: requestHeaders(currentConfig, options),
    }, REQUEST_TIMEOUT_MS);
  } catch (error) {
    updateConnectionState("offline");
    readinessPromise = undefined;
    throw readableNetworkError(error);
  }
  if (!response.ok) throw new Error(`Prévisualisation impossible (${response.status}).`);
  return response.text();
}

export function setDevelopmentToken(token: string) {
  localStorage.setItem("agentsec-api-token", token);
  configPromise = undefined;
  readinessPromise = undefined;
  updateConnectionState("connecting");
}
