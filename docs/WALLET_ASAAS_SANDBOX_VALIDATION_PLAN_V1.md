# Aurea Gold — Plano de Validação Sandbox Asaas v1

Status: draft
Marco planejado: v0.2.29-wallet-asaas-sandbox-validation-plan
Projeto: Aurea Gold / dils-wallet
Parceiro candidato: Asaas
Prioridade atual: A
Natureza: produto real/comercial, não projeto de estudo.

## 1. Objetivo

Este documento define o plano técnico para validar o ambiente Sandbox do Asaas antes de qualquer implementação produtiva na Aurea Gold / dils-wallet.

O objetivo é testar, de forma controlada e sem dinheiro real, se o Asaas atende aos fluxos mínimos necessários para uma carteira digital com possível modelo BaaS futuro.

Este plano não libera operação real.

## 2. Regra central

A resposta do Asaas é promissora, mas não autoriza produção real.

A Aurea Gold permanece com operação real bloqueada até:

1. validação técnica em Sandbox;
2. revisão dos resultados;
3. conta PJ aprovada;
4. homologação BaaS;
5. preenchimento de Checklist/Playbook;
6. análise regulatória e operacional;
7. contrato BaaS formal;
8. liberação técnica;
9. compliance;
10. revisão jurídica;
11. decisão explícita do Dilson para avançar.

Enquanto isso:

- não criar Pix real;
- não receber Pix real;
- não enviar Pix real;
- não creditar saldo real;
- não criar subconta real;
- não ativar split real;
- não emitir comprovante financeiro real;
- não tratar evento Sandbox como liquidação real.

## 3. Confirmações recebidas do Asaas

O Asaas confirmou por atendimento humano:

- Sandbox pode ser acessado pela conta Asaas em Minha Conta > Integrações > Acessar ambiente Sandbox;
- Sandbox não exige contrato específico ou aprovação prévia;
- conta de testes é criada automaticamente;
- testes devem usar apenas dados fictícios;
- Sandbox permite testar cobranças, Pix, webhooks, subcontas e outros recursos disponíveis;
- Pix de entrada pode usar cobranças com QR Code dinâmico/estático ou recebimento via chave Pix;
- Pix de saída pode usar transferências para outras instituições por chave Pix ou dados bancários;
- API permite consulta de status de cobrança/pagamento;
- API permite consulta de extrato e histórico de transações;
- webhooks usam token no header asaas-access-token;
- Asaas fornece lista de IPs oficiais para restrição de rotas de webhook;
- existem subcontas e split de pagamento;
- modelo recomendado para a Aurea Gold é BaaS com conta PJ principal e subcontas;
- produção BaaS exige homologação;
- processo BaaS envolve Checklist, Playbook, análise, contrato e liberação técnica;
- contrato BaaS será formal e assinado digitalmente.

## 4. Escopo desta validação

A validação Sandbox Asaas deve verificar:

- acesso e criação do ambiente Sandbox;
- leitura da documentação técnica aplicável;
- criação segura de variáveis de ambiente locais;
- proteção de tokens e credenciais;
- criação de cobrança Pix em Sandbox;
- geração de QR Code ou payload Pix Sandbox;
- consulta de status da cobrança;
- recebimento de webhook em rota local/controlada;
- validação do header asaas-access-token;
- tratamento de idempotência;
- reconciliação entre cobrança criada, webhook recebido e status consultado;
- consulta de extrato/histórico Sandbox;
- teste de subcontas Sandbox, se disponível;
- teste de split Sandbox, se disponível;
- registro dos gaps técnicos;
- definição de critérios mínimos para avançar para homologação BaaS.

## 5. Fora do escopo

Este marco não deve:

- implementar Pix real;
- implementar transferência real;
- criar subconta real;
- criar split real;
- criar saldo real;
- alterar ledger real;
- alterar regras financeiras produtivas;
- salvar token real no repositório;
- ativar operação em produção;
- assumir que Sandbox aprovado equivale a homologação BaaS;
- tratar Asaas como parceiro fechado.

## 6. Variáveis de ambiente previstas

Variáveis planejadas para validação futura, sem valores reais no repositório:

- ASAAS_ENV=sandbox
- ASAAS_BASE_URL
- ASAAS_API_KEY
- ASAAS_WEBHOOK_TOKEN
- ASAAS_WEBHOOK_ALLOWED_IPS
- WALLET_PARTNER_PROVIDER=asaas
- WALLET_MODE=partner
- REAL_MONEY_ENABLED=false

Regras obrigatórias:

- nunca commitar tokens;
- nunca colocar chave real em exemplo público;
- nunca misturar token de produção com Sandbox;
- nunca usar conta real de cliente em teste;
- usar apenas dados fictícios;
- revisar logs para garantir que tokens não apareçam em texto puro.

## 7. Fluxos de validação

### 7.1 Acesso ao Sandbox

Validar:

- acesso ao ambiente Sandbox;
- geração de credencial Sandbox;
- URL/base técnica do ambiente;
- documentação mínima de Pix, cobranças, webhooks, extrato, subcontas e split.

Critério de sucesso:

- Sandbox acessível;
- credencial Sandbox gerada;
- nenhuma credencial registrada no código.

### 7.2 Cobrança Pix Sandbox

Validar:

- criação de cobrança Pix com dados fictícios;
- retorno de identificador externo;
- retorno de status inicial;
- geração de QR Code ou payload Pix;
- consulta posterior da cobrança.

Critério de sucesso:

- cobrança criada em Sandbox;
- identificador recebido;
- cobrança consultável por API;
- nenhum saldo real afetado.

### 7.3 Consulta de status

Validar:

- consulta da cobrança pelo identificador Asaas;
- mapeamento dos status Asaas para status interno;
- diferença entre pagamento simulado e liquidação real.

Critério de sucesso:

- status consultável por API;
- resposta suficiente para auditoria e reconciliação.

### 7.4 Webhook Sandbox

Validar:

- configuração de endpoint de webhook Sandbox;
- recebimento de evento;
- presença do header asaas-access-token;
- comparação do token com variável segura local;
- tratamento de replay e idempotência;
- recusa de evento sem token ou com token incorreto.

Critério de sucesso:

- webhook recebido;
- header validado;
- evento salvo de forma auditável;
- replay tratado com segurança.

### 7.5 Reconciliação

Validar cruzamento entre:

- cobrança criada;
- webhook recebido;
- status consultado;
- histórico/extrato Sandbox.

Critério de sucesso:

- cobrança, webhook e status fecham entre si;
- divergências são detectáveis;
- não há movimentação real;
- fluxo permite auditoria.

### 7.6 Extrato e histórico Sandbox

Validar:

- consulta de extrato;
- consulta de histórico por filtros;
- campos úteis para auditoria;
- relação com cobranças e webhooks.

Critério de sucesso:

- extrato/histórico disponível;
- filtros mínimos funcionam;
- dados ajudam na conciliação.

### 7.7 Subcontas Sandbox

Validar:

- se subcontas estão disponíveis no Sandbox;
- criação apenas com dados fictícios, se permitido;
- consulta de status da subconta;
- limites e diferenças entre subconta não-BaaS e BaaS.

Critério de sucesso:

- subcontas testáveis em Sandbox ou documentação clara;
- riscos regulatórios identificados.

### 7.8 Split Sandbox

Validar:

- disponibilidade de split no Sandbox;
- criação de regra fictícia, se permitido;
- associação do split a cobrança Sandbox;
- consulta do resultado;
- campos obrigatórios e limitações.

Critério de sucesso:

- split testável ou documentação suficiente;
- regra de divisão clara;
- rastreabilidade possível.

## 8. Segurança técnica mínima

Antes de qualquer implementação com Asaas, exigir:

- separação explícita entre Sandbox e produção;
- flag interna para eventos Sandbox;
- logs sem tokens;
- validação do asaas-access-token;
- idempotência por evento;
- reconciliação por identificador externo;
- bloqueio de crédito real;
- bloqueio de comprovante real;
- bloqueio de endpoint produtivo sem homologação;
- testes automatizados mínimos;
- revisão manual do diff.

## 9. Critérios para considerar Asaas tecnicamente viável

O Asaas pode ser considerado tecnicamente viável para próxima etapa se:

- Sandbox for acessível e estável;
- cobrança Pix Sandbox funcionar;
- consulta de status funcionar;
- webhook Sandbox funcionar com autenticação;
- reconciliação for possível;
- extrato/histórico ajudarem na auditoria;
- subcontas/split forem testáveis ou documentados de forma suficiente;
- houver separação clara entre Sandbox e produção;
- riscos de token, replay e conciliação estiverem controlados.

## 10. Critérios que ainda bloqueiam produção

Mesmo com Sandbox aprovado, produção continua bloqueada até:

- conta PJ aprovada;
- homologação BaaS solicitada;
- Checklist e Playbook preenchidos;
- análise regulatória e operacional concluída;
- contrato BaaS assinado;
- liberação técnica concedida;
- compliance revisado;
- jurídico revisado;
- política de KYC/KYB definida;
- termos de uso e política de privacidade revisados;
- suporte operacional definido;
- monitoramento e auditoria definidos;
- decisão explícita do Dilson para avançar.

## 11. Resultado esperado deste marco

Ao final deste marco, o repositório deve ter apenas documentação.

Entregáveis:

- plano técnico de validação Sandbox Asaas;
- critérios de sucesso;
- critérios de bloqueio;
- escopo seguro para próximo ciclo;
- nenhuma alteração produtiva;
- nenhuma credencial;
- nenhum Pix real;
- nenhuma subconta real;
- nenhuma movimentação financeira real.

## 12. Próximo marco provável

Se este plano for aprovado, o próximo marco técnico pode ser:

- v0.2.30-wallet-asaas-sandbox-readiness-checklist

Ou, se o ambiente já estiver acessível e validado manualmente:

- v0.2.30-wallet-asaas-sandbox-technical-spike

A decisão deve ser tomada somente depois de revisar o acesso real ao Sandbox e a documentação técnica do Asaas.
