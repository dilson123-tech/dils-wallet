export const API_BASE =
  (import.meta as any).env.VITE_API_BASE || "http://127.0.0.1:8080";

export type PainelReservasPeriodo = "hoje" | "7d" | "30d";

export interface PainelReceitaDTO {
  id: number;
  origem: string;
  valor: number;
  data: string;
  status: string;
}

export interface PainelReservaDTO {
  id: number;
  cliente: string;
  recurso: string;
  data: string;
  horario: string;
  status: string;
}

export interface PainelReservasTotaisDTO {
  receitas_confirmadas: number;
  reservas_periodo: number;
}

export interface PainelReservasResponseDTO {
  periodo: string;
  label_periodo: string;
  receitas: PainelReceitaDTO[];
  reservas: PainelReservaDTO[];
  totais: PainelReservasTotaisDTO;
}

// Endpoint oficial do painel de reservas
// GET /api/v1/reservas/painel?periodo=7d
export async function fetchPainelReservas(
  periodo: PainelReservasPeriodo = "7d"
): Promise<PainelReservasResponseDTO> {
  const url = `${API_BASE}/api/v1/reservas/painel?periodo=${periodo}`;
  const res = await fetch(url);

  if (!res.ok) {
    throw new Error(
      `Erro ao carregar painel reservas: ${res.status} ${res.statusText}`
    );
  }

  const data = (await res.json()) as PainelReservasResponseDTO;
  return data;
}

export const fetchPainelReservasLab = fetchPainelReservas;
