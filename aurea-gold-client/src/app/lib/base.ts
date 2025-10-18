export const globalThis.BASE_API = String(
  import.meta.env.VITE_API_BASE || 'https://dils-wallet-production.up.railway.app/api/v1'
).trim().replace(/\/+$/,'');
