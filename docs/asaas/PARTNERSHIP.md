# Aurea Gold — Parceria e Onboarding Comercial com o Asaas

Este documento descreve o estado comercial/operacional da relação entre a Aurea Gold e o Asaas como parceiro candidato, e sua fronteira com o estado técnico já documentado nos demais canônicos. Não é um changelog — para o histórico completo de contato e avaliação de parceiros, veja os documentos históricos listados em [`docs/asaas/README.md`](./README.md). O eventual arquivamento é tratado separadamente no ME1-C, ainda não realizado.

## 1. Propósito

Registrar o estado da parceria comercial com o Asaas, distinguindo claramente o que está documentado no repositório do que é estado operacional confirmado diretamente pelo responsável do projeto, e evitar que qualquer um dos dois seja confundido com prontidão técnica ou aprovação comercial.

## 2. Escopo

Este documento cobre exclusivamente a relação comercial/onboarding com o Asaas. Não descreve novamente a arquitetura técnica, o contrato outbound, subcontas, preparação PIX ou webhooks — esses já têm documentos canônicos próprios (seção 13).

## 3. Status comercial atual

O Asaas foi um de nove candidatos PSP/BaaS avaliados pela Aurea Gold (Celcoin, Dock, FitBank, Zoop, Stark Bank, Asaas, Efí Bank, iugu, Matera), inicialmente classificado como Prioridade B em uma shortlist comparativa. Após contato real (17/06) e resposta técnica detalhada de dois atendentes do Asaas, sua prioridade foi elevada para A, com status registrado como "próximos passos do BaaS confirmados".

O Asaas confirmou o modelo recomendado para a Aurea Gold como BaaS, com conta PJ principal e subcontas, e descreveu seu processo de homologação BaaS em quatro etapas: entendimento do modelo de negócio (com envio de checklist e playbook pelo Asaas), análise e validação regulatória/operacional, formalização da parceria (contrato assinado digitalmente) e liberação técnica. Um dos pré-requisitos informados pelo Asaas para esse processo é conta Pessoa Jurídica com cadastro aprovado.

## 4. Status técnico relacionado

Em paralelo ao processo comercial, uma extensa validação técnica em Sandbox foi conduzida e está consolidada nos demais documentos canônicos: configuração e guards de segurança ([`ARCHITECTURE.md`](./ARCHITECTURE.md)), contrato representacional de HTTP de saída ([`HTTP_CLIENT_CONTRACT.md`](./HTTP_CLIENT_CONTRACT.md)), modelo de subcontas ([`SUBACCOUNTS.md`](./SUBACCOUNTS.md)), preparação local de PIX ([`DRY_RUN.md`](./DRY_RUN.md)) e recebimento funcional de webhooks ([`WEBHOOKS.md`](./WEBHOOKS.md)). Nenhum desses documentos técnicos afirma outbound habilitado, dinheiro real ativo ou Production Asaas em uso.

## 5. Histórico do onboarding

- O Asaas foi contatado comercialmente e respondeu com detalhes técnicos (Pix de entrada/saída, Sandbox completo, webhooks, subcontas, split, modelo BaaS recomendado).
- A partir dessa resposta, um plano técnico de validação em Sandbox foi criado — correspondendo à extensa documentação técnica já consolidada nos canônicos B1 a B5.
- **Estado operacional confirmado pelo responsável do projeto** (não registrado como tal em nenhum documento do repositório): o processo comercial de onboarding/parceria com o Asaas avançou e foi interrompido especificamente quando passou a exigir o CNPJ da nova empresa Aurea Gold, que ainda não existia naquele momento.

## 6. Ponto exato de interrupção

O processo foi pausado no requisito de CNPJ da Aurea Gold como empresa. Não há, no repositório, registro de em qual das quatro etapas do processo de homologação BaaS isso ocorreu, e este documento não presume essa granularidade.

## 7. Dependência do CNPJ

A retomada do onboarding depende da disponibilidade do CNPJ ativo da Aurea Gold. Este documento não afirma, e não deve ser lido como afirmando, que esse CNPJ já está ativo, qual é seu número, sua data de abertura ou sua situação cadastral.

## 8. Próximo passo após CNPJ ativo

Assim que o CNPJ da Aurea Gold estiver ativo, o próximo passo comercial é retomar o processo Asaas já iniciado, no ponto em que foi interrompido pelo requisito de CNPJ — não reiniciar o cadastro do zero, salvo se o próprio Asaas indicar essa necessidade ao ser contatado novamente. A ação exata (tela, formulário, canal) dependerá do estado real da conta Asaas nesse momento futuro e não é presumida aqui.

## 9. O que ainda NÃO está confirmado/aprovado

Até o estado conhecido nesta consolidação:

- não há confirmação de homologação BaaS concluída;
- não há registro ou confirmação de contrato de parceria assinado;
- não há evidência de conta Production Asaas liberada;
- não há autorização confirmada para operação com dinheiro real;
- não há confirmação de conta PJ da Aurea Gold aprovada junto ao Asaas.

Essas ausências de confirmação não devem ser transformadas em afirmações sobre o painel ou sistemas externos não consultados nesta tarefa.

## 10. Separação Sandbox × Production

Toda a validação técnica realizada até hoje ocorreu exclusivamente em ambiente Sandbox do Asaas. Nenhuma evidência técnica ou comercial neste repositório indica uso de Production. Sandbox aprovado ou funcional não equivale a Production liberada.

## 11. Separação comercial × técnica

Progresso comercial (resposta detalhada do Asaas, elevação de prioridade) não equivale a progresso técnico de execução (que permanece bloqueado por design, ver `HTTP_CLIENT_CONTRACT.md`). Da mesma forma, progresso técnico (webhook inbound funcional, testado) não equivale a progresso comercial (homologação, contrato). As duas trilhas evoluem de forma independente.

## 12. Guardrails

- Parceria comercial não equivale a integração técnica pronta.
- Sandbox não equivale a Production.
- Onboarding iniciado não equivale a aprovação.
- Webhook inbound funcional não equivale a outbound habilitado.
- CNPJ ativo não habilita automaticamente dinheiro real.
- Qualquer ativação de Production exigirá revisão própria, separada deste documento.
- Qualquer efeito financeiro real exigirá aprovação técnica, comercial e operacional específica.
- Segredos (API keys, tokens) permanecem fora do Git em qualquer etapa deste processo.

## 13. Relação com os demais documentos canônicos

- Arquitetura geral e configuração: [`docs/asaas/ARCHITECTURE.md`](./ARCHITECTURE.md)
- Contrato do cliente HTTP de saída: [`docs/asaas/HTTP_CLIENT_CONTRACT.md`](./HTTP_CLIENT_CONTRACT.md)
- Subcontas: [`docs/asaas/SUBACCOUNTS.md`](./SUBACCOUNTS.md)
- Preparação PIX local: [`docs/asaas/DRY_RUN.md`](./DRY_RUN.md)
- Webhooks inbound: [`docs/asaas/WEBHOOKS.md`](./WEBHOOKS.md)

Ver o mapa completo em [`docs/asaas/README.md`](./README.md).

## 14. Fontes e limites

As seções 3 a 5 (status comercial, histórico até a resposta técnica do Asaas) são sustentadas por `docs/WALLET_PARTNER_CONTACT_LOG_V1.md`, `docs/WALLET_PSP_BAAS_SHORTLIST_V1.md` e `docs/WALLET_PARTNER_CONTACT_CHANNELS_AND_OUTREACH_V1.md`, todos rastreados neste repositório.

A informação de que o onboarding foi interrompido especificamente pelo requisito de CNPJ da Aurea Gold (seções 5 a 8) é um estado operacional confirmado diretamente pelo responsável do projeto durante a elaboração deste documento — não há registro textual equivalente em nenhum arquivo do repositório até a data desta consolidação. Futuras atualizações deste documento devem substituir essa informação por evidência documental assim que ela existir.
