import { create } from "zustand";
import { API } from "../lib/api";

type User = { id:number; email:string; role:string };

type AuthState = {
  token: string | null;
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  fetchMe: () => Promise<void>;
};

export const useAuth = create<AuthState>((set, get) => ({
  token: localStorage.getItem("token"),
  user: null,
  async login(email, password) {
    const body = new URLSearchParams({ username: email, password });
    const res = await fetch(`${API}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    const json = await res.json();
    if (!res.ok || !json?.access_token) throw new Error("Login inválido");
    localStorage.setItem("token", json.access_token);
    set({ token: json.access_token });
    await get().fetchMe();
  },
  logout() { localStorage.removeItem("token"); set({ token: null, user: null }); },
  async fetchMe() {
    const res = await fetch(`${API}/api/v1/admin/me`, {
      headers: { Authorization: `Bearer ${get().token}` || "" },
    });
    if (!res.ok) throw new Error("Falha em /me");
    set({ user: await res.json() });
  },
}));
