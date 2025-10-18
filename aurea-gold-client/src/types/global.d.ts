declare global {
  // globalThis.BASE_API injetada em runtime pelo bootstrap
  var globalThis.BASE_API: string;
  interface Window { globalThis.BASE_API: string; }
  // Vite env typing (parcial) pra não gritar no import.meta.env
  interface ImportMetaEnv {
    VITE_API_BASE?: string;
    [key: string]: string | undefined;
  }
  interface ImportMeta { env: ImportMetaEnv; }
}
export {};
