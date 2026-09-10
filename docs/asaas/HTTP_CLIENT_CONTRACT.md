# Aurea Gold — Contrato do Client HTTP Asaas (Cliente)

Este documento descreve o contrato técnico atual para a futura primeira chamada HTTP de saída ao Asaas (criação de cliente, `POST /customers`), como implementado em `backend/app/partner/asaas_client.py`. Não é um changelog — para o histórico incremental de cada etapa, veja os documentos históricos listados em [`docs/asaas/README.md`](./README.md). O eventual arquivamento desses documentos é tratado separadamente no ME1-C, ainda não realizado.

## 1. Propósito

Definir, de forma centralizada, o contrato de dados que qualquer futura implementação de transporte HTTP real para `POST /customers` deveria respeitar — sem implementar esse transporte.

## 2. Status executivo atual

No estado atual do código, **não existe nenhum caminho executável que envie uma requisição HTTP real ao Asaas** para criar um cliente. A cadeia de classes descrita abaixo modela metadados, contratos e checklists — nenhuma delas abre uma conexão de rede. Isso foi confirmado por inspeção direta do código (ausência de bibliotecas HTTP importadas no caminho alcançável, e ausência de qualquer consumidor fora dos testes automatizados).

## 3. Fluxo lógico atual

1. **Preparação** — `AsaasSandboxClient.prepare_create_customer()` monta um `AsaasPreparedRequest` (método, URL, payload) sem enviá-lo.
2. **Cadeia de gates de contrato** — uma sequência de classes (`AsaasFirstCustomerHttp*Result`) encadeadas por composição, cada uma incorporando a anterior como campo, definindo o contrato de request, response, erro, sanitização e envelope esperado de uma futura implementação.
3. **Gates de "autorização"** — reconhecem frases de confirmação textual específicas, mas **nenhuma combinação de frases habilita execução**; todos os campos de habilitação (`can_send_http`, `adapter_enabled`, `execution_enabled`, `ready_for_http_execution`) permanecem `False` de forma fixa.
4. **Boundary final e readiness gate** — checklists de revisão humana, não verificações programáticas contra o estado real do sistema.

Nenhum estágio chama o próximo automaticamente; são objetos de dados independentes, não um pipeline de execução.

## 4. Objetos/contratos principais

| Objeto | Papel |
|---|---|
| `AsaasPreparedRequest` | Metadados de uma requisição preparada (método, URL, payload, `http_call_executed=False`) |
| `AsaasFirstCustomerHttpBlockedAdapterContractResult` | Contrato de request/response/error esperado para `POST /customers` |
| `AsaasFirstCustomerHttpResponseSanitizerContractResult` | Campos permitidos/bloqueados de uma futura resposta |
| `AsaasFirstCustomerHttpErrorSanitizerContractResult` | Campos permitidos/bloqueados de um futuro erro, com categorias de erro sanitizadas |
| `AsaasFirstCustomerHttpSanitizedResultEnvelopeContractResult` | Formato do envelope de sucesso/erro que uma futura resposta sanitizada deveria ter |
| `AsaasFirstCustomerHttpSanitizedSuccessErrorFixtureContractResult` | Exemplos fixos (fixtures) do formato esperado |
| `AsaasFirstCustomerHttpAdapterBoundaryFinalContractResult` | Define, no contrato, quais contratos anteriores devem estar satisfeitos antes de uma eventual implementação de adapter |

## 5. Cadeia de gates (nomes preservados, natureza esclarecida)

Os seguintes nomes existem no código como classes/métodos, cada um reconhecendo uma frase de confirmação textual distinta: *client gate, transport adapter gate, manual execution approval gate, disabled adapter shell, explicit enable preflight, runtime enable contract, runtime switch guard, execution gate contract*.

**Nenhum desses elementos altera o comportamento de execução do sistema.** São modelos de um futuro protocolo de autorização em camadas — reconhecem a presença de uma string específica e registram esse reconhecimento em um campo booleano, mas os campos que efetivamente controlariam execução (`can_send_http`, `execution_enabled`, `adapter_enabled`) permanecem `False` de forma fixa no código atual, independentemente do input.

## 6. Sanitização de resposta e erro

Os contratos definem os formatos, campos permitidos/bloqueados e fixtures de sanitização, mas o fluxo atual não processa nenhuma resposta HTTP real do Asaas.

- **Resposta de sucesso**: campos permitidos (`id`, `name`, `cpfCnpj`, `email`, `mobilePhone`); campos bloqueados (`access_token`, `api_key`, `webhook_token`, `wallet_id`, `headers`, `raw`, `provider_raw`).
- **Erro**: campos permitidos (`status_code`, `provider_error_code`, `safe_message`, `retryable`, `category`); campos bloqueados (os mesmos acima + `stacktrace`, `request_body`).

Como nenhuma resposta ou erro real é produzido hoje, esta sanitização nunca foi exercida contra um dado dinâmico — apenas contra as fixtures estáticas descritas na seção 7.

## 7. Result envelope e fixtures

Formato de envelope de sucesso e erro definidos como contrato (campos como `ok`, `operation`, `provider`, `environment`, `http_status_class`), com fixtures sanitizadas fixas (`sanitized_customer_reference: "asaas_customer_sandbox_fixture_redacted"`, `error_category: "provider_rejected_or_unavailable"`) usadas apenas em testes.

## 8. Boundary final

`AsaasFirstCustomerHttpAdapterBoundaryFinalContractResult` declara, no contrato, o nome do caller interno previsto para uma eventual implementação futura (`first_customer_http_sanitized_execution_handler`), e a lista completa de contratos anteriores que deveriam estar válidos antes de qualquer implementação de adapter. Isso é intenção/modelagem contratual, não autorização executável — não há adapter implementado hoje para verificar contra essa lista, nem qualquer mecanismo que restrinja execução a esse caller.

## 9. Configuração relacionada

A configuração que este contrato pressupõe (URL Sandbox, `WALLET_MODE`, `REAL_MONEY_ENABLED`, etc.) está documentada em [`docs/asaas/ARCHITECTURE.md`](./ARCHITECTURE.md). Não é repetida aqui.

## 10. Fail-closed

Todas as proteções de configuração (`WALLET_MODE`, `WALLET_PARTNER_PROVIDER`, `REAL_MONEY_ENABLED`, `ASAAS_ENV`, URL Sandbox/produção, presença de credenciais) são implementadas em `asaas_config.py` e cobertas por testes parametrizados que exercitam cada rejeição individualmente. As "aprovações manuais" da cadeia de gates também são testadas nos dois sentidos (frase presente/ausente), confirmando que seu efeito sobre a execução é nulo em ambos os casos.

## 11. O que NÃO existe hoje

- Nenhum transporte HTTP executável (`httpx`/`requests`/`urllib`/`aiohttp`/SDK Asaas) no caminho alcançável pela integração Asaas.
- Nenhum consumidor de rota que instancie qualquer classe `AsaasFirstCustomerHttp*` fora dos testes automatizados — a cadeia `FIRST_CUSTOMER_HTTP` não possui consumidor no runtime atual.
- Nenhuma verificação programática do "readiness gate" ou do "first controlled attempt" contra o estado real do ambiente — são checklists de dataclass com campos fixos.
- Nenhuma continuação documentada além desta cadeia (o marco seguinte planejado, `first-customer-http-operator-decision-gate`, nunca foi criado).

## 12. Guardrails para qualquer mudança futura de transporte

Os itens abaixo são regras de governança que qualquer eventual mudança futura de transporte deveria seguir — não uma afirmação de que existe hoje um caminho técnico pronto para ser habilitado:

- qualquer implementação de transporte HTTP real exigiria patch e revisão dedicados, com validação explícita;
- restrita a ambiente Sandbox;
- nenhuma alteração para Production como parte dessa mudança;
- nenhuma habilitação de dinheiro real;
- manutenção de todas as proteções fail-closed já existentes;
- uso da URL Sandbox atual correta (`https://api-sandbox.asaas.com/v3`, ver `ARCHITECTURE.md`), nunca a citada nos documentos históricos.

Este documento não propõe nem agenda essa implementação.

## 13. Relação com os demais documentos canônicos

- Arquitetura geral e configuração: [`docs/asaas/ARCHITECTURE.md`](./ARCHITECTURE.md)
- O runtime atual monta outros endpoints Asaas fora da cadeia `FIRST_CUSTOMER_HTTP` descrita aqui — recebimento e auditoria de webhook, status de parceiro, e um endpoint de preparação de saída que instancia `AsaasSandboxClient` e usa `prepare_create_pix_payment`, um método separado (opera em `/payments`, não em `/customers`) que também não executa HTTP real. Detalhes desses fluxos: `docs/asaas/DRY_RUN.md` e `docs/asaas/WEBHOOKS.md` (futuros, ME1-B4 e ME1-B5).
- Estado comercial/onboarding do parceiro — incluindo o processo de onboarding Asaas já iniciado e interrompido na etapa do CNPJ, que aparece aqui apenas como referência para tratamento futuro — pertence a `docs/asaas/PARTNERSHIP.md` (futuro, ME1-B6) e não é aprofundado neste documento técnico.

Ver o mapa completo em [`docs/asaas/README.md`](./README.md).
