import { apiPost } from "./api";
import { ApiError } from "../../lib/api";

export interface PromiseLogin {
  ok: boolean;
  token?: string;
  raw?: string;
  status?: number;
  retryAfter?: number;
  message?: string;
}

function pickDetailMessage(raw?: string): string | undefined {
  if (!raw) return undefined;
  try {
    const j = JSON.parse(raw);
    const d = (j as any)?.detail;
    if (typeof d === "string") return d;
  } catch {}
  return undefined;
}

export async function login(username: string, password: string): Promise<PromiseLogin> {
  try {
    // chama FastAPI em /api/v1/auth/login (JSON)
    const data = await apiPost("/api/v1/auth/login", { username, password });

    const token =
      (data as any)?.access_token ??
      (data as any)?.token ??
      (data as any)?.jwt ??
      "";

    return {
      ok: true,
      token,
      raw: JSON.stringify(data),
    };
  } catch (e: any) {
    // ApiError (nosso CORE agora carrega status + retry-after + bodyText)
    if (e instanceof ApiError) {
      const status = e.status;
      const retryAfter = e.retryAfter;
      const detail = pickDetailMessage(e.bodyText);

      if (status === 429) {
        const ra = typeof retryAfter === "number" ? retryAfter : 60;
        return {
          ok: false,
          status,
          retryAfter: ra,
          message: detail || `Muitas tentativas. Aguarde ${ra}s e tente de novo.`,
          raw: e.bodyText,
        };
      }

      if (status === 401) {
        return {
          ok: false,
          status,
          message: detail || "Credenciais inválidas",
          raw: e.bodyText,
        };
      }

      return {
        ok: false,
        status,
        message: detail || `Erro ${status}`,
        raw: e.bodyText,
      };
    }

    const msg = (e && typeof e.message === "string") ? e.message : "Erro desconhecido";
    return { ok: false, message: msg };
  }
}
