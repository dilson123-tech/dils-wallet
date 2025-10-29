const BASE_URL = `${import.meta.env.VITE_API_BASE || "http://localhost:8080"}/api/v1`;

export async function loginRequest(username: string, password: string) {
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({
      username,
      password,
    }),
  });

  if (!res.ok) {
    const txt = await res.text();
    console.error("Erro /auth/login", res.status, txt);
    throw new Error(`login status ${res.status}`);
  }

  const data = await res.json();

  // assumindo { access_token: "...", token_type: "bearer" }
  if (data.access_token) {
    localStorage.setItem("authToken", data.access_token);
  }

  return data;
}

export function getToken() {
  return localStorage.getItem("authToken") || "";
}

export function clearToken() {
  localStorage.removeItem("authToken");
}

export function isLoggedIn() {
  return getToken() !== "";
}
