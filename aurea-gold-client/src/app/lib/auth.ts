import { apiPost } from "./api";

export type LoginResult = { token?: string; user?: any; raw?: string };

export async function login(email: string, password: string): Promise<LoginResult> {
  // manda o corpo certinho; apiPost já trata 204 / non-JSON / erro HTTP
  const res = await apiPost("/auth/login", { body: { email, password } });

  // Se a API devolveu JSON com token
  if (res && typeof res === "object" && "token" in res) {
    return res as LoginResult;
  }

  // Se não veio JSON, apiPost retorna { raw }
  if (res && typeof res === "object" && "raw" in res) {
    return res as LoginResult;
  }

  // fallback — não quebre a UI
  return { raw: String(res ?? "") };
}
