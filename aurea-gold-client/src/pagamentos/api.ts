export const API_BASE_RESERVAS =
  (import.meta as any).env.VITE_API_BASE || "http://127.0.0.1:8000";

export type PainelReservasPeriodo = "hoje" | "7d" | "30d";

export interface PainelReservasReceitaDTO {
  id: number;
  origem: string;
  valor: number;
  data: string;
  status: "confirmada" | "pendente";
}

export interface PainelReservasReservaDTO {
  id: number;
  cliente: string;
  recurso: string;
  data: string;
  horario: string;
  status: "ativa" | "cancelada" | "concluída";
}

export interface PainelReservasTotaisDTO {
  receitas_confirmadas: number;
  reservas_periodo: number;
}

export interface PainelReservasResponseDTO {
  periodo: PainelReservasPeriodo;
  label_periodo: string;
  receitas: PainelReservasReceitaDTO[];
  reservas: PainelReservasReservaDTO[];
  totais: PainelReservasTotaisDTO;
}

/**
 * Endpoint oficial do painel de reservas:
 * GET /api/v1/reservas/painel?periodo=hoje|7d|30d
 */
export async function fetchPainelReservasLab(
  periodo: PainelReservasPeriodo
): Promise<PainelReservasResponseDTO> {
  const url = `${API_BASE_RESERVAS}/api/v1/reservas/painel?periodo=${encodeURIComponent(
    periodo
  )}`;

  const resp = await fetch(url);
  if (!resp.ok) {
    throw new Error(`Erro ao carregar painel reservas: ${resp.status}`);
  }
  return (await resp.json()) as PainelReservasResponseDTO;
}

/**
 * Compatibilidade com o nome antigo usado pelo painel de pagamentos.
 */
export type PagamentosAIResponseDTO = PainelReservasResponseDTO;

export async function fetchPagamentosAI(
  periodo: PainelReservasPeriodo = "hoje"
): Promise<PagamentosAIResponseDTO> {
  return fetchPainelReservasLab(periodo);
}
