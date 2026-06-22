# Regras de Qualidade de Dados

Este documento registra achados de qualidade de dado identificados durante o
desenvolvimento — campos com cobertura insuficiente, comportamentos
sistêmicos inesperados na origem, e decisões sobre como tratá-los. Cada
regra documenta o achado, a causa provável, e a decisão tomada sobre uso do
campo nas camadas Silver/Gold.

---

## RQ-001 — Cobertura insuficiente em campos de médico de laudo (`gold_events_exames_imagem`)

- **Tabela de origem:** `silver_exames_imagem`
- **Campos afetados:** `MEDICO_LAUDO_DEFINITIVO`, `MEDICO_LAUDO_ULTIMAMODIFICACAO`
- **Data do achado:** 2026-06-22
- **Contexto:** ADR-0008 (extensão do schema canônico para suportar Social
  Network Analysis)

### Achado

Os dois campos têm cobertura de 34,6% e 36,2%, respectivamente — valores
próximos entre si, o que sugere preenchimento sistemicamente parcial (por
exemplo, restrito a determinadas modalidades de exame ou a partir de uma
janela de tempo específica), não ausência aleatória de dado.

### Decisão

Os dois campos **não são utilizados** para popular a coluna `resource` no
schema canônico da Gold. Usar um campo com essa cobertura introduziria
exclusão silenciosa de aproximadamente 65% dos casos em qualquer análise de
rede (Handover of Work, Subcontracting) que dependesse dele — sem nenhum
sinal visível de que a exclusão estava ocorrendo.

`MEDICO_SOLICITANTE`, que tem cobertura completa, é usado no evento
`Prescrição do Exame de Imagem`. Os demais nove eventos de
`gold_events_exames_imagem` ficam com `resource` nulo.

### Ação futura recomendada

Investigar na origem (sistema RIS) por que `MEDICO_LAUDO_DEFINITIVO` e
`MEDICO_LAUDO_ULTIMAMODIFICACAO` têm cobertura parcial — se é uma limitação
de captura por modalidade de exame, por fluxo de trabalho do radiologista, ou
por mudança de processo em determinado período. Não é bloqueio para o
projeto atual; é item de melhoria de captura de dado na origem.