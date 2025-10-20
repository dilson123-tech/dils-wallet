import { BASE_API } from "./env";

if (typeof globalThis !== "undefined") {
  // Normaliza valor e corrige barra inicial indevida
  const cleanBase = (BASE_API ?? "")
    .replace(/^\/+/, "")
    .replace(/\/+$/, "");
  (globalThis as any).BASE_API = cleanBase;
  console.log("[BOOTSTRAP] BASE_API set to:", cleanBase);
}
