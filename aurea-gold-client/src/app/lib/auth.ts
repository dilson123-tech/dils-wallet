import { login } from "@/app/lib/auth";
import { apiPost } from "@/app/lib/api";

export type LoginResult =
  | { ok: true; token: string }
  | { ok: false; error: string };

export async function login(email: string, password: string): Promise<LoginResult> {
  try {
    const data = await apiPost("/auth/login", { body: { email, password } }) as any;
    const token = data?.token || data?.access_token || data?.accessToken;
    if (typeof token === "string" && token.length > 0) return { ok: true, token };
    return { ok: false, error: String(data?.detail || data?.message || "Credenciais inválidas.") };
  } catch (e: any) {
    return { ok: false, error: String(e?.message || "Falha ao autenticar.") };
  }
}
