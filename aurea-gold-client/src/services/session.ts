import { getToken } from "./auth";

export function restoreSession() {
  const token = getToken();
  if (!token) return null;

  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    const exp = payload.exp ? payload.exp * 1000 : null;

    if (exp && Date.now() > exp) {
      console.warn("Token expirado");
      localStorage.removeItem("authToken");
      return null;
    }

    return payload;
  } catch {
    console.error("Erro ao decodificar token");
    return null;
  }
}
