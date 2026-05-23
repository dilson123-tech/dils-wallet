# Aurea Gold — Runbook da Wallet Sandbox

Status: v0.2.0-wallet-sandbox-cycle
Tag base: v0.2.0-wallet-sandbox-cycle
Projeto: Aurea Gold / dils-wallet
Natureza: produto real/comercial, não projeto de estudo.

## 1. Objetivo

Este documento registra o ciclo sandbox da wallet Aurea Gold.

O ciclo permite testar a arquitetura financeira sem movimentar dinheiro real:

- cobrança PIX sandbox;
- webhook sandbox;
- idempotência/replay;
- reconciliação por provider_reference;
- painel de reconciliação;
- histórico/auditoria sandbox.

Regra central: sandbox não é dinheiro real, não é liquidação real e não gera comprovante financeiro real.

## 2. Marco fechado

PRs incluídos:

- #107 PIX sandbox entrada/cobrança simulada
- #108 Webhook sandbox + idempotência
- #109 Reconciliação sandbox backend
- #110 Painel de reconciliação sandbox
- #111 Histórico/auditoria sandbox

Tag oficial:

- v0.2.0-wallet-sandbox-cycle

Commits principais:

- 304c951 feat(wallet): add sandbox audit history (#111)
- 67c57fe feat(wallet): add sandbox reconciliation panel (#110)
- ad51e9b feat(wallet): add sandbox reconciliation foundation (#109)
- ff0d7d1 feat(wallet): add pix sandbox webhook idempotency (#108)
- 648b652 feat(wallet): add pix sandbox payment foundation (#107)

## 3. Regras de segurança

O ciclo sandbox deve sempre manter:

- real_money_enabled=false
- can_credit_balance=false
- can_generate_real_receipt=false
- can_mark_real_paid=false
- não creditar saldo real
- não alterar PixLedger
- não alterar Transaction
- não emitir comprovante financeiro real
- não enviar nem receber Pix real

Nunca remover avisos de sandbox da interface sem decisão explícita.

## 4. Variáveis do backend sandbox

Usar localmente:

- SECRET_KEY=ci-local-smoke-secret-1234567890
- JWT_SECRET=ci-local-smoke-secret-1234567890
- WALLET_MODE=partner
- WALLET_PARTNER_PROVIDER=sandbox
- CORS_ORIGINS=http://localhost:5175,http://127.0.0.1:5175

Esperado no endpoint /api/v1/wallet/partner/status:

- wallet_mode=partner
- provider=sandbox
- real_money=false

Importante: WALLET_MODE=demo deve bloquear endpoints sandbox com HTTP 409.

## 5. Endpoints do ciclo sandbox

### Cobrança PIX sandbox

POST /api/v1/wallet/pix/sandbox-payment

Responsabilidade:

- criar cobrança técnica sandbox;
- retornar provider_reference;
- retornar QR/copia e cola fake;
- não movimentar dinheiro real.

### Webhook sandbox

POST /api/v1/wallet/pix/sandbox-webhook

Responsabilidade:

- receber evento sandbox;
- validar idempotência;
- bloquear replay perigoso;
- retornar duplicated=true em replay válido;
- retornar HTTP 409 quando a mesma chave for reutilizada com payload diferente.

### Reconciliação sandbox

GET /api/v1/wallet/pix/sandbox-reconciliation/{provider_reference}

Responsabilidade:

- consultar evento sandbox por provider_reference;
- retornar sandbox_reconciled quando houver webhook salvo;
- retornar pending_webhook quando não houver evento;
- não consultar PSP real.

### Histórico/Auditoria sandbox

GET /api/v1/wallet/pix/sandbox-audit-history?limit=5

Responsabilidade:

- listar últimos eventos sandbox;
- usar eventos salvos em IdempotencyKey.response_json;
- mostrar provider_reference, status, valor, event_type e reconciliation_status;
- não mexer em saldo real.

## 6. Painel Mais

A aba Mais deve mostrar:

### PIX sandbox

- geração de cobrança sandbox;
- provider_reference;
- copia e cola sandbox;
- aviso de que não representa Pix real.

### Reconciliação sandbox

- consulta por provider_reference;
- status confirmed/not_found;
- evento localizado ou pendente;
- sandbox_reconciled;
- aviso de que não representa liquidação financeira real.

### Auditoria sandbox

- últimos eventos técnicos;
- status;
- provider_reference;
- sandbox_reconciled;
- aviso de que não representa movimentação financeira real.

## 7. Testes mínimos antes de PR futuro

Backend:

python -m py_compile backend/app/api/v1/routes/wallet.py backend/app/config.py backend/app/models/idempotency.py

Frontend:

npm run build dentro de aurea-gold-client

Git:

git diff --check
git status -sb

## 8. Troubleshooting

### Rota retorna 404

Provável backend antigo rodando em memória. Matar processo da porta 8090 e subir novamente.

### Rota retorna 401

Bom sinal. A rota existe e exige token.

### Rota retorna 409 em demo

Correto. Endpoints sandbox devem bloquear WALLET_MODE=demo.

### Porta 5175 em uso

Provavelmente frontend já está rodando.

### Porta 8090 em uso

Provavelmente backend antigo está rodando.

## 9. Próximos passos antes de PIX real

Antes de qualquer dinheiro real:

1. definir parceiro PSP/BaaS;
2. criar adapter sandbox do parceiro real;
3. validar webhook assinado/tokenizado;
4. criar tabela própria de auditoria/reconciliação;
5. implementar KYC/KYB real;
6. implementar ledger real separado do sandbox;
7. liberar Pix real somente após homologação e revisão de segurança.

Não avançar para dinheiro real sem parceiro financeiro homologado.
