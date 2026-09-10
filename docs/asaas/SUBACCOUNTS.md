# Aurea Gold — Subcontas Asaas Sandbox

Este documento descreve o estado técnico atual do domínio de subcontas na integração Asaas, como implementado em `backend/app/partner/asaas_client.py`. Não é um changelog — para o histórico incremental, veja os documentos históricos listados em [`docs/asaas/README.md`](./README.md). O eventual arquivamento desses documentos é tratado separadamente no ME1-C, ainda não realizado.

Estado comercial/onboarding do parceiro (incluindo o processo de onboarding Asaas já iniciado e interrompido na etapa de exigência do CNPJ da Aurea Gold) não é tratado aqui — ver `docs/asaas/PARTNERSHIP.md` (futuro, ME1-B6). Esse fato histórico não deve ser interpretado como autorização técnica para criar subcontas.

## 1. Propósito

Definir o contrato de dados e o estado atual de preparação para uma futura criação de subconta Asaas (`POST /accounts`), incluindo os conceitos relacionados de split, reconciliação de income e rate limiting — sem implementar nenhum desses comportamentos em runtime.

## 2. Status executivo atual

No estado atual do código, **nenhuma subconta Asaas é criada pelo runtime**, **não existe split implementado**, **não existe reconciliação de income Asaas implementada**, e a classificação de rate limit, embora funcionalmente real, **não tem nenhum consumidor**. Toda a cadeia de subcontas é uma sequência de contratos/dataclasses representacionais, seguindo o mesmo padrão já documentado em [`docs/asaas/HTTP_CLIENT_CONTRACT.md`](./HTTP_CLIENT_CONTRACT.md) para a cadeia de cliente.

## 3. Modelo técnico atual

A investigação identificou **11 classes/objetos relevantes** no domínio investigado (subcontas + split + reconciliação + rate limit) em `asaas_client.py`:

- **10 classes** compõem a cadeia representacional específica de subconta, encadeadas por composição (cada uma incorpora a anterior como campo): guarda de estrutura, contrato de payload, builder de payload, fixture sanitizada, contrato de sanitização de resposta, implementação de sanitização de resposta, gate de execução manual, preflight de tentativa controlada, contrato de registro de tentativa, e tentativa controlada pós-execução.
- **1 classe adicional**, `AsaasSanitizedRateLimitAndErrorResult` (com o classificador `classify_rate_limit_and_error_response()`), pertence ao mesmo domínio investigado mas não é nomeada como "Subaccount" — é um classificador de rate limit/erro de propósito mais geral.

Nenhum estágio da cadeia de subconta executa uma requisição HTTP real. Nenhum estágio tem consumidor fora dos testes automatizados. O classificador de rate limit é a única peça funcionalmente real entre as 11 (ver seção 8), mas também sem consumidor.

## 4. Preparação de subconta

Não existe hoje um método runtime chamado `prepare_create_subaccount` nem qualquer endpoint runtime de criação ou preparação de subconta.

O que existe é um contrato de payload (`AsaasSandboxSubaccountPayloadContractResult`) e um builder de payload (`AsaasSandboxSubaccountPayloadBuilderGuardResult`) que, juntos, modelam — sem executar — o formato de uma futura requisição `POST /accounts`:

- o contrato de payload exige campos como `name`, `email`, `cpfCnpj`, `mobilePhone`, `incomeValue`, `address`, `addressNumber`, `province`, `postalCode`, e proíbe explicitamente que `apiKey`, `walletId`, `id` ou `onboardingUrl` apareçam no corpo da requisição;
- o payload builder monta um `template_payload` inteiramente sintético (dados fictícios), nunca um payload com dado real de cliente.

O payload builder apenas modela/prepara esses dados sintéticos — não executa HTTP, não envia nada, e não há nenhum caminho de código que o conecte a um endpoint real da aplicação.

## 5. Dados e identificadores

Identificadores sensíveis (`apiKey`, `walletId`, `id` da conta, `onboardingUrl`) nunca aparecem por valor em nenhum resumo seguro — são sempre reduzidos a um booleano de presença (`api_key_present`, `wallet_id_present`, etc.). A única fixture de resposta existente usa exclusivamente valores literais mascarados (`"<masked>"`), nunca dados reais ou gerados dinamicamente.

## 6. Split

Split é descrito apenas em documentação histórica (regras de negócio, campos esperados, cuidados de segurança). **Não existe nenhuma classe, campo ou função de split no código atual.** Não há nem uma modelagem inerte — é ausência total.

## 7. Reconciliação

Reconciliação entre income Asaas (`GET /v3/accounts/me/income`) e webhooks `PAYMENT_RECEIVED` é descrita apenas em documentação histórica. **Nenhum código implementa essa comparação.**

Atenção: existe, sim, um endpoint real e montado — `GET /api/v1/wallet/pix/sandbox-reconciliation/{provider_reference}` — mas ele pertence ao adapter interno de demonstração (`WALLET_PARTNER_PROVIDER=sandbox`), não ao Asaas, e reconcilia eventos de webhook PIX genéricos já registrados. **Não deve ser confundido com a reconciliação de subconta Asaas descrita acima** — são dois conceitos distintos que compartilham o nome "reconciliação sandbox".

## 8. Rate limit

`AsaasSandboxClient.classify_rate_limit_and_error_response()` é a única peça genuinamente funcional desta cadeia: dado um `status_code` e headers reais (`ratelimit-limit`, `ratelimit-remaining`, etc.), ela efetivamente os parseia e classifica. Ainda assim, **nenhum código do sistema a invoca** — não há nenhuma chamada HTTP real cuja resposta chegaria a este classificador.

## 9. Controlled attempt / operator review

Os conceitos de runbook, revisão de operador e template de evidência são checklists textuais — listas de itens que um humano deveria confirmar manualmente. Nenhum deles inspeciona programaticamente o estado real do ambiente, do Git ou de uma resposta HTTP (que não existe). Nenhuma combinação de confirmações registradas nesses objetos habilita execução HTTP; os campos de habilitação (`can_send_http`, `can_create_subaccount`, `operator_approval_to_execute_http`) permanecem `False` de forma fixa.

## 10. Segurança / fail-closed

Toda a configuração de base (Sandbox, `REAL_MONEY_ENABLED=false`, credenciais fora do Git) herda as mesmas guardas fail-closed documentadas em [`docs/asaas/ARCHITECTURE.md`](./ARCHITECTURE.md), implementadas e testadas. As proteções específicas de subconta (payload proibido, resposta mascarada) são modeladas no contrato, mas nunca exercitadas contra um payload ou resposta reais, pois nenhum existe hoje.

## 11. O que NÃO existe hoje

- Nenhuma subconta Asaas real criada pelo runtime.
- Nenhum método runtime `prepare_create_subaccount` e nenhum endpoint runtime que prepare ou tente criar subconta.
- Nenhum transporte HTTP executável para subcontas.
- Nenhuma persistência de identificador de subconta Asaas em banco/modelo.
- Nenhuma implementação de split (zero código).
- Nenhuma implementação de reconciliação Asaas de income (o endpoint de reconciliação existente pertence a outro domínio, seção 7).
- Nenhum consumidor do classificador de rate limit, apesar de ele ser funcional isoladamente.

## 12. Guardrails para evolução futura

Qualquer implementação futura de subconta real, split ou reconciliação Asaas exigiria:

- patch e revisão dedicados, com validação explícita;
- restrição a ambiente Sandbox;
- nenhuma alteração para Production como parte dessa mudança;
- nenhuma habilitação de dinheiro real;
- uso da URL Sandbox atual correta (`https://api-sandbox.asaas.com/v3`, ver `ARCHITECTURE.md`), nunca a citada nos documentos históricos;
- clareza explícita, em qualquer novo código, sobre a diferença entre reconciliação de subconta Asaas e a reconciliação do adapter interno de demonstração já existente (seção 7).

Este documento não propõe nem agenda essa implementação.

## 13. Relação com os demais documentos canônicos

- Arquitetura geral e configuração: [`docs/asaas/ARCHITECTURE.md`](./ARCHITECTURE.md)
- Contrato do cliente HTTP (cadeia `/customers`): [`docs/asaas/HTTP_CLIENT_CONTRACT.md`](./HTTP_CLIENT_CONTRACT.md)
- Eventos de webhook e evidência de compliance relacionada: `docs/asaas/WEBHOOKS.md` (futuro, ME1-B5)
- Estado comercial/onboarding, incluindo a etapa do CNPJ: `docs/asaas/PARTNERSHIP.md` (futuro, ME1-B6)

Ver o mapa completo em [`docs/asaas/README.md`](./README.md).
