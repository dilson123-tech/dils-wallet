import axios from "axios";

export const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE || import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export const LOGIN_PATH = "/api/v1/auth/login";

// Armazenamento único da sessão. Nunca logar estes valores.
const ACCESS_KEY = "aurea_token";
const REFRESH_KEY = "aurea_refresh";
// Chaves antigas (inclui o "demo" da tela fictícia), removidas ao limpar a sessão.
const LEGACY_KEYS = ["aurea_user", "aurea_role", "auth_token"];

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY);
}

export function saveTokens(access: string, refresh: string): void {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearSession(): void {
  for (const k of [ACCESS_KEY, REFRESH_KEY, ...LEGACY_KEYS]) localStorage.removeItem(k);
}

export const API = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

API.interceptors.request.use((cfg) => {
  const t = getAccessToken();
  if (t) cfg.headers.Authorization = `Bearer ${t}`;
  return cfg;
});

// 401 = sessão inválida/expirada: limpa a sessão local e volta ao login.
// Não redireciona na própria chamada de login (a tela mostra a mensagem) nem
// quando já está em /login (evita loop). 403 é propagado para a tela tratar.
API.interceptors.response.use(r => r, err => {
  if (err?.response?.status === 401 && err.config?.url !== LOGIN_PATH) {
    clearSession();
    if (window.location.pathname !== "/login") window.location.assign("/login");
  }
  return Promise.reject(err);
});

export default API;
