const RAW_BASE = String(import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000").replace(/\/+$/, "");
const BASE_URL = `${RAW_BASE}/api/v1`;

function getToken() {
  return (
    localStorage.getItem("aurea.access_token") ||
    localStorage.getItem("aurea_access_token") ||
    localStorage.getItem("aurea.jwt") ||
    localStorage.getItem("aurea_jwt") ||
    localStorage.getItem("authToken") ||
    ""
  );
}


// rota protegida (precisa Bearer)
export async function getPixBalance() {
  const res = await fetch(`${BASE_URL}/pix/balance`, {
    method: "GET",
    headers: {
      "Authorization": `Bearer ${getToken()}`,
          },
    credentials: "include",
  });

  if (!res.ok) {
    const txt = await res.text();
    console.error("Erro /pix/balance", res.status, txt);
    throw new Error(`pix/balance status ${res.status}`);
  }

  return res.json(); // { balance: number }
}

// rota mock / pública
export async function getPixHistory(limit = 10) {
  const res = await fetch(`${BASE_URL}/pix/history?limit=${limit}`, {
    method: "GET",
    headers: {
            // se futuramente exigir auth, já deixo pronto:
      "Authorization": `Bearer ${getToken()}`
    },
    credentials: "include",
  });

  if (!res.ok) {
    const txt = await res.text();
    console.error("Erro /pix/history", res.status, txt);
    throw new Error(`pix/history status ${res.status}`);
  }

  return res.json(); // lista
}

// tentativa de identificar usuário logado
export async function getMe() {
  try {
    // tenta rota comum "whoami"
    const res = await fetch(`${BASE_URL}/whoami`, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${getToken()}`,
              },
      credentials: "include",
    });

    if (!res.ok) {
      // se backend ainda não tem rota /whoami, cai no fallback
      return { displayName: "Cliente Aurea Gold" };
    }

    const data = await res.json();
    // normaliza em { displayName: string }
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
