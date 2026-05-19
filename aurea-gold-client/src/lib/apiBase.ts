export function resolveApiBase(): string {
  const raw = String(
    (import.meta as any)?.env?.VITE_API_BASE ??
    (import.meta as any)?.env?.VITE_API_BASE_URL ??
    ""
  ).trim().replace(/\/+$|\s+/g, "");

  if (raw) return raw;

  try {
    if (typeof window !== "undefined" && window.location?.hostname) {
      const h = window.location.hostname;
      if (h) {
        return `http://${h}:8090`;
      }
    }
  } catch {}

  return "http://127.0.0.1:8090";
}

export const API_BASE = resolveApiBase();

export type WalletMode = "demo" | "partner";

export function resolveWalletMode(): WalletMode {
  const raw = String(
    (import.meta as any)?.env?.VITE_WALLET_MODE ?? "demo"
  ).trim().toLowerCase();

  return raw === "partner" ? "partner" : "demo";
}

export const WALLET_MODE = resolveWalletMode();
export const IS_DEMO_WALLET = WALLET_MODE === "demo";
export const IS_PARTNER_WALLET = WALLET_MODE === "partner";

