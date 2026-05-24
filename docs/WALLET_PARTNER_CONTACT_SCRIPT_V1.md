# Aurea Gold / dils-wallet — Roteiro de Contato com Parceiro PSP/BaaS v1

## 1. Objetivo deste documento

Este documento transforma a prontidão técnica da Aurea Gold em um roteiro prático para conversar com parceiros financeiros, PSPs, BaaS, instituições de pagamento, gateways ou provedores de infraestrutura financeira.

A Aurea Gold / dils-wallet é um produto real e comercial, com objetivo de chegar à Play Store e gerar renda real. Portanto, qualquer avanço para Pix real, saldo real, liquidação real ou movimentação financeira depende de parceiro homologado, contrato formal, compliance, KYC/KYB, ledger real, webhook seguro, reconciliação oficial e operação mínima.

Este documento não autoriza operação financeira real por conta própria.

---

## 2. Posição atual da Aurea Gold

Estado atual validado:

- Aplicação visual premium em evolução.
- Wallet demo/local implementada.
- Ciclo sandbox de parceiro validado.
- Cobrança sandbox validada.
- Webhook sandbox com idempotência validado.
- Replay idempotente validado.
- Conflito de payload com mesma chave retornando HTTP 409.
- Reconciliação sandbox validada.
- Histórico/auditoria sandbox validado.
- Aba Mais validada visualmente com dinheiro real desativado.
- Documentação operacional criada.

Estado bloqueado:

- Pix real bloqueado.
- Saldo real bloqueado.
- Liquidação real bloqueada.
- Comprovante real bloqueado.
- Crédito real em carteira bloqueado.
- Operação financeira real bloqueada.

---

## 3. Regra permanente antes de dinheiro real

Não avançar para Pix real, saldo real, carteira real ou liquidação real sem:

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

Sem isso, a Aurea Gold permanece em modo demo/sandbox.

---

## 4. Documentos internos relacionados

Usar estes documentos como base da conversa:

- `docs/WALLET_SANDBOX_CYCLE_RUNBOOK.md`
- `docs/WALLET_PARTNER_READINESS_MATRIX_V1.md`
- `docs/WALLET_PRODUCTION_ENV_CHECKLIST_V1.md`
- `docs/WALLET_PSP_BAAS_QUESTIONNAIRE_V1.md`

---

## 5. Perfil ideal do parceiro

O parceiro ideal precisa oferecer:

- API Pix de entrada.
- API Pix de saída, quando autorizado e viável.
- Webhooks seguros.
- Assinatura de webhook ou token de validação.
- Idempotência.
- Ambiente sandbox/homologação.
- Ambiente produção documentado.
- KYC/KYB.
- Suporte a subcontas, contas de pagamento, wallet ou modelo equivalente.
- Ledger ou extrato transacional confiável.
- Reconciliação.
- Suporte técnico.
- SLA.
- Documentação clara.
- Responsabilidade regulatória bem definida.
- Contrato formal.
- Política de chargeback/disputa/estorno quando aplicável.
- Plano de incidentes.

---

## 6. Mensagem curta para primeiro contato

> Olá, tudo bem?
>
> Estou desenvolvendo a Aurea Gold, uma carteira digital/app financeiro com foco comercial e operação responsável.
>
> O produto já possui uma fundação técnica em ambiente demo/sandbox, incluindo fluxo de cobrança, webhook, idempotência, reconciliação e histórico operacional, sempre sem movimentar dinheiro real.
>
> Neste momento estou buscando um parceiro PSP/BaaS homologado para avaliar integração oficial com Pix, KYC/KYB, webhooks seguros, reconciliação, compliance e operação em produção.
>
> Gostaria de entender se vocês oferecem infraestrutura para esse modelo e se podemos marcar uma conversa técnica/comercial.

---

## 7. Mensagem mais profissional por e-mail

Assunto sugerido:

Parceria PSP/BaaS para integração da carteira digital Aurea Gold

Corpo sugerido:

> Olá,
>
> Meu nome é Dilson Pereira e estou à frente do projeto Aurea Gold / dils-wallet, uma carteira digital em desenvolvimento com foco comercial, experiência premium e operação responsável.
>
> O projeto já possui uma fundação técnica validada em ambiente sandbox, incluindo:
>
> - fluxo de cobrança simulada;
> - webhook com idempotência;
> - proteção contra replay;
> - reconciliação sandbox;
> - histórico/auditoria operacional;
> - separação explícita entre ambiente demo/sandbox e dinheiro real.
>
> A Aurea Gold ainda não movimenta dinheiro real. O objetivo deste contato é justamente buscar um parceiro PSP/BaaS homologado para avaliar integração oficial com Pix, KYC/KYB, compliance, ledger, webhooks seguros, reconciliação e operação em produção.
>
> Gostaria de saber se a empresa de vocês oferece infraestrutura para esse tipo de parceria e quais seriam os requisitos técnicos, comerciais, regulatórios e operacionais para avançarmos.
>
> Podemos marcar uma conversa técnica/comercial?
>
> Atenciosamente,
> Dilson Pereira

---

## 8. Perguntas essenciais para o parceiro

### 8.1 Modelo de parceria

- Vocês atuam como PSP, BaaS, instituição de pagamento, gateway ou provedor de infraestrutura?
- Qual é o modelo regulatório oferecido?
- A operação ficaria sob licença/regulação de quem?
- A Aurea Gold poderia operar como camada de experiência/tecnologia usando a infraestrutura de vocês?
- Existe contrato específico para wallet, conta digital, Pix ou cobrança?
- Existe modelo white-label?
- Existe modelo marketplace/subcontas?
- Existe modelo de conta transacional para pessoa física e jurídica?

### 8.2 Pix de entrada

- A API permite gerar cobrança Pix?
- A API permite QR Code dinâmico?
- A API permite Pix copia e cola?
- Existe vencimento de cobrança?
- Existe metadata customizada?
- Existe provider_reference único?
- Existe status de pagamento em tempo real?
- Existe ambiente sandbox?
- Quais status possíveis existem?
- Como consultar uma cobrança específica?

### 8.3 Pix de saída

- A API permite Pix de saída?
- Quais critérios para liberar Pix de saída?
- Exige KYC/KYB aprovado?
- Exige saldo em conta transacional?
- Existe limite por transação?
- Existe limite diário/mensal?
- Existe antifraude?
- Existe aprovação manual?
- Existe confirmação forte?
- Existe bloqueio preventivo?

### 8.4 Webhook

- O webhook é assinado?
- Usa HMAC, JWT, token fixo, certificado ou outro padrão?
- Como validar autenticidade?
- Existe proteção contra replay?
- Existe timestamp?
- Existe idempotency key?
- Existe event_id único?
- O parceiro reenvia eventos em caso de falha?
- Qual política de retry?
- Qual tempo médio de entrega do webhook?
- O webhook informa pagamento confirmado, cancelado, expirado, estornado e falho?

### 8.5 Idempotência

- A API aceita idempotency key em criação de cobrança?
- A API aceita idempotency key em pagamento Pix de saída?
- O webhook possui identificador único de evento?
- Como tratar replay legítimo?
- Como tratar duplicidade?
- Como tratar payload divergente com mesma chave?
- Existe documentação oficial de idempotência?

### 8.6 KYC/KYB

- Vocês oferecem KYC para pessoa física?
- Vocês oferecem KYB para pessoa jurídica?
- Quais dados são exigidos?
- Existe validação documental?
- Existe biometria?
- Existe prova de vida?
- Existe análise de sócios?
- Existe validação de CNPJ?
- Existe validação de CPF?
- O resultado do KYC/KYB vem por API?
- O status do KYC/KYB vem por webhook?
- Quais status possíveis existem?

### 8.7 Ledger, saldo e custódia

- Vocês oferecem ledger?
- Vocês oferecem saldo por cliente?
- Existe subconta por usuário?
- Existe conta de pagamento individual?
- O dinheiro fica custodiado onde?
- Quem é o responsável pela custódia?
- Como consultar saldo?
- Como consultar extrato?
- Como reconciliar saldo interno com saldo do parceiro?
- Existe reserva, bloqueio ou saldo pendente?
- Existe separação entre saldo disponível e saldo em liquidação?

### 8.8 Reconciliação

- Existe endpoint de reconciliação?
- Existe relatório diário?
- Existe exportação CSV/JSON?
- Existe conciliação por provider_reference?
- Existe conciliação por event_id?
- Existe conciliação por transaction_id?
- Como tratar divergência entre webhook e consulta?
- Qual é a fonte da verdade: webhook, consulta ou extrato?
- Existe janela de liquidação?
- Existe status final irreversível?

### 8.9 Segurança

- Qual método de autenticação da API?
- API key, OAuth2, mTLS ou certificado?
- Existe rotação de chave?
- Existe segregação sandbox/produção?
- Existe IP allowlist?
- Existe limite de requisições?
- Existe escopo de credenciais?
- Existe chave separada para webhook?
- Existe painel para revogar credenciais?
- Existe trilha de auditoria?

### 8.10 Compliance e jurídico

- Quem responde regulatoriamente pela operação?
- Existe contrato de prestação de serviço?
- Existe contrato de correspondente, parceiro ou tecnologia?
- Existem termos obrigatórios para o usuário final?
- Existem regras obrigatórias de comunicação com o cliente?
- Existem limites obrigatórios por perfil de cliente?
- Existe política antilavagem de dinheiro?
- Existe monitoramento transacional?
- Existe obrigação de reporte?
- Existe política de bloqueio/encerramento de conta?
- Existe revisão jurídica antes da produção?

### 8.11 Tarifas e modelo comercial

- Existe mensalidade?
- Existe setup?
- Existe tarifa por Pix recebido?
- Existe tarifa por Pix enviado?
- Existe tarifa por conta ativa?
- Existe tarifa por KYC/KYB?
- Existe tarifa por webhook/evento?
- Existe volume mínimo?
- Existe contrato mínimo?
- Existe split de receita?
- Existe taxa diferente para PF e PJ?
- Existe tabela progressiva por volume?

### 8.12 SLA e suporte

- Qual SLA de API?
- Qual SLA de webhook?
- Qual SLA de suporte?
- Existe suporte técnico para integração?
- Existe suporte em incidentes?
- Existe canal emergencial?
- Existe status page?
- Existe ambiente de homologação estável?
- Existe changelog da API?
- Existe aviso prévio para breaking changes?

---

## 9. Checklist antes da reunião

Antes de reunião com parceiro, preparar:

- Nome do produto: Aurea Gold.
- Objetivo: carteira/app financeiro com integração via parceiro homologado.
- Estado atual: sandbox validado, sem dinheiro real.
- Explicar que não quer operar fora de compliance.
- Ter claro que Pix real só será liberado com parceiro e contrato.
- Ter os documentos internos abertos.
- Ter perguntas de KYC/KYB, Pix, webhook, ledger e reconciliação.
- Perguntar sobre responsabilidades regulatórias.
- Perguntar sobre custos.
- Perguntar sobre prazo de homologação.
- Perguntar sobre exigências jurídicas.
- Perguntar sobre requisitos técnicos para produção.

---

## 10. Critérios para aprovar parceiro

Um parceiro só deve ser considerado bom candidato se atender ao mínimo:

- Possui contrato formal.
- Explica claramente a responsabilidade regulatória.
- Possui API documentada.
- Possui sandbox.
- Possui Pix entrada.
- Explica critérios para Pix saída.
- Possui webhook seguro.
- Possui idempotência.
- Possui KYC/KYB.
- Possui reconciliação.
- Possui trilha de auditoria.
- Possui suporte técnico.
- Possui SLA.
- Explica tarifas.
- Possui caminho claro para produção.
- Aceita operação comercial do tipo wallet/app financeiro.

---

## 11. Sinais de alerta

Descartar ou pausar parceiro se houver:

- Não explica responsabilidade regulatória.
- Não tem contrato claro.
- Não tem sandbox.
- Não tem webhook seguro.
- Não tem idempotência.
- Não oferece KYC/KYB.
- Não permite reconciliação confiável.
- Não explica custódia.
- Não explica tarifas.
- Não tem suporte técnico.
- Promete Pix real fácil sem compliance.
- Incentiva operação informal.
- Não entrega documentação.
- Não responde sobre incidentes.
- Não separa homologação de produção.

Regra prática: se o parceiro trata dinheiro real como se fosse simples botão de API, é risco.

---

## 12. Resumo executivo para apresentação

A Aurea Gold busca um parceiro financeiro homologado para operar como camada regulatória e transacional da carteira.

A aplicação já possui uma base técnica sandbox validada, incluindo cobrança simulada, webhook, idempotência, reconciliação e auditoria, mas mantém dinheiro real bloqueado até existir infraestrutura formal de produção.

O objetivo da parceria é permitir evolução segura para:

- Pix de entrada;
- Pix de saída, se aprovado;
- KYC/KYB;
- ledger;
- reconciliação;
- webhooks seguros;
- operação monitorada;
- conformidade jurídica e regulatória.

---

## 13. Próximos passos após resposta do parceiro

Se o parceiro responder positivamente:

1. Solicitar documentação técnica.
2. Solicitar documentação comercial.
3. Solicitar contrato/minuta.
4. Solicitar tabela de tarifas.
5. Solicitar requisitos de homologação.
6. Solicitar acesso sandbox oficial.
7. Mapear variáveis reais exigidas.
8. Mapear fluxo KYC/KYB.
9. Mapear fluxo de webhook assinado.
10. Mapear fluxo de reconciliação.
11. Criar branch técnica somente depois disso.
12. Implementar adapter real sem misturar com sandbox.
13. Criar testes de contrato.
14. Criar checklist de produção.
15. Validar com dinheiro real apenas em ambiente controlado e autorizado.

---

## 14. Próxima branch técnica sugerida depois da conversa

Somente depois de obter documentação real do parceiro:

`feat/wallet-production-safety-guards`

Essa branch deverá implementar travas de ambiente com base nas variáveis reais existentes e nas exigências oficiais do parceiro.

Não inventar flags antes de conhecer o contrato técnico real.

---

## 15. Estado deste documento

Versão: v1
Tipo: documento operacional/comercial
Status: pronto para primeira abordagem com parceiro PSP/BaaS
Dinheiro real: bloqueado
Pix real: bloqueado
Objetivo: preparar conversa profissional e segura com parceiro financeiro
