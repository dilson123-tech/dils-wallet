import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// P1: "Sair" revoga a sessão no servidor (POST /api/v1/auth/logout) antes
// de limpar o localStorage. fetch e localStorage são simulados.

const API = "http://api.test";
const LOGOUT_URL = `${API}/api/v1/auth/logout`;
const AT = "header.payload.sig-access";
const RT = "opaque-refresh-logout";

const KEYS = ["aurea.access_token", "aurea_access_token", "aurea.jwt", "aurea_jwt", "aurea.refresh_token", "aurea_refresh_token"];

class MemoryStorage {
  private m = new Map<string, string>();
  getItem(k: string) { return this.m.has(k) ? (this.m.get(k) as string) : null; }
  setItem(k: string, v: string) { this.m.set(k, String(v)); }
  removeItem(k: string) { this.m.delete(k); }
  clear() { this.m.clear(); }
}

let storage: MemoryStorage;
let fetchMock: ReturnType<typeof vi.fn>;

function login(rt: string | null = RT) {
  for (const k of ["aurea.access_token", "aurea_access_token", "aurea.jwt", "aurea_jwt"]) storage.setItem(k, AT);
  if (rt) for (const k of ["aurea.refresh_token", "aurea_refresh_token"]) storage.setItem(k, rt);
}

// mesma sequência do handleLogout em App.tsx
async function logout() {
  vi.resetModules();
  const { logoutServer, clearTokens } = await import("./authClient");
  const pending = logoutServer();
  clearTokens();
  return pending;
}

beforeEach(() => {
  storage = new MemoryStorage();
  fetchMock = vi.fn();
  vi.stubEnv("VITE_API_BASE", API);
  vi.stubGlobal("localStorage", storage);
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("logout no servidor", () => {
  it("envia o refresh token para /auth/logout e limpa a sessão local", async () => {
    login();
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }));

    await logout();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(LOGOUT_URL);
    expect(init.method).toBe("POST");
    expect(init.keepalive).toBe(true);
    expect(JSON.parse(String(init.body))).toEqual({ refresh_token: RT });
    // refresh token nunca vai como Bearer
    expect(new Headers(init.headers).get("Authorization")).toBeNull();
    expect(KEYS.every((k) => storage.getItem(k) === null)).toBe(true);
  });

  it.each([
    ["rede fora", () => Promise.reject(new TypeError("network"))],
    ["5xx", () => Promise.resolve(new Response("x", { status: 503 }))],
    ["fetch lança síncrono", () => { throw new Error("boom"); }],
  ])("falha do servidor (%s) não impede o logout local", async (_label, impl) => {
    login();
    fetchMock.mockImplementation(impl);

    await expect(logout()).resolves.toBeUndefined();

    expect(KEYS.every((k) => storage.getItem(k) === null)).toBe(true);
  });

  it("sem refresh token salvo → não chama o servidor", async () => {
    login(null);

    await logout();

    expect(fetchMock).not.toHaveBeenCalled();
    expect(KEYS.every((k) => storage.getItem(k) === null)).toBe(true);
  });
});
