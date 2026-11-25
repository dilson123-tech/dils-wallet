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

## 9. Customer Asaas Sandbox (P0.5) — flags e trava pendente

Escopo: somente Asaas Sandbox, com dados fictícios. Nenhum dinheiro real.

### Dependência entre flags

- `ASAAS_SANDBOX_CUSTOMER_HTTP_ENABLED` só tem efeito junto com
  `ASAAS_SANDBOX_CHARGE_HTTP_ENABLED`. As duas são fail-closed: somente o valor
  literal `true` habilita.
- Com `CHARGE_HTTP` desligada, `POST /api/v1/wallet/pix/asaas/sandbox/prepare`
  segue o caminho local de preparação e não faz chamada HTTP. Nesse caso
  nenhum customer é consultado ou criado, mesmo com `CUSTOMER_HTTP=true`.
- Com as duas ligadas, a rota consulta o customer do usuário pelo
  `externalReference` (`agcus_<32 hex>`). Só cria o customer quando a consulta
  comprova que não existe nenhum, e faz no máximo 1 POST por tentativa, sem
  retry.

### Como identificar uma trava pendente

- Sintoma: a rota `prepare` responde HTTP 409 com "Criação do customer Asaas
  Sandbox em andamento ou com desfecho incerto" e o 409 persiste nas
  requisições seguintes do mesmo usuário. Esse mesmo 409 também aparece se
  outra requisição do usuário estiver em andamento ao mesmo tempo.
- Causa: a trava fica mantida após qualquer POST sem sucesso comprovado:
  timeout, 5xx, 4xx sem rejeição estruturada, corpo inválido, reconsulta
  inconclusiva, ou queda do processo no meio do fluxo. **Inclusive** um HTTP
  400 com `errors` estruturado seguido de reconsulta com 0 customers: a rota
  classifica como rejeição, mas a trava é **mantida**, porque um GET vazio
  logo após o 400 não comprova ausência de efeito remoto. Não há lista de
  códigos de erro Asaas que libere a trava, nem retry de POST. Novas
  tentativas só fazem GET.
- A trava só é liberada automaticamente quando o próprio dono comprova
  exatamente 1 customer válido (POST 2xx válido ou reconsulta com 1).
- Listagem malformada (`hasMore` não booleano, `totalCount` inválido ou
  incoerente com a página) nunca é tratada como ausência de customer.
- Registro: a trava é uma linha na tabela `idempotency_keys` com
  `key = "asaas-sandbox-customer-pending:" + sha256(str(user_id))` e
  `response_json` com `"contract": "asaas_sandbox_customer_pending_lock_v2"` e
  um `token` aleatório exclusivo de cada aquisição. Somente o dono (mesmo
  token) remove a trava, por DELETE atômico condicionado ao token; um dono
  antigo nunca remove uma trava mais nova.
- Conferir essa linha exige acesso de leitura ao banco devidamente autorizado.
  Somente SELECT.
- **Não existe expiração automática da trava.** Ela não tem TTL nem job de
  limpeza, e o soft cap de namespace não se aplica a esse prefixo.

### Como confirmar no painel Asaas Sandbox

No painel do Asaas **Sandbox**, nunca em Production, procure os clientes por
qualquer um destes campos:

- referência externa `agcus_...` do usuário;
- nome `Aurea Gold Sandbox agcus_...`;
- e-mail `agcus_...@example.com`.

O CPF fictício `12345678909` é o mesmo para todos os usuários e não serve para
identificar um customer.

### Recuperação segura

1. **Exatamente 1 customer ativo no painel:** basta uma nova requisição à rota
   `prepare`. A consulta confirma o customer e o fluxo segue, sem novo POST.
   A trava não é do dono dessa requisição e por isso permanece no banco,
   inerte. Não é preciso intervir no banco.
2. **Mais de 1 customer:** a rota responde 409 de duplicidade e exige revisão
   manual no painel Sandbox. Nenhuma cobrança é enviada.
3. **Nenhum customer, ou resultado ainda incerto (inclusive após 400
   estruturado):** **não remover a trava** enquanto **todas** as condições
   abaixo não estiverem comprovadas. Remover a trava com qualquer uma delas em
   aberto pode causar um segundo POST e duplicar o customer.

#### Condições cumulativas para remoção manual da trava

A remoção só é permitida se **todas** forem comprovadas e registradas. Se
qualquer uma não puder ser comprovada, a trava **permanece**.

1. **Operação anterior encerrada ou quiescente:** comprovar que o processo
   ou worker que adquiriu a trava terminou, ou está parado e não pode retomar,
   por exemplo por logs, reinício de deploy registrado ou ausência do
   processo.
2. **Nenhuma requisição em voo:** comprovar que não existe POST `/customers`
   pendente desse usuário, incluindo um timeout do lado cliente cujo request
   ainda pode ser processado pelo Asaas, nem requisição concorrente à rota
   `prepare`.
3. **Reconciliação remota conclusiva:** no painel Asaas **Sandbox**, a busca
   pelos três identificadores de "Como confirmar no painel Asaas Sandbox"
   comprova a ausência do customer, feita **depois** das condições 1 e 2.
4. **Autorização humana específica:** autorização explícita do responsável
   para aquela remoção, daquele usuário, naquele momento. Uma autorização
   genérica ou anterior não vale.
5. **Remoção condicionada à identidade exata da trava:** primeiro um SELECT
   do `response_json` completo, depois um DELETE condicionado à `key` **e** ao
   `response_json` idêntico ao conferido. É o mesmo CAS de `_release_lock`.
   Se 0 linhas forem afetadas, a trava mudou: não repetir, e reavaliar desde
   a condição 1. Nunca apagar só pela `key` nem por prefixo.

Não existe serviço de recuperação, endpoint administrativo, TTL ou automação
para isso, e nenhum deve ser criado sem decisão do responsável.

### Contrato de paginação Asaas (pendente de confirmação)

A listagem `GET /customers` é validada de forma estrita: `data`, `hasMore`
booleano, `totalCount`, `limit`, `offset` e a coerência entre eles. Qualquer
divergência é tratada como indisponível ou pendente, nunca como ausência de
customer.

**Pendente de confirmação:** o formato real da resposta do Asaas para
`limit`, `offset` e `deleted` ainda não foi confirmado. Ainda não se sabe se
`limit` e `offset` sempre aparecem na resposta, com que tipos, e se customers
removidos (`deleted: true`) aparecem ou não na listagem por
`externalReference`. Até essa confirmação documental e contratual:

- a validação estrita permanece como está;
- o fluxo de customer fica **desligado**, com `ASAAS_SANDBOX_CUSTOMER_HTTP_ENABLED`
  diferente de `true`;
- nenhuma chamada ao Asaas, nem ao Sandbox remoto, é feita para "descobrir"
  o formato sem autorização específica.

### Banco de dados

Nenhuma exclusão, alteração ou limpeza na tabela `idempotency_keys`, ou em
qualquer outra tabela, pode ser executada sem autorização específica e
explícita para aquela operação.

## 10. Próximos passos antes de PIX real

Antes de qualquer dinheiro real:

1. definir parceiro PSP/BaaS;
2. criar adapter sandbox do parceiro real;
3. validar webhook assinado/tokenizado;
4. criar tabela própria de auditoria/reconciliação;
5. implementar KYC/KYB real;
6. implementar ledger real separado do sandbox;
7. liberar Pix real somente após homologação e revisão de segurança.

Não avançar para dinheiro real sem parceiro financeiro homologado.
