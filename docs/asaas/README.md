# Aurea Gold — Asaas Sandbox Documentation Index

Este é o documento canônico de entrada para toda a documentação relacionada à
integração com o Asaas Sandbox.

## 1. Propósito

Orientar a leitura da documentação Asaas: onde está o estado atual, onde está
o histórico, e em que ordem ler.

## 2. Estado atual resumido

- Sandbox é o único ambiente Asaas habilitado/permitido no estado atual do
  projeto; Production não está habilitada.
- HTTP de saída ao Asaas (cliente, subconta, pagamento): sem transporte
  executável — ver [`HTTP_CLIENT_CONTRACT.md`](./HTTP_CLIENT_CONTRACT.md).
- Preparação PIX local: existe um endpoint runtime local ativo e testado
  para preparação — ver [`DRY_RUN.md`](./DRY_RUN.md).
- Webhook Asaas Sandbox (inbound): implementado, autenticado e testado — ver
  [`WEBHOOKS.md`](./WEBHOOKS.md).
- Subcontas: apenas contrato representacional, nenhuma criada — ver
  [`SUBACCOUNTS.md`](./SUBACCOUNTS.md).
- Dinheiro real: desabilitado por configuração obrigatória — ver
  [`ARCHITECTURE.md`](./ARCHITECTURE.md).
- Onboarding comercial com o Asaas já foi iniciado e está pausado no
  requisito de CNPJ da Aurea Gold, com retomada esperada do mesmo processo
  quando o CNPJ estiver ativo — ver [`PARTNERSHIP.md`](./PARTNERSHIP.md).

Este resumo não substitui os documentos linkados — qualquer detalhe técnico
ou comercial deve ser verificado no documento correspondente.

## 3. Leitura principal — documentos canônicos

| Ordem | Documento | Cobre |
|---|---|---|
| 1 | [`ARCHITECTURE.md`](./ARCHITECTURE.md) | Fronteira Aurea Gold↔Asaas, configuração obrigatória, guards |
| 2 | [`HTTP_CLIENT_CONTRACT.md`](./HTTP_CLIENT_CONTRACT.md) | Contrato representacional da cadeia de criação de cliente |
| 3 | [`SUBACCOUNTS.md`](./SUBACCOUNTS.md) | Modelo de subcontas, split, reconciliação, rate limit |
| 4 | [`DRY_RUN.md`](./DRY_RUN.md) | Preparação PIX local e endpoint runtime de preparação |
| 5 | [`WEBHOOKS.md`](./WEBHOOKS.md) | Recebimento de webhook Asaas — o único fluxo inbound real |
| 6 | [`PARTNERSHIP.md`](./PARTNERSHIP.md) | Estado comercial e onboarding |

## 4. Limites atuais da integração

Nenhuma chamada HTTP de saída ao Asaas é executada hoje; nenhuma subconta é
criada; nenhum dinheiro real é movimentado; produção não está habilitada.
Detalhes e evidência de cada limite estão nos documentos da seção 3 — este
índice não os repete.

## 5. Arquivo histórico

Os 48 documentos que originaram os 6 canônicos acima foram preservados em
[`docs/archive/asaas/`](../archive/asaas/) por valor histórico. Eles **não
representam o estado atual** e podem conter informação superada (datas, URLs,
decisões). Organizados por tema:

### Setup / configuração Sandbox
- [`WALLET_ASAAS_SANDBOX_VALIDATION_PLAN_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_VALIDATION_PLAN_V1.md)
- [`WALLET_ASAAS_SANDBOX_TECHNICAL_SPIKE_PLAN_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_TECHNICAL_SPIKE_PLAN_V1.md)
- [`WALLET_ASAAS_SANDBOX_READINESS_CHECKLIST_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_READINESS_CHECKLIST_V1.md)
- [`WALLET_ASAAS_SANDBOX_ACCESS_NOTES_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_ACCESS_NOTES_V1.md)
- [`WALLET_ASAAS_SANDBOX_TECHNICAL_SPIKE_PREFLIGHT_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_TECHNICAL_SPIKE_PREFLIGHT_V1.md)
- [`WALLET_ASAAS_SANDBOX_ACCESS_CONFIRMATION_NOTES_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_ACCESS_CONFIRMATION_NOTES_V1.md)
- [`WALLET_ASAAS_SANDBOX_TECHNICAL_CONFIRMATION_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_TECHNICAL_CONFIRMATION_V1.md) — documento mais consolidado deste grupo
- [`WALLET_ASAAS_SANDBOX_API_WEBHOOK_NOTES_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_API_WEBHOOK_NOTES_V1.md)
- [`WALLET_ASAAS_SANDBOX_CONFIG_GUARDS_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_CONFIG_GUARDS_V1.md) ⚠️ contém a URL de Sandbox anterior à correção de 11/07/2026 — ver [`ARCHITECTURE.md`](./ARCHITECTURE.md)
- [`WALLET_ASAAS_SANDBOX_ENV_EXAMPLE_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_ENV_EXAMPLE_V1.md)
- [`WALLET_ASAAS_SANDBOX_CLIENT_SKELETON_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_CLIENT_SKELETON_V1.md)
- [`WALLET_ASAAS_SANDBOX_FIRST_SPIKE_PLAN_V1.md`](../archive/asaas/WALLET_ASAAS_SANDBOX_FIRST_SPIKE_PLAN_V1.md) ⚠️ contém a URL de Sandbox anterior à correção de 11/07/2026 — ver [`ARCHITECTURE.md`](./ARCHITECTURE.md)

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

Um aviso de enquadramento histórico está disponível em
[`docs/archive/asaas/README.md`](../archive/asaas/README.md).

## 6. Documentos transversais

[`docs/product-maturity.md`](../product-maturity.md) cobre a maturidade geral
do produto (não específica ao Asaas). Uma seção sua ("Asaas Sandbox Execution
Gate") resume, em nível mais alto, o mesmo estado já detalhado em
[`HTTP_CLIENT_CONTRACT.md`](./HTTP_CLIENT_CONTRACT.md).

## 7. O que NÃO deve ser inferido

- Sandbox funcional não implica Production liberada.
- Onboarding iniciado não implica parceria aprovada.
- Webhook inbound funcional não implica outbound habilitado.
- Um documento arquivado não implica que sua informação ainda é válida —
  verifique sempre o canônico correspondente.

## 8. Manutenção futura

Ao criar ou substituir um documento canônico, atualize a tabela da seção 3.
Ao arquivar um novo documento histórico, adicione-o à seção 5 e não o liste
em nenhum outro lugar.
