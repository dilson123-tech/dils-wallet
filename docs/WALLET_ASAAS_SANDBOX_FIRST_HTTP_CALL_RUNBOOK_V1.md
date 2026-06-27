# Aurea Gold Wallet - Asaas Sandbox First HTTP Call Runbook v1

## Marco

v0.2.48-wallet-asaas-sandbox-first-http-call-runbook

## Status

Este marco prepara o runbook da primeira chamada HTTP real no Asaas Sandbox.

Ele nao executa chamada HTTP.
Ele nao cria cliente no Asaas.
Ele nao cria cobranca Pix.
Ele nao obtem QR Code Pix.
Ele nao consulta status real.
Ele nao movimenta dinheiro real.
Ele nao usa producao.

## Objetivo

O objetivo e documentar, com seguranca, como devera ser feita a primeira chamada HTTP real no Asaas Sandbox quando houver autorizacao manual explicita.

Este runbook respeita a trava definida em:

- docs/WALLET_ASAAS_SANDBOX_MANUAL_EXECUTION_GATE_V1.md

Sem a autorizacao manual, o projeto continua apenas em dry-run.

## Chamada alvo da primeira execucao

A primeira chamada HTTP real no Sandbox devera ser a criacao de cliente ficticio:

- Metodo: POST
- Endpoint: /customers
- Base URL: https://sandbox.asaas.com/api/v3
- Ambiente: Sandbox
- Operacao: create_customer

## Por que comecar por cliente

A criacao de cliente ficticio e o primeiro passo mais seguro porque:

- nao cria cobranca Pix
- nao gera QR Code Pix
- nao consulta saldo
- nao movimenta dinheiro
- permite validar autenticacao Sandbox e formato de request
- permite confirmar se o painel Sandbox recebeu o registro

## Payload ficticio permitido

O payload deve usar somente dados ficticios de teste.

Exemplo de campos permitidos:

- name: Cliente Sandbox Aurea Gold
- cpfCnpj: CPF ficticio de teste
- email: cliente.sandbox@example.com
- mobilePhone: telefone ficticio de teste

## Dados proibidos

Nao usar:

- nome real de cliente
- CPF real de cliente
- e-mail real de cliente
- telefone real de cliente
- dados bancarios reais
- chave Pix real
- Wallet ID real
- qualquer dado sensivel de usuario real

## Checklist obrigatorio antes da execucao

Antes da primeira chamada HTTP real no Sandbox, confirmar:

- [ ] A branch atual esta limpa.
- [ ] A main esta alinhada com origin/main.
- [ ] A execucao e somente Sandbox.
- [ ] A URL base e exatamente https://sandbox.asaas.com/api/v3.
- [ ] ASAAS_ENV=sandbox.
- [ ] REAL_MONEY_ENABLED=false.
- [ ] WALLET_MODE=partner.
- [ ] WALLET_PARTNER_PROVIDER=asaas.
- [ ] A API Key Sandbox esta somente no .env local.
- [ ] A API Key Sandbox nao aparece em Git.
- [ ] A API Key Sandbox nao aparece no chat.
- [ ] A API Key Sandbox nao aparece nos logs.
- [ ] O webhook token nao aparece em Git, chat ou logs.
- [ ] Nenhum Wallet ID real aparece em Git, chat ou logs.
- [ ] O payload usa somente dados ficticios.
- [ ] O painel Asaas Sandbox esta acessivel.
- [ ] A frase obrigatoria de autorizacao foi registrada.

## Frase obrigatoria de autorizacao

A primeira chamada HTTP real no Sandbox so pode ser feita depois desta frase:

`AUTORIZO EXECUTAR PRIMEIRA CHAMADA HTTP ASAAS SANDBOX, SEM PRODUCAO E SEM DINHEIRO REAL.`

Sem essa frase, nenhuma chamada deve ser executada.

## Como registrar o resultado

O registro do resultado deve conter apenas informacoes seguras:

- data da execucao
- ambiente: sandbox
- endpoint chamado
- status HTTP
- operacao executada
- se houve erro ou sucesso
- id retornado mascarado ou omitido
- confirmacao de que nenhum segredo foi exposto
- confirmacao de que nenhum dinheiro real foi movimentado

## O que nao registrar

Nao registrar:

- API Key
- webhook token
- Wallet ID real
- headers completos
- payload com dado real
- resposta completa se contiver identificador sensivel
- print com segredo
- log bruto com segredo

## Criterios de sucesso

A primeira chamada sera considerada bem-sucedida se:

- a chamada ocorrer somente no Sandbox
- o HTTP responder com sucesso esperado
- nenhum segredo for exposto
- nenhum dado real for usado
- nenhum dinheiro real for movimentado
- o resultado puder ser registrado de forma segura
- o painel Sandbox puder ser conferido sem expor segredo

## Criterios de parada

Parar imediatamente se:

- houver duvida entre Sandbox e producao
- a URL nao for a URL oficial do Sandbox
- REAL_MONEY_ENABLED estiver true
- aparecer qualquer segredo no terminal, log, chat ou PR
- o payload tiver dado real
- o painel Sandbox nao estiver acessivel
- a autorizacao manual nao tiver sido registrada
- qualquer comportamento parecer diferente do esperado

## Fora de escopo

Este marco nao executa chamada HTTP.

Este marco nao implementa cliente HTTP real.
Este marco nao envia request para o Asaas.
Este marco nao cria cliente real.
Este marco nao cria cobranca Pix.
Este marco nao obtem QR Code Pix.
Este marco nao consulta status real.
Este marco nao ativa webhook.
Este marco nao faz conciliacao.
Este marco nao libera producao.
Este marco nao libera dinheiro real.

## Proximo passo provavel

v0.2.49-wallet-asaas-sandbox-first-http-call-preflight

Esse proximo marco deve preparar uma validacao preflight local antes da primeira execucao HTTP real no Sandbox.
