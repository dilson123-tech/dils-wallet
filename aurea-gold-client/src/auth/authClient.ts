
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

const ACCESS_TOKEN_KEY = "aurea_access_token";
const REFRESH_TOKEN_KEY = "aurea_refresh_token";

function isBrowser(): boolean {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

export async function login(payload: LoginRequest): Promise<TokenResponse> {
  const url = API_BASE ? `${API_BASE}/api/v1/auth/login` : "/api/v1/auth/login";

  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    let message = "Falha ao autenticar. Verifique usuário e senha.";

    try {
      const data = await res.json();
      if (data && typeof data === "object" && "detail" in data) {
        const detail: any = (data as any).detail;
        if (typeof detail === "string") {
          message = detail;
        } else if (Array.isArray(detail) && detail.length > 0 && detail[0].msg) {
          message = detail[0].msg;
        }
      }
    } catch {
      // ignora erros ao tentar ler o corpo
    }

    throw new Error(message);
  }

  const data = (await res.json()) as TokenResponse;
  return data;
}

export function saveTokens(tokens: TokenResponse): void {
  if (!isBrowser()) return;
  window.localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
}

export function getAccessToken(): string | null {
  if (!isBrowser()) return null;
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (!isBrowser()) return null;
  return window.localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function clearTokens(): void {
  if (!isBrowser()) return;
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function getAuthHeaders(): HeadersInit {
  const token = getAccessToken();
  if (!token) return {};
  return {
    Authorization: `Bearer ${token}`,
  };
}
