import axios from "axios";
const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000",
  timeout: 10000,
});
API.interceptors.request.use((cfg) => {
  const t = localStorage.getItem("aurea_token");
  if (t) cfg.headers.Authorization = `Bearer ${t}`;
  return cfg;
});
API.interceptors.response.use(r => r, err => {
  if (err?.response?.status === 401) {
    localStorage.removeItem("aurea_token");
    localStorage.removeItem("aurea_user");
    localStorage.removeItem("aurea_role");
    window.location.href = "/login";
  }
  return Promise.reject(err);
});
export default API;
