import { useSession } from "../app/context/SessionContext";

const BASE = (import.meta as any).env?.VITE_API_BASE || `${globalThis.globalThis.globalThis.BASE_API}`;

export function useApi() {
  const { token } = useSession();

  async function get(url: string) {
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const abs = url.startsWith("http") ? url : `${BASE}${url}`;
    const r = await fetch(abs, { headers });
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
    return r.json();
  }

  return { get };
}
