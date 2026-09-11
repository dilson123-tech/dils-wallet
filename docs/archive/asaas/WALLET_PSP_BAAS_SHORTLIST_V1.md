# Aurea Gold / dils-wallet — Shortlist PSP/BaaS v1

## 1. Objetivo deste documento

Este documento cria uma shortlist inicial de possíveis parceiros PSP/BaaS para a Aurea Gold / dils-wallet.

A Aurea Gold é um app real, comercial, com objetivo de Play Store e renda real. Por isso, este documento não autoriza Pix real, saldo real, liquidação real ou operação financeira real.

A finalidade aqui é organizar candidatos para conversa técnica/comercial, usando os documentos já criados no projeto:

- `docs/WALLET_PARTNER_READINESS_MATRIX_V1.md`
- `docs/WALLET_PRODUCTION_ENV_CHECKLIST_V1.md`
- `docs/WALLET_PSP_BAAS_QUESTIONNAIRE_V1.md`
- `docs/WALLET_PARTNER_CONTACT_SCRIPT_V1.md`

---

## 2. Regra permanente

Não avançar para Pix real, dinheiro real, saldo real, liquidação real ou comprovante real sem:

- PSP/BaaS homologado.
- Contrato/parceria formal.
- KYC/KYB real.
- Compliance.
- Webhook assinado/tokenizado.
- Ledger real separado.
- Reconciliação oficial.
- Plano de incidentes.
- Operação/admin mínima.
- Revisão jurídica, termos de uso e política de privacidade.
- Definição clara de responsabilidade regulatória.

Enquanto isso não existir, a Aurea Gold permanece em demo/sandbox.

---

## 3. Como ler esta shortlist

Esta lista não é recomendação final, não é aprovação jurídica e não é autorização de integração real.

Classificação usada:

- **Prioridade A**: candidato com maior aderência inicial para conversa BaaS/wallet/infra financeira.
- **Prioridade B**: candidato útil para pagamentos, cobrança, Pix, checkout ou API financeira, mas precisa validar se atende wallet/conta/saldo/ledger.
- **Prioridade C**: candidato que pode ser estratégico no futuro, mas exige mais validação ou pode ser mais enterprise.

Critérios de avaliação:

- BaaS/conta digital.
- Pix de entrada.
- Pix de saída.
- KYC/KYB.
- Webhook seguro.
- Idempotência.
- Ledger/saldo/subcontas.
- Reconciliação.
- Sandbox.
- Documentação pública.
- Contrato/parceria.
- Responsabilidade regulatória.
- Suporte técnico.
- SLA.
- Custos.
- Viabilidade para startup/produto em fase inicial.

---

## 4. Shortlist executiva

| Parceiro | Categoria inicial | Prioridade | Por que avaliar | Atenção principal |
|---|---:|---:|---|---|
| Celcoin | BaaS / Core / Pix | A | Forte aderência para BaaS, Pix e infraestrutura de contas | Validar contrato, KYC/KYB, ledger, modelo regulatório e custos |
| Dock | BaaS / Banking / Pix B2B | A | Forte para Banking as a Service, Pix, white label e operação B2B | Validar porte mínimo, contrato, onboarding e requisitos comerciais |
| Zoop | Banking API / BaaS / pagamentos | A/B | Tem Banking API, BaaS e proposta de banco digital com marca do cliente | Validar modelo atual, suporte para wallet e responsabilidade regulatória |
| FitBank | BaaS / Pix API / white label | A/B | Documentação pública de APIs financeiras, Pix, onboarding, saldo/extrato e white label | Validar contrato, operação, suporte, custos e exigências de homologação |
| Stark Bank | Banking API / Pix / pagamentos corporativos | B | API bancária forte para empresas e automações financeiras | Validar se atende modelo de carteira para usuários finais |
| Asaas | API pagamentos / conta digital / cobranças | B | Pode ser bom caminho para cobrança, Pix, pagamentos e operação inicial controlada | Validar se atende wallet/ledger real e modelo regulatório desejado |
| Efí Bank | API Pix / pagamentos / dev friendly | B | Forte para Pix API, cash-in/cash-out, cobrança e conciliação | Validar se atende wallet, conta por usuário, ledger e compliance |
| iugu | Cobrança / Pix / recorrência | B/C | Forte para cobrança, faturas, links, Pix e recorrência | Pode ser mais gateway/cobrança do que BaaS completo |
| Matera | Pix/Core/infra financeira | C | Forte em tecnologia financeira, Pix as a Service e infraestrutura para instituições | Validar se aceita modelo e porte da Aurea no estágio atual |

---

## 5. Ordem recomendada de abordagem

### Primeira onda

1. Celcoin
2. Dock
3. Zoop
4. FitBank

Motivo: parecem mais próximos do modelo BaaS/wallet/infra financeira.

### Segunda onda

5. Stark Bank
6. Asaas
7. Efí Bank

Motivo: podem acelerar Pix, cobrança, pagamentos e APIs financeiras, mas precisam validação de wallet, saldo, conta por usuário, ledger e responsabilidade regulatória.

### Terceira onda

8. iugu
9. Matera

Motivo: úteis, mas podem exigir encaixe mais específico. iugu pode ser mais cobrança/recorrência; Matera pode ser mais enterprise/institucional.

---

## 6. Candidato 1 — Celcoin

### Tipo inicial

BaaS, Core Banking, Pix e infraestrutura financeira.

### Por que entrou na shortlist

A Celcoin se posiciona com Banking as a Service, Core Banking, APIs e Pix. A documentação pública menciona BaaS conectando empresas às APIs e uso de infraestrutura/licença bancária, além de Pix para cash-in e cash-out.

### Pontos para validar

- Modelo de parceria para app financeiro/wallet.
- Quem responde regulatoriamente.
- KYC/KYB.
- Conta individual ou subconta.
- Ledger.
- Saldo por cliente.
- Pix entrada.
- Pix saída.
- Webhook assinado.
- Idempotência.
- Reconciliação.
- Sandbox.
- SLA.
- Tarifas.
- Volume mínimo.
- Requisitos de produção.

### Perguntas prioritárias

- A Aurea pode operar como camada de experiência usando a infraestrutura de vocês?
- Vocês oferecem conta/saldo por cliente final?
- O dinheiro fica custodiado em qual estrutura?
- Existe ledger por cliente?
- Existe webhook assinado/tokenizado?
- Existe conciliação oficial por provider_reference ou transaction_id?
- Quais requisitos para Pix cash-out?
- Quais requisitos de KYC/KYB?
- Qual contrato é necessário?

### Fonte pública de triagem

- https://www.celcoin.com.br/cel_banking/banking-as-a-service/
- https://developers.celcoin.com.br/docs/sobre-o-baas
- https://developers.celcoin.com.br/docs/realizar-um-pix-cash-out

### Status

- Status de contato: pendente.
- Prioridade: A.
- Próxima ação: enviar mensagem curta e solicitar reunião técnica/comercial.

---

## 7. Candidato 2 — Dock

### Tipo inicial

BaaS, Banking, Pix, soluções financeiras B2B e white label.

### Por que entrou na shortlist

A Dock se posiciona como plataforma de Banking as a Service, com soluções de banking, Pix, boletos, Open Finance e serviços financeiros para empresas. A página pública também destaca atuação em Pix B2B e APIs para participantes indiretos.

### Pontos para validar

- Se atende startup/produto em estágio inicial.
- Modelo comercial mínimo.
- Modelo white label.
- Conta digital.
- Pix entrada.
- Pix saída.
- KYC/KYB.
- Ledger.
- Subcontas.
- Regras de compliance.
- Webhook.
- Reconciliação.
- SLA.
- Suporte técnico.
- Processo de homologação.

### Perguntas prioritárias

- Vocês aceitam integração de carteira/app financeiro em fase inicial?
- Existe modelo white label para wallet?
- Existe conta/saldo individual por usuário?
- Quais requisitos regulatórios ficam com a Dock e quais ficam com a Aurea?
- O webhook possui assinatura?
- Como funciona a reconciliação?
- Quais custos mínimos e prazo de homologação?

### Fonte pública de triagem

- https://dock.tech/en/solution/banking/
- https://dock.tech/en/solution/banking/product-pix-a/
- https://dock.tech/

### Status

- Status de contato: pendente.
- Prioridade: A.
- Próxima ação: enviar e-mail profissional e solicitar requisitos comerciais mínimos.

---

## 8. Candidato 3 — Zoop

### Tipo inicial

Banking API, Banking as a Service, pagamentos e serviços financeiros com marca do cliente.

### Por que entrou na shortlist

A documentação pública da Zoop Banking API descreve APIs para acesso a funcionalidades financeiras da plataforma de Banking as a Service. Materiais públicos também falam em banco digital com marca, conta PF/PJ, TED, Pix, pagamento de contas e cartão pré-pago.

### Pontos para validar

- Status atual da oferta Banking/BaaS.
- Se o produto atende wallet com saldo.
- Conta por usuário PF/PJ.
- Pix entrada e saída.
- KYC/KYB.
- Webhook.
- Ledger.
- Reconciliação.
- Modelo regulatório.
- Custos.
- Suporte e homologação.

### Perguntas prioritárias

- A Zoop Banking API atende carteira digital com saldo por usuário?
- Existe conta individual PF/PJ?
- Existe ledger ou extrato transacional por cliente?
- Como funciona o Pix de saída?
- Qual o modelo regulatório?
- Existe contrato específico para app financeiro?
- Quais os requisitos para produção?

### Fonte pública de triagem

- https://docs.zoop.co/v2.5-banking/docs/sobre-o-produto
- https://www.zoop.com.br/blog/pagamento/o-que-e-pix-banking-as-a-service
- https://www.zoop.com.br/

### Status

- Status de contato: pendente.
- Prioridade: A/B.
- Próxima ação: conversar com consultor e validar se a oferta atual atende wallet real.

---

## 9. Candidato 4 — FitBank

### Tipo inicial

BaaS, API financeira, Pix, saldo/extrato, onboarding e white label.

### Por que entrou na shortlist

A documentação pública do FitBank fala em integrações financeiras por API REST, incluindo Pix, boleto, saldo/extrato, onboarding digital, cartão pré-pago e experiência white-label. A documentação também mostra módulos Pix, PixOut, QR Code, consulta de Pix e webhooks.

### Pontos para validar

- Modelo regulatório.
- Contrato.
- KYC/KYB.
- Conta/saldo por cliente.
- Ledger.
- Pix entrada.
- Pix saída.
- Webhook.
- Reconciliação.
- Sandbox.
- Custos.
- SLA.
- Suporte.
- Exigências para produção.

### Perguntas prioritárias

- Vocês atendem carteira digital white label?
- Existe saldo/conta por cliente?
- Existe ledger interno ou extrato reconciliável?
- Como é feita a custódia?
- Webhooks são assinados?
- Existe idempotência para Pix e pagamentos?
- Quais pré-requisitos para homologação?

### Fonte pública de triagem

- https://dev.fitbank.com.br/
- https://dev.fitbank.com.br/docs/1-introdu%C3%A7%C3%A3o
- https://dev.fitbank.com.br/docs/overview
- https://dev.fitbank.com.br/docs/31-generate-pixout

### Status

- Status de contato: pendente.
- Prioridade: A/B.
- Próxima ação: enviar contato técnico/comercial e pedir documentação de homologação.

---

## 10. Candidato 5 — Stark Bank

### Tipo inicial

Banking API, Pix, pagamentos e automação financeira corporativa.

### Por que entrou na shortlist

A Stark Bank possui documentação pública de API bancária e recursos relacionados a Pix/BR Code. Pode ser interessante para automações financeiras e operações empresariais.

### Pontos para validar

- Se atende carteira para usuários finais.
- Se atende conta por cliente.
- Se possui KYC/KYB para clientes finais da Aurea.
- Se oferece ledger/saldo/subcontas.
- Como funciona Pix entrada e saída.
- Como funciona webhook.
- Como funciona reconciliação.
- Modelo regulatório e contrato.

### Perguntas prioritárias

- Vocês atendem modelo de carteira digital para clientes PF/PJ?
- A Aurea poderia criar contas/saldos individuais?
- Existe KYC/KYB integrado?
- Existe ledger?
- Existe reconciliação por transação?
- Existe sandbox?
- Quais requisitos para produção?

### Fonte pública de triagem

- https://starkbank.com/docs/api
- https://starkbank.com/docs/dynamic-brcodes
- https://starkbank.com/

### Status

- Status de contato: pendente.
- Prioridade: B.
- Próxima ação: validar aderência a wallet antes de avançar.

---

## 11. Candidato 6 — Asaas

### Tipo inicial

API de pagamentos, conta digital, cobranças, Pix e automação financeira.

### Por que entrou na shortlist

O Asaas possui API de pagamentos, documentação pública, ambiente de testes/sandbox, Pix, cobrança e recursos de cash-in/cash-out conforme materiais públicos. Pode ser um caminho mais rápido para cobrança e pagamentos, mas não deve ser assumido como BaaS completo sem validação.

### Pontos para validar

- Se atende wallet com saldo por usuário.
- Se permite subcontas ou separação transacional.
- KYC/KYB.
- Ledger.
- Pix entrada.
- Pix saída.
- Webhook assinado.
- Idempotência.
- Reconciliação.
- Whitelabel.
- Contrato e responsabilidades.

### Perguntas prioritárias

- O Asaas atende modelo de carteira digital com saldo por cliente?
- Existe subconta por usuário?
- Existe ledger oficial?
- Existe webhook assinado ou tokenizado?
- Existe Pix cash-out por API?
- Como funciona KYC/KYB?
- O modelo é adequado para app financeiro com marca Aurea?

### Fonte pública de triagem

- https://www.asaas.com/api-de-pagamentos
- https://www.asaas.com/desenvolvedores
- https://docs.asaas.com/docs/visao-geral
- https://docs.asaas.com/docs/pix
- https://docs.asaas.com/docs/cobrancas-via-pix

### Status

- Status de contato: pendente.
- Prioridade: B.
- Próxima ação: avaliar como alternativa de pagamentos/cobranças, sem presumir BaaS completo.

---

## 12. Candidato 7 — Efí Bank

### Tipo inicial

API Pix, pagamentos, cobranças, cash-in/cash-out, split e conciliação.

### Por que entrou na shortlist

A Efí divulga API Pix, Pix Cash-In, Pix Cash-Out, cobranças Pix, split/repasse e conciliação. É forte para integração de pagamentos e pode ser uma alternativa prática para Pix, mas precisa validação de wallet, saldo individual e responsabilidade regulatória.

### Pontos para validar

- Wallet com saldo por cliente.
- Conta por cliente.
- KYC/KYB.
- Ledger.
- Pix entrada.
- Pix saída.
- Split/repasse.
- Conciliação.
- Webhook.
- Assinatura de webhook.
- Idempotência.
- Contrato.
- Homologação.

### Perguntas prioritárias

- A Efí atende carteira digital com saldo por cliente?
- Existe conta/subconta por usuário?
- Existe KYC/KYB integrado?
- Existe ledger oficial?
- O webhook é assinado?
- Como funciona a conciliação?
- Quais requisitos para Pix de saída?
- Quais tarifas e limites?

### Fonte pública de triagem

- https://sejaefi.com.br/efi-pay/api-pix
- https://sejaefi.com.br/efi-pay
- https://sejaefi.com.br/lp/api-de-pagamento-para-software-houses
- https://comunidade.sejaefi.com.br/

### Status

- Status de contato: pendente.
- Prioridade: B.
- Próxima ação: avaliar como alternativa dev friendly para Pix/pagamentos.

---

## 13. Candidato 8 — iugu

### Tipo inicial

Cobrança, pagamentos, Pix, recorrência, faturas e links.

### Por que entrou na shortlist

A iugu oferece infraestrutura de pagamentos, cobrança, Pix, recorrência, faturas e documentação pública de API. Pode servir para cobrança e recebimento, mas precisa validação forte para wallet, saldo real, conta por usuário e ledger.

### Pontos para validar

- Se atende apenas cobrança ou também wallet.
- Conta por usuário.
- Pix entrada.
- Pix saída.
- Transferências.
- KYC/KYB.
- Webhook.
- Reconciliação.
- Ledger.
- Modelo regulatório.
- Custos.
- Suporte.

### Perguntas prioritárias

- A iugu atende modelo de carteira digital ou apenas cobrança/recebíveis?
- Existe saldo por cliente final?
- Existe subconta?
- Existe Pix cash-out?
- Existe KYC/KYB?
- Existe ledger e reconciliação oficial?
- Existe webhook assinado?

### Fonte pública de triagem

- https://www.iugu.com/
- https://www.iugu.com/metodo-pagamento-pix
- https://dev.iugu.com/docs/introdu%C3%A7%C3%A3o
- https://dev.iugu.com/docs/realizar-cobran%C3%A7a-com-pix-por-api
- https://dev.iugu.com/docs/cobrar-com-pix-automatico-por-api

### Status

- Status de contato: pendente.
- Prioridade: B/C.
- Próxima ação: considerar para cobrança/recorrência, não como BaaS principal sem validação.

---

## 14. Candidato 9 — Matera

### Tipo inicial

Infraestrutura financeira, Core Banking, Pix as a Service e tecnologia para instituições.

### Por que entrou na shortlist

A Matera publica conteúdos sobre Pix as a Service, BaaS, embedded finance e infraestrutura financeira. Pode ser relevante, especialmente se a Aurea precisar de tecnologia mais robusta ou parceria mais enterprise.

### Pontos para validar

- Se atende projeto em estágio inicial.
- Se oferece solução direta para wallet/app financeiro.
- Modelo comercial.
- Porte mínimo.
- Integração via API.
- Pix entrada.
- Pix saída.
- Ledger.
- Reconciliação.
- Compliance.
- Suporte e SLA.

### Perguntas prioritárias

- A Matera atende startups/produtos comerciais em fase inicial?
- Existe modelo BaaS/Pix as a Service aplicável à Aurea?
- Qual parceiro regulatório entra na operação?
- Existe sandbox?
- Quais custos e prazos?
- Existe ledger/reconciliação?
- Existe suporte para wallet?

### Fonte pública de triagem

- https://www.matera.com/br/
- https://www.matera.com/br/blog/pix-as-a-service/
- https://www.matera.com/br/blog/baas-x-saas-como-comecar-oferecer-servicos-financeiros/
- https://www.matera.com/br/blog/embedded-finance/

### Status

- Status de contato: pendente.
- Prioridade: C.
- Próxima ação: deixar como opção estratégica, não primeira abordagem.

---

## 15. Matriz rápida de aderência inicial

Escala:

- 5 = muito aderente
- 4 = aderente
- 3 = possível, exige validação
- 2 = fraco para o objetivo atual
- 1 = não recomendado agora

| Parceiro | Wallet/BaaS | Pix entrada | Pix saída | KYC/KYB | Ledger/saldo | Sandbox/docs | Aderência inicial |
|---|---:|---:|---:|---:|---:|---:|---:|
| Celcoin | 5 | 5 | 5 | 4 | 4 | 5 | 4.7 |
| Dock | 5 | 5 | 4 | 4 | 4 | 4 | 4.3 |
| Zoop | 4 | 4 | 4 | 4 | 4 | 4 | 4.0 |
| FitBank | 4 | 5 | 5 | 4 | 4 | 5 | 4.5 |
| Stark Bank | 3 | 4 | 4 | 3 | 3 | 5 | 3.7 |
| Asaas | 3 | 5 | 4 | 3 | 3 | 5 | 3.8 |
| Efí Bank | 3 | 5 | 5 | 3 | 3 | 5 | 4.0 |
| iugu | 2 | 4 | 3 | 3 | 2 | 5 | 3.2 |
| Matera | 4 | 4 | 4 | 4 | 4 | 3 | 3.8 |

Observação: essa matriz é inicial e baseada em triagem pública. A nota real só pode ser definida depois de reunião, documentação técnica, contrato e validação de sandbox oficial.

---

## 16. Perguntas obrigatórias para todos os candidatos

1. Vocês atendem carteira digital/app financeiro com marca própria?
2. A Aurea pode operar como camada de UX/produto usando a infraestrutura de vocês?
3. Quem é o responsável regulatório?
4. Existe contrato formal para esse modelo?
5. Existe KYC/KYB?
6. Existe conta ou subconta por cliente?
7. Existe saldo por cliente?
8. Existe ledger oficial?
9. O dinheiro fica custodiado onde?
10. Existe Pix de entrada?
11. Existe Pix de saída?
12. Existe webhook assinado/tokenizado?
13. Existe idempotência?
14. Existe reconciliação oficial?
15. Existe sandbox?
16. Existe documentação técnica completa?
17. Existe SLA?
18. Existe suporte para homologação?
19. Quais tarifas existem?
20. Existe volume mínimo?
21. Quais requisitos jurídicos existem?
22. Quais requisitos de segurança existem?
23. Quais são os limites operacionais?
24. Como funciona bloqueio por suspeita de fraude?
25. Como funciona incidente operacional?

---

## 17. Critérios para descartar

Descartar ou pausar se o parceiro:

- Não explicar responsabilidade regulatória.
- Não oferecer contrato formal.
- Não tiver documentação técnica.
- Não tiver sandbox.
- Não tiver webhook seguro.
- Não tiver idempotência.
- Não oferecer KYC/KYB quando necessário.
- Não explicar custódia.
- Não permitir reconciliação.
- Não explicar tarifas.
- Não tiver suporte técnico.
- Prometer Pix real sem compliance.
- Incentivar operação informal.
- Não separar homologação de produção.
- Não for claro sobre limites, bloqueios e incidentes.

---

## 18. Próxima ação operacional

### Ação 1

Selecionar 3 primeiros contatos:

1. Celcoin
2. Dock
3. FitBank ou Zoop

### Ação 2

Usar a mensagem curta de:

`docs/WALLET_PARTNER_CONTACT_SCRIPT_V1.md`

### Ação 3

Registrar respostas em documento futuro:

`docs/WALLET_PARTNER_CONTACT_LOG_V1.md`

### Ação 4

Só criar branch técnica de produção depois de receber:

- documentação técnica real;
- requisitos de homologação;
- modelo de autenticação;
- modelo de webhook;
- modelo de KYC/KYB;
- modelo de ledger;
- modelo de reconciliação;
- contrato/minuta;
- tabela de tarifas.

---

## 19. Decisão técnica recomendada

Não criar adapter real ainda.

Motivo:

Sem documentação real do parceiro, qualquer implementação seria chute. O risco é inventar flags, endpoints, status e fluxos que depois não batem com a API oficial.

Próxima branch técnica possível somente após resposta de parceiro:

`feat/wallet-production-safety-guards`

Mas antes dela, mapear variáveis já existentes no projeto para evitar duplicidade ou gambiarra.

---

## 20. Estado deste documento

Versão: v1
Tipo: shortlist operacional/comercial
Status: pronto para orientar primeira rodada de contatos
Pix real: bloqueado
Dinheiro real: bloqueado
Próximo passo: contatar candidatos Prioridade A
