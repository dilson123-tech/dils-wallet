import axios from "axios";

const BASE_API = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export const api = axios.create({
  baseURL: BASE_API,
  headers: { "Content-Type": "application/json" }
});

// injeta o token (se existir) em todas as requisições
api.interceptors.request.use((cfg) => {
  const token = localStorage.getItem("token");
  if (token) {
    cfg.headers = cfg.headers ?? {};
    (cfg.headers as any).Authorization = `Bearer ${token}`;
  }
  return cfg;
});

export default api;
