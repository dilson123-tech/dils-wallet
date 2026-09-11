# Aurea Gold Wallet - Asaas Sandbox Manual Execution Gate v1

## Marco

v0.2.47-wallet-asaas-sandbox-manual-execution-gate

## Status

Este marco define a trava formal de autorizacao manual antes de qualquer chamada HTTP real para o Asaas Sandbox.

Mesmo em Sandbox, nenhuma execucao externa deve ocorrer automaticamente.

## Objetivo

O objetivo e impedir que o projeto avance de dry-run seguro para chamada HTTP real sem uma decisao explicita, documentada e revisada.

A trava protege o projeto contra:

- execucao acidental de HTTP
- uso acidental de API Key real
- exposicao de segredo em Git, chat, log ou PR
- confusao entre Sandbox e producao
- criacao inesperada de cliente Sandbox
- criacao inesperada de cobranca Pix Sandbox
- obtencao inesperada de QR Code Pix Sandbox
- consulta inesperada de status Sandbox

## Contexto

Os marcos anteriores prepararam o fluxo tecnico em modo seguro:

- v0.2.40: config guards
- v0.2.41: client skeleton
- v0.2.42: customer dry-run
- v0.2.43: payment dry-run
- v0.2.44: Pix QR Code dry-run
- v0.2.45: payment status dry-run
- v0.2.46: full dry-run flow

Todos esses marcos mantem HTTP bloqueado.

## Regra principal

Antes de qualquer chamada HTTP real no Asaas Sandbox, os seguintes pontos devem estar confirmados:

1. A execucao continua em Sandbox.
2. A URL base e exatamente `https://sandbox.asaas.com/api/v3`.
3. `ASAAS_ENV=sandbox`.
4. `REAL_MONEY_ENABLED=false`.
5. `WALLET_MODE=partner`.
6. `WALLET_PARTNER_PROVIDER=asaas`.
7. A API Key Sandbox esta apenas em `.env` local seguro.
8. A API Key Sandbox nao aparece em Git, chat, log, issue, PR ou print.
9. O webhook token Sandbox nao aparece em Git, chat, log, issue, PR ou print.
10. Nenhum Wallet ID real aparece em Git, chat, log, issue, PR ou print.
11. O payload de teste nao usa dados reais de cliente.
12. O valor de teste e pequeno e claramente identificado como Sandbox.
13. O painel do Asaas Sandbox esta acessivel para confirmar ou cancelar o teste.
14. Existe decisao manual explicita antes da execucao.

## Checklist de autorizacao manual

A chamada HTTP real no Sandbox so pode acontecer se este checklist estiver marcado:

- [ ] Eu confirmei que a execucao e Sandbox.
- [ ] Eu confirmei que producao esta bloqueada.
- [ ] Eu confirmei que dinheiro real esta bloqueado.
- [ ] Eu confirmei que a API Key usada e somente Sandbox.
- [ ] Eu confirmei que nenhum segredo foi colado no chat.
- [ ] Eu confirmei que nenhum segredo foi commitado.
- [ ] Eu confirmei que nenhum segredo aparece nos logs.
- [ ] Eu confirmei que os dados de teste sao ficticios.
- [ ] Eu confirmei que o valor de teste e controlado.
- [ ] Eu confirmei que o painel Sandbox esta disponivel.
- [ ] Eu autorizei manualmente a primeira chamada HTTP Sandbox.

## Frase obrigatoria de autorizacao

Antes da primeira chamada HTTP real no Sandbox, a decisao deve ser registrada assim:

`AUTORIZO EXECUTAR PRIMEIRA CHAMADA HTTP ASAAS SANDBOX, SEM PRODUCAO E SEM DINHEIRO REAL.`

Sem essa frase, o projeto continua apenas em dry-run.

## O que permanece bloqueado

- producao
- dinheiro real
- saldo real
- Pix real de cliente real
- transferencia real
- subconta real
- split real
- BaaS real
- webhook real de producao
- qualquer execucao com segredo exposto
- qualquer execucao automatica sem revisao manual

## Fora de escopo

Este marco nao executa chamada HTTP.

Este marco nao cria cliente no Asaas.
Este marco nao cria cobranca Pix.
Este marco nao obtem QR Code Pix.
Este marco nao consulta status real.
Este marco nao ativa webhook.
Este marco nao faz conciliacao.
Este marco nao altera ambiente de producao.

## Resultado esperado

Ao final deste marco, o projeto tera uma barreira documental clara entre:

- dry-run seguro
- primeira chamada real no Asaas Sandbox

## Proximo passo provavel

v0.2.48-wallet-asaas-sandbox-first-http-call-runbook

Esse proximo marco deve preparar o runbook da primeira chamada HTTP real no Sandbox, ainda sem executar a chamada automaticamente.
