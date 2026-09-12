// Coordenador do protocolo server-side de intent de envio PIX real (M2).
//
// A autoridade da Idempotency-Key financeira do PIX NÃO vive mais aqui —
// vive inteiramente no backend, na tabela `pix_send_intents`
// (backend/app/services/pix_send_intent_service.py). Este módulo é só um
// cliente fino desse protocolo: nunca gera UUID/hash localmente, nunca
// guarda a send_key como fonte de verdade, e nunca decide sozinho se uma
// nova geração (K2) pode existir — isso é sempre resposta do backend.
//
// Histórico: a versão anterior deste módulo mantinha um Map em memória
// (module-scope singleton) como autoridade local da chave, o que não
// sobrevivia a reload/fechar app/outra aba/outro dispositivo — o gap
// exato investigado e corrigido nesta mesma branch (ver
// docs/archive ou o histórico de commits de
// fix/pix-retry-intent-persistence). Nenhum Map equivalente existe mais
// aqui: cada chamada consulta o backend diretamente.
//
// Reutiliza a infraestrutura HTTP/auth já existente (`withAuth` + fetch,
// o mesmo mecanismo já usado por AureaPixPanel.tsx para o próprio
// POST /api/v1/pix/send) — nenhum segundo cliente HTTP é criado.

import { API_BASE } from "./apiBase";
import { withAuth } from "./api";

export interface PixIntentPayload {
  dest: string;
  valor: number;
  descricao: string | null;
}

export interface PixIntentReservation {
  state: "pending" | "acknowledged";
  sendKey: string | null;
  generation: number;
  reused: boolean;
  canSend: boolean;
  requiresExplicitNew: boolean;
  forceNewRejected: boolean;
}

export interface PixIntentAckResult {
  state: "pending" | "acknowledged";
  generation: number;
  reused: boolean;
}

export class PixSendIntentError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "PixSendIntentError";
    this.status = status;
  }
}

async function postIntentEndpoint(
  path: string,
  body: unknown
): Promise<{ status: number; body: any }> {
  let resp: Response;
  try {
    resp = await fetch(
      `${API_BASE}${path}`,
      withAuth({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })
    );
  } catch (err) {
    throw new PixSendIntentError("pix_intent_network_error");
  }

  const parsed = await resp.json().catch(() => null);
  return { status: resp.status, body: parsed };
}

function toReservation(body: any): PixIntentReservation {
  return {
    state: body?.state,
    sendKey: body?.send_key ?? null,
    generation: body?.generation,
    reused: !!body?.reused,
    canSend: !!body?.can_send,
    requiresExplicitNew: !!body?.requires_explicit_new,
    forceNewRejected: !!body?.force_new_rejected,
  };
}

async function reserve(
  payload: PixIntentPayload,
  forceNew: boolean
): Promise<PixIntentReservation> {
  const { status, body } = await postIntentEndpoint("/api/v1/pix/send/intent", {
    chave_pix: payload.dest,
    valor: payload.valor,
    descricao: payload.descricao,
    force_new: forceNew,
  });

  // 200 (reserva/reuso normal) e 409 com force_new_rejected=true são
  // ambas respostas VÁLIDAS do protocolo — nunca um erro de transporte.
  // Um 409 com esse campo significa "fail-closed: existe intent pending,
  // nunca gerar K2" e deve ser devolvido ao caller como está, não tratado
  // como falha de rede.
  if (body == null || (status >= 400 && !body.force_new_rejected)) {
    throw new PixSendIntentError("pix_intent_reserve_failed", status);
  }

  return toReservation(body);
}

/**
 * Reserva ou recupera a intent atual (force_new=false). Primeira chamada
 * para (usuário, payload) cria uma send_key nova no backend; chamadas
 * seguintes para a MESMA combinação recuperam exatamente a mesma
 * send_key (reload, retry, outra aba, outro dispositivo) — nunca uma
 * nova key gerada localmente.
 */
export function reserveIntent(
  payload: PixIntentPayload
): Promise<PixIntentReservation> {
  return reserve(payload, false);
}

/**
 * Só deve ser chamada depois de confirmação humana explícita, e só faz
 * sentido quando a reserva normal já devolveu state="acknowledged". O
 * backend é quem decide se uma nova geração (K2) pode de fato existir —
 * se a intent anterior ainda estiver pending, o backend recusa
 * (force_new_rejected=true) e esta função devolve essa recusa ao caller
 * sem nunca inventar uma K2 localmente.
 */
export function reserveNewIntent(
  payload: PixIntentPayload
): Promise<PixIntentReservation> {
  return reserve(payload, true);
}

/**
 * Confirma no backend que a send_key foi genuinamente processada com
 * sucesso. O backend é quem verifica owner, conclusão real do PIX e
 * correspondência de fingerprint — este módulo nunca simula essa
 * verificação. Uma falha aqui NUNCA significa que o PIX falhou: se
 * POST /pix/send já retornou 2xx, o dinheiro já pode ter sido
 * processado — o chamador não deve tratar uma falha de ack como falha
 * financeira, nem gerar uma nova intent/key para "tentar de novo".
 */
export async function acknowledgeIntent(
  sendKey: string
): Promise<PixIntentAckResult> {
  const { status, body } = await postIntentEndpoint(
    "/api/v1/pix/send/intent/ack",
    { send_key: sendKey }
  );

  if (body == null || status >= 400) {
    throw new PixSendIntentError("pix_intent_ack_failed", status);
  }

  return {
    state: body.state,
    generation: body.generation,
    reused: !!body.reused,
  };
}

// Objeto agrupador — só por conveniência de import (`pixIntentManager.x`),
// mantendo o padrão de chamada já usado nos dois componentes. Não guarda
// nenhum estado: cada método é uma chamada de rede independente.
export const pixIntentManager = {
  reserveIntent,
  reserveNewIntent,
  acknowledgeIntent,
};
