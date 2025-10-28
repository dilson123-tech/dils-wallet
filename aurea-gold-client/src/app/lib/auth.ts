import { apiPost } from "./api";

export interface PromiseLogin {
  ok: boolean;
  token?: string;
  raw?: string;
}

export async function login(username: string, password: string): Promise<PromiseLogin> {
  // chama FastAPI em /api/v1/auth/login
  const data = await apiPost("/api/v1/auth/login", {
    username,
    password,
  });

  // tentamos pegar o token que vier
  const token =
    data?.access_token ??
    data?.token ??
    data?.jwt ??
    "";

  return {
    ok: true,
    token,
    raw: JSON.stringify(data),
  };
}
