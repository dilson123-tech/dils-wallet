import axios from "axios";
export const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";
export const api = axios.create({ baseURL: `${API_BASE}/api/v1`, timeout: 15000 });
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("jwt");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
api.interceptors.response.use((r)=>r,(e)=>{ if(e?.response?.status===401){ console.warn("401"); } return Promise.reject(e);});
