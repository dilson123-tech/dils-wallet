export function decodeJwt<T=any>(token: string): T | null {
  try {
    const payload = token.split(".")[1];
    const json = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    // decodeURIComponent/escape lida com UTF-8
    return JSON.parse(decodeURIComponent(escape(json)));
  } catch { return null; }
}
