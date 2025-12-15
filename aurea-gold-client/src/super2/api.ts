import { authFetch } from "../auth/authClient";
const DEFAULT_API_BASE = "http://127.0.0.1:8000";
const DEFAULT_USER_EMAIL = "dilsonpereira231@gmail.com";

export const API_BASE = import.meta.env.VITE_API_BASE || DEFAULT_API_BASE;
export const USER_EMAIL = import.meta.env.VITE_USER_EMAIL || DEFAULT_USER_EMAIL;
console.log("SUPER2 API_BASE =>", API_BASE, "USER_EMAIL =>", USER_EMAIL);


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

// Histórico transacional cru (se precisar no futuro)
export type PixHistoryItem = {
  id: number;
  tipo: "envio" | "recebido";
  valor: number;
  descricao?: string | null;
  created_at: string;
  // campos de taxa vindos do backend (opcionais enquanto fazemos a transição)
  taxa_percentual?: number | null;
  taxa_valor?: number | null;
  valor_liquido?: number | null;
};

async function apiGet<T>(path: string): Promise<T> {
  const headers: Record<string, string> = {};
  if (USER_EMAIL) {
    headers["X-User-Email"] = USER_EMAIL;
  }

  const r = await fetch(`${API_BASE}${path}`, {
    method: "GET",
    headers,
  });

  if (!r.ok) {
    throw new Error(`GET ${path} -> HTTP ${r.status}`);
  }

  return (await r.json()) as T;
}

async function apiPost<T>(path: string, body: any): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (USER_EMAIL) {
    headers["X-User-Email"] = USER_EMAIL;
  }

  const r = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });

  if (!r.ok) {
    const t = await r.text().catch(() => "");
    throw new Error(`POST ${path} -> HTTP ${r.status} ${t}`);
  }

  return (await r.json()) as T;
}

// 🔹 usado pelo painel Super2 (gráfico + saldos)
// Por enquanto apontando para a rota estável com days=7
export function fetchPixBalance(): Promise<PixBalancePayload> {
  return apiGet<PixBalancePayload>("/api/v1/pix/balance?days=7");
}

// 🔹 histórico de PIX — backend pode devolver vários formatos, tratamos no front
export async function fetchPixHistory(): Promise<any> {
  const headers: Record<string, string> = {};
  if (USER_EMAIL) {
    headers["X-User-Email"] = USER_EMAIL;
  }

  const r = await authFetch(`${API_BASE}/api/v1/pix/history`, {
    method: "GET",
    headers,
  });

  if (!r.ok) {
    const t = await r.text().catch(() => "");
    throw new Error(`PIX history HTTP ${r.status} ${t}`);
  }

  return r.json();
}

// 🔹 envio de PIX
export type PixSendPayload = {
  dest: string;
  valor: number;
  descricao?: string | null;
};

// overload: aceita payload OU (dest, valor, descricao)
export function sendPix(payload: PixSendPayload): Promise<any>;
export function sendPix(
  dest: string,
  valor: number,
  descricao?: string | null
): Promise<any>;
export function sendPix(
  arg1: any,
  arg2?: any,
  arg3?: any
): Promise<any> {
  let payload: PixSendPayload;

  if (typeof arg1 === "string") {
    payload = {
      dest: arg1,
      valor: typeof arg2 === "number" ? arg2 : 0,
      descricao: arg3 ?? null,
    };
  } else {
    payload = arg1 as PixSendPayload;
  }

  return apiPost<any>("/api/v1/pix/send", payload);
}
