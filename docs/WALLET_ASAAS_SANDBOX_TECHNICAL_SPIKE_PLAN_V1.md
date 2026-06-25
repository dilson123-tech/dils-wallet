# Aurea Gold — Plano de Spike Técnico Sandbox Asaas v1

Status: draft
Marco planejado: v0.2.31-wallet-asaas-sandbox-technical-spike-plan
Projeto: Aurea Gold / dils-wallet
Parceiro candidato: Asaas
Prioridade atual: A
Natureza: produto real/comercial, não projeto de estudo.

## 1. Objetivo

Este documento define o plano do primeiro spike técnico controlado com o Sandbox Asaas.

O objetivo é validar, com o menor risco possível, se a API Sandbox do Asaas pode atender aos fluxos técnicos mínimos da Aurea Gold / dils-wallet antes de qualquer integração produtiva.

Este plano ainda não implementa a integração.

## 2. Regra central

Este marco é apenas planejamento técnico.

Permite planejar:

- leitura da documentação;
- desenho do fluxo técnico;
- definição dos endpoints a testar;
- definição dos arquivos candidatos para um spike futuro;
- critérios de sucesso e bloqueio.

Não permite:

- Pix real;
- saldo real;
- subconta real;
- split real;
- token real no Git;
- alteração produtiva;
- operação financeira real;
- comprovante financeiro real;
- promessa de produção.

## 3. Base documental anterior

Este plano se apoia nos documentos:

- `docs/WALLET_PARTNER_CONTACT_LOG_V1.md`
- `docs/WALLET_ASAAS_SANDBOX_VALIDATION_PLAN_V1.md`
- `docs/WALLET_ASAAS_SANDBOX_READINESS_CHECKLIST_V1.md`
- `docs/WALLET_SANDBOX_CYCLE_RUNBOOK.md`

A ordem correta é:

1. resposta BaaS registrada;
2. plano de validação Sandbox criado;
3. checklist de prontidão criado;
4. plano de spike técnico criado;
5. somente depois, spike técnico controlado.

## 4. Escopo do spike futuro

O spike técnico futuro deve validar apenas ambiente Sandbox.

Escopo permitido:

- carregar variáveis Sandbox localmente;
- consultar status básico da configuração;
- criar cobrança Pix Sandbox;
- consultar cobrança criada;
- receber ou simular webhook Sandbox;
- validar header `asaas-access-token`;
- testar idempotência;
- testar reconciliação técnica;
- consultar extrato/histórico Sandbox se disponível;
- estudar subcontas Sandbox se disponível;
- estudar split Sandbox se disponível.

Escopo proibido:

- ativar produção;
- usar credencial de produção;
- criar cobrança real;
- receber dinheiro real;
- enviar Pix real;
- criar subconta real;
- ativar split real;
- creditar saldo real;
- gerar comprovante real;
- alterar ledger real;
- alterar regras financeiras produtivas.

## 5. Variáveis planejadas

Variáveis previstas para o spike futuro:

- `ASAAS_ENV=sandbox`
- `ASAAS_BASE_URL`
- `ASAAS_API_KEY`
- `ASAAS_WEBHOOK_TOKEN`
- `ASAAS_WEBHOOK_ALLOWED_IPS`
- `WALLET_PARTNER_PROVIDER=asaas`
- `WALLET_MODE=partner`
- `REAL_MONEY_ENABLED=false`

Regras:

- nenhum valor real deve entrar no repositório;
- nenhum token deve aparecer em Markdown;
- nenhum token deve aparecer em log;
- nenhum print com token deve entrar em issue ou PR;
- `.env` local deve continuar fora do Git;
- produção e Sandbox devem ficar explicitamente separados.

## 6. Endpoints candidatos do spike futuro

Os endpoints exatos devem ser confirmados na documentação oficial do Asaas antes de codar.

Categorias candidatas:

- criação de cobrança;
- cobrança Pix;
- consulta de cobrança;
- webhooks;
- extrato;
- histórico;
- subcontas;
- split;
- transferências Sandbox, somente se claramente disponíveis e seguras.

Nenhum endpoint produtivo deve ser usado.

## 7. Arquivos candidatos para avaliação futura

O spike técnico futuro pode exigir análise destes pontos do projeto:

- configuração do backend;
- rotas de wallet;
- services/adapters de parceiro;
- modelos de idempotência;
- fluxo de reconciliação sandbox;
- testes automatizados;
- documentação de ambiente.

Arquivos candidatos para inspeção futura, sem obrigação de alteração neste marco:

- `backend/app/config.py`
- `backend/app/api/v1/routes/wallet.py`
- `backend/app/models/idempotency.py`
- `docs/WALLET_SANDBOX_CYCLE_RUNBOOK.md`

Se novos arquivos forem necessários, devem ser criados com separação clara entre Sandbox Asaas e produção.

## 8. Estratégia técnica recomendada

O spike futuro deve ser pequeno e reversível.

Sequência recomendada:

1. criar branch própria;
Se novos arquivos forem necessários, devem ser criados com separação clara entre Sandbox Asaas e produção.
3. adicionar configuração Sandbox Asaas sem valores reais;
4. criar camada isolada de adapter Asaas Sandbox, se necessário;
5. criar teste mínimo de configuração;
6. testar criação de cobrança Sandbox;
7. testar consulta de status;
8. testar webhook com validação de token;
9. testar idempotência;
10. testar reconciliação técnica;
11. documentar resultado;
12. bloquear produção explicitamente.

## 9. Critérios de sucesso do spike futuro

O spike futuro pode ser considerado bem-sucedido se:

- ambiente Sandbox Asaas for acessível;
- credenciais Sandbox ficarem fora do Git;
- cobrança Pix Sandbox puder ser criada;
- cobrança puder ser consultada;
- webhook puder ser recebido ou validado em fluxo controlado;
- header `asaas-access-token` puder ser validado;
- replay/idempotência for tratado;
- reconciliação técnica for possível;
- logs não expuserem token;
- nenhum saldo real for alterado;
- nenhum comprovante real for gerado;
- produção continuar bloqueada.

## 10. Critérios de bloqueio

O spike futuro deve ser bloqueado se:

- houver risco de usar produção por engano;
- a credencial Sandbox não estiver segura;
- documentação do Asaas estiver insuficiente;
- webhook não tiver validação clara;
- token aparecer em log;
- não houver identificador confiável para reconciliação;
- Sandbox não separar claramente operação de teste e produção;
- subcontas exigirem produção real;
- split exigir produção real;
- qualquer chamada puder movimentar dinheiro real.

## 11. Resultado esperado deste marco

Ao final deste marco, o repositório deve conter apenas documentação.

Entregáveis:

- plano de spike técnico Sandbox Asaas;
- escopo permitido;
- escopo proibido;
- variáveis planejadas;
- endpoints candidatos;
- arquivos candidatos;
- critérios de sucesso;
- critérios de bloqueio;
- nenhuma credencial;
- nenhum código produtivo;
- nenhuma operação real.

## 12. Próximo marco provável

Se este plano for aprovado, o próximo marco poderá ser:

- `v0.2.32-wallet-asaas-sandbox-technical-spike`

Ou, se o acesso ao Sandbox ainda não estiver pronto:

- `v0.2.32-wallet-asaas-sandbox-access-notes`

A decisão deve depender do acesso real ao Sandbox, da documentação técnica disponível e da segurança das credenciais.
