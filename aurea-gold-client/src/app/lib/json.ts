export async function readJson(res: Response) {
  // 204 sem corpo -> retorna null
  if (res.status === 204) return null;

  const ct = res.headers.get('content-type') || '';
  const text = await res.text();

  if (!text) return null;

  // Só tenta JSON quando o content-type indicar JSON
  if (ct.includes('application/json')) {
    try { return JSON.parse(text); }
    catch (err: any) {
      throw new Error(`JSON parse fail: ${err?.message || err}`);
    }
  }

  // Fallback: devolve bruto para inspeção (sem quebrar a UI)
  return { raw: text };
}
