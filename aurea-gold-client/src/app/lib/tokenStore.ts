const OFFICIAL = "aurea.access_token";

export function getAccessToken(): string {
  try { return String(localStorage.getItem(OFFICIAL) ?? ""); } catch { return ""; }
}

export function setAccessToken(t: string): void {
  try { localStorage.setItem(OFFICIAL, String(t ?? "")); } catch {}
}

export function clearAccessToken(): void {
  try { localStorage.removeItem(OFFICIAL); } catch {}
}

// compat: tinha import com nome alternativo no SuperAureaHome
export const clearAccessToken2 = clearAccessToken;
