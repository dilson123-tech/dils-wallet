# Aurea Gold / dils-wallet — Partner Presentation Readiness v1

## 1. Objetivo deste documento

Este documento consolida a posição atual da Aurea Gold / dils-wallet para apresentação a possíveis parceiros PSP/BaaS.

Ele não substitui os documentos técnicos já existentes. A função dele é servir como material ponte para conversa executiva e técnica com parceiros financeiros, mostrando:

- o que é a Aurea Gold;
- o que já está pronto;
- o que está intencionalmente bloqueado;
- o que depende do parceiro financeiro;
- quais perguntas precisam ser respondidas antes de qualquer dinheiro real;
- qual é o próximo caminho para homologação.

## 2. Regra-mãe da Aurea Gold

A Aurea Gold é um produto financeiro real em construção para mercado.

Não é projeto de estudo.
Não é carteira fake.
Não é simulação enganosa.
Não é maquininha improvisada.
Não deve liberar Pix real, saldo real, pagamento real, boleto real, cartão real, comprovante real ou liquidação real sem parceiro PSP/BaaS homologado.

A regra central permanece:

> Segurança antes de dinheiro real.

Enquanto não houver parceiro homologado, contrato, KYC/KYB, compliance, webhook seguro, ledger separado, reconciliação oficial, revisão jurídica e operação mínima, a carteira deve continuar em modo demo/sandbox.

## 3. Estado atual do produto

A Aurea Gold já possui uma base funcional e visual avançada para demonstração responsável.

Estado atual validado:

- UX mobile premium aprovada como base visual.
- Home/Conta compactada e padronizada.
- Abas Conta, Pix, Gestão, Pagar e Mais com navegação interna premium.
- Tela de planos com apresentação comercial premium.
- Blocos de segurança, sandbox, limites e auditoria preservados.
- Pix sandbox estruturado para simulação técnica.
- Valor demonstrativo do Pix sandbox zerado para R$ 0,00.
- Bloqueios de dinheiro real preservados.
- Separação conceitual entre demo, sandbox e produção real.

Últimos marcos oficiais:

- `v0.2.18-wallet-pay-internal-navigation`
- `v0.2.19-wallet-premium-mobile-spacing`
- `v0.2.20-wallet-final-visual-polish`

## 4. O que já está pronto

### 4.1 Produto e interface

A Aurea Gold já possui interface mobile com padrão premium, incluindo:

- Home/Conta;
- Pix;
- Gestão;
- Pagar;
- Mais;
- Planos;
- cards internos;
- navegação com botão voltar;
- labels de demo/sandbox;
- área de suporte;
- acessos rápidos;
- blocos de auditoria e segurança.

### 4.2 Sandbox técnico

Já existe ciclo sandbox/documental para:

- cobrança Pix sandbox;
- webhook sandbox;
- reconciliação sandbox;
- histórico/auditoria sandbox;
- painel Mais com Pix sandbox;
- avisos explícitos de que não há movimentação real.

### 4.3 Preparação para parceiro

Já existem documentos internos para apoiar conversa com parceiro:

- matriz de prontidão;
- questionário PSP/BaaS;
- shortlist de candidatos;
- roteiro de contato;
- log de contatos;
- checklist de produção;
- auditoria de prontidão real;
- runbook sandbox.

## 5. O que está intencionalmente bloqueado

Os seguintes recursos permanecem bloqueados por segurança:

- Pix real;
- pagamento real;
- boleto real;
- cartão real;
- saldo real;
- comprovante real;
- liquidação real;
- alteração de saldo real;
- operação financeira em produção;
- cobrança real de cliente;
- saque ou movimentação bancária real.

Esses bloqueios não são bugs.

São travas de segurança necessárias até o parceiro financeiro estar homologado.

## 6. O que depende do parceiro PSP/BaaS

Para transformar a Aurea Gold de carteira em prontidão para carteira real operacional, o parceiro precisa fornecer ou viabilizar:

### 6.1 Pix de entrada

- criação de cobrança Pix real;
- QR Code real;
- copia e cola real;
- status de pagamento;
- expiração;
- cancelamento;
- identificação do pagador quando aplicável.

### 6.2 Pix de saída

- envio Pix real;
- validação de chave;
- limites;
- autenticação;
- confirmação;
- comprovante;
- status final da transação.

### 6.3 Saldo

- consulta de saldo real;
- saldo disponível;
- saldo bloqueado;
- atualização confiável;
- separação por conta/subconta, se aplicável.

### 6.4 Extrato

- extrato real;
- filtros por período;
- tipo de transação;
- identificação de entrada/saída;
- status;
- conciliação.

### 6.5 Webhooks

- webhooks assinados;
- validação de assinatura;
- idempotência;
- reprocessamento seguro;
- logs;
- tratamento de eventos duplicados.

### 6.6 Ledger e reconciliação

- ledger interno separado;
- conciliação com parceiro;
- divergências;
- estorno;
- falha parcial;
- auditoria técnica;
- trilha de eventos.

### 6.7 KYC/KYB e compliance

- validação de pessoa física;
- validação de pessoa jurídica;
- documentos;
- análise de risco;
- limites operacionais;
- bloqueios;
- prevenção a fraude;
- LGPD;
- termos e responsabilidades.

## 7. Fluxos planejados com parceiro homologado

Quando houver parceiro aprovado, a Aurea poderá evoluir para:

- Pix ativo via parceiro homologado;
- saldo real atualizado pelo parceiro;
- cobranças reais;
- pagamentos reais;
- comprovantes reais;
- reconciliação real;
- auditoria operacional;
- limites por perfil;
- KYC/KYB real;
- relatórios financeiros;
- gestão para PF/PJ;
- planos comerciais com checkout seguro.

## 8. Como a comunicação muda quando houver parceiro

### Hoje — demo/sandbox

A linguagem correta é:

- “Modo demonstração”
- “Sem movimentar dinheiro real”
- “Pix real bloqueado”
- “Operação real depende de parceiro homologado”
- “Comprovante real bloqueado”
- “Saldo demonstrativo”

### Futuro — produção com parceiro

A linguagem deverá mudar para:

- “Pix ativo via parceiro homologado”
- “Saldo atualizado pela infraestrutura oficial”
- “Comprovante gerado pelo parceiro”
- “Movimentação sujeita a limites e validações”
- “Operação monitorada e reconciliada”
- “Ambiente de produção”

Essa troca deve ser feita apenas quando a operação real estiver juridicamente, tecnicamente e operacionalmente aprovada.

## 9. Requisitos mínimos antes de produção real

Antes de qualquer liberação real, a Aurea precisa validar:

- contrato com parceiro;
- escopo de responsabilidade;
- tarifas;
- SLA;
- documentação técnica;
- sandbox oficial;
- homologação;
- KYC/KYB;
- webhook assinado;
- ledger real;
- reconciliação;
- logs/auditoria;
- plano de incidentes;
- suporte operacional;
- termos de uso;
- política de privacidade;
- revisão jurídica.

## 10. Roteiro de demonstração para parceiro

A apresentação deve seguir esta ordem:

1. Explicar que a Aurea é produto financeiro real em construção.
2. Mostrar que dinheiro real está bloqueado por segurança.
3. Demonstrar a Home/Conta.
4. Demonstrar Pix em modo seguro.
5. Demonstrar Gestão.
6. Demonstrar Pagar.
7. Demonstrar Mais, incluindo KYC/KYB, limites, sandbox e auditoria.
8. Mostrar tela de planos como proposta comercial.
9. Explicar ciclo sandbox.
10. Explicar o que falta para produção real.
11. Apresentar perguntas técnicas ao parceiro.
12. Definir próximos passos de homologação.

## 11. Perguntas essenciais ao parceiro

### Integração

- Quais APIs estão disponíveis?
- Há sandbox oficial?
- A documentação é pública ou privada?
- Como funciona autenticação?
- Há ambiente de homologação?
- Há SDK ou somente API REST?

### Pix

- Suporta Pix cobrança?
- Suporta Pix saída?
- Suporta QR Code dinâmico?
- Suporta copia e cola?
- Suporta consulta de status?
- Suporta cancelamento/expiração?

### Webhook

- Webhook é assinado?
- Como validar assinatura?
- Há retry?
- Há idempotência?
- Quais eventos são enviados?
- Como tratar eventos fora de ordem?

### Saldo e ledger

- Existe conta própria, subconta ou conta de pagamento?
- Quem é o custodiante?
- Como consultar saldo?
- Como reconciliar saldo?
- Existe extrato oficial?

### Compliance

- Quem faz KYC?
- Quem faz KYB?
- Quais dados são obrigatórios?
- Quais limites existem?
- Quais riscos bloqueiam operação?
- Quem responde por chargeback, fraude ou disputa?

### Comercial

- Quais tarifas existem?
- Há mensalidade?
- Há custo por transação?
- Há volume mínimo?
- Há prazo de liquidação?
- Há split ou subcontas?
- Há white label?

## 12. Critério para aprovar parceiro

Um parceiro só deve ser considerado apto se cumprir, no mínimo:

- sandbox funcional;
- Pix entrada e/ou saída conforme escopo;
- webhooks assinados;
- documentação técnica clara;
- KYC/KYB compatível;
- modelo comercial viável;
- suporte operacional;
- contrato claro;
- compliance compatível;
- possibilidade de reconciliação;
- segurança aceitável.

Se algum ponto crítico não for atendido, a Aurea deve manter dinheiro real bloqueado.

## 13. O que não prometer na reunião

Não prometer:

- que a Aurea já movimenta dinheiro real;
- que já possui licença própria;
- que já substitui banco;
- que já emite cartão real;
- que já opera Pix real;
- que já gera comprovante real;
- que já possui checkout real ativo;
- que já pode captar clientes com dinheiro real sem parceiro.

A mensagem correta é:

> A Aurea Gold já possui produto, interface, fluxos, sandbox e visão operacional preparados. A operação financeira real será ativada somente com parceiro homologado e controles formais.

## 14. Próximos passos recomendados

1. Atualizar shortlist de parceiros priorizados.
2. Selecionar primeira onda de contato.
3. Preparar mensagem/e-mail com base no roteiro já existente.
4. Registrar contatos no log.
5. Agendar conversa técnica.
6. Solicitar documentação e sandbox.
7. Validar requisitos do questionário.
8. Escolher parceiro candidato.
9. Planejar integração real em branch própria.
10. Manter dinheiro real bloqueado até aprovação completa.

## 15. Estado deste documento

Status: v1 criado após o marco `v0.2.20-wallet-final-visual-polish`.

Este documento marca a virada do foco visual para o foco de apresentação e negociação com parceiros PSP/BaaS.

A UI atual fica aprovada como base visual por enquanto.

Quando houver parceiro homologado, os textos de demo/sandbox/bloqueio devem ser revisados e substituídos por mensagens de operação real, sem quebrar segurança, compliance ou transparência.
