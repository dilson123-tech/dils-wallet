# Aurea Gold Wallet — Contrato Técnico do Partner Adapter

## Objetivo

Este documento descreve o contrato interno da Aurea Gold para integração com parceiro financeiro, PSP ou BaaS.

A Aurea não deve acoplar suas rotas diretamente a um fornecedor específico.

Toda integração financeira real deve passar por uma camada de adapter.

## Estrutura criada

Backend:

- `backend/app/partner/types.py`
- `backend/app/partner/base.py`
- `backend/app/partner/demo_adapter.py`
- `backend/app/partner/registry.py`
- `backend/app/partner/__init__.py`

## Modos da wallet

- `demo`: modo atual/lab, sem dinheiro real.
- `partner`: futuro modo com parceiro financeiro real.

## Operações obrigatórias do adapter

Todo adapter financeiro deve implementar:

### 1. `get_balance`

Consulta saldo disponível do usuário.

Deve retornar:

- user_id;
- saldo disponível;
- moeda;
- provider;
- modo;
- payload bruto opcional.

### 2. `create_pix_payment`

Cria cobrança Pix para recebimento.

Deve suportar:

- user_id;
- valor;
- descrição;
- identificador externo;
- QR Code;
- copia e cola;
- referência do provedor;
- status.

### 3. `send_pix`

Executa envio Pix.

Deve suportar:

- user_id;
- valor;
- chave Pix;
- descrição;
- idempotency key;
- referência do provedor;
- status.

### 4. `get_statement`

Consulta extrato financeiro.

Deve retornar lista padronizada de movimentações:

- referência;
- valor;
- direção: credit/debit;
- status;
- descrição;
- payload bruto opcional.

### 5. `handle_webhook`

Processa evento recebido do parceiro.

Deve suportar:

- provider;
- tipo do evento;
- referência do provedor;
- status;
- payload bruto.

## Status padronizados

Aurea usa os seguintes status internos:

- `pending`
- `processing`
- `confirmed`
- `failed`
- `canceled`
- `rejected`

## Regra crítica

Nenhuma rota da Aurea deve depender diretamente de API externa de parceiro.

Fluxo correto:

Aurea Route
↓
Aurea Service
↓
Partner Adapter
↓
PSP/BaaS/Parceiro

## Adapter demo

O adapter demo:

- não movimenta dinheiro real;
- não representa saldo real;
- não gera cobrança Pix real;
- não envia Pix real;
- serve para desenvolvimento, QA, apresentação e separação segura de fluxo.

## Próxima etapa

Após este contrato, a próxima etapa é criar uma camada de serviço interna que use o adapter sem alterar as rotas Pix atuais.

Somente depois disso a Aurea deve implementar adapter sandbox de um parceiro real.
