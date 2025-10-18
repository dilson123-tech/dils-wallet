declare global { interface Window { BASE_API?: string } }

const fromEnv = (import.meta as any)?.env?.VITE_API_BASE as string | undefined;
const fallback = 'https://dils-wallet-production.up.railway.app/api/v1';

export const BASE_API: string =
  (typeof window !== 'undefined' && window.BASE_API) ||
  fromEnv ||
  fallback;

// expõe pro legado
;(globalThis as any).BASE_API = BASE_API;
