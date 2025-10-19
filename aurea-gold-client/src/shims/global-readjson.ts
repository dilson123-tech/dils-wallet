import { readJsonSafe } from "@/app/lib/api";
// @ts-ignore - expõe no window para testes no console, se quiser
if (typeof window !== "undefined") (window as any).readJson = readJsonSafe;
