# Aurea Gold — Confirmação Técnica Asaas Sandbox v1

Status: draft
Marco planejado: v0.2.38-wallet-asaas-sandbox-technical-confirmation
Projeto: Aurea Gold / dils-wallet
Parceiro candidato: Asaas
Prioridade atual: A
Origem: resposta técnica do Asaas via Valentina Menezes
Natureza: confirmação técnica para futuro spike controlado em Sandbox.

## 1. Objetivo

Este documento registra a resposta técnica recebida do Asaas sobre o uso do ambiente Sandbox para a Aurea Gold.

O objetivo é consolidar as informações necessárias antes do primeiro spike técnico com código.

Este marco ainda não implementa integração.

## 2. Regra central

Esta confirmação permite preparar o primeiro spike técnico apenas em Sandbox.

Ela não autoriza:

- Pix real;
- saldo real;
- cobrança real;
- subconta real;
- split real;
- transferência real;
- operação financeira produtiva;
- uso de API key de produção;
- API key real no Git;
- token real no Git;
- Wallet ID no Git;
- segredo em log, issue, PR, chat ou documento.

## 3. URL base oficial

O Asaas confirmou a URL base oficial do ambiente Sandbox:

    https://sandbox.asaas.com/api/v3

Também foi informada a URL produtiva para separação de ambientes:

    https://api.asaas.com/v3

Regra:

- o ciclo atual deve usar somente Sandbox;
- a URL produtiva não deve ser usada neste ciclo;
- produção continua bloqueada.

## 4. Autenticação

O Asaas confirmou que a autenticação no Sandbox usa o mesmo padrão da produção.

A API Key deve ser enviada em todas as requisições no header:

    access_token: <API_KEY_SANDBOX>

Regras:

- usar apenas API Key Sandbox;
- nunca usar API Key de produção no ambiente local;
- nunca versionar API Key;
- nunca exibir API Key em logs;
- nunca colar API Key em PR, issue, chat ou documento.

## 5. Separação entre Sandbox e produção

O Asaas confirmou que a chave de API do Sandbox é separada da chave de produção.

A chave Sandbox pertence exclusivamente ao ambiente Sandbox.

A chave de produção deve ser criada separadamente no ambiente de produção quando houver autorização futura.

Regra do projeto:

- Sandbox e produção devem permanecer totalmente separados;
- nenhum fallback automático para produção deve existir;
- qualquer tentativa de usar produção deve ser bloqueada.

## 6. Fluxo recomendado para cobrança Pix Sandbox

O Asaas confirmou o fluxo recomendado:

1. Criar cliente pagador.
2. Criar cobrança Pix.
3. Obter QR Code e Pix copia e cola.
4. Confirmar pagamento manualmente pelo painel Sandbox.
5. Consultar status da cobrança.

## 7. Endpoints confirmados

Endpoints informados para o fluxo Sandbox:

Criar cliente:

    POST /v3/customers

Criar cobrança Pix:

    POST /v3/payments

Consultar QR Code e Pix copia e cola:

    GET /v3/payments/{id}/pixQrCode

Consultar status da cobrança:

    GET /v3/payments/{id}

## 8. Payload mínimo informado para cobrança Pix

Exemplo informado pelo Asaas, mantendo apenas dados fictícios:

    customer: cus_xxxxxxxx
    billingType: PIX
    value: 50.00
    dueDate: 2026-07-10
    description: Teste cobrança Pix

Regra:

- usar apenas dados fictícios;
- não usar cliente real;
- não usar CPF/CNPJ real;
- não usar valor operacional real;
- não tratar como cobrança produtiva.

## 9. Confirmação manual de pagamento no Sandbox

O Asaas confirmou que, no Sandbox, é possível confirmar pagamento manualmente pelo painel.

Essa ação simula a liquidação da cobrança.

Regra:

- confirmação manual deve ocorrer apenas no painel Sandbox;
- não gerar interpretação de liquidação real;
- não alterar saldo real;
- não gerar comprovante real.

## 10. Status de cobrança

O endpoint de consulta de cobrança retorna o campo `status`.

Exemplos de status citados:

- `PENDING`
- `RECEIVED`
- `OVERDUE`

Regra:

- o spike deve tratar status como informação Sandbox;
- `RECEIVED` em Sandbox não deve gerar saldo real;
- `RECEIVED` em Sandbox não deve liberar operação real.

## 11. Eventos de webhook recomendados

Eventos recomendados pelo Asaas para fluxo Pix:

- `PAYMENT_CREATED`
- `PAYMENT_RECEIVED`
- `PAYMENT_OVERDUE`
- `PAYMENT_DELETED`
- `PAYMENT_REFUNDED`
- `PAYMENT_UPDATED`

Evento principal para Pix:

- `PAYMENT_RECEIVED`

Observação:

Para Pix, o evento principal é `PAYMENT_RECEIVED`.

## 12. Validação de webhook

O Asaas confirmou que, ao configurar o webhook, pode ser definido um token de autenticação.

Esse token será enviado pelo Asaas no header:

    asaas-access-token

O sistema deve validar se o header recebido corresponde ao token configurado.

Regra:

- webhook sem token deve ser bloqueado;
- token não deve ser versionado;
- token não deve aparecer em log;
- token não deve ser exposto em PR, issue, chat ou documento.

## 13. IPs de webhook

O Asaas informou que não publica uma lista fixa de IPs de saída para webhooks.

A recomendação principal de segurança é usar a validação por token via header:

    asaas-access-token

Regra:

- não depender de allowlist de IP como mecanismo principal;
- validar token em toda notificação;
- logs devem mascarar headers sensíveis.

## 14. Logs no painel Sandbox

O Asaas confirmou que, no painel Sandbox, em Integrações > Logs de Webhooks, é possível visualizar:

- notificações enviadas;
- status de entrega;
- tentativas de reenvio;
- detalhes do evento.

Uso esperado:

- depurar integração Sandbox;
- confirmar entrega dos webhooks;
- validar reenvios;
- verificar divergências sem expor segredo no Git.

## 15. Recomendações contra uso acidental de produção

Recomendações confirmadas:

- nunca usar API Key de produção em desenvolvimento ou homologação;
- usar exclusivamente a chave Sandbox;
- diferenciar URLs base por variável de ambiente.

Regra do projeto:

- `ASAAS_ENV=sandbox`;
- `REAL_MONEY_ENABLED=false`;
- `ASAAS_BASE_URL=https://sandbox.asaas.com/api/v3`;
- produção segue bloqueada.

## 16. Documentação indicada

O Asaas indicou documentação sobre:

- guia de cobranças;
- cobranças via Pix.

As URLs foram fornecidas no e-mail de resposta e podem ser usadas como referência técnica externa durante o spike.

## 17. Critérios para liberar o próximo marco

O próximo marco poderá preparar o primeiro spike técnico se:

- o ambiente local usar apenas `ASAAS_ENV=sandbox`;
- a URL base Sandbox estiver em variável de ambiente;
- a API Key Sandbox ficar fora do Git;
- o token de webhook ficar fora do Git;
- a validação do header `asaas-access-token` for planejada;
- os endpoints confirmados forem usados apenas em Sandbox;
- `REAL_MONEY_ENABLED=false` permanecer obrigatório;
- houver testes de bloqueio contra produção.

## 18. Próximo marco provável

Próximo marco recomendado:

- `v0.2.39-wallet-asaas-sandbox-first-spike-plan`

Esse próximo marco deve planejar o primeiro código controlado, ainda sem operação real.

O código só deve ser iniciado com travas explícitas contra produção e sem qualquer segredo versionado.
