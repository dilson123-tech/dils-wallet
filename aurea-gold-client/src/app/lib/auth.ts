import { login } from "@/app/lib/auth";
import { apiPost } from "@/app/lib/api";

export type LoginResult =
  | { ok: true; token: string }
  | { ok: false; error: string };

export async function login(email: string, password: string): Promise<LoginResult> {
  try {
    const data = await apiPost("/auth/login", {
      body: { email, password },
    }) as any;

    const token = data?.token || data?.access_token || data?.accessToken;
    if (token && typeof token === "string") {
      return { ok: true, token };
    }

    const msg = data?.detail || data?.message || "Credenciais inválidas.";
    return { ok: false, error: String(msg) };
  } catch (e: any) {
    const msg = e?.message || "Falha ao autenticar.";
    return { ok: false, error: String(msg) };
  }
}
