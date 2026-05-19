# Aurea Gold Wallet — Checklist de Avaliação de Parceiros Financeiros

## Objetivo

Avaliar PSPs, BaaS, instituições de pagamento e parceiros financeiros para operar a Aurea Gold Wallet de forma real, segura e escalável.

A Aurea Gold não será banco próprio no início. A operação financeira real deverá ocorrer via parceiro regulado.

## 1. Informações básicas do parceiro

- [ ] Nome do parceiro:
- [ ] Tipo: PSP / BaaS / IP / banco / gateway / outro
- [ ] CNPJ:
- [ ] Site:
- [ ] Contato comercial:
- [ ] Contato técnico:
- [ ] Possui sandbox?
- [ ] Possui documentação pública?
- [ ] Possui suporte técnico para integração?

## 2. Pix

O parceiro oferece:

- [ ] Recebimento Pix
- [ ] Envio Pix
- [ ] QR Code estático
- [ ] QR Code dinâmico
- [ ] Pix copia e cola
- [ ] Webhook de confirmação
- [ ] Consulta de status da transação
- [ ] Devolução Pix
- [ ] Contestação/MED
- [ ] Limites transacionais
- [ ] Chaves Pix por cliente
- [ ] Pix para PF
- [ ] Pix para PJ

## 3. Conta e saldo

O parceiro oferece:

- [ ] Conta transacional
- [ ] Saldo por cliente
- [ ] Extrato
- [ ] Bloqueio/desbloqueio de saldo
- [ ] Liquidação automática
- [ ] Separação por subcontas
- [ ] Conta para PF
- [ ] Conta para PJ
- [ ] Identificação clara do titular
- [ ] Relatórios financeiros

## 4. KYC e onboarding

O parceiro oferece:

- [ ] KYC PF
- [ ] KYC PJ
- [ ] Validação de CPF
- [ ] Validação de CNPJ
- [ ] Validação documental
- [ ] Biometria/foto, se necessário
- [ ] Status de aprovação
- [ ] Motivo de reprovação
- [ ] Reanálise manual
- [ ] Webhook de mudança de status KYC

## 5. Segurança e compliance

Verificar:

- [ ] O parceiro é regulado/autorizado?
- [ ] Possui política de prevenção a fraude?
- [ ] Possui trilha de auditoria?
- [ ] Possui logs de transações?
- [ ] Possui mecanismo antifraude?
- [ ] Possui suporte para contestação?
- [ ] Possui SLA de incidente?
- [ ] Possui documentação LGPD?
- [ ] Possui contrato de operador/controlador de dados?
- [ ] Possui política de retenção de dados?

## 6. Webhooks

O parceiro oferece:

- [ ] Webhook para Pix recebido
- [ ] Webhook para Pix enviado
- [ ] Webhook para falha/cancelamento
- [ ] Webhook para KYC
- [ ] Webhook para saldo/conta
- [ ] Assinatura/HMAC dos eventos
- [ ] Reenvio de eventos
- [ ] Idempotência de webhook
- [ ] Ambiente sandbox para webhook

## 7. API e integração

Avaliar:

- [ ] Documentação clara
- [ ] SDK oficial
- [ ] API REST
- [ ] Autenticação por token/OAuth/API key
- [ ] Rate limit documentado
- [ ] Ambientes sandbox e produção separados
- [ ] Logs de requisições
- [ ] Erros padronizados
- [ ] Idempotency-Key
- [ ] Versionamento de API
- [ ] SLA de disponibilidade

## 8. Custos

Levantar:

- [ ] Setup inicial
- [ ] Mensalidade
- [ ] Custo por Pix recebido
- [ ] Custo por Pix enviado
- [ ] Custo por conta criada
- [ ] Custo por KYC
- [ ] Custo por webhook/evento
- [ ] Custo por saque/transferência
- [ ] Mínimo mensal
- [ ] Reserva/garantia exigida
- [ ] Prazo de liquidação

## 9. Cartão e expansão futura

O parceiro oferece:

- [ ] Cartão virtual
- [ ] Cartão físico
- [ ] Cartão pré-pago
- [ ] Cartão múltiplo
- [ ] Bloqueio/desbloqueio
- [ ] Limite por cartão
- [ ] Segunda via
- [ ] Tokenização
- [ ] Wallets Apple/Google
- [ ] Tap to Pay
- [ ] Link de pagamento
- [ ] Boleto
- [ ] Cobrança recorrente

## 10. Critérios de aprovação para a Aurea

Parceiro só deve avançar se atender pelo menos:

- [ ] Pix recebido
- [ ] Pix enviado
- [ ] Webhooks confiáveis
- [ ] Conta/saldo por cliente
- [ ] KYC PF/PJ
- [ ] Sandbox funcional
- [ ] Documentação técnica clara
- [ ] Suporte técnico real
- [ ] Custos compatíveis com MVP
- [ ] Segurança/compliance aceitáveis

## 11. Perguntas obrigatórias para reunião

1. Vocês operam como PSP, BaaS, IP ou gateway?
2. Vocês permitem white label ou wallet embarcada?
3. A conta fica em nome do cliente final ou da Aurea?
4. Vocês fazem KYC PF e PJ?
5. Como funciona Pix recebido?
6. Como funciona Pix enviado?
7. Existe webhook assinado?
8. Existe idempotência?
9. Como funciona contestação/MED?
10. Quais são os custos por transação?
11. Existe sandbox completo?
12. Qual SLA de suporte?
13. Qual prazo para homologação?
14. Quais documentos a Aurea precisa apresentar?
15. O que a Aurea pode ou não pode prometer ao cliente final?

## 12. Decisão

Resultado da avaliação:

- [ ] Aprovado para sandbox
- [ ] Aprovado com ressalvas
- [ ] Reprovado
- [ ] Aguardar nova proposta

Observações:

