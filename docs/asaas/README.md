# Aurea Gold — Asaas Sandbox Documentation Index

Este é o documento canônico de entrada para toda a documentação relacionada à integração com o Asaas Sandbox. O estado técnico e comercial atual está consolidado nos 6 documentos canônicos deste diretório (`ARCHITECTURE.md`, `HTTP_CLIENT_CONTRACT.md`, `SUBACCOUNTS.md`, `DRY_RUN.md`, `WEBHOOKS.md`, `PARTNERSHIP.md`). Os 48 documentos históricos que deram origem a esses canônicos foram arquivados em `docs/archive/asaas/` (ME1-C) — preservados por valor histórico, sem representar necessariamente o estado atual — e estão organizados abaixo por tema. `docs/product-maturity.md` permanece em `docs/` (não é um documento histórico específico do Asaas).

## Status atual real (confirmado por inspeção de código em 2026-09-10)

- **Chamadas HTTP de saída ao Asaas (criar cliente, subconta, pagamento): bloqueadas/não implementadas.** Todo o código em `backend/app/partner/asaas_client.py` (36 classes) é uma cadeia de gates/contratos que nunca executa uma requisição HTTP real (`can_send_http=False`, `http_call_executed=False` em todas as classes).
- **Webhook receiver do Asaas Sandbox: implementado e montado no runtime atual da aplicação** em `POST /api/v1/partners/asaas/webhooks/sandbox`, com histórico de auditoria em `GET /api/v1/partners/asaas/webhooks/sandbox/audit-history`.
- **Dinheiro real: não habilitado no estado atual.** `REAL_MONEY_ENABLED` é validado como obrigatoriamente `false` em `backend/app/partner/asaas_config.py`.
- **Integração Asaas de saída:** somente Sandbox no estado atual. A URL de produção do Asaas é explicitamente bloqueada pelo código.

### URL Sandbox oficial (correção)

A URL Sandbox realmente usada pelo código e por `backend/.env.example` é:

```
ASAAS_BASE_URL=https://api-sandbox.asaas.com/v3
```

⚠️ Alguns documentos mais antigos desta pasta ([`WALLET_ASAAS_SANDBOX_CONFIG_GUARDS_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_CONFIG_GUARDS_V1.md), [`WALLET_ASAAS_SANDBOX_FIRST_SPIKE_PLAN_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_FIRST_SPIKE_PLAN_V1.md)) mencionam `https://sandbox.asaas.com/api/v3`, que **não é** a URL aceita pelo código atual. Use sempre o valor acima.

## Mapa de documentos por tema

### Setup / configuração Sandbox
- [`WALLET_ASAAS_SANDBOX_VALIDATION_PLAN_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_VALIDATION_PLAN_V1.md)
- [`WALLET_ASAAS_SANDBOX_TECHNICAL_SPIKE_PLAN_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_TECHNICAL_SPIKE_PLAN_V1.md)
- [`WALLET_ASAAS_SANDBOX_READINESS_CHECKLIST_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_READINESS_CHECKLIST_V1.md)
- [`WALLET_ASAAS_SANDBOX_ACCESS_NOTES_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_ACCESS_NOTES_V1.md)
- [`WALLET_ASAAS_SANDBOX_TECHNICAL_SPIKE_PREFLIGHT_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_TECHNICAL_SPIKE_PREFLIGHT_V1.md)
- [`WALLET_ASAAS_SANDBOX_ACCESS_CONFIRMATION_NOTES_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_ACCESS_CONFIRMATION_NOTES_V1.md)
- [`WALLET_ASAAS_SANDBOX_TECHNICAL_CONFIRMATION_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_TECHNICAL_CONFIRMATION_V1.md) — documento mais consolidado deste grupo
- [`WALLET_ASAAS_SANDBOX_API_WEBHOOK_NOTES_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_API_WEBHOOK_NOTES_V1.md)
- [`WALLET_ASAAS_SANDBOX_CONFIG_GUARDS_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_CONFIG_GUARDS_V1.md) ⚠️ contém a URL desatualizada acima
- [`WALLET_ASAAS_SANDBOX_ENV_EXAMPLE_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_ENV_EXAMPLE_V1.md)
- [`WALLET_ASAAS_SANDBOX_CLIENT_SKELETON_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_CLIENT_SKELETON_V1.md)
- [`WALLET_ASAAS_SANDBOX_FIRST_SPIKE_PLAN_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_FIRST_SPIKE_PLAN_V1.md) ⚠️ contém a URL desatualizada acima

### Dry-run (PIX / pagamentos)
- [`WALLET_ASAAS_SANDBOX_CUSTOMER_DRY_RUN_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_CUSTOMER_DRY_RUN_V1.md)
- [`WALLET_ASAAS_SANDBOX_FIRST_HTTP_CALL_PREFLIGHT_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_FIRST_HTTP_CALL_PREFLIGHT_V1.md)
- [`WALLET_ASAAS_SANDBOX_FIRST_HTTP_CALL_RUNBOOK_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_FIRST_HTTP_CALL_RUNBOOK_V1.md)
- [`WALLET_ASAAS_SANDBOX_MANUAL_EXECUTION_GATE_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_MANUAL_EXECUTION_GATE_V1.md)
- [`WALLET_ASAAS_SANDBOX_PAYMENT_DRY_RUN_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_PAYMENT_DRY_RUN_V1.md)
- [`WALLET_ASAAS_SANDBOX_PAYMENT_STATUS_DRY_RUN_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_PAYMENT_STATUS_DRY_RUN_V1.md)
- [`WALLET_ASAAS_SANDBOX_PIX_QR_CODE_DRY_RUN_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_PIX_QR_CODE_DRY_RUN_V1.md)
- [`WALLET_ASAAS_SANDBOX_FULL_DRY_RUN_FLOW_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_FULL_DRY_RUN_FLOW_V1.md) — resumo consolidado deste grupo

### Cadeia de gates — primeira chamada HTTP ao cliente (histórico incremental)
- [`WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_CLIENT_GATE_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_CLIENT_GATE_V1.md)
- [`WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_TRANSPORT_REVIEW_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_TRANSPORT_REVIEW_V1.md)
- [`WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_TRANSPORT_SKELETON_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_TRANSPORT_SKELETON_V1.md)
- [`WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_TRANSPORT_ADAPTER_GATE_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_TRANSPORT_ADAPTER_GATE_V1.md)
- [`WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_BLOCKED_ADAPTER_CONTRACT_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_BLOCKED_ADAPTER_CONTRACT_V1.md)
- [`WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_MANUAL_EXECUTION_APPROVAL_GATE_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_MANUAL_EXECUTION_APPROVAL_GATE_V1.md)
- [`WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_DISABLED_ADAPTER_SHELL_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_DISABLED_ADAPTER_SHELL_V1.md)
- [`WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_ERROR_SANITIZER_CONTRACT_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_ERROR_SANITIZER_CONTRACT_V1.md)
- [`WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_PRE_EXECUTION_SAFETY_REVIEW_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_PRE_EXECUTION_SAFETY_REVIEW_V1.md)
- [`WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_RESPONSE_SANITIZER_CONTRACT_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_RESPONSE_SANITIZER_CONTRACT_V1.md)
- [`WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_EXECUTION_GATE_CONTRACT_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_EXECUTION_GATE_CONTRACT_V1.md)
- [`WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_EXPLICIT_ENABLE_PREFLIGHT_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_EXPLICIT_ENABLE_PREFLIGHT_V1.md)
- [`WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_RUNTIME_ENABLE_CONTRACT_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_RUNTIME_ENABLE_CONTRACT_V1.md)
- [`WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_RUNTIME_SWITCH_GUARD_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_RUNTIME_SWITCH_GUARD_V1.md)
- [`WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_SANITIZED_EXECUTION_HANDLER_CONTRACT_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_SANITIZED_EXECUTION_HANDLER_CONTRACT_V1.md)
- [`WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_SANITIZED_RESULT_ENVELOPE_CONTRACT_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_SANITIZED_RESULT_ENVELOPE_CONTRACT_V1.md)
- [`WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_SANITIZED_SUCCESS_ERROR_FIXTURE_CONTRACT_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_SANITIZED_SUCCESS_ERROR_FIXTURE_CONTRACT_V1.md)
- [`WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_ADAPTER_BOUNDARY_FINAL_CONTRACT_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_ADAPTER_BOUNDARY_FINAL_CONTRACT_V1.md)
- [`WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_FINAL_MANUAL_EXECUTION_RUNBOOK_READINESS_GATE_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_FINAL_MANUAL_EXECUTION_RUNBOOK_READINESS_GATE_V1.md)
- [`WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_FIRST_CONTROLLED_SANDBOX_ATTEMPT_PREPARATION_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_FIRST_CUSTOMER_HTTP_FIRST_CONTROLLED_SANDBOX_ATTEMPT_PREPARATION_V1.md) — estado mais avançado desta cadeia (ainda sem execução HTTP real)

### Subcontas / webhooks de compliance
- [`WALLET_ASAAS_SANDBOX_WEBHOOK_COMPLIANCE_EVIDENCE_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_WEBHOOK_COMPLIANCE_EVIDENCE_V1.md)
- [`WALLET_ASAAS_SANDBOX_SUBACCOUNTS_SPLIT_RECONCILIATION_RATE_LIMIT_READINESS_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_SUBACCOUNTS_SPLIT_RECONCILIATION_RATE_LIMIT_READINESS_V1.md)
- [`WALLET_ASAAS_SANDBOX_SUBACCOUNT_FIRST_CONTROLLED_ATTEMPT_RUNBOOK_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_SUBACCOUNT_FIRST_CONTROLLED_ATTEMPT_RUNBOOK_V1.md)
- [`WALLET_ASAAS_SANDBOX_SUBACCOUNT_FIRST_CONTROLLED_ATTEMPT_OPERATOR_REVIEW_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_SUBACCOUNT_FIRST_CONTROLLED_ATTEMPT_OPERATOR_REVIEW_V1.md)
- [`WALLET_ASAAS_SANDBOX_SUBACCOUNT_FIRST_CONTROLLED_ATTEMPT_EVIDENCE_TEMPLATE_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_SUBACCOUNT_FIRST_CONTROLLED_ATTEMPT_EVIDENCE_TEMPLATE_V1.md) — estado mais avançado desta cadeia (mais recente de toda a documentação Asaas)

### Onboarding / parceria (não específico ao Asaas)
- [`WALLET_PARTNER_CONTACT_LOG_V1.md`](../archive/asaas/WALLET_PARTNER_CONTACT_LOG_V1.md)
- [`WALLET_PSP_BAAS_SHORTLIST_V1.md`](../archive/asaas/WALLET_PSP_BAAS_SHORTLIST_V1.md)
- [`WALLET_PARTNER_CONTACT_CHANNELS_AND_OUTREACH_V1.md`](../archive/asaas/WALLET_PARTNER_CONTACT_CHANNELS_AND_OUTREACH_V1.md)

### Maturidade / histórico transversal
- [`product-maturity.md`](../product-maturity.md) — contém histórico/changelog relacionado ao Asaas; a redundância com o README.md da raiz será tratada separadamente em ME1-D.

## Limites deste documento

Este README organiza e contextualiza os 48 documentos históricos arquivados em `docs/archive/asaas/` (ME1-C) e o documento de maturidade transversal (`product-maturity.md`, não movido). A consolidação de conteúdo desses históricos nos 6 documentos canônicos foi feita em ME1-B1 a ME1-B6. Uma reorganização editorial mais ampla deste índice (por exemplo, destacar os 6 canônicos como leitura primária) permanece em aberto para ME1-D.
