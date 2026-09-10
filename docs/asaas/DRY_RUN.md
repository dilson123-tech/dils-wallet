# Aurea Gold — Dry-Run e Preparação PIX Asaas Sandbox

Este documento descreve o estado técnico atual da preparação de operações PIX Asaas Sandbox (dry-run), como implementado em `backend/app/partner/asaas_client.py` e consumido pelo único endpoint runtime desse domínio. Não é um changelog — para o histórico incremental, veja os documentos históricos listados em [`docs/asaas/README.md`](./README.md). O eventual arquivamento desses documentos é tratado separadamente no ME1-C, ainda não realizado.

## 1. Propósito

Documentar o que existe hoje em termos de preparação local (sem HTTP real) de operações PIX no domínio Asaas — cliente, cobrança, QR Code e status — e identificar precisamente qual parte disso tem uso runtime real.

## 2. Status executivo atual

Diferente de outras áreas da integração Asaas já documentadas ([`HTTP_CLIENT_CONTRACT.md`](./HTTP_CLIENT_CONTRACT.md), [`SUBACCOUNTS.md`](./SUBACCOUNTS.md)), este domínio tem **um fluxo runtime local ativo**: `POST /api/v1/wallet/pix/asaas/sandbox/prepare`, autenticado, testado e que persiste um registro de correlação em banco — mas ainda sem transporte HTTP real ao Asaas e sem nenhum consumidor de frontend conhecido.

Os demais objetos de "dry-run" — `dry_run_create_customer`, `dry_run_create_pix_payment`, `dry_run_get_pix_qr_code`, `dry_run_get_payment_status` e `dry_run_full_pix_flow` — são exercitados somente por testes. O endpoint runtime compartilha a mesma função de baixo nível de preparação (`prepare_create_pix_payment`) usada por `dry_run_create_pix_payment`, mas não instancia o objeto `AsaasPaymentDryRunResult` nem nenhum dos demais wrappers de teste.

## 3. Endpoint runtime atual

`POST /api/v1/wallet/pix/asaas/sandbox/prepare` (`backend/app/api/v1/routes/wallet.py`), protegido por autenticação de cliente. Fluxo: valida entrada → carrega configuração Sandbox (`AsaasConfigError` → HTTP 503) → gera referência externa opaca local → registra correlação em banco → monta o request `POST /payments` via `prepare_create_pix_payment` → retorna um resumo seguro, sem executar HTTP.

## 4. `prepare_create_pix_payment` e a família `dry_run_*`

`prepare_create_pix_payment` é a função de baixo nível que efetivamente monta o payload (`customer`, `billingType=PIX`, `value`, `dueDate`, `description`, `externalReference`) e é usada tanto pelo endpoint runtime quanto pelo wrapper `dry_run_create_pix_payment` (usado apenas em testes). Existem ainda `dry_run_create_customer`, `dry_run_get_pix_qr_code`, `dry_run_get_payment_status` e `dry_run_full_pix_flow` — todos sem nenhum consumidor fora de `backend/tests/`.

## 5. Request preparado

O request preparado nunca é enviado. `AsaasPreparedRequest` registra método, URL, payload e mantém `http_call_executed=False` de forma fixa.

## 6. Ausência de HTTP real

Nenhum dos caminhos deste domínio executa uma requisição HTTP real — nem o endpoint runtime, nem os métodos `dry_run_*` órfãos. Não há transporte HTTP implementado em nenhum lugar alcançável por este domínio (mesma conclusão de [`HTTP_CLIENT_CONTRACT.md`](./HTTP_CLIENT_CONTRACT.md)).

## 7. PIX / pagamento / QR Code / status

- **PIX/correlação**: preparação local usada pelo runtime, persistida e testada — via endpoint runtime.
- **Pagamento (`POST /payments`)**: mesma função de preparação usada pelo endpoint real e pelo wrapper de teste `dry_run_create_pix_payment`.
- **QR Code (`GET /payments/{id}/pixQrCode`)**: apenas preparação de path, sem consumidor runtime, nunca gerado nem sintético.
- **Status (`GET /payments/{id}`)**: apenas preparação de path, sem consumidor runtime.

Nenhuma resposta real do Asaas é processada em nenhum destes.

## 8. Dados e sanitização

Identificadores e valores de negócio (`customer_id`, `value`, `due_date`, `description`) nunca são retornados na resposta HTTP nem em `safe_summary()`. A referência externa é gerada localmente e aparece no request preparado em memória como `externalReference`, mas não é persistida em texto puro — no registro de correlação, permanece apenas sua derivação (hash SHA-256), e ela também não é retornada ao frontend nem exposta em `safe_summary()`. `api_key`/`access_token` nunca aparecem além de um booleano de presença.

## 9. Idempotência/correlação

O registro de correlação reaproveita a mesma tabela `IdempotencyKey` usada pelo sistema de idempotência PIX geral (namespace próprio, chave prefixada `asaas-payment-correlation:`), mas gerado a partir de uma referência opaca criada localmente — nunca de um identificador do Asaas. Esse registro é consumido pelo handler de recebimento de webhook Asaas para resolver a qual usuário um evento pertence; os detalhes desse consumo pertencem a `docs/asaas/WEBHOOKS.md` (futuro, ME1-B5).

## 10. Frontend/consumidores

Nenhum dos três frontends (`aurea-gold-client/`, `frontend/`, `aurea-gold-admin/`) chama esse endpoint hoje.

## 11. Fail-closed

Configuração inválida, payload inválido, usuário inválido, referência reutilizada com dado diferente e falha de armazenamento são todos tratados e cobertos por testes automatizados de serviço e endpoint.

## 12. O que NÃO existe hoje

- Nenhuma cobrança PIX real criada no Asaas.
- Nenhum QR Code real ou sintético gerado.
- Nenhuma consulta real de status.
- Nenhum consumidor de frontend para o endpoint de preparação.
- Nenhum transporte HTTP real em qualquer parte deste domínio.

## 13. Guardrails para evolução futura

Qualquer implementação futura de envio real exigiria: patch e revisão dedicados; restrição a Sandbox; nenhuma alteração para Production nessa mudança; nenhuma habilitação de dinheiro real; uso da URL Sandbox atual correta (`https://api-sandbox.asaas.com/v3`, ver `ARCHITECTURE.md`), nunca a citada nos documentos históricos; e, se um frontend vier a consumir o endpoint existente, revisão de segurança própria para essa integração.

## 14. Relação com os demais documentos canônicos

- Arquitetura geral e configuração: [`docs/asaas/ARCHITECTURE.md`](./ARCHITECTURE.md)
- Contrato do cliente HTTP (cadeia `/customers`): [`docs/asaas/HTTP_CLIENT_CONTRACT.md`](./HTTP_CLIENT_CONTRACT.md)
- Subcontas: [`docs/asaas/SUBACCOUNTS.md`](./SUBACCOUNTS.md)
- Webhooks e consumo da correlação por eventos assíncronos: `docs/asaas/WEBHOOKS.md` (futuro, ME1-B5)

Ver o mapa completo em [`docs/asaas/README.md`](./README.md).
