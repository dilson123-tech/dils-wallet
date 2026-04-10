import { getToken } from "../lib/auth";
import { apiGet, type PixHistoryResponse} from "../super2/api";

const RAW_BASE = String(import.meta.env.VITE_API_BASE || "").replace(/\/+$/, "");
const BASE_URL = `${RAW_BASE}/api/v1`;

function authHeaders(): Record<string, string> {
  const tok = getToken();
  return tok ? { Authorization: `Bearer ${tok}` } : {};
}

// rota protegida (precisa Bearer)
export async function getPixBalance() {
  const res = await fetch(`${BASE_URL}/pix/balance`, {
    method: "GET",
    headers: {
...authHeaders(),
    },
    credentials: "include",
  });

  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    console.error("Erro /pix/balance", res.status, txt);
    throw new Error(`pix/balance status ${res.status}`);
  }

  return res.json();
}

// rota protegida (se exigir auth)
export async function getPixHistory(limit = 50): Promise<PixHistoryResponse> {
  const q = `?limit=${encodeURIComponent(String(limit))}`;
  return apiGet<PixHistoryResponse>(`/api/v1/pix/history${q}`);
}




// tentativa de identificar usuário logado
export async function getMe() {
  try {
    const res = await fetch(`${BASE_URL}/users/me`, {
      method: "GET",
      headers: {
        ...authHeaders(),
      },
      credentials: "include",
    });

    if (!res.ok) {
      return { displayName: "Cliente Aurea Gold" };
    }

    const data = await res.json();
    return {
      displayName:
        data.full_name ||
        data.name ||
        data.username ||
        data.user ||
        data.email ||
        "Cliente Aurea Gold",
    };
  } catch (_) {
    return { displayName: "Cliente Aurea Gold" };
  }
}