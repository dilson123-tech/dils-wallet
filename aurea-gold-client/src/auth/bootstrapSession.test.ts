import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// F10: na abertura do app, AT ausente/expirado tenta o refresh existente
// (single-flight) antes de mandar para o login. fetch e localStorage são
// simulados.

const API = "http://api.test";
const REFRESH_URL = `${API}/api/v1/auth/refresh`;
const RT = "opaque-refresh-boot";
const RT_NEW = "opaque-refresh-boot-rotated";

const AT_KEYS = ["aurea.access_token", "aurea_access_token", "aurea.jwt", "aurea_jwt"];
const RT_KEYS = ["aurea.refresh_token", "aurea_refresh_token"];
const KEYS = [...AT_KEYS, ...RT_KEYS];

class MemoryStorage {
  private m = new Map<string, string>();
  getItem(k: string) { return this.m.has(k) ? (this.m.get(k) as string) : null; }
  setItem(k: string, v: string) { this.m.set(k, String(v)); }
  removeItem(k: string) { this.m.delete(k); }
  clear() { this.m.clear(); }
}

function b64url(s: string) {
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function jwt(expOffsetSec: number, tag = "sig") {
  const exp = Math.floor(Date.now() / 1000) + expOffsetSec;
  return `${b64url('{"alg":"HS256"}')}.${b64url(JSON.stringify({ sub: "1", exp }))}.${tag}`;
}

const AT_VALID = jwt(1800, "valid");
const AT_EXPIRED = jwt(-60, "expired");
const AT_NEW = jwt(1800, "rotated");

let storage: MemoryStorage;
let fetchMock: ReturnType<typeof vi.fn>;

function seed(at: string | null, rt: string | null) {
  if (at) for (const k of AT_KEYS) storage.setItem(k, at);
  if (rt) for (const k of RT_KEYS) storage.setItem(k, rt);
}

function okRefresh() {
  return new Response(JSON.stringify({ access_token: AT_NEW, refresh_token: RT_NEW, token_type: "bearer" }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

async function load() {
  vi.resetModules();
  return import("./bootstrapSession");
}

beforeEach(() => {
  storage = new MemoryStorage();
  fetchMock = vi.fn();
  vi.stubEnv("VITE_API_BASE", API);
  vi.stubEnv("VITE_DEV_TOKEN", "");
  vi.stubEnv("VITE_DEV_REFRESH_TOKEN", "");
  vi.stubGlobal("localStorage", storage);
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
  vi.restoreAllMocks();
});

describe("bootstrapSession", () => {
  it("AT válido → autenticado sem refresh", async () => {
    seed(AT_VALID, RT);
    const { bootstrapSession } = await load();

    await expect(bootstrapSession()).resolves.toBe("authenticated");

    expect(fetchMock).not.toHaveBeenCalled();
    expect(storage.getItem("aurea.access_token")).toBe(AT_VALID);
  });

  it("AT expirado + RT válido → 1 refresh, tokens rotacionados, autenticado", async () => {
    seed(AT_EXPIRED, RT);
    fetchMock.mockResolvedValue(okRefresh());
    const { bootstrapSession } = await load();

    await expect(bootstrapSession()).resolves.toBe("authenticated");

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(REFRESH_URL);
    expect(JSON.parse(String(init.body))).toEqual({ refresh_token: RT });
    expect(AT_KEYS.every((k) => storage.getItem(k) === AT_NEW)).toBe(true);
    expect(RT_KEYS.every((k) => storage.getItem(k) === RT_NEW)).toBe(true);
  });

  it("sem AT + RT válido → 1 refresh, autenticado", async () => {
    seed(null, RT);
    fetchMock.mockResolvedValue(okRefresh());
    const { bootstrapSession } = await load();

    await expect(bootstrapSession()).resolves.toBe("authenticated");

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(storage.getItem("aurea.access_token")).toBe(AT_NEW);
  });

  it("AT expirado + RT inválido → 1 refresh, anônimo, tokens limpos", async () => {
    seed(AT_EXPIRED, RT);
    fetchMock.mockResolvedValue(new Response("{}", { status: 401 }));
    const { bootstrapSession } = await load();

    await expect(bootstrapSession()).resolves.toBe("anonymous");

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(KEYS.every((k) => storage.getItem(k) === null)).toBe(true);
  });

  it("sem AT + sem RT → anônimo, nenhuma chamada", async () => {
    const { bootstrapSession } = await load();

    await expect(bootstrapSession()).resolves.toBe("anonymous");

    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("duas inicializações simultâneas (StrictMode) → 1 refresh", async () => {
    seed(AT_EXPIRED, RT);
    fetchMock.mockImplementation(() => Promise.resolve(okRefresh()));
    const { bootstrapSession } = await load();

    const results = await Promise.all([bootstrapSession(), bootstrapSession()]);

    expect(results).toEqual(["authenticated", "authenticated"]);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("429 → transitório, tokens preservados, sem retry automático", async () => {
    vi.useFakeTimers();
    try {
      seed(AT_EXPIRED, RT);
      fetchMock.mockResolvedValue(new Response("{}", { status: 429 }));
      const { bootstrapSession } = await load();

      await expect(bootstrapSession()).resolves.toBe("transient");

      await vi.advanceTimersByTimeAsync(120_000);
      expect(fetchMock).toHaveBeenCalledTimes(1);
      expect(AT_KEYS.every((k) => storage.getItem(k) === AT_EXPIRED)).toBe(true);
      expect(RT_KEYS.every((k) => storage.getItem(k) === RT)).toBe(true);
    } finally {
      vi.useRealTimers();
    }
  });

  it("não escreve tokens nos logs", async () => {
    const spies = (["log", "info", "warn", "error", "debug"] as const).map((m) =>
      vi.spyOn(console, m).mockImplementation(() => {}),
    );
    const { bootstrapSession } = await load();

    seed(AT_EXPIRED, RT);
    fetchMock.mockResolvedValueOnce(okRefresh());
    await bootstrapSession();

    seed(AT_EXPIRED, RT);
    fetchMock.mockResolvedValueOnce(new Response("{}", { status: 429 }));
    await bootstrapSession();

    seed(AT_EXPIRED, RT);
    fetchMock.mockResolvedValueOnce(new Response("{}", { status: 401 }));
    await bootstrapSession();

    const logged = spies.flatMap((s) => s.mock.calls).map((c) => c.map(String).join(" ")).join("\n");
    for (const secret of [RT, RT_NEW, AT_EXPIRED, AT_NEW]) {
      expect(logged).not.toContain(secret);
    }
  });
});

describe("isJwtUsable", () => {
  it.each([
    ["nulo", null, false],
    ["não-JWT", "abc", false],
    ["payload inválido", "a.!!!.c", false],
    ["expirado", AT_EXPIRED, false],
    ["expira em <5s", jwt(3), false],
    ["válido", AT_VALID, true],
  ])("%s", async (_label, token, expected) => {
    const { isJwtUsable } = await load();
    expect(isJwtUsable(token)).toBe(expected);
  });
});
