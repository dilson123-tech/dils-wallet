import { authFetch } from "../auth/authClient";

const DEFAULT_API_BASE = "http://127.0.0.1:8000";
export const API_BASE = String(import.meta.env.VITE_API_BASE || DEFAULT_API_BASE).replace(/\/+$/, "");


export const USER_EMAIL: string = String((import.meta as any).env?.VITE_USER_EMAIL || "");
console.log("SUPER2 API_BASE =>", API_BASE);

// Dia agregado (gráfico + resumos)
export type PixDayPoint = {
  dia: string;
  entradas: number;
  saidas: number;
};

// aliases para manter compatibilidade com arquivos antigos
export type PixDailyRaw = PixDayPoint;
export type PixHistoryDay = PixDayPoint;

// Payload de saldo + últimos 7 dias
export type PixBalancePayload = {
  saldo_atual: number;
  entradas_mes: number;
  saidas_mes: number;
  ultimos_7d: PixDayPoint[];
};

// Histórico transacional (alinhado com o backend)
export type PixHistoryItem = {
  id: number;
  tipo: string;
  valor: number;
  descricao?: string | null;
  timestamp?: string | null;
    created_at?: string | null; // compat legado
  taxa_percentual?: number | null;
  taxa_valor?: number | null;
  valor_liquido?: number | null;
};

export type PixHistoryResponse = {
  dias: PixHistoryDay[];
  history: PixHistoryItem[];
  updated_at: string;
  source?: string;
};

async function apiGet<T>(path: string): Promise<T> {
  const r = await authFetch(`${API_BASE}${path}`, {
    method: "GET",
  });

  if (!r.ok) {
    const txt = await r.text().catch(() => "");
    throw new Error(`GET ${path} -> HTTP ${r.status} ${txt}`);
  }

  return (await r.json()) as T;
}

async function apiPost<T>(path: string, body: any): Promise<T> {
  const r = await authFetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!r.ok) {
    const txt = await r.text().catch(() => "");
    throw new Error(`POST ${path} -> HTTP ${r.status} ${txt}`);
  }

  return (await r.json()) as T;
}

// 🔹 usado pelo painel Super2 (gráfico + saldos)
export function fetchPixBalance(): Promise<PixBalancePayload> {
  return apiGet<PixBalancePayload>("/api/v1/pix/balance?days=7");
}

// 🔹 histórico de PIX (já padronizado no backend)
export function fetchPixHistory(): Promise<PixHistoryResponse> {
  return apiGet<PixHistoryResponse>("/api/v1/pix/history");
}

// 🔹 lista rápida (TxHistoryLive/Home etc.)
export type PixListItem = {
  id: number;
  tipo: string;
  valor: number;
  descricao?: string | null;
  taxa_percentual?: number | null;
  taxa_valor?: number | null;
  valor_liquido?: number | null;
};
export function fetchPixList(limit = 50): Promise<PixListItem[]> {
  return apiGet<PixListItem[]>(`/api/v1/pix/list?limit=${encodeURIComponent(String(limit))}`);
}

// 🔹 envio de PIX (backend espera msg)
export type PixSendPayload = {
  dest: string;
  valor: number;
  msg?: string | null;
  idem_key?: string | null;

  // legado: alguns lugares usam "descricao"
  descricao?: string | null;
};

// overload: aceita payload OU (dest, valor, msg)
export function sendPix(payload: PixSendPayload): Promise<any>;
export function sendPix(dest: string, valor: number, msg?: string | null): Promise<any>;
export function sendPix(arg1: any, arg2?: any, arg3?: any): Promise<any> {
  let payload: PixSendPayload;

  if (typeof arg1 === "string") {
    payload = { dest: arg1, valor: typeof arg2 === "number" ? arg2 : 0, msg: arg3 ?? null };
  } else {
    payload = arg1 as PixSendPayload;
  }

  // normaliza legado: "descricao" -> "msg"
  const msg = (payload.msg ?? payload.descricao ?? null);
  const out = {
    dest: payload.dest,
    valor: payload.valor,
    msg,
    idem_key: payload.idem_key ?? null,
  };

  return apiPost<any>("/api/v1/pix/send", out);
}
