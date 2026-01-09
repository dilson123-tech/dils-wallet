import { getToken } from "../lib/auth";

const RAW_BASE = String(import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000").replace(/\/+$/, "");
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
      Authorization: `Bearer ${getToken()}`,
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
export async function getPixHistory(limit = 10) {
  const res = await fetch(`${BASE_URL}/pix/history?limit=${limit}`, {
    method: "GET",
    headers: {
      ...authHeaders(),
    },
    credentials: "include",
  });

  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    console.error("Erro /pix/history", res.status, txt);
    throw new Error(`pix/history status ${res.status}`);
  }

  return res.json();
}

// tentativa de identificar usuário logado
export async function getMe() {
  try {
    const res = await fetch(`${BASE_URL}/whoami`, {
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