const ACCESS_TOKEN_KEYS = [
  "aurea.access_token",  // padrão novo
  "aurea_access_token",  // legado
  "aurea.jwt",           // legado
  "aurea_jwt",           // legado
];

const REFRESH_TOKEN_KEYS = [
  "aurea.refresh_token", // padrão novo
  "aurea_refresh_token", // legado
];

function getFirst(keys: string[]): string | null {
  try {
    for (const k of keys) {
      const v = localStorage.getItem(k);
      if (v && typeof v === "string") return v;
    }
    return null;
  } catch {
    return null;
  }
}

function setAll(keys: string[], value: string) {
  for (const k of keys) localStorage.setItem(k, value);
}

function removeAll(keys: string[]) {
  for (const k of keys) localStorage.removeItem(k);
}


export interface TokenResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

function getApiBase(): string {
  const raw = (import.meta as any)?.env?.VITE_API_BASE ?? (import.meta as any)?.env?.VITE_API_BASE_URL ?? "";
  const envBase = String(raw || "").replace(/\/+$/, "");

  // Se o front abriu por IP na rede (ex: 192.168.x.x:5173),
  // o backend está no mesmo host na porta 8000.
  try {
    if (typeof window !== "undefined" && window.location?.hostname) {
      const h = window.location.hostname;
      if (h && h !== "localhost" && h !== "127.0.0.1") {
        if (!envBase || /localhost|127\.0\.0\.1/.test(envBase)) {
          return `http://${h}:8000`;
        }
      }
    }
  } catch {}

  return envBase;
}


function maybeInjectDevToken(): void {
  // --- AUREA LAB (DEV): injeta token via ?token=... ou VITE_DEV_TOKEN ---
const DEV_RT: string = String(((import.meta as any)?.env?.VITE_DEV_REFRESH_TOKEN as string) || "").trim();
try { if (DEV_RT) { localStorage.setItem("aurea.refresh_token", DEV_RT); localStorage.setItem("aurea_refresh_token", DEV_RT); } } catch {}
  try {
    const isDev = !!((import.meta as any)?.env?.DEV);
    if (!isDev || typeof window === "undefined") return;

    const sp = new URLSearchParams(window.location.search);
    const qtok = (sp.get("token") || "").trim();
    const etok = String(((import.meta as any)?.env?.VITE_DEV_TOKEN as string) || "").trim();
    const tok = qtok || etok;

    // JWT básico: 3 partes
    if (tok && tok.split(".").length === 3) {
      try { setAll(ACCESS_TOKEN_KEYS, tok); } catch {}

      // limpa token da URL pra não vazar em print
      if (qtok) {
        sp.delete("token");
        const qs = sp.toString();
        const clean = window.location.pathname + (qs ? "?" + qs : "") + window.location.hash;
        window.history.replaceState({}, "", clean);
      }
    }
  } catch {}
  // --- /AUREA LAB (DEV) ---
}
export async function login(payload: LoginRequest): Promise<TokenResponse> {
  const API_BASE = getApiBase();

  const url = API_BASE
    ? `${API_BASE}/api/v1/auth/login`
    : "/api/v1/auth/login";

  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error("Falha ao autenticar na Aurea Gold.");
  }

  const data = (await res.json()) as TokenResponse;
  saveTokens(data.access_token, (data as any).refresh_token ?? null);
  return data;
}

export function getAccessToken(): string | null {
  try {
      maybeInjectDevToken();
    return getFirst(ACCESS_TOKEN_KEYS);
  } catch {
    return null;
  }
}

export function setAccessToken(token: string | null): void {
  try {
    const tok =
      typeof token === "string"
        ? token
        : (token as any)?.access_token; // defesa contra [object Object]

    if (tok && typeof tok === "string") {
      setAll(ACCESS_TOKEN_KEYS, tok);
    } else {
      removeAll(ACCESS_TOKEN_KEYS);
    }
  } catch {
    // ambiente sem localStorage
  }
}

export function clearAuth(): void {
  clearTokens();
}
export function authHeaders(extra?: HeadersInit): HeadersInit {
  const token = getAccessToken();

  const base: Record<string, string> = {};
  if (token) {
    base["Authorization"] = "Bearer " + token;
  }

  const extraObj: Record<string, string> = {};
  if (extra) {
    const h = new Headers(extra as HeadersInit);
    h.forEach((value, key) => {
      extraObj[key] = value;
    });
  }

  return {
    ...extraObj,
    ...base,
  };
}

export async function authFetch(
  input: RequestInfo | URL,
  init: RequestInit = {},
): Promise<Response> {
  const headers = authHeaders(init.headers);
  return fetch(input, {
    ...init,
    headers,
  });
}

export function clearTokens() {
  try {
    removeAll(ACCESS_TOKEN_KEYS);
    removeAll(REFRESH_TOKEN_KEYS);
  } catch (err) {
    console.warn("[auth] erro ao limpar tokens:", err);
  }
}

export function saveTokens(accessToken: string, refreshToken?: string | null) {
  try {
    if (accessToken) {
      setAll(ACCESS_TOKEN_KEYS, accessToken);
    }
    if (refreshToken) {
      setAll(REFRESH_TOKEN_KEYS, refreshToken);
    }
  } catch (err) {
    console.warn("[auth] erro ao salvar tokens:", err);
  }
}

