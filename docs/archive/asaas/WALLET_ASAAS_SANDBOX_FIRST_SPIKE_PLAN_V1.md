# Aurea Gold / dils-wallet — Asaas Sandbox First Spike Plan V1

Marco planejado: v0.2.39-wallet-asaas-sandbox-first-spike-plan

Status: planejamento tecnico documental.

Este documento registra o plano seguro para o primeiro spike tecnico da integracao Asaas Sandbox no projeto Aurea Gold / dils-wallet.

Este marco ainda nao implementa codigo, nao faz chamada HTTP, nao usa API Key real, nao usa token real, nao cria cobranca real, nao cria saldo real e nao habilita operacao produtiva.

## 1. Objetivo

Definir a ordem segura para iniciar a integracao Asaas Sandbox em marco futuro.

O foco deste marco e proteger o projeto antes de qualquer codigo de integracao.

O primeiro codigo deve comecar somente no proximo marco provavel:

v0.2.40-wallet-asaas-sandbox-config-guards

Esse proximo marco deve implementar apenas configuracao, leitura de variaveis e travas de seguranca.

## 2. Confirmacoes tecnicas do Asaas

O Asaas confirmou os seguintes pontos para o planejamento:

- URL base Sandbox: https://sandbox.asaas.com/api/v3
- URL base producao: https://api.asaas.com/v3
- A producao nao deve ser usada agora.
- A autenticacao usa o header access_token.
- O valor do header deve ser a API Key Sandbox.
- A API Key Sandbox e independente da API Key de producao.
- A chave Sandbox nao serve para producao.
- A chave de producao so deve ser criada futuramente, com autorizacao explicita.

## 3. Escopo permitido

O primeiro spike futuro pode preparar:

- leitura segura de variaveis de ambiente;
- validacao de ambiente Sandbox;
- bloqueio contra URL de producao;
- bloqueio contra dinheiro real;
- bloqueio contra modo produtivo;
- testes automatizados das travas;
- logs seguros sem segredo;
- estrutura inicial do servico Asaas sem operacao financeira real.

## 4. Fora de escopo

Nao faz parte deste marco:

- Pix real;
- cobranca real;
- saldo real;
- saque real;
- transferencia real;
- subconta real;
- split real;
- producao Asaas;
- Wallet ID real;
- API Key real;
- token real;
- webhook publico real;
- comprovante financeiro real;
- conciliacao financeira real.

## 5. Variaveis obrigatorias planejadas

Variaveis planejadas para ambiente local seguro:

WALLET_MODE=partner
WALLET_PARTNER_PROVIDER=asaas
REAL_MONEY_ENABLED=false
ASAAS_ENV=sandbox
ASAAS_BASE_URL=https://sandbox.asaas.com/api/v3
ASAAS_API_KEY=<DEFINIR_APENAS_NO_ENV_LOCAL_SEGURO>
ASAAS_WEBHOOK_TOKEN=<DEFINIR_APENAS_NO_ENV_LOCAL_SEGURO>
ASAAS_WEBHOOK_ALLOWED_IPS=<OPCIONAL_SE_HOUVER_LISTA_OFICIAL>

A API Key real nunca deve ser colocada no Git.

O token real nunca deve ser colocado no Git.

## 6. Travas obrigatorias antes de qualquer chamada HTTP

Antes de qualquer chamada para o Asaas, o backend deve validar:

1. WALLET_MODE deve ser partner.
2. WALLET_PARTNER_PROVIDER deve ser asaas.
3. REAL_MONEY_ENABLED deve ser false.
4. ASAAS_ENV deve ser sandbox.
5. ASAAS_BASE_URL deve ser exatamente https://sandbox.asaas.com/api/v3.
6. ASAAS_BASE_URL nao pode apontar para producao.
7. API Key nao pode aparecer em logs.
8. Token de webhook nao pode aparecer em logs.
9. Nenhum fluxo pode marcar saldo real.
10. Nenhum fluxo pode gerar comprovante real.

Se qualquer trava falhar, a integracao deve abortar.

## 7. Sequencia tecnica planejada

Ordem segura para o marco futuro:

1. Criar configuracao Asaas Sandbox.
2. Ler variaveis de ambiente.
3. Validar modo Sandbox.
4. Bloquear producao.
5. Validar REAL_MONEY_ENABLED=false.
6. Criar testes automatizados de falha.
7. Criar estrutura de servico Asaas sem chamada externa.
8. Criar cliente HTTP somente depois das travas.
9. Registrar logs seguros sem segredo.
10. Planejar a primeira chamada Sandbox somente depois da validacao.

## 8. Arquivos candidatos para marco futuro

Arquivos candidatos para v0.2.40:

- backend/app/core/config.py
- backend/app/services/asaas_config.py
- backend/app/services/asaas_client.py
- backend/tests/test_asaas_config_guards.py
- backend/.env.example
- docs/WALLET_ASAAS_SANDBOX_CONFIG_GUARDS_V1.md

A lista pode mudar apos inspecao real do codigo.

## 9. Dados ficticios permitidos

Somente dados ficticios podem ser usados em Sandbox.

Cliente ficticio permitido:

- Nome: Cliente Sandbox Aurea Gold
- CPF de teste: 12345678909
- E-mail: cliente.sandbox@example.com
- Telefone: 11999999999

Cobranca Pix Sandbox ficticia:

- billingType: PIX
- value: 50.00
- dueDate: 2026-07-10
- description: Teste cobranca Pix Sandbox Aurea Gold

Nenhum dado real de cliente deve ser usado nesta fase.

## 10. Fluxo Pix Sandbox planejado

Fluxo confirmado para planejamento:

1. Criar cliente pagador ficticio.
2. Criar cobranca Pix Sandbox.
3. Obter QR Code e Pix copia e cola.
4. Confirmar pagamento manualmente pelo painel Sandbox.
5. Consultar status da cobranca.

Endpoints planejados:

- POST /v3/customers
- POST /v3/payments
- GET /v3/payments/{id}/pixQrCode
- GET /v3/payments/{id}

## 11. Status de cobranca

O status deve ser consultado em:

GET /v3/payments/{id}

Campo esperado:

status

Status citados:

- PENDING
- RECEIVED
- OVERDUE

Em Sandbox, RECEIVED nao representa saldo real.

O produto nao deve exibir isso como dinheiro real disponivel.

## 12. Webhook Sandbox planejado

Eventos recomendados:

- PAYMENT_CREATED
- PAYMENT_RECEIVED
- PAYMENT_OVERDUE
- PAYMENT_DELETED
- PAYMENT_REFUNDED
- PAYMENT_UPDATED

Evento principal para Pix:

- PAYMENT_RECEIVED

Validacao obrigatoria:

- header: asaas-access-token

Regras:

- rejeitar webhook sem token;
- rejeitar webhook com token invalido;
- nunca logar token real;
- nunca aceitar evento Sandbox como dinheiro real;
- nunca liberar saldo real por evento Sandbox.

## 13. Logs Sandbox

O painel Sandbox do Asaas permite acompanhar logs em:

Integracoes > Logs de Webhooks

Esses logs podem ser usados para verificar notificacoes, status de entrega, tentativas de reenvio e detalhes do evento.

Logs internos do dils-wallet devem mascarar qualquer segredo.

## 14. Testes minimos obrigatorios no marco futuro

O marco futuro deve testar:

1. Falha quando ASAAS_ENV nao for sandbox.
2. Falha quando ASAAS_BASE_URL apontar para producao.
3. Falha quando REAL_MONEY_ENABLED nao for false.
4. Falha quando WALLET_PARTNER_PROVIDER nao for asaas.
5. Sucesso apenas com configuracao Sandbox segura.
6. Garantia de que API Key nao aparece em logs.
7. Garantia de que token de webhook nao aparece em logs.
8. Garantia de que chamada externa nao ocorre antes da liberacao planejada.

## 15. Criterios de abortar

Abortar imediatamente se:

- URL parecer producao;
- API Key parecer producao;
- REAL_MONEY_ENABLED nao for false;
- ASAAS_ENV nao for sandbox;
- segredo aparecer em log;
- segredo aparecer em diff;
- segredo aparecer em teste;
- segredo aparecer em PR;
- qualquer fluxo tentar criar saldo real;
- qualquer fluxo tentar gerar comprovante real;
- qualquer fluxo tentar usar producao.

## 16. Criterios de sucesso deste marco

Este marco sera considerado concluido quando:

- este documento estiver criado;
- nao houver segredo no arquivo;
- git diff --check passar;
- o commit for criado;
- o PR for aberto;
- os checks passarem;
- o PR for mergeado;
- a tag oficial for criada;
- a main ficar limpa e alinhada com origin/main.

Tag esperada:

v0.2.39-wallet-asaas-sandbox-first-spike-plan

## 17. Ordem segura dos proximos marcos

Ordem recomendada:

1. v0.2.39-wallet-asaas-sandbox-first-spike-plan
2. v0.2.40-wallet-asaas-sandbox-config-guards
3. v0.2.41-wallet-asaas-sandbox-client-skeleton
4. v0.2.42-wallet-asaas-sandbox-customer-dry-run
5. v0.2.43-wallet-asaas-sandbox-pix-charge-dry-run
6. v0.2.44-wallet-asaas-sandbox-webhook-validation

## 18. Decisao operacional

A Aurea Gold / dils-wallet seguira em modo seguro.

O Asaas Sandbox sera usado somente para validacao tecnica.

Nenhuma operacao real sera liberada antes de:

- homologacao BaaS;
- compliance;
- revisao juridica;
- contrato formal;
- decisao explicita do Dilson;
- revisao final de seguranca;
- separacao completa entre Sandbox e producao.

Ate la, todo fluxo Asaas deve ser tratado como teste tecnico sem dinheiro real.
