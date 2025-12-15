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
  return String(raw || "").replace(/\/+$/, "");
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

