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
- **Campos afetados:** `timestamp`
- **Data do achado:** 2026-06-24 (achado inicial) / 2026-07-02 (causa raiz confirmada)
- **Contexto:** Sprint 3, Fase 3 (Social Network Analysis / investigação dedicada)

### Achado

O volume lido de `gold_event_log` é maior do que o volume de eventos que
efetivamente chega ao objeto `EventLog` do PM4Py. A perda é concentrada
de forma desproporcional em uma única fonte (`silver_exames_imagem`),
que responde pela grande maioria da diferença total, enquanto as demais
fontes apresentam perdas pequenas e relativamente uniformes.

### Causa raiz confirmada

A perda ocorre na chamada de `pm4py.format_dataframe()`, que descarta
silenciosamente (com aviso via `UserWarning`) linhas com `case_id`,
`activity` ou `timestamp` nulos — exigência do PM4Py para o funcionamento
correto dos algoritmos de descoberta e conformidade.

Em `silver_exames_imagem`, os nulos de timestamp já existem na tabela
Silver, na origem do sistema hospitalar (RIS) — confirmado por comparação
direta, campo a campo, entre a contagem de nulos na Silver e a contagem
de nulos por atividade na Gold, com correspondência exata. Não há
introdução de nulos pela transformação Gold.

O padrão de nulidade segue a ordem cronológica do fluxo de exame: etapas
administrativas de entrada (admissão, prescrição) têm cobertura completa;
etapas mais avançadas do processo clínico (preparo, execução, laudo,
ditado) têm cobertura crescentemente incompleta, com o evento de ditado
do laudo sendo o mais afetado. Interpretação mais provável: limitação de
captura estruturada do sistema RIS para essas etapas específicas, não um
defeito de engenharia do pipeline.

### Decisão

Nenhuma correção de pipeline aplicada — não há bug identificado no
Bronze, Silver ou Gold. A perda é uma característica dos dados de origem,
não da transformação. Análises de Process Mining continuam operando
sobre os eventos com timestamp válido, com essa limitação documentada
como contexto de leitura dos resultados.

### Ação futura recomendada

Nenhuma investigação técnica adicional necessária — causa raiz
confirmada com evidência direta na fonte. Recomenda-se reportar o achado
como insight de qualidade de dados ao time responsável pelo sistema RIS
do hospital, já que é exatamente o tipo de lacuna de processo que uma
ferramenta de Process Mining deve expor.

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

### Atualização — 2026-07-02

Investigado diretamente na fonte. A discrepância de timestamp não é causada
por mapeamento incorreto de coluna no pipeline — o dado já chega com esse
registro na origem. Trata-se de erro de input operacional no sistema
hospitalar. Nenhuma correção de pipeline aplicada ou necessária.

**Decisão:** surfacing no dashboard executivo (Sprint 4), junto com demais
inconsistências de qualidade de dados identificadas no projeto, para
visibilidade da diretoria.

## RQ-006: ORIGEM_ATEND em silver_internacoes — campo com falhas de input manual

**Status:** Fechado — decisão tomada  
**Tabela afetada:** `silver_internacoes`  
**Coluna afetada:** `ORIGEM_ATEND`  
**Descoberto em:** Sprint 4 — Fase 1 (gold_patient_journey)

### Descrição

O campo `ORIGEM_ATEND` de `silver_internacoes` registra a origem do paciente no
momento da internação (ex: `EMERGENCIA ADULTO`, `EMERGENCIA INFANTIL`). O
preenchimento é manual no HIS e apresenta inconsistências conhecidas: casos
originados da emergência aparecem com origem incorreta, e vice-versa. Não existe
processo de curadoria humana equivalente ao implementado no projeto BigQuery de
emergência.

### Impacto

O campo não pode ser usado como critério de filtro em joins, pois excluiria
casos reais de conversão emergência → internação registrados incorretamente.

### Decisão

`ORIGEM_ATEND` é mantido na `gold_patient_journey` como atributo informativo,
com a ressalva de qualidade registrada nesta regra. A estratégia de junção
entre emergência e internação usa `COD_PACIENTE` + janela temporal de 1 dia,
conforme documentado em ADR-0011. Gestores e analistas que utilizarem esse
campo para filtros devem estar cientes das limitações de confiabilidade.