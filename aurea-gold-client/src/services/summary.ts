const API = import.meta.env.VITE_API_BASE || "";

export type SummaryTx = {
  id?: number|string;
  tipo?: string;
  valor?: number;
  descricao?: string;
  created_at?: string;
};

export type SummaryRes = { txs: SummaryTx[] };

const mapTx = (t: any): SummaryTx => ({
  id: t?.id ?? t?.tx_id ?? t?.uuid ?? undefined,
  tipo: t?.tipo ?? t?.type ?? (Number(t?.amount ?? t?.valor ?? 0) < 0 ? "ENVIO" : "PIX"),
  valor: Number(t?.valor ?? t?.value ?? t?.amount ?? 0),
  descricao: t?.descricao ?? t?.desc ?? t?.message ?? t?.memo ?? "",
  created_at: t?.created_at ?? t?.data ?? t?.date ?? undefined,
});

async function getJSON(path: string): Promise<any> {
  const r = await fetch(`${API}${path}`, { method: "GET" });
  if (!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json();
}

/**
 * Busca o summary e normaliza diversos formatos.
 * Se vier vazio, cai para /api/v1/pix/list.
 * Nunca lança erro para não quebrar a UI.
 */
export async function fetchSummary(): Promise<SummaryRes> {
  try {
    const s: any = await getJSON("/api/v1/ai/summary").catch(() => ({}));
    const pick = (...c: any[]) => c.find(a => Array.isArray(a)) || [];
    let txs: any[] = pick(s?.txs, s?.recent, s?.items, s?.transactions, s?.ultimas, s?.rows);

    if (!Array.isArray(txs) || txs.length === 0) {
      const list: any[] = await getJSON("/api/v1/pix/list").catch(() => []);
      txs = Array.isArray(list) ? list.slice(0, 10) : [];
    }
    return { txs: (txs || []).map(mapTx) };
  } catch {
    return { txs: [] };
  }
}
