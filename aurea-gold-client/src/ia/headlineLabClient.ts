// IA 3.0 – Cliente HEADLINE LAB
// Endpoint: POST http://127.0.0.1:8100/api/v1/ai/headline-lab

export type IAHeadlineNivel = "ok" | "atencao" | "critico";

export interface IAHeadlineResponse {
  nivel: IAHeadlineNivel;
  headline: string;
  subheadline: string;
  resumo: string;
  destaques: string[];
  recomendacao: string;
}

const BASE_URL = "http://127.0.0.1:8000"; // backend local padrão

export async function fetchHeadlineLab(
  message: string,
  userEmail: string = "dilsonpereira231@gmail.com"
): Promise<IAHeadlineResponse> {
  const resp = await fetch(`${BASE_URL}/api/v1/ai/headline-lab`, {
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
