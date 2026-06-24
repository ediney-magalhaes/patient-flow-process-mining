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

## RQ-002 — Cobertura parcial de especialidade em `altas` e `exames_imagem`

- **Tabelas de origem:** `silver_altas`, `silver_exames_imagem`
- **Campos afetados:** `DS_ESPECIALID` (altas), `ESPECIALIDADE` (exames_imagem)
- **Data do achado:** 2026-06-22
- **Contexto:** ADR-0008 (extensão do schema canônico para suportar Social
  Network Analysis)

### Achado

Validação pós-implementação do schema canônico mostrou cobertura de 74,6%
em `DS_ESPECIALID` e 45,8% em `ESPECIALIDADE`, confirmada tanto no
`gold_event_log` quanto diretamente na Silver — não é artefato da
transformação, é cobertura real da origem.

### Decisão

Os campos são utilizados normalmente para popular `especialidade` no
schema canônico, sem exclusão. Diferente de RQ-001, aqui a cobertura
parcial não compromete o campo a ponto de descartá-lo — apenas significa
que qualquer análise de SNA segmentada por especialidade nessas duas
fontes terá exclusão proporcional de casos sem esse dado (cerca de 25%
em altas, 54% em exames de imagem), refletindo limitação real de captura
na origem, não erro de pipeline.

### Ação futura recomendada

Nenhuma correção necessária no pipeline. Ao apresentar resultados de SNA
segmentados por especialidade para essas duas fontes, mencionar
explicitamente a cobertura como contexto da análise.

---

## RQ-003 — Inversão sistêmica entre término e liberação do exame de imagem

- **Tabela de origem:** `silver_exames_imagem`
- **Campos afetados:** `STATUS_TERMINO_EXAME`, `STATUS_LIBERADO`
- **Data do achado:** Sprint 2
- **Contexto:** ADR-0006 (mapeamento de eventos por fonte)

### Achado

Em 100% dos casos onde ambos os campos estão preenchidos,
`STATUS_TERMINO_EXAME` ocorre depois de `STATUS_LIBERADO` — ordem invertida
em relação ao que o nome das colunas sugere (liberação aparentando ocorrer
antes do término do exame). Investigação concluiu que isso é um
comportamento real do fluxo de trabalho do setor de imagem, não um erro de
dado: a "liberação" registrada nesse campo refere-se a um evento
administrativo diferente do que o nome sugere.

### Decisão

A flag de consistência temporal correspondente foi ajustada para refletir
a ordem real observada, em vez de assumir a ordem que o nome das colunas
sugeria. Mantido como evento legítimo no schema canônico — não é
inconsistência a ser corrigida.

### Ação futura recomendada

Nenhuma. Achado documentado para que análises futuras não interpretem essa
sequência como erro de qualidade de dado.

---

## RQ-004 — Perda de eventos entre `gold_event_log` e o EventLog do PM4Py

- **Tabela de origem:** `gold_event_log`
- **Campos afetados:** `timestamp` (suspeito, não confirmado)
- **Data do achado:** 2026-06-24
- **Contexto:** Sprint 3, Fase 3 (Social Network Analysis)

### Achado

O volume total lido de `gold_event_log` é maior do que o volume de eventos
que efetivamente chega ao objeto `EventLog` do PM4Py, após a conversão
Spark > Pandas > `format_dataframe()` → `convert_to_event_log()`. A perda
é proporcionalmente relevante (na ordem de dezenas de milhares de eventos
sobre o total) e não distribuída igualmente entre fontes, uma verificação
isolada em `silver_atendimento_emergencia` confirmou perda também nessa
fonte especificamente, antes de medirmos o total agregado.

### Decisão

Nenhuma correção aplicada ainda. Hipótese mais provável: descarte
silencioso de eventos com `timestamp` nulo/NaT durante a conversão, o
PM4Py é estrito quanto a esse campo, e nenhuma das etapas da conversão
emite aviso quando uma linha é descartada por esse motivo. Não confirmado
por inspeção direta do código-fonte do PM4Py nem por comparação de
contagem por fonte em cada etapa da pipeline.

### Ação futura recomendada

Investigação dedicada: comparar contagem por `source` em cada etapa da
conversão (leitura Spark, `.toPandas()`, `format_dataframe()`,
`convert_to_event_log()`) para isolar em qual etapa exata a perda ocorre,
e então decidir se cabe correção no notebook ou se é uma característica
aceitável da conversão para esse formato.

---

## RQ-005 — Timestamp incoerente no evento `Alta médica` (`gold_events_altas`)

- **Tabela de origem:** `silver_altas` (provável, não confirmado se a
  causa está na Silver ou no mapeamento da Gold)
- **Campos afetados:** evento `Alta médica` (distinto de `Alta Hospitalar`)
- **Data do achado:** 2026-06-24
- **Contexto:** Sprint 3, Fase 3 (Social Network Analysis Subcontracting Setor ↔ Setor)

### Achado

Em casos que envolvem cirurgia, o evento `Alta médica` aparece
cronologicamente **antes** do `Fim da Anestesia` do mesmo procedimento,
sequência clinicamente impossível. O evento `Alta Hospitalar` (distinto,
mesma fonte) mantém timestamp coerente com o restante da jornada do caso.
Esse comportamento gera falsos positivos na análise de Subcontracting
Setor↔Setor: o padrão Cirurgias>Altas>Cirurgias aparece no resultado sem
representar delegação real — é artefato do timestamp incoerente de
`Alta médica`.

### Decisão

Nenhuma correção aplicada. A análise de Subcontracting (#3,
`docs/05-process-mining/`) foi mantida sem filtrar os casos afetados,
para que uma futura correção na origem se reflita automaticamente no
resultado, sem necessidade de ajustar filtros no notebook.

### Ação futura recomendada

Investigar a coluna de origem do evento `Alta médica` em `silver_altas`,
provável mapeamento de timestamp incorreto (ex: lendo de um campo que não
representa esse evento especificamente). Após a correção, reexecutar a
análise de Subcontracting Setor↔Setor para confirmar se o padrão
Cirurgias↔Altas desaparece ou se revela um sinal real.