// src/app/lib/env.ts
// Resolve BASE_API a partir de window.BASE_API, VITE_API_BASE ou fallback.
export const BASE_API: string =
  (typeof window !== 'undefined' && (window as any).BASE_API) ||
  // Vite injeta import.meta.env.* nos módulos JS/TS
  ((import.meta as any)?.env?.VITE_API_BASE as string | undefined) ||
  'https://dils-wallet-production.up.railway.app/api/v1';

// Expõe também no global para compat com código legado
try { (globalThis as any).BASE_API = BASE_API; } catch {}
