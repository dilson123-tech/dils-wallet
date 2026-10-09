import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// P1: renovação automática do access token em 401 (authFetch e lib/api).
// fetch e localStorage são simulados; nenhum token real é usado.

const API = "http://api.test";
const REFRESH_URL = `${API}/api/v1/auth/refresh`;

function fakeJwt(label: string): string {
  const b64 = (o: object) =>
    btoa(JSON.stringify(o)).replace(/=+$/, "").replace(/\+/g, "-").replace(/\//g, "_");
  const exp = Math.floor(Date.now() / 1000) + 3600;
  return `${b64({ alg: "HS256", typ: "JWT" })}.${b64({ sub: label, exp })}.sig-${label}-xxxxxxxxxxxxxxxx`;
}

const OLD_AT = fakeJwt("old-access");
const NEW_AT = fakeJwt("new-access");
const OLD_RT = "opaque-refresh-old";
const NEW_RT = "opaque-refresh-new";

class MemoryStorage {
  private m = new Map<string, string>();
  getItem(k: string) { return this.m.has(k) ? (this.m.get(k) as string) : null; }
  setItem(k: string, v: string) { this.m.set(k, String(v)); }
  removeItem(k: string) { this.m.delete(k); }
  clear() { this.m.clear(); }
}

let storage: MemoryStorage;
let fetchMock: ReturnType<typeof vi.fn>;

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function urlOf(input: unknown): string {
  return typeof input === "string" ? input : input instanceof URL ? input.href : (input as Request).url;
}

function authOf(init?: RequestInit): string | null {
  return new Headers(init?.headers || {}).get("Authorization");
}

// Backend simulado: rotas protegidas aceitam só NEW_AT; refresh aceita só OLD_RT.
function backend(opts: { refresh?: () => Response | Promise<Response>; protectedOk?: (auth: string | null) => boolean } = {}) {
  const protectedOk = opts.protectedOk ?? ((auth) => auth === `Bearer ${NEW_AT}`);
  return async (input: unknown, init?: RequestInit) => {
    const url = urlOf(input);
    if (url === REFRESH_URL) {
      if (opts.refresh) return opts.refresh();
      const body = JSON.parse(String(init?.body || "{}"));
      if (body.refresh_token !== OLD_RT) return json(401, { detail: "invalid" });
      return json(200, { access_token: NEW_AT, refresh_token: NEW_RT, token_type: "bearer" });
    }
    if (url.includes("/api/v1/public/")) return json(401, { detail: "public 401" });
    return protectedOk(authOf(init)) ? json(200, { ok: true }) : json(401, { detail: "expired" });
  };
}

function refreshCalls() {
  return fetchMock.mock.calls.filter(([input]) => urlOf(input) === REFRESH_URL);
}

function protectedCalls() {
  return fetchMock.mock.calls.filter(([input]) => urlOf(input) !== REFRESH_URL);
}

function login(at = OLD_AT, rt: string | null = OLD_RT) {
  for (const k of ["aurea.access_token", "aurea_access_token", "aurea.jwt", "aurea_jwt"]) storage.setItem(k, at);
  if (rt) for (const k of ["aurea.refresh_token", "aurea_refresh_token"]) storage.setItem(k, rt);
}

function sessionCleared() {
  return ["aurea.access_token", "aurea_access_token", "aurea.jwt", "aurea_jwt", "aurea.refresh_token", "aurea_refresh_token"]
    .every((k) => storage.getItem(k) === null);
}

async function loadModules() {
  vi.resetModules();
  const authClient = await import("./authClient");
  const api = await import("../lib/api");
  return { authFetch: authClient.authFetch, apiGet: api.apiGet, apiPost: api.apiPost };
}

beforeEach(() => {
  storage = new MemoryStorage();
  fetchMock = vi.fn();
  vi.stubEnv("VITE_API_BASE", API);
  vi.stubEnv("VITE_USER_EMAIL", "");
  vi.stubEnv("VITE_DEV_TOKEN", "");
  vi.stubEnv("VITE_DEV_REFRESH_TOKEN", "");
  vi.stubGlobal("localStorage", storage);
  vi.stubGlobal("window", { location: { search: "", pathname: "/", hash: "", hostname: "localhost" }, history: { replaceState() {} } });
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe.each(["authFetch", "apiGet", "apiPost"] as const)("refresh automático via %s", (via) => {
  async function call(path = "/api/v1/pix/balance") {
    const m = await loadModules();
    if (via === "authFetch") {
      const r = await m.authFetch(`${API}${path}`, { method: "GET" });
      return { status: r.status };
    }
    try {
      if (via === "apiGet") await m.apiGet(path);
      else await m.apiPost(path, { a: 1 });
      return { status: 200 };
    } catch (e: any) {
      return { status: e?.status as number };
    }
  }

  it("1) 401 → refresh → retry → sucesso", async () => {
    login();
    fetchMock.mockImplementation(backend());

    const r = await call();

    expect(r.status).toBe(200);
    expect(refreshCalls()).toHaveLength(1);
    expect(protectedCalls()).toHaveLength(2);
    expect(storage.getItem("aurea.access_token")).toBe(NEW_AT);
    expect(storage.getItem("aurea.refresh_token")).toBe(NEW_RT);
  });

  it("2) vários 401 simultâneos → um único refresh", async () => {
    login();
    let release!: () => void;
    const gate = new Promise<void>((res) => { release = res; });
    fetchMock.mockImplementation(backend({
      refresh: async () => {
        await gate;
        return json(200, { access_token: NEW_AT, refresh_token: NEW_RT, token_type: "bearer" });
      },
    }));

    const m = await loadModules();
    const one = () =>
      via === "authFetch"
        ? m.authFetch(`${API}/api/v1/pix/balance`).then((r) => r.status)
        : via === "apiGet"
          ? m.apiGet("/api/v1/pix/balance").then(() => 200)
          : m.apiPost("/api/v1/pix/balance", {}).then(() => 200);
    const all = Promise.all([one(), one(), one(), one()]);
    await vi.waitFor(() => expect(refreshCalls()).toHaveLength(1));
    release();

    expect(await all).toEqual([200, 200, 200, 200]);
    expect(refreshCalls()).toHaveLength(1);
    // 4 tentativas originais + 4 retries
    expect(protectedCalls()).toHaveLength(8);
  });

  it("3) refresh falha → sessão limpa", async () => {
    login();
    fetchMock.mockImplementation(backend({ refresh: () => json(401, { detail: "invalid" }) }));

    const r = await call();

    expect(r.status).toBe(401);
    expect(refreshCalls()).toHaveLength(1);
    expect(protectedCalls()).toHaveLength(1);
    expect(sessionCleared()).toBe(true);
  });

  it("4) 401 também no retry → sem loop", async () => {
    login();
    fetchMock.mockImplementation(backend({ protectedOk: () => false }));

    const r = await call();

    expect(r.status).toBe(401);
    expect(refreshCalls()).toHaveLength(1);
    expect(protectedCalls()).toHaveLength(2);
  });

  it("5) request público (sem token) não dispara refresh", async () => {
    storage.setItem("aurea.refresh_token", OLD_RT);
    fetchMock.mockImplementation(backend());

    const r = await call("/api/v1/public/ping");

    expect(r.status).toBe(401);
    expect(refreshCalls()).toHaveLength(0);
    expect(protectedCalls()).toHaveLength(1);
    expect(authOf(protectedCalls()[0][1])).toBeNull();
  });

  it("5b) 401 em rota /api/v1/auth/ não dispara refresh", async () => {
    login();
    fetchMock.mockImplementation(backend({ protectedOk: () => false }));

    await call("/api/v1/auth/me");

    expect(refreshCalls()).toHaveLength(0);
  });

  it("6) o retry usa o access token novo", async () => {
    login();
    fetchMock.mockImplementation(backend());

    await call();

    const [first, retry] = protectedCalls();
    expect(authOf(first[1])).toBe(`Bearer ${OLD_AT}`);
    expect(authOf(retry[1])).toBe(`Bearer ${NEW_AT}`);
  });

  it("7) refresh token nunca é enviado como Bearer", async () => {
    login();
    fetchMock.mockImplementation(backend());

    await call();

    for (const [, init] of fetchMock.mock.calls) {
      const auth = authOf(init) || "";
      expect(auth).not.toContain(OLD_RT);
      expect(auth).not.toContain(NEW_RT);
    }
    const [[, refreshInit]] = refreshCalls();
    expect(authOf(refreshInit)).toBeNull();
    expect(JSON.parse(String(refreshInit.body))).toEqual({ refresh_token: OLD_RT });
  });

  it("429 no refresh → não limpa a sessão e não faz retry", async () => {
    login();
    fetchMock.mockImplementation(backend({ refresh: () => json(429, { detail: "rate" }) }));

    const r = await call();

    expect(r.status).toBe(401);
    expect(protectedCalls()).toHaveLength(1);
    expect(storage.getItem("aurea.access_token")).toBe(OLD_AT);
    expect(storage.getItem("aurea.refresh_token")).toBe(OLD_RT);
  });

  it("401 + Retry-After no refresh (rotação concorrente) → não limpa a sessão", async () => {
    login();
    fetchMock.mockImplementation(backend({
      refresh: () => new Response(JSON.stringify({ detail: "Refresh token inválido/expirado" }), {
        status: 401,
        headers: { "Content-Type": "application/json", "Retry-After": "1" },
      }),
    }));

    const r = await call();

    expect(r.status).toBe(401);
    expect(protectedCalls()).toHaveLength(1);
    expect(sessionCleared()).toBe(false);
    expect(storage.getItem("aurea.access_token")).toBe(OLD_AT);
    expect(storage.getItem("aurea.refresh_token")).toBe(OLD_RT);
  });

  it("401 + Retry-After e outra aba já rotacionou → usa os tokens novos", async () => {
    login();
    fetchMock.mockImplementation(backend({
      refresh: () => {
        // outra aba venceu a rotação e gravou os tokens novos no storage
        login(NEW_AT, NEW_RT);
        return new Response(null, { status: 401, headers: { "Retry-After": "1" } });
      },
    }));

    const r = await call();

    expect(r.status).toBe(200);
    expect(refreshCalls()).toHaveLength(1);
    expect(protectedCalls()).toHaveLength(2);
    expect(authOf(protectedCalls()[1][1])).toBe(`Bearer ${NEW_AT}`);
    expect(storage.getItem("aurea.refresh_token")).toBe(NEW_RT);
  });

  it("sem refresh token salvo → limpa sessão sem chamar /auth/refresh", async () => {
    login(OLD_AT, null);
    fetchMock.mockImplementation(backend());

    const r = await call();

    expect(r.status).toBe(401);
    expect(refreshCalls()).toHaveLength(0);
    expect(sessionCleared()).toBe(true);
  });
});

describe("logs", () => {
  it("nenhum token aparece em console durante refresh bem ou mal sucedido", async () => {
    const spies = (["log", "info", "warn", "error", "debug"] as const).map((k) =>
      vi.spyOn(console, k).mockImplementation(() => {}),
    );
    try {
      login();
      fetchMock.mockImplementation(backend());
      const m = await loadModules();
      await m.authFetch(`${API}/api/v1/pix/balance`);

      login();
      fetchMock.mockImplementation(backend({ refresh: () => { throw new Error("network"); } }));
      await (await loadModules()).authFetch(`${API}/api/v1/pix/balance`);
      expect(sessionCleared()).toBe(true);

      const printed = spies.flatMap((s) => s.mock.calls.flat().map(String)).join("\n");
      for (const t of [OLD_AT, NEW_AT, OLD_RT, NEW_RT]) expect(printed).not.toContain(t);
    } finally {
      spies.forEach((s) => s.mockRestore());
    }
  });
});
