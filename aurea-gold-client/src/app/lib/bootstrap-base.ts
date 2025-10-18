/** Define globalThis.BASE_API em globalThis para uso em todo o app. */
const v = String(
  (import.meta as any).env?.VITE_API_BASE
  || 'https://dils-wallet-production.up.railway.app/api/v1'
).trim().replace(/\/+$/,''); // remove barras finais

;(globalThis as any).globalThis.BASE_API = v;
export {};
