import { saveTokens, getAccessToken, clearTokens } from "../auth/authClient";
const RAW_BASE = String(import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000").replace(/\/+$/, "");
const BASE_URL = `${RAW_BASE}/api/v1`;

export async function loginRequest(username: string, password: string) {
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({
      username,
      password,
    }),
  });

  if (!res.ok) {
    const txt = await res.text();
    console.error("Erro /auth/login", res.status, txt);
    throw new Error(`login status ${res.status}`);
  }

  const data = await res.json();

  // assumindo { access_token: "...", token_type: "bearer" }
  if (data.access_token) {
  // padrão Aurea (novo)
  saveTokens(data.access_token, (data as any).refresh_token ?? null);
  // legado (compat)
  localStorage.setItem("authToken", data.access_token);
}

  return data;
}

export function getToken() {
  return getAccessToken() || localStorage.getItem("authToken") || "";
}


export function clearToken() {
  clearTokens();
  localStorage.removeItem("authToken");
}


export function isLoggedIn() {
  return getToken() !== "";
}
