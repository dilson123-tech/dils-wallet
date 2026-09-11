# Aurea Gold — Checklist de Prontidão Sandbox Asaas v1

Status: draft
Marco planejado: v0.2.30-wallet-asaas-sandbox-readiness-checklist
Projeto: Aurea Gold / dils-wallet
Parceiro candidato: Asaas
Prioridade atual: A
Natureza: produto real/comercial, não projeto de estudo.

## 1. Objetivo

Este documento define o checklist prático de prontidão antes de iniciar qualquer spike técnico com o Sandbox Asaas.

O objetivo é garantir que a Aurea Gold / dils-wallet só avance para testes técnicos quando houver ambiente, documentação, variáveis, credenciais sandbox e regras de segurança minimamente organizadas.

Este checklist não libera operação real.

## 2. Regra central

Nenhum item deste checklist autoriza produção real.

Antes de qualquer operação real, continuam obrigatórios:

- validação técnica em Sandbox;
- revisão dos resultados;
- conta PJ aprovada;
- homologação BaaS;
- Checklist e Playbook oficiais do Asaas;
- análise regulatória e operacional;
- contrato BaaS formal;
- liberação técnica;
- compliance;
- revisão jurídica;
- decisão explícita do Dilson para avançar.

Enquanto este checklist estiver em andamento:

- não usar Pix real;
- não usar saldo real;
- não criar subconta real;
- não ativar split real;
- não salvar credenciais reais;
- não tratar evento sandbox como liquidação real.

## 3. Estado esperado antes do spike técnico

Antes de iniciar qualquer código ou teste técnico, confirmar:

- [ ] conta Asaas acessível;
- [ ] acesso ao menu Minha Conta > Integrações > Acessar ambiente Sandbox;
- [ ] ambiente Sandbox criado ou disponível;
- [ ] documentação técnica localizada;
- [ ] credencial Sandbox gerada;
- [ ] credencial mantida fora do Git;
- [ ] URL/base do Sandbox confirmada;
- [ ] endpoint de cobrança Pix localizado na documentação;
- [ ] endpoint de consulta de cobrança/status localizado;
- [ ] documentação de webhooks localizada;
- [ ] regra do header asaas-access-token confirmada;
- [ ] documentação de extrato/histórico localizada;
- [ ] disponibilidade de subcontas Sandbox confirmada ou documentada como pendente;
- [ ] disponibilidade de split Sandbox confirmada ou documentada como pendente.

## 4. Checklist de segurança de credenciais

Antes de testar qualquer chamada com API:

- [ ] criar arquivo local `.env` fora do Git;
- [ ] garantir que `.env` está ignorado pelo Git;
- [ ] nunca colar token real no terminal compartilhado;
- [ ] nunca commitar token;
- [ ] nunca colocar token real em Markdown;
- [ ] nunca colocar token real em issue, PR, print ou log;
- [ ] revisar se logs mascaram credenciais;
- [ ] separar token Sandbox de qualquer token de produção;
- [ ] nomear variáveis com prefixo claro de Asaas;
- [ ] confirmar que `REAL_MONEY_ENABLED=false` permanece obrigatório.

Variáveis previstas, sem valores reais no repositório:

- `ASAAS_ENV`
- `ASAAS_BASE_URL`
- `ASAAS_API_KEY`
- `ASAAS_WEBHOOK_TOKEN`
- `ASAAS_WEBHOOK_ALLOWED_IPS`
- `WALLET_PARTNER_PROVIDER`
- `WALLET_MODE`
- `REAL_MONEY_ENABLED`

## 5. Checklist de ambiente local

Antes de iniciar spike técnico:

- [ ] repositório na `main` limpo antes de criar branch;
- [ ] branch específica criada;
- [ ] backend local sobe sem erro;
- [ ] frontend local builda sem erro, se necessário;
- [ ] testes existentes continuam verdes;
- [ ] porta local de backend definida;
- [ ] estratégia de webhook local definida;
- [ ] ferramenta para expor webhook local definida, se necessária;
- [ ] logs locais revisados para não imprimir tokens;
- [ ] plano de rollback claro.

## 6. Checklist de cobrança Pix Sandbox

Antes de implementar teste de cobrança:

- [ ] endpoint de criação de cobrança identificado;
- [ ] campos obrigatórios documentados;
- [ ] dados fictícios definidos;
- [ ] valor de teste definido;
- [ ] referência interna definida;
- [ ] identificador Asaas esperado documentado;
- [ ] status inicial esperado documentado;
- [ ] retorno de QR Code ou payload Pix confirmado na documentação;
- [ ] regra para não creditar saldo real definida;
- [ ] regra para não gerar comprovante real definida.

Critério mínimo para avançar:

- criar cobrança Sandbox;
- receber identificador externo;
- consultar cobrança depois;
- manter tudo marcado como Sandbox.

## 7. Checklist de consulta de status

Antes de implementar consulta:

- [ ] endpoint de consulta identificado;
- [ ] identificador necessário confirmado;
- [ ] status possíveis mapeados;
- [ ] diferença entre pagamento simulado e liquidação real registrada;
- [ ] regra de auditoria definida;
- [ ] regra de erro definida;
- [ ] regra para status desconhecido definida.

Critério mínimo para avançar:

- status precisa ser consultável;
- resposta precisa permitir reconciliação;
- status ambíguo deve bloquear evolução.

## 8. Checklist de webhook Sandbox

Antes de configurar webhook:

- [ ] documentação de webhook localizada;
- [ ] eventos relevantes identificados;
- [ ] payload de exemplo localizado ou obtido;
- [ ] rota local planejada;
- [ ] estratégia para expor rota local definida, se necessário;
- [ ] token do header asaas-access-token configurado localmente;
- [ ] validação de token planejada;
- [ ] regra de rejeição para token ausente definida;
- [ ] regra de rejeição para token incorreto definida;
- [ ] regra de idempotência definida;
- [ ] regra de replay definida;
- [ ] logs sem dados sensíveis definidos.

Critério mínimo para avançar:

- webhook precisa ser autenticável;
- evento precisa ser auditável;
- replay precisa ser seguro;
- evento inválido precisa ser rejeitado.

## 9. Checklist de reconciliação

Antes de declarar o fluxo tecnicamente viável:

- [ ] cobrança criada com referência interna;
- [ ] identificador Asaas salvo em ambiente de teste;
- [ ] webhook recebido;
- [ ] status consultado;
- [ ] valor comparado;
- [ ] status comparado;
- [ ] data/hora comparada;
- [ ] divergências detectáveis;
- [ ] nenhum saldo real creditado;
- [ ] nenhum comprovante real emitido.

Critério mínimo para avançar:

- cobrança, webhook e status precisam fechar entre si;
- divergência precisa ficar visível;
- conciliação precisa ser auditável.

## 10. Checklist de extrato e histórico

Antes de considerar auditoria suficiente:

- [ ] endpoint de extrato localizado;
- [ ] endpoint de histórico localizado;
- [ ] filtros disponíveis documentados;
- [ ] campos úteis documentados;
- [ ] relação com cobrança e webhook validada;
- [ ] limitações registradas.

Critério mínimo para avançar:

- extrato/histórico precisa ajudar na auditoria;
- ausência de filtros úteis deve ser registrada como risco.

## 11. Checklist de subcontas Sandbox

Antes de testar subcontas:

- [ ] confirmar se subcontas estão disponíveis no Sandbox;
- [ ] confirmar se criação exige dados fictícios;
- [ ] confirmar campos obrigatórios;
- [ ] confirmar diferença entre subconta comum e BaaS;
- [ ] confirmar limites do período de avaliação;
- [ ] confirmar que BaaS em produção exige homologação prévia;
- [ ] registrar risco regulatório.

Critério mínimo para avançar:

- subconta precisa ser testável em Sandbox ou bem documentada;
- qualquer dependência de produção real bloqueia o teste.

## 12. Checklist de split Sandbox

Antes de testar split:

- [ ] confirmar se split está disponível no Sandbox;
- [ ] identificar campos obrigatórios;
- [ ] definir regra fictícia de divisão;
- [ ] associar split a cobrança Sandbox, se permitido;
- [ ] consultar resultado;
- [ ] registrar limitações.

Critério mínimo para avançar:

- split precisa ser rastreável;
- ausência de split Sandbox deve ser registrada como gap;
- split real permanece bloqueado.

## 13. Checklist de documentação interna

Antes de abrir PR de spike técnico futuro:

- [ ] registrar links oficiais consultados;
- [ ] registrar endpoints usados sem expor token;
- [ ] registrar payloads sanitizados;
- [ ] registrar prints sem credenciais, se necessário;
- [ ] registrar decisões técnicas;
- [ ] registrar riscos;
- [ ] registrar próximos bloqueios;
- [ ] atualizar log de parceiro se houver novo retorno humano;
- [ ] manter aviso de que Asaas ainda não é parceiro fechado.

## 14. Critérios para liberar o próximo marco técnico

O próximo marco técnico só deve começar se:

- [ ] Sandbox acessível;
- [ ] credencial Sandbox disponível com segurança;
- [ ] documentação mínima revisada;
- [ ] fluxo Pix Sandbox entendido;
- [ ] webhook entendido;
- [ ] autenticação por asaas-access-token entendida;
- [ ] estratégia de idempotência definida;
- [ ] estratégia de reconciliação definida;
- [ ] riscos de subcontas/split anotados;
- [ ] produção real continuar explicitamente bloqueada.

## 15. Critérios que bloqueiam avanço

Bloquear avanço técnico se:

- [ ] credencial não estiver segura;
- [ ] houver risco de usar produção por engano;
- [ ] documentação de webhook estiver insuficiente;
- [ ] não houver validação clara do asaas-access-token;
- [ ] não houver identificador confiável para reconciliação;
- [ ] subcontas exigirem produção real;
- [ ] split exigir produção real;
- [ ] qualquer teste puder movimentar dinheiro real;
- [ ] qualquer log expuser token;
- [ ] houver dúvida sobre responsabilidade regulatória.

## 16. Resultado esperado deste marco

Ao final deste marco, o repositório deve ter apenas documentação.

Entregáveis:

- checklist de prontidão Sandbox Asaas;
- lista de requisitos antes do spike técnico;
- critérios de avanço;
- critérios de bloqueio;
- reforço de segurança;
- nenhuma credencial;
- nenhum código produtivo;
- nenhuma operação real.

## 17. Próximo marco provável

Se este checklist for aprovado, o próximo marco pode ser:

- v0.2.31-wallet-asaas-sandbox-technical-spike-plan

Ou, se o ambiente Sandbox já estiver acessível e pronto:

- v0.2.31-wallet-asaas-sandbox-technical-spike

A decisão deve ser tomada somente depois de preencher este checklist com base no ambiente real do Asaas.
