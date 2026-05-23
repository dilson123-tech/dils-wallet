import { authFetch } from "../auth/authClient";
import { API_BASE } from "../lib/apiBase";
export { API_BASE };


export const USER_EMAIL: string = String((import.meta as any).env?.VITE_USER_EMAIL || "");

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

export async function apiGet<T>(path: string): Promise<T> {
  // authFetch injeta Authorization (access token oficial) e pode fazer refresh/retry.
  const r = await authFetch(`${API_BASE}${path}`, { method: "GET" });
if (!r.ok) {
    const txt = await r.text().catch(() => "");
    throw new Error(`GET ${path} -> HTTP ${r.status} ${txt}`);
  }

  return (await r.json()) as T;
}

async function apiPost<T>(path: string, body: any): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
const r = await authFetch(`${API_BASE}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });

  if (!r.ok) {
    const txt = await r.text().catch(() => "");
    throw new Error(`POST ${path} -> HTTP ${r.status} ${txt}`);
  }

  return (await r.json()) as T;
}


export type WalletPartnerStatus = {
  ok: boolean;
  service: string;
  wallet_mode: "demo" | "partner";
  provider: string;
  real_money: boolean;
};

export function fetchWalletPartnerStatus(): Promise<WalletPartnerStatus> {
  return apiGet<WalletPartnerStatus>("/api/v1/wallet/partner/status");
}

export type WalletAccountStatus = {
  ok: boolean;
  service: string;
  user?: {
    id?: number | null;
    email?: string | null;
    full_name?: string | null;
    type?: string | null;
    role?: string | null;
  };
  wallet: {
    mode: "demo" | "partner" | string;
    provider: string;
    provider_adapter_ready: boolean;
    provider_adapter_error?: string | null;
    real_money_enabled: boolean;
    account_status: string;
    kyc_status: string;
    kyb_status: string;
    currency: string;
  };
  limitations: string[];
  next_steps: string[];
};

export function fetchWalletAccountStatus(): Promise<WalletAccountStatus> {
  return apiGet<WalletAccountStatus>("/api/v1/wallet/account-status");
}

export type WalletStructuredBalance = {
  ok: boolean;
  service: string;
  user_id?: number | null;
  balance: {
    available: string;
    blocked: string;
    pending: string;
    currency: string;
  };
  wallet: {
    mode: "demo" | "partner" | string;
    provider: string;
    source: string;
    real_money_enabled: boolean;
    adapter_error?: string | null;
  };
  notice: string;
};

export function fetchWalletStructuredBalance(): Promise<WalletStructuredBalance> {
  return apiGet<WalletStructuredBalance>("/api/v1/wallet/structured-balance");
}

export type WalletStructuredStatementItem = {
  provider_reference: string;
  direction: "credit" | "debit" | string;
  amount: string;
  status: string;
  description: string;
  created_at?: string | null;
  source: string;
  real_money_enabled: boolean;
};

export type WalletStructuredStatement = {
  ok: boolean;
  service: string;
  user_id?: number | null;
  statement: {
    items: WalletStructuredStatementItem[];
    count: number;
    limit: number;
    currency: string;
  };
  wallet: {
    mode: "demo" | "partner" | string;
    provider: string;
    source: string;
    real_money_enabled: boolean;
    adapter_error?: string | null;
  };
  notice: string;
};

export function fetchWalletStructuredStatement(limit = 20): Promise<WalletStructuredStatement> {
  return apiGet<WalletStructuredStatement>(`/api/v1/wallet/structured-statement?limit=${encodeURIComponent(String(limit))}`);
}

export type WalletReceiptReconciliation = {
  ok: boolean;
  service: string;
  user_id?: number | null;
  receipt: {
    receipt_id: string;
    provider_reference: string;
    transaction_status: string;
    audit_status: string;
    reconciliation_status: string;
    issued_at: string;
    currency: string;
  };
  wallet: {
    mode: "demo" | "partner" | string;
    provider: string;
    source: string;
    real_money_enabled: boolean;
    adapter_error?: string | null;
  };
  notice: string;
  next_steps: string[];
};

export function fetchWalletReceiptReconciliation(providerReference = "demo-ui-preview"): Promise<WalletReceiptReconciliation> {
  return apiGet<WalletReceiptReconciliation>(
    `/api/v1/wallet/receipt-reconciliation?provider_reference=${encodeURIComponent(providerReference)}`
  );
}

export type WalletOperationalLimits = {
  ok: boolean;
  service: string;
  user_id?: number | null;
  wallet: {
    mode: "demo" | "partner" | string;
    provider: string;
    source: string;
    adapter_ready: boolean;
    adapter_error?: string | null;
    real_money_enabled: boolean;
  };
  permissions: {
    can_send_pix: boolean;
    can_receive_pix: boolean;
    requires_confirmation: boolean;
  };
  limits: {
    per_transaction_limit: string;
    daily_limit: string;
    monthly_limit: string;
    currency: string;
  };
  security: {
    sensitive_action_confirmation_required: boolean;
    kyc_required: boolean;
    kyb_required_for_business: boolean;
    audit_required: boolean;
    reconciliation_required: boolean;
  };
  reason: string;
  limitations: string[];
  next_steps: string[];
};

export function fetchWalletOperationalLimits(): Promise<WalletOperationalLimits> {
  return apiGet<WalletOperationalLimits>("/api/v1/wallet/operational-limits");
}

export type WalletOnboardingStatus = {
  ok: boolean;
  service: string;
  user_id?: number | null;
  wallet: {
    mode: "demo" | "partner" | string;
    provider: string;
    source: string;
    adapter_ready: boolean;
    adapter_error?: string | null;
    real_money_enabled: boolean;
  };
  onboarding: {
    customer_type: "pf" | "pj" | "unknown" | string;
    status: "not_started" | "pending" | "in_review" | "approved" | "rejected" | string;
    kyc_status: "not_started" | "pending" | "in_review" | "approved" | "rejected" | string;
    kyb_status: "not_required" | "not_started" | "pending" | "in_review" | "approved" | "rejected" | string;
    required_documents: string[];
    missing_fields: string[];
    can_start_real_operations: boolean;
    can_send_pix: boolean;
    can_receive_pix: boolean;
  };
  reason: string;
  limitations: string[];
  next_steps: string[];
};

export function fetchWalletOnboardingStatus(): Promise<WalletOnboardingStatus> {
  return apiGet<WalletOnboardingStatus>("/api/v1/wallet/onboarding-status");
}

export type WalletPixSandboxPaymentPayload = {
  amount: string | number;
  description?: string;
  external_id?: string | null;
};

export type WalletPixSandboxPayment = {
  ok: boolean;
  service: string;
  user_id?: number | null;
  payment: {
    provider: string;
    provider_reference: string;
    status: string;
    amount: string;
    currency: string;
    description: string;
    qr_code?: string | null;
    copy_paste?: string | null;
    created_at: string;
  };
  wallet: {
    mode: "demo" | "partner" | string;
    provider: string;
    source: string;
    real_money_enabled: boolean;
  };
  can_credit_balance: boolean;
  can_generate_real_receipt: boolean;
  notice: string;
  limitations: string[];
  next_steps: string[];
};

export function createWalletPixSandboxPayment(
  payload: WalletPixSandboxPaymentPayload
): Promise<WalletPixSandboxPayment> {
  return apiPost<WalletPixSandboxPayment>("/api/v1/wallet/pix/sandbox-payment", payload);
}

export type WalletPixSandboxReconciliation = {
  ok: boolean;
  service: string;
  user_id?: number | null;
  reconciliation: {
    provider: string;
    provider_reference: string;
    status: string;
    event_found: boolean;
    audit_status: string;
    reconciliation_status: string;
    amount?: string | null;
    received_at?: string | null;
    event_type?: string | null;
  };
  wallet: {
    mode: "demo" | "partner" | string;
    provider: string;
    source: string;
    real_money_enabled: boolean;
  };
  webhook?: Record<string, unknown>;
  idempotency?: {
    key: string;
    request_hash?: string | null;
    status_code?: number | null;
    stored_at?: string | null;
  };
  can_credit_balance: boolean;
  can_generate_real_receipt: boolean;
  can_mark_real_paid: boolean;
  notice: string;
  limitations?: string[];
  next_steps?: string[];
};

export function fetchWalletPixSandboxReconciliation(
  providerReference: string
): Promise<WalletPixSandboxReconciliation> {
  return apiGet<WalletPixSandboxReconciliation>(
    `/api/v1/wallet/pix/sandbox-reconciliation/${encodeURIComponent(providerReference)}`
  );
}

export type WalletPixSandboxAuditHistoryItem = {
  provider: string;
  provider_reference: string;
  event_type?: string | null;
  status: string;
  amount?: string | null;
  received_at?: string | null;
  audit_status: string;
  reconciliation_status: string;
  real_money_enabled: boolean;
  idempotency?: {
    key: string;
    request_hash?: string | null;
    status_code?: number | null;
    stored_at?: string | null;
  };
  can_credit_balance: boolean;
  can_generate_real_receipt: boolean;
  can_mark_real_paid: boolean;
};

export type WalletPixSandboxAuditHistory = {
  ok: boolean;
  service: string;
  user_id?: number | null;
  history: {
    provider: string;
    source: string;
    limit: number;
    total_returned: number;
    audit_status: string;
  };
  wallet: {
    mode: "demo" | "partner" | string;
    provider: string;
    source: string;
    real_money_enabled: boolean;
  };
  items: WalletPixSandboxAuditHistoryItem[];
  can_credit_balance: boolean;
  can_generate_real_receipt: boolean;
  can_mark_real_paid: boolean;
  notice: string;
  limitations?: string[];
  next_steps?: string[];
};

export function fetchWalletPixSandboxAuditHistory(
  limit = 10
): Promise<WalletPixSandboxAuditHistory> {
  return apiGet<WalletPixSandboxAuditHistory>(
    `/api/v1/wallet/pix/sandbox-audit-history?limit=${encodeURIComponent(String(limit))}`
  );
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
