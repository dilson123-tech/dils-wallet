import { readJson } from "@/app/lib/http";
export async function readJson(res: Response): Promise<any> {
  // 204 No Content
  if (res.status === 204) return null;

  const ct = res.headers.get('content-type') || '';
  const text = await res.text();

  if (!res.ok) {
    // Inclui um snippet do corpo para debug
    const snippet = text?.slice(0, 300);
    throw new Error(`${res.status} ${res.statusText} :: ${snippet}`);
  }

  if (ct.includes('application/json')) {
    if (!text) return null;
    try {
      return JSON.parse(text);
    } catch (e) {
      throw new Error(`JSON parse fail: ${(e as Error).message} :: body="${text.slice(0,200)}"`);
    }
  }

  // Não-JSON: devolve bruto
  return { raw: text };
}
