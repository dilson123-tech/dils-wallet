# Aurea Gold — Asaas Sandbox Env Example v1

Status: draft
Marco planejado: v0.2.36-wallet-asaas-sandbox-env-example
Projeto: Aurea Gold / dils-wallet
Parceiro candidato: Asaas
Prioridade atual: A
Natureza: documentação segura de variáveis de ambiente.

## 1. Objetivo

Este documento registra um modelo seguro de variáveis de ambiente para um futuro spike técnico com Asaas Sandbox.

Este marco não adiciona credenciais reais.
Este marco não implementa integração.
Este marco não altera produção.

## 2. Regra central

Nenhum valor real deve ser registrado neste documento.

É proibido registrar:

- API key real;
- token real;
- senha;
- Wallet ID;
- chave Pix real;
- QR Code real;
- dado bancário real;
- dado de cliente real;
- URL com credencial;
- segredo de produção;
- segredo de Sandbox.

## 3. Observação sobre frontend

O arquivo atual `aurea-gold-client/.env.example` é do frontend.

Variáveis com prefixo `VITE_` podem ser expostas no navegador.

Por isso, credenciais do Asaas nunca devem entrar em variável `VITE_`.

Proibido no frontend:

- `VITE_ASAAS_API_KEY`;
- `VITE_ASAAS_WEBHOOK_TOKEN`;
- `VITE_WALLET_ID`;
- qualquer token;
- qualquer segredo.

## 4. Modelo seguro para backend/local

Exemplo seguro, apenas com placeholders:

    ASAAS_ENV=sandbox
    ASAAS_BASE_URL=<CONFIRMAR_URL_BASE_SANDBOX_OFICIAL_ASAAS>
    ASAAS_API_KEY=<DEFINIR_APENAS_NO_ENV_LOCAL_SEGURO>
    ASAAS_WEBHOOK_TOKEN=<DEFINIR_APENAS_NO_ENV_LOCAL_SEGURO>
    ASAAS_WEBHOOK_ALLOWED_IPS=<CONFIRMAR_LISTA_OFICIAL_SE_NECESSARIO>
    WALLET_PARTNER_PROVIDER=asaas
    WALLET_MODE=partner
    REAL_MONEY_ENABLED=false

## 5. Regras para `.env` local

O arquivo `.env` local pode existir apenas na máquina do desenvolvedor ou no ambiente seguro de deploy.

Regras:

- `.env` não deve ser versionado;
- `.env.local` não deve ser versionado;
- `.env.*` não deve ser versionado se contiver segredo;
- API key real deve ficar apenas em ambiente seguro;
- token de webhook real deve ficar apenas em ambiente seguro;
- qualquer log deve mascarar segredos;
- produção deve continuar bloqueada.

## 6. Regras para `.env.example`

Um futuro `.env.example` versionado pode conter somente:

- nomes de variáveis;
- valores falsos;
- placeholders claros;
- comentários de segurança;
- `REAL_MONEY_ENABLED=false`.

Um futuro `.env.example` versionado não pode conter:

- API key real;
- token real;
- Wallet ID;
- senha;
- segredo;
- endpoint com credencial;
- payload real;
- dado bancário;
- dado de cliente.

## 7. Variáveis obrigatórias para futuro spike

Variáveis mínimas candidatas:

- `ASAAS_ENV`
- `ASAAS_BASE_URL`
- `ASAAS_API_KEY`
- `ASAAS_WEBHOOK_TOKEN`
- `ASAAS_WEBHOOK_ALLOWED_IPS`
- `WALLET_PARTNER_PROVIDER`
- `WALLET_MODE`
- `REAL_MONEY_ENABLED`

## 8. Travas obrigatórias

O futuro código deve bloquear execução se:

- `ASAAS_ENV` não for `sandbox`;
- `REAL_MONEY_ENABLED` não for `false`;
- `ASAAS_BASE_URL` estiver vazia;
- `ASAAS_API_KEY` estiver ausente;
- `ASAAS_API_KEY` aparecer em log;
- `ASAAS_WEBHOOK_TOKEN` aparecer em log;
- URL base parecer produtiva;
- qualquer flag tentar habilitar dinheiro real.

## 9. Separação Sandbox e produção

Sandbox e produção devem ser tratados como ambientes diferentes.

Regras:

- chave Sandbox não deve ser misturada com produção;
- token Sandbox não deve ser misturado com produção;
- URL Sandbox deve ser confirmada antes de código;
- URL produtiva não deve ser usada neste ciclo;
- produção segue bloqueada até homologação BaaS, compliance, revisão jurídica, contrato formal e decisão explícita do Dilson.

## 10. Critério de aceitação deste marco

Este marco será aceito se:

- apenas documentação for adicionada;
- nenhum segredo for registrado;
- nenhum código de integração for criado;
- o modelo de variáveis estiver claro;
- o frontend permanecer sem credenciais sensíveis;
- a trava `REAL_MONEY_ENABLED=false` estiver documentada;
- o próximo marco puder criar um `.env.example` real somente se for seguro.

## 11. Próximo marco provável

Se este modelo for aprovado, o próximo marco poderá ser:

- `v0.2.37-wallet-asaas-sandbox-env-example-file`

Ou, se ainda faltar confirmação técnica:

- `v0.2.37-wallet-asaas-sandbox-api-webhook-followup-notes`

O primeiro código de integração deve continuar bloqueado até as variáveis, URL base, endpoints e webhooks estarem confirmados.
