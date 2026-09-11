# Aurea Gold — Confirmação de Acesso ao Asaas Sandbox v1

Status: draft
Marco planejado: v0.2.33-wallet-asaas-sandbox-access-confirmation-notes
Projeto: Aurea Gold / dils-wallet
Parceiro candidato: Asaas
Prioridade atual: A
Natureza: produto real/comercial, não projeto de estudo.

## 1. Objetivo

Este documento registra a confirmação manual de acesso ao ambiente Asaas Sandbox.

O objetivo é documentar, de forma segura, que o ambiente Sandbox foi acessado com sucesso antes de qualquer spike técnico com código.

Este marco ainda não implementa integração.

## 2. Regra central de segurança

Este documento não registra e nunca deve registrar:

- API key;
- token;
- senha;
- segredo;
- Wallet ID;
- QR Code real;
- chave Pix real;
- payload sensível;
- print com credencial;
- dados bancários reais;
- dados de cliente real.

## 3. Confirmação manual

Data da confirmação: 2026-06-25.

Resultado da verificação manual:

- Ambiente Sandbox acessado com sucesso.
- Conta Sandbox já existente identificada.
- Login no ambiente Sandbox realizado.
- Dashboard Sandbox carregado com sucesso.
- Ambiente separado em domínio Sandbox confirmado.
- Saldo exibido no Sandbox: R$ 0,00.
- Nenhuma operação financeira real realizada.
- Nenhum Pix real realizado.
- Nenhuma cobrança real criada.
- Nenhuma credencial registrada no repositório.

## 4. Telas e áreas localizadas

Durante a verificação manual, foram localizadas as seguintes áreas:

- Tela de login do Asaas Sandbox.
- Dashboard inicial do Asaas Sandbox.
- Menu lateral do Sandbox.
- Área de criação de cobrança.
- Área de clientes.
- Área de cobranças.
- Área Pix.
- Área de links de pagamento.
- Área de cartão Asaas.
- Área de dinheiro/saldo.
- Área de notas fiscais.
- Área de Open Finance.
- Área de negativação.

Também foram vistas, no painel de integrações da conta principal, áreas relacionadas a:

- Chaves de API.
- Segurança.
- Webhooks.
- Logs de requisições.
- Logs de webhooks.

## 5. Estado atual

Status geral: Sandbox acessível.

Itens confirmados:

- [x] Acesso ao painel Asaas.
- [x] Área de integrações localizada.
- [x] Opção de ambiente Sandbox localizada.
- [x] Ambiente Sandbox aberto.
- [x] Conta Sandbox já existente acessada.
- [x] Dashboard Sandbox carregado.
- [x] Saldo Sandbox exibido como R$ 0,00.
- [x] Menu Pix localizado.
- [x] Menu Cobranças localizado.
- [x] Menu Clientes localizado.
- [x] Menu Links de Pagamento localizado.

Itens ainda pendentes:

- [ ] Confirmar Chaves de API sem expor chave.
- [ ] Confirmar URL base Sandbox na documentação.
- [ ] Confirmar Webhooks sem expor token.
- [ ] Confirmar Logs de Requisições.
- [ ] Confirmar Logs de Webhooks.
- [ ] Confirmar documentação pública da API.
- [ ] Confirmar endpoints mínimos para cobrança Sandbox.
- [ ] Confirmar endpoints mínimos para consulta de cobrança.
- [ ] Confirmar como configurar webhook em Sandbox.
- [ ] Confirmar se subcontas estão disponíveis em Sandbox.
- [ ] Confirmar se split está disponível em Sandbox.

## 6. Decisão operacional

Com esta confirmação, o Asaas segue como parceiro candidato Prioridade A para validação técnica em Sandbox.

Mesmo com o Sandbox acessível, a produção continua bloqueada.

Não está autorizado:

- Pix real;
- saldo real;
- cobrança real;
- subconta real;
- split real;
- transferência real;
- operação financeira produtiva;
- uso de credencial de produção.

## 7. Critério para próximo marco

O próximo marco técnico só deve avançar se:

- as Chaves de API forem confirmadas sem exposição;
- a URL base Sandbox for confirmada;
- o webhook Sandbox for entendido;
- os endpoints mínimos forem identificados;
- as credenciais ficarem fora do Git;
- produção continuar explicitamente bloqueada.

## 8. Próximo marco provável

Se as informações de API e Webhook forem confirmadas com segurança, o próximo marco poderá ser:

- `v0.2.34-wallet-asaas-sandbox-api-webhook-notes`

Depois disso, poderá ser planejado o spike técnico com código em ambiente Sandbox.
