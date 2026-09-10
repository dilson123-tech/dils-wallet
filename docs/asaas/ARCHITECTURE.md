# Aurea Gold — Arquitetura da Integração Asaas Sandbox

Este documento descreve o estado atual da integração com o Asaas, como implementada no código deste repositório. Não é um changelog nem um registro de sessões de trabalho — para o histórico incremental, veja os documentos históricos listados em [`docs/asaas/README.md`](./README.md). Esses documentos permanecem no local atual; seu eventual arquivamento é tratado separadamente no ME1-C, ainda não realizado.

## 1. Objetivo da integração

O código atual implementa dois comportamentos distintos, que não devem ser confundidos:

- **HTTP de saída ao Asaas** (criar cliente, cobrança, subconta): preparação de requisições, validação de configuração e guards de segurança, sem transporte HTTP real executável (seção 8).
- **Webhook Sandbox de entrada** (eventos enviados pelo Asaas): implementado e montado no runtime atual da aplicação (seção 9).

Nenhuma operação financeira real está habilitada em nenhum dos dois casos.

## 2. Fronteira técnica Aurea Gold ↔ Asaas

- A Aurea Gold é responsável por: validar configuração local, preparar requisições de saída, validar e processar webhooks recebidos, aplicar guards de segurança.
- O Asaas é responsável por: processar cobranças PIX, gerar QR Codes, emitir eventos de webhook, fornecer o ambiente Sandbox e, futuramente, produção mediante homologação.
- Nenhuma chamada HTTP de saída da Aurea Gold ao Asaas está implementada hoje (seção 8).

Estado comercial, onboarding e homologação do parceiro não são tratados aqui — ver `docs/asaas/PARTNERSHIP.md` (futuro, ME1-B6).

## 3. Modo Sandbox atual

A configuração Asaas aceita pelo código atual é exclusivamente Sandbox. Uma configuração fora desses parâmetros é rejeitada antes de qualquer preparação de requisição.

## 4. Configuração obrigatória

| Variável | Valor exigido | Efeito se ausente/incorreto |
|---|---|---|
| `WALLET_MODE` | `partner` | Configuração rejeitada |
| `WALLET_PARTNER_PROVIDER` | `asaas` | Configuração rejeitada |
| `REAL_MONEY_ENABLED` | `false` | Configuração rejeitada se `true` |
| `ASAAS_ENV` | `sandbox` | Configuração rejeitada se diferente |
| `ASAAS_BASE_URL` | `https://api-sandbox.asaas.com/v3` | Configuração rejeitada se diferente (inclui bloqueio explícito da URL de produção) |
| `ASAAS_API_KEY` | valor não vazio/não-placeholder, mantido fora do Git | Configuração rejeitada se vazio/placeholder |
| `ASAAS_WEBHOOK_TOKEN` | valor não vazio/não-placeholder, mantido fora do Git | Configuração rejeitada se vazio/placeholder |

Consulte `backend/.env.example` para o modelo seguro versionado (sem valores reais).

## 5. Guards de segurança

`load_asaas_sandbox_config()` (`backend/app/partner/asaas_config.py`) é o ponto central de validação utilizado pelo fluxo atual. A função:

- não realiza nenhuma chamada de rede;
- mascara `api_key` e `webhook_token` em `__repr__`;
- expõe apenas presença/ausência (não o valor) desses campos via `safe_summary()`;
- força `real_money_enabled=False` no resultado retornado, independentemente do que a validação de entrada já rejeitou.

## 6. URL Sandbox

A URL Sandbox aceita pelo código atual é:

```
ASAAS_BASE_URL=https://api-sandbox.asaas.com/v3
```

Nota histórica: entre 26/06/2026 e 11/07/2026, o código usava `https://sandbox.asaas.com/api/v3`. Essa URL foi deliberadamente corrigida em 11/07/2026 (commit `a97bef1`). Alguns documentos históricos existentes, anteriores a essa data, ainda citam a URL antiga — não é uma contradição não resolvida, é um registro histórico que precede a correção.

## 7. Client / transport atual

`backend/app/partner/asaas_client.py` define `AsaasSandboxClient` e uma cadeia extensa de dataclasses de preparo (`AsaasPreparedRequest` e variantes específicas por etapa — criação de cliente, subconta, sanitização de resposta/erro, etc.). Cada uma:

- monta metadados de uma requisição (método, URL, payload) sem enviá-la;
- expõe `safe_summary()` com campos booleanos (`can_send_http`, `http_call_executed`, `real_money`) sempre `False`.

## 8. HTTP de saída bloqueado

A inspeção do fluxo atual não encontrou nenhum transporte HTTP executável no caminho de código que prepara requisições ao Asaas (criar cliente, cobrança, subconta ou consultar status) — toda a cadeia de classes em `asaas_client.py` monta metadados e para antes da execução. Como evidência adicional, não há import de bibliotecas HTTP (`httpx`/`requests`) em nenhum arquivo do módulo `partner/`. Isso é uma característica estrutural do client atual, não uma configuração alternável.

## 9. Webhook (referência)

Diferente do HTTP de saída, o recebimento de webhooks do Asaas **está implementado e montado no runtime atual**: `POST /api/v1/partners/asaas/webhooks/sandbox`, com validação do header `asaas-access-token` (`backend/app/api/v1/routes/wallet.py`). Detalhes de payload, eventos e auditoria: ver `docs/asaas/WEBHOOKS.md` (futuro, ME1-B5).

## 10. Subcontas (referência)

O domínio de subcontas possui uma cadeia extensa de classes de preparo em `asaas_client.py` (estrutura, contrato de payload, builder, fixtures sanitizadas, gate de execução manual) — nenhuma cria uma subconta real. Detalhes: ver `docs/asaas/SUBACCOUNTS.md` (futuro, ME1-B3).

## 11. Relação com os demais documentos canônicos

Este documento cobre apenas a arquitetura vigente. Fluxos e contratos em detalhe têm (ou terão) documentos próprios:

- `docs/asaas/HTTP_CLIENT_CONTRACT.md` — futuro, ME1-B2
- `docs/asaas/SUBACCOUNTS.md` — futuro, ME1-B3
- `docs/asaas/DRY_RUN.md` — futuro, ME1-B4
- `docs/asaas/WEBHOOKS.md` — futuro, ME1-B5
- `docs/asaas/PARTNERSHIP.md` — futuro, ME1-B6

Ver o mapa completo em [`docs/asaas/README.md`](./README.md).
