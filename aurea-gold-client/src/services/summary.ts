const API = import.meta.env.VITE_API_BASE || "";

export type SummaryTx = {
  id?: number|string;
  tipo?: string;
  valor?: number;
  descricao?: string;
  created_at?: string;
};

export type SummaryRes = {
  txs: SummaryTx[];
  total_envios: number;
  total_transacoes: number;
  recebimentos: number;
  entradas: number;
  saldo_estimado: number;
};

const mapTx = (t: any): SummaryTx => ({
  id: t?.id ?? t?.tx_id ?? t?.uuid ?? undefined,
  tipo: t?.tipo ?? t?.type ?? (Number(t?.amount ?? t?.valor ?? 0) < 0 ? "ENVIO" : "PIX"),
  valor: Number(t?.valor ?? t?.value ?? t?.amount ?? 0),
  descricao: t?.descricao ?? t?.desc ?? t?.message ?? t?.memo ?? "PIX",
  created_at: (t?.created_at ?? t?.timestamp ?? t?.data ?? t?.date),
});

async function getJSON(path: string): Promise<any> {
  const r = await fetch(`${API}${path}`, { method: "GET" });
  if (!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json();
}

export async function fetchSummary(): Promise<SummaryRes> {
  const s: any = await getJSON("/api/v1/ai/summary").catch(() => ({}));

  const arr = (...c: any[]) => c.find(a => Array.isArray(a)) || [];
  let txsRaw: any[] = arr(s?.txs, s?.recent, s?.items, s?.transactions, s?.ultimas, s?.rows);

  if (!Array.isArray(txsRaw) || txsRaw.length === 0) {
    const list: any[] = await getJSON("/api/v1/pix/list").catch(() => []);
    txsRaw = Array.isArray(list) ? list.slice(0, 10) : [];
  }

  const txs = (txsRaw || []).map(mapTx);

  let total_envios       = Number(s?.total_envios ?? s?.envios ?? 0);
  let total_transacoes   = Number(s?.total_transacoes ?? s?.transacoes ?? 0);
  let recebimentos       = Number(s?.recebimentos ?? 0);
  let entradas           = Number(s?.entradas ?? 0);
  let saldo_estimado     = Number(s?.saldo_estimado ?? s?.saldo ?? 0);

  if (!total_transacoes) total_transacoes = txs.length;
  if (!total_envios)     total_envios     = txs.filter(t => String(t.tipo).toLowerCase()==="envio").reduce((a,b)=>a+(b.valor||0),0);
  if (!recebimentos)     recebimentos     = txs.filter(t => ["pix","recebimento","credito","entrada","in"].includes(String(t?.tipo||"").toLowerCase())).reduce((a,b)=>a+(b.valor||0),0);
  if (!entradas)         entradas         = txs.filter(t => ["pix","recebimento","credito","entrada","in"].includes(String(t?.tipo||"").toLowerCase())).length;
  if (!saldo_estimado && (recebimentos || total_envios))
                          saldo_estimado   = recebimentos - total_envios;

  return { txs, total_envios, total_transacoes, recebimentos, entradas, saldo_estimado };
}
