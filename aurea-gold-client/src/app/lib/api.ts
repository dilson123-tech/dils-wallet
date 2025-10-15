import { readJson } from "@/app/lib/http";

const BASE_API = String(import.meta.env.VITE_API_BASE); // ex: https://dils-wallet-production.up.railway.app/api/v1

type Opts = { token?: string; body?: any; headers?: Record<string,string> };

function h(token?: string, extra?: Record<string,string>) {
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(extra || {}),
  };
}

async function req(method: "GET"|"POST", path: string, opts: Opts = {}) {
  const res = await fetch(`${BASE_API}${path}`, {
    method,
    headers: h(opts.token, opts.headers),
    body: method === "POST" && opts.body ? JSON.stringify(opts.body) : undefined,
    mode: "cors",
    credentials: "omit",
  });
  return readJson(res);
}

export const apiGet  = (path: string, opts?: Opts) => req("GET",  path, opts);
export const apiPost = (path: string, opts?: Opts) => req("POST", path, opts);
export { BASE_API };
