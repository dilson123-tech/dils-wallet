const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";
const USER_EMAIL = import.meta.env.VITE_USER_EMAIL || "";

export type PagamentosAIResponse = {
  reply: string;
  tema?: string;
};

/**
 * Chama a IA 3.0 de Pagamentos (LAB).
 */
export async function fetchPagamentosAI(message: string): Promise<PagamentosAIResponse> {
  const res = await fetch(`${API_BASE}/api/v1/ai/pagamentos_lab`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-User-Email": USER_EMAIL,
    },
    body: JSON.stringify({ message }),
  });

  if (!res.ok) {
    throw new Error(`Erro ao chamar IA de Pagamentos (HTTP ${res.status})`);
  }

  return (await res.json()) as PagamentosAIResponse;
}
