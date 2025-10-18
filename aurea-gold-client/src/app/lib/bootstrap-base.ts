/**
 * Define uma globalThis.BASE_API global e bem formatada.
 * Use sempre:  globalThis.globalThis.BASE_API
 */
const v = String(
  // Vite: defina VITE_API_BASE="https://.../api/v1" no .env.prod/local
  (import.meta as any).env?.VITE_API_BASE
  || 'https://dils-wallet-production.up.railway.app/api/v1'
).trim().replace(/\/+$/,'');     // remove barras finais duplicadas

;(globalThis as any).globalThis.BASE_API = v;
export {}; // módulo vazio só para side-effect
