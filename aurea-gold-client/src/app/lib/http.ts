export async function readJson(res: Response): Promise<any> {
  if (res.status === 204) return null;
  const ct = res.headers.get('content-type') || '';
  const text = await res.text();

  if (!res.ok) {
    const snippet = text?.slice(0, 300);
    throw new Error(`${res.status} ${res.statusText} :: ${snippet}`);
  }
  if (ct.includes('application/json')) {
    if (!text) return null;
    try { return JSON.parse(text); }
    catch (e) { throw new Error(`JSON parse fail: ${(e as Error).message} :: body="${text.slice(0,200)}"`); }
  }
  return { raw: text };
}
