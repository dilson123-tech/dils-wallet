import axios from "axios";
import API, { LOGIN_PATH, clearSession, getRefreshToken, saveTokens } from "./api";

export type WhoamiUser = {
  id: number;
  email: string;
  full_name: string | null;
  type?: string;
  role: string;
};

type LoginResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export function isAdmin(user: WhoamiUser | null | undefined): boolean {
  return user?.role === "admin";
}

export async function login(username: string, password: string): Promise<void> {
  const { data } = await API.post<LoginResponse>(LOGIN_PATH, { username, password });
  saveTokens(data.access_token, data.refresh_token);
}

export async function whoami(): Promise<WhoamiUser> {
  const { data } = await API.get<{ user: WhoamiUser }>("/api/v1/whoami");
  return data.user;
}

// Revoga o refresh token no servidor e limpa a sessão local mesmo se a
// chamada falhar (rede fora, timeout etc.).
export async function logout(): Promise<void> {
  const refresh_token = getRefreshToken();
  try {
    if (refresh_token) await API.post("/api/v1/auth/logout", { refresh_token });
  } catch {
    // sessão local é limpa de qualquer forma
  } finally {
    clearSession();
  }
}

export function httpStatus(err: unknown): number | undefined {
  return axios.isAxiosError(err) ? err.response?.status : undefined;
}

// Mensagem amigável para erros HTTP/rede. Nunca inclui tokens ou credenciais.
export function errorMessage(err: unknown): string {
  if (!axios.isAxiosError(err)) return "Erro inesperado. Tente novamente.";
  if (!err.response) return "Não foi possível conectar ao servidor. Verifique sua conexão.";
  switch (err.response.status) {
    case 401:
      return err.config?.url === LOGIN_PATH
        ? "Usuário ou senha inválidos."
        : "Sessão expirada. Faça login novamente.";
    case 403:
      return "Acesso negado.";
    case 429: {
      const retry = Number(err.response.headers?.["retry-after"]);
      return Number.isFinite(retry) && retry > 0
        ? `Muitas tentativas. Aguarde ${retry}s e tente novamente.`
        : "Muitas tentativas. Aguarde e tente novamente.";
    }
    default:
      return "Erro no servidor. Tente novamente.";
  }
}
