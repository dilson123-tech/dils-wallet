import { readJson } from "@/app/lib/http";
// @ts-ignore
if (typeof window !== "undefined") (window as any).readJson = readJson;
export {};
