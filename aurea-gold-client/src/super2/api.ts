// -----------------------------------------------------
// API Super2 – Aurea Gold
// -----------------------------------------------------

export interface PixHistoryDay {
  dia: string;
  entradas: number;
  saidas: number;
}

export interface PixHistory7Payload {
  dias: PixHistoryDay[];
}

export const API_BASE = import.meta.env.VITE_API_BASE || "";
export const USER_EMAIL = import.meta.env.VITE_USER_EMAIL || "";

// ---------------- Histórico 7 dias ----------------
export async function fetchPix7d(): Promise<PixHistory7Payload> {
  const r = await fetch(`${API_BASE}/api/v1/pix/history?days=7`, {
    headers: {
      "X-User-Email": USER_EMAIL,
    },
  });

  if (!r.ok) {
    throw new Error(`Erro ao carregar histórico PIX 7d (HTTP ${r.status})`);
  }

  return r.json() as Promise<PixHistory7Payload>;
}

// ---------------- Saldo PIX ----------------
export interface PixBalancePayload {
  saldo: number;
}

export async function fetchPixBalance(): Promise<PixBalancePayload> {
  const r = await fetch(`${API_BASE}/api/v1/pix/balance`, {
    headers: {
      "X-User-Email": USER_EMAIL,
    },
  });

  if (!r.ok) {
    throw new Error(`Erro ao carregar saldo PIX (HTTP ${r.status})`);
  }

  return r.json() as Promise<PixBalancePayload>;
}

// ---------------- Envio PIX ----------------
export async function sendPix(
  dest: string,
  valor: number,
  desc: string = "PIX",
  ngfi?: string
): Promise<any> {
  const r = await fetch(`${API_BASE}/api/v1/pix/send`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-User-Email": USER_EMAIL,
      ...(ngfi ? { "X-NGFI": ngfi } : {}),
    },
    body: JSON.stringify({
      dest,
      valor,
      descricao: desc,
    }),
  });

  if (!r.ok) {
    throw new Error(`Erro no envio PIX (HTTP ${r.status})`);
  }

  return r.json();
}

export const fetchPixHistory7d = fetchPix7d;
