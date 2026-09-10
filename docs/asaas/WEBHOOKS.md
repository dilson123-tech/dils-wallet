# Aurea Gold — Webhooks Asaas Sandbox

Este documento descreve o estado técnico atual do recebimento de webhooks Asaas Sandbox, como implementado em `backend/app/api/v1/routes/wallet.py`. Não é um changelog — para o histórico, veja os documentos históricos listados em [`docs/asaas/README.md`](./README.md). O eventual arquivamento é tratado separadamente no ME1-C, ainda não realizado.

## 1. Propósito

Documentar o recebimento (inbound) de eventos de webhook do Asaas Sandbox, sua autenticação, idempotência, correlação com usuários e auditoria — distinguindo claramente de qualquer capacidade de envio (outbound) ao Asaas, que permanece bloqueada.

## 2. Status executivo atual

A cadeia outbound `/customers` documentada em [`HTTP_CLIENT_CONTRACT.md`](./HTTP_CLIENT_CONTRACT.md) é representacional — não existe transporte HTTP outbound executável em nenhum ponto da integração Asaas, inclusive na preparação local de `/payments` descrita em [`DRY_RUN.md`](./DRY_RUN.md), que também nunca envia HTTP. Já o recebimento de webhook Asaas Sandbox **é um fluxo inbound real, autenticado, idempotente e testado**, com evidência histórica de uma entrega real recebida via túnel público durante desenvolvimento. Isso não implica outbound habilitado, dinheiro real habilitado ou homologação concluída.

## 3. Rotas inbound atuais

| Rota | Papel |
|---|---|
| `POST /api/v1/partners/asaas/webhooks/sandbox` | Rota oficial |
| `POST /api/v1/partners` / `POST /api/v1/partners/` | Aliases — mesma função, paths genéricos herdados de entregas anteriores do painel Asaas Sandbox |
| `GET /api/v1/partners/asaas/webhooks/sandbox/audit-history` | Consulta de auditoria (exige usuário Aurea Gold autenticado) |

As três rotas POST são decorators empilhados sobre uma única função — não são implementações distintas. Os aliases genéricos permanecem por decisão de compatibilidade já registrada (finding A1); não são removidos aqui.

## 4. Autenticação/token

O header `asaas-access-token` é validado contra `ASAAS_WEBHOOK_TOKEN` (fora do Git) usando `hmac.compare_digest`. Ausência retorna 401; valor incorreto retorna 403. O valor do token nunca aparece em resposta, log, exceção ou registro de auditoria.

## 5. Parsing/validação

O corpo deve ser um objeto JSON; caso contrário, 422. Um identificador único do evento (`id`/`eventId`/`event_id`) e um tipo de evento (`event`/`event_type`) são obrigatórios; ausência de qualquer um retorna 422. A configuração Sandbox é validada antes de qualquer processamento (`AsaasConfigError` → 503).

## 6. Eventos reconhecidos

Apenas `PAYMENT_RECEIVED` é tratado como aceito. Qualquer outro tipo de evento é recebido, autenticado, registrado para auditoria e respondido com 200 — mas marcado explicitamente como não aceito (`accepted: false`), sem qualquer efeito adicional.

## 7. Correlação pagamento ↔ usuário

Quando o payload traz `externalReference`, o sistema tenta localizar, na mesma tabela usada pela preparação PIX (`docs/asaas/DRY_RUN.md`), o registro de correlação criado localmente para aquela referência, resolvendo o `user_id` correspondente. Se não houver correlação, o estado é reportado como `"unresolved"` ou `"missing"` — nunca um erro, nunca um efeito colateral.

## 8. Idempotência/replay

Cada evento é indexado por `asaas-sandbox-webhook:` + hash do identificador do evento, na tabela `IdempotencyKey` (namespace próprio, distinto do usado pela correlação de preparação e do webhook interno de simulação). Reenvio do mesmo evento retorna uma resposta de replay sanitizada; o mesmo identificador com conteúdo diferente retorna 409; uma corrida entre requisições concorrentes retorna 503 com `Retry-After`.

## 9. Persistência/auditoria

Nenhum payload bruto, identificador bruto de evento/pagamento ou token é persistido. É armazenado um resumo sanitizado da resposta (incluindo, quando há correlação resolvida, `user_id` e o valor monetário do pagamento — não identificadores brutos do Asaas). Um endpoint de auditoria lista esses registros de forma segura, exigindo autenticação do usuário Aurea Gold.

## 10. Simulação interna × webhook Asaas

Existe um endpoint separado, `POST /api/v1/wallet/pix/sandbox-webhook`, que **não é o webhook Asaas**: exige login de usuário Aurea Gold e opera apenas quando o provedor de parceiro configurado é o adapter interno de demonstração (`WALLET_PARTNER_PROVIDER=sandbox`), rejeitando com 409 caso contrário. Compartilha a mesma tabela de idempotência, com namespace de chave distinto. Os dois sistemas usam nomes semelhantes ("sandbox webhook") mas são mecanismos independentes — atenção recomendada para não confundi-los.

## 11. Rate limiting

Rate limiting específico não identificado em nenhuma rota deste domínio. O mecanismo de limitação (`slowapi`) existe no projeto e é usado em outra rota (`backend/app/api/v1/routes/pix.py`), mas não foi aplicado aqui.

## 12. Segurança/dados/logs

O handler investigado não persiste nem retorna token, event id bruto, payment id bruto ou payload bruto, e não foi identificado logging explícito desses valores nesse fluxo. O único dado de negócio persistido sem mascaramento é o valor monetário do pagamento, apenas quando uma correlação é resolvida — não é um identificador pessoal.

## 13. Fail-closed

Token ausente/incorreto, payload inválido, evento sem identificador, configuração inválida, replay, conflito de payload, correlação ausente e falha de banco são todos tratados e cobertos por testes automatizados dedicados a este handler.

## 14. O que NÃO existe hoje

- Nenhuma alteração de saldo, ledger ou geração de comprovante real por este webhook.
- Nenhuma chamada HTTP de saída ao Asaas disparada pelo recebimento de um webhook.
- Nenhum rate limiting específico para este domínio.
- Nenhuma tabela de auditoria dedicada (reaproveita `IdempotencyKey`).
- Nenhuma prova de que a entrega via túnel de desenvolvimento continua ativa hoje — é um marco histórico, não uma capacidade contínua.

## 15. Guardrails para evolução futura

Qualquer mudança futura que ligue este webhook a um efeito financeiro real exigiria: patch e revisão dedicados; permanência em Sandbox; nenhuma alteração para Production nessa mudança; nenhuma habilitação de dinheiro real; e clareza explícita para não confundir este webhook com a simulação interna (seção 10).

Qualquer futuro efeito financeiro (crédito de saldo, ledger, marcação de pagamento real, comprovante ou equivalente) **deve exigir correlação resolvida e validada** — os estados `"missing"` e `"unresolved"` não podem, em nenhuma implementação futura, autorizar um side effect financeiro. Hoje isso não é uma falha em aberto: `can_credit_balance`, `can_generate_real_receipt` e `can_mark_real_paid` permanecem `False` de forma fixa, e não existe nenhum side effect financeiro no código atual — este parágrafo é exclusivamente um guardrail para uma implementação futura, não uma correção do estado presente.

## 16. Relação com os demais documentos canônicos

- Arquitetura geral e configuração: [`docs/asaas/ARCHITECTURE.md`](./ARCHITECTURE.md)
- Contrato do cliente HTTP de saída: [`docs/asaas/HTTP_CLIENT_CONTRACT.md`](./HTTP_CLIENT_CONTRACT.md)
- Subcontas: [`docs/asaas/SUBACCOUNTS.md`](./SUBACCOUNTS.md)
- Preparação PIX e origem da correlação usada aqui: [`docs/asaas/DRY_RUN.md`](./DRY_RUN.md)
- Estado comercial/onboarding: `docs/asaas/PARTNERSHIP.md` (futuro, ME1-B6)

Ver o mapa completo em [`docs/asaas/README.md`](./README.md).
