# Aurea Gold Wallet — Dados Mínimos para Parceiro Financeiro

## Objetivo

Mapear os dados mínimos que a Aurea Gold precisa coletar, armazenar e trafegar para operar como wallet real via parceiro financeiro, PSP ou BaaS.

## Princípio

Coletar apenas o necessário para operação, KYC, segurança, compliance e suporte.

A Aurea não deve prometer operação financeira real sem parceiro regulado.

## 1. Dados do usuário PF

- Nome completo
- CPF
- Data de nascimento
- E-mail
- Telefone
- Endereço
- Status KYC
- ID interno Aurea
- ID no parceiro
- Data de criação
- Data de atualização
- Consentimento LGPD

## 2. Dados do usuário PJ

- Razão social
- Nome fantasia
- CNPJ
- CNAE, quando exigido
- Porte
- Endereço comercial
- E-mail
- Telefone
- Representante legal
- CPF do representante
- Status KYC PJ
- ID interno Aurea
- ID no parceiro

## 3. Dados de conta/wallet

- ID da wallet Aurea
- ID da conta no parceiro
- Tipo: demo ou partner
- Moeda: BRL
- Status: active, pending, blocked, closed
- Saldo disponível
- Saldo bloqueado
- Data de criação
- Última sincronização

## 4. Dados Pix

- ID interno da transação
- ID/referência do parceiro
- Tipo: entrada ou saída
- Valor
- Chave Pix
- Descrição
- Status
- Idempotency-Key
- QR Code, quando aplicável
- Pix copia e cola, quando aplicável
- Data de criação
- Data de confirmação
- Payload bruto do parceiro

## 5. Dados de webhook

- Provider
- Event type
- Provider reference
- Status
- Payload bruto
- Assinatura/HMAC
- Data recebida
- Processado: sim/não
- Tentativas de processamento
- Erro, se houver

## 6. Dados de segurança

- Limite por transação
- Limite diário
- Último login
- Dispositivo, quando aplicável
- IP, quando aplicável
- Eventos sensíveis
- Logs de auditoria

## 7. Dados LGPD

- Termo aceito
- Política aceita
- Data/hora do aceite
- Versão do termo
- Versão da política
- Base legal
- Consentimento para tratamento
- Solicitação de exclusão/exportação

## 8. Fora de escopo inicial

- Score de crédito próprio
- Empréstimo próprio
- Rendimento próprio
- Cartão próprio sem parceiro
- Dados sensíveis além do necessário
