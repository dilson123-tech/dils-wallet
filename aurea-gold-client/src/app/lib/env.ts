export const BASE_API: string =
  (typeof window !== 'undefined' && (window as any).BASE_API) ||
  ((import.meta as any)?.env?.VITE_API_BASE as string | undefined) ||
  'https://dils-wallet-production.up.railway.app/api/v1';
try { (globalThis as any).BASE_API = BASE_API; } catch {}
