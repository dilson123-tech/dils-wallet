// Intent Manager do envio de PIX real (M1 — correção do BUG REAL DE RETRY).
//
// Sem isso, cada tentativa de envio (inclusive um retry manual após
// timeout/erro de rede) gerava uma Idempotency-Key nova, fazendo o
// backend tratar a mesma intenção financeira como uma operação
// independente — com risco real de dupla operação quando o backend já
// tinha comitado a tentativa anterior e a resposta simplesmente se
// perdeu no caminho de volta ao cliente.
//
// Módulo puro, sem React. UMA instância compartilhada (module-scope
// singleton) é exportada abaixo e deve ser importada — nunca
// reinstanciada — por qualquer componente que envie PIX real, para que
// duas UIs diferentes da mesma sessão (ex.: AureaPixPanel e
// SuperAureaHome) reconheçam a mesma intenção ainda pendente em vez de
// gerarem chaves independentes para o mesmo pagamento.
//
// Isolamento por usuário: cada intenção é indexada por `ownerId` (o
// `sub` do JWT do usuário autenticado, decodificado localmente pelo
// próprio componente chamador — este módulo nunca lê token nem decide
// o que é um ownerId válido). Isso garante, por construção, que a
// intenção pendente de um usuário nunca seja reaproveitada por outro,
// mesmo que a troca de sessão ocorra sem reload de página — sem
// precisar de nenhum reset explícito amarrado a logout/login.
//
// Este módulo NUNCA limpa uma intenção sozinho em caso de falha (4xx,
// 5xx, erro de rede, o que for) — a mesma key deve continuar
// disponível para retry, porque o backend já resolve corretamente os
// dois casos possíveis (replay se já comitou, nova tentativa se não
// comitou, conflito fail-closed se o payload realmente mudou sem
// avisar). A intenção só é encerrada por:
//   - complete(): sucesso HTTP 2xx confirmado;
//   - beginNewIntent(): substituição deliberada, chamada pelo
//     componente somente depois de confirmação explícita do usuário.

export interface PixIntentPayload {
  dest: string;
  valor: number;
  descricao: string | null;
}

export type PixIntentResult =
  | { status: "created"; key: string }
  | { status: "reused"; key: string }
  | { status: "pending_conflict" };

interface PendingIntent {
  key: string;
  fingerprint: string;
}

function generateIdempotencyKey(): string {
  if (
    typeof crypto !== "undefined" &&
    "randomUUID" in crypto &&
    typeof crypto.randomUUID === "function"
  ) {
    return crypto.randomUUID();
  }
  return `pix-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

// Representação inequívoca e determinística da intenção financeira.
// Mesmo shape (array de 3 posições, mesma ordem/tipos) usado por todo
// consumidor deste manager, para que a mesma intenção real produza
// sempre o mesmo fingerprint independente de qual UI a originou.
function fingerprintOf(payload: PixIntentPayload): string {
  return JSON.stringify([payload.dest, payload.valor, payload.descricao]);
}

class PixIntentManager {
  private intents = new Map<string, PendingIntent>();

  keyFor(ownerId: string, payload: PixIntentPayload): PixIntentResult {
    const fingerprint = fingerprintOf(payload);
    const current = this.intents.get(ownerId);

    if (!current) {
      const key = generateIdempotencyKey();
      this.intents.set(ownerId, { key, fingerprint });
      return { status: "created", key };
    }

    if (current.fingerprint === fingerprint) {
      return { status: "reused", key: current.key };
    }

    // Fail-closed: payload diferente com intenção pendente NUNCA gera
    // K2 silenciosamente aqui. O caller precisa chamar beginNewIntent()
    // explicitamente, depois de confirmar com o usuário.
    return { status: "pending_conflict" };
  }

  beginNewIntent(ownerId: string, payload: PixIntentPayload): string {
    const key = generateIdempotencyKey();
    this.intents.set(ownerId, { key, fingerprint: fingerprintOf(payload) });
    return key;
  }

  // Só limpa se a key corrente daquele owner ainda for exatamente a
  // esperada — protege contra uma resposta atrasada de uma key antiga
  // apagar uma intenção mais nova já iniciada (respostas fora de ordem).
  complete(ownerId: string, expectedKey: string): void {
    const current = this.intents.get(ownerId);
    if (current && current.key === expectedKey) {
      this.intents.delete(ownerId);
    }
  }
}

export const pixIntentManager = new PixIntentManager();
