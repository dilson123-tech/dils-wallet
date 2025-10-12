import { useSession } from "../app/context/SessionContext";

export function useApi() {
  const { token } = useSession();

  async function get(url: string) {
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const r = await fetch(url, { headers });
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
    return r.json();
  }

  return { get };
}
