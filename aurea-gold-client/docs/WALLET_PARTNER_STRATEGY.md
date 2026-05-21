# Aurea Gold Wallet — Estratégia via Parceiro Financeiro

## 1. Decisão oficial do produto

A Aurea Gold será preparada para operar como uma wallet real por meio de parceiro financeiro, PSP ou BaaS.

A Aurea Gold não tentará operar como banco próprio no início.

A estratégia correta é:

- Aurea Gold controla a experiência premium do usuário;
- Aurea Gold controla a IA financeira;
- Aurea Gold controla gestão de caixa, relatórios, UX, planos e relacionamento;
- parceiro regulado fornece Pix real, saldo transacional, KYC, liquidação, conta, webhooks e compliance financeiro.

## 2. O que a Aurea Gold vai ser

Aurea Gold será uma carteira inteligente premium para pequenos negócios, MEIs, autônomos, comércios locais e empresas que precisam enxergar melhor seu dinheiro.

A proposta central:

> Carteira digital inteligente com IA, gestão de caixa, Pix, extrato, alertas, relatórios e operação financeira real via parceiro.

## 3. O que já existe no projeto

Base atual já construída:

- frontend com identidade premium petróleo + ouro;
- Home da carteira;
- login e autenticação local/dev;
- módulos de Pix;
- saldo e histórico em estrutura inicial;
- gestão financeira;
- pagamentos;
- IA/insights;
- planos;
- backend com rotas financeiras e Pix em modo base/lab;
- estrutura de transações, wallet, usuários e refresh token.

## 4. O que ainda falta para virar wallet real

Para operar como carteira real, ainda faltam:

- parceiro financeiro/PSP/BaaS;
- KYC PF/PJ;
- saldo real via parceiro;
- Pix real de entrada;
- Pix real de saída;
- QR Code Pix;
- Pix copia e cola;
- comprovante real;
- extrato real;
- webhooks de status;
- limites transacionais;
- logs/auditoria;
- antifraude;
- contestação/MED;
- suporte operacional;
- termos de uso;
- política de privacidade;
- checklist Play Store para app financeiro.

## 5. Arquitetura recomendada

A arquitetura futura deve seguir este desenho:

Aurea Frontend
↓
Aurea Backend
↓
Partner Adapter
↓
PSP/BaaS/Instituição parceira

A camada Partner Adapter deve evitar acoplamento direto com um único fornecedor.

Isso permitirá trocar ou adicionar parceiros no futuro sem reescrever a carteira inteira.

## 6. MVP real via parceiro

O MVP financeiro real deve priorizar:

1. Cadastro e KYC básico;
2. Conta/saldo via parceiro;
3. Receber Pix;
4. Enviar Pix;
5. QR Code e copia e cola;
6. Extrato real;
7. Comprovante;
8. Webhooks;
9. Limites;
10. Logs e auditoria;
11. Termos e privacidade.

## 7. O que não prometer ainda

Enquanto não houver parceiro financeiro fechado, a Aurea não deve prometer:

- banco próprio;
- conta bancária própria;
- cartão físico real;
- cartão virtual real;
- rendimento real;
- crédito;
- empréstimo;
- maquininha própria;
- Pix real em produção sem parceiro;
- garantia de aprovação financeira.

## 8. Posicionamento honesto

Antes do parceiro:

> Aurea Gold — gestão financeira inteligente e carteira em preparação para operação real via parceiro.

Depois do parceiro:

> Aurea Gold Wallet — carteira digital inteligente para negócios, com operação financeira real via parceiro regulado.

## 9. Diretriz visual oficial

A Aurea Gold não deve usar fotos de pessoas, imagens genéricas ou banners artificiais.

Identidade visual oficial:

- interface premium;
- petróleo + ouro;
- preto carbono somente se for bem lapidado;
- monograma/símbolo AG;
- cards;
- textura CSS;
- ícones minimalistas;
- sem fotos genéricas.

## 10. Ordem de execução

Prioridade P0:

- documentar estratégia;
- mapear parceiros possíveis;
- criar Partner Adapter;
- criar contrato interno de integração;
- separar modo demo/lab de modo real;
- preparar checklist KYC/Pix/webhook;
- criar termos e privacidade iniciais.

Prioridade P1:

- implementar adapter sandbox;
- criar fluxo de cadastro/KYC;
- receber Pix sandbox;
- enviar Pix sandbox;
- registrar webhooks;
- gerar comprovante;
- auditar transações.

Prioridade P2:

- cartão virtual/físico via parceiro;
- link de pagamento;
- cobrança recorrente;
- rendimento;
- crédito;
- Aurea Black/Gold Card.

## 11. Regra para handoffs futuros

Todo handoff futuro da Aurea Gold deve explicar:

- que o projeto é real e comercial;
- que a carteira será wallet via parceiro financeiro;
- o que a Aurea controla;
- o que o parceiro fornece;
- o que já existe;
- o que falta;
- que não usaremos fotos/imagens genéricas;
- que o foco é Play Store e mercado real, mas sem prometer operação financeira antes do parceiro.
