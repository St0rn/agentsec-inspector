const FALLBACK_URL = "http://127.0.0.1:8765";
let configPromise: Promise<{baseUrl:string; token:string}> | undefined;

async function config() {
  if (!configPromise) configPromise = (async () => {
    const envToken = import.meta.env.VITE_API_TOKEN || localStorage.getItem("agentsec-api-token") || "";
    try {
      const { invoke } = await import("@tauri-apps/api/core");
      return await invoke<{baseUrl:string; token:string}>("backend_config");
    } catch {
      return { baseUrl: import.meta.env.VITE_API_URL || FALLBACK_URL, token: envToken };
    }
  })();
  return configPromise;
}

export async function api<T>(path:string, options:RequestInit = {}):Promise<T> {
  const cfg = await config();
  const response = await fetch(`${cfg.baseUrl}/api/v1${path}`, { ...options, headers: {"Content-Type":"application/json", ...(cfg.token ? {Authorization:`Bearer ${cfg.token}`} : {}), ...options.headers} });
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try { message = (await response.json()).detail || message; } catch { /* non-JSON */ }
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function downloadApi(path:string):Promise<Blob> {
  const cfg = await config();
  const response = await fetch(`${cfg.baseUrl}/api/v1${path}`, {headers: cfg.token ? {Authorization:`Bearer ${cfg.token}`} : {}});
  if (!response.ok) throw new Error(`Download failed: ${response.status}`);
  return response.blob();
}

export function setDevelopmentToken(token:string) { localStorage.setItem("agentsec-api-token", token); configPromise = undefined; }
