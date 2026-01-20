import { apiPost, USER_EMAIL } from "@/lib/api";

export type SendReq = { dest?: string; valor?: number; msg?: string };
export type SendRes = any;

export async function sendQuickPix(req: SendReq = {}): Promise<SendRes> {
  const body = {
    dest: req.dest || USER_EMAIL,     // destino padrão: seu próprio e-mail
    valor: req.valor ?? 10,           // R$10 para teste
    msg: req.msg ?? "PIX via Aurea Gold",
  };
  return apiPost("/api/v1/pix/send", body);
}
