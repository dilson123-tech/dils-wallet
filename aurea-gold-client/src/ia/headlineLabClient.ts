import { API_BASE, USER_EMAIL } from "../super2/api";

// IA 3.0 – Cliente HEADLINE LAB
// Endpoint: POST POST ${API_BASE}/api/v1/ai/headline-lab

export type IAHeadlineNivel = "ok" | "atencao" | "critico";

export interface IAHeadlineResponse {
  nivel: IAHeadlineNivel;
  headline: string;
  subheadline: string;
  resumo: string;
  destaques: string[];
  recomendacao: string;
}


export async function fetchHeadlineLab(
  message: string,
  userEmail: string = USER_EMAIL
): Promise<IAHeadlineResponse> {
  const resp = await fetch(`${API_BASE}/api/v1/ai/headline-lab`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-User-Email": userEmail,
    },
    body: JSON.stringify({ message }),
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(
      `Erro ao chamar HEADLINE LAB: ${resp.status} ${resp.statusText} – ${text}`
    );
  }

  const data = (await resp.json()) as IAHeadlineResponse;
  return data;
}
