export type AureaIaNivel = "ok" | "atencao" | "critico";

export interface AureaIaHeadlinePanel {
  nivel: AureaIaNivel;
  headline: string;
  subheadline: string;
  resumo: string;
  destaques: string[];
  recomendacao: string;
}
