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
com a ressalva de qualidade registrada nesta regra. Gestores e analistas que
utilizarem esse campo para filtros devem estar cientes das limitações de
confiabilidade.

**Atualização — 2026-08-04:** a estratégia de junção entre emergência e
internação deixou de usar `COD_PACIENTE` + janela temporal de 1 dia — o
join hoje é direto por `atend_internacao == CD_INTERNACAO`, usando o
identificador de internação curado pelo projeto BigQuery (ver ADR pendente
de numeração). `ORIGEM_ATEND` continua com a mesma limitação de
confiabilidade descrita acima; a mudança de critério de join não afeta esta
regra.

## RQ-007 — Cast silencioso em coluna anonimizada (`CD_AVISO_CIRURGIA`)

- **Tabela de origem:** `silver_cirurgias`
- **Campo afetado:** `CD_AVISO_CIRURGIA`
- **Data do achado:** 2026-08-04
- **Contexto:** Sprint 4 — Fase 2 (investigação de fan-out em `gold_patient_journey`)

### Achado

`CD_AVISO_CIRURGIA` está listada em `hash_columns` na config de anonimização
de `cirurgias` (`config.py`) — anonimizada via SHA-256 antes do upload para
o Databricks, corretamente, por ser identificador de episódio cirúrgico.
Porém a transformação `silver_cirurgias` aplicava `.cast("int")` sobre essa
coluna, herdado do tratamento de outras colunas numéricas da mesma tabela
(`CODIGO_CIRURGIA`, `COD_FATURAMENTO`).

Cast de string não-numérica (hash SHA-256) para `int` no PySpark **não
lança exceção** — retorna `null` silenciosamente. A coluna chegava com
100% de cobertura na Bronze e 0% na Silver, sem nenhum erro visível no
pipeline.

### Causa raiz

Decisão de anonimização (Sprint 0, `config.py`) e decisão de tipagem
(Sprint 1, `silver_cirurgias`) foram tomadas em momentos diferentes, sem
checagem cruzada entre "colunas hasheadas" e "colunas com cast numérico"
para essa tabela.

### Decisão

`.cast("int")` removido de `CD_AVISO_CIRURGIA` em `silver_cirurgias`. A
coluna permanece como `string` (hash), consistente com seu papel de
identificador anonimizado.

### Ação futura recomendada

Ao adicionar cast numérico em qualquer coluna de uma tabela Silver, checar
antes se essa coluna está em `hash_columns` da config de anonimização
correspondente. Vale considerar, no futuro, uma validação automatizada
(teste ou expectation) que sinalize colunas hasheadas com cast numérico
aplicado — hoje a checagem é manual.

## RQ-008 — Fan-out em `gold_patient_journey` por múltiplos procedimentos principais

- **Tabela de origem:** `silver_cirurgias`
- **Campo afetado:** `SN_PRINCIPAL`
- **Data do achado:** 2026-08-04
- **Contexto:** Sprint 4 — Fase 2 (integração `fl_conversao` curado)

### Achado

`SN_PRINCIPAL = 'SIM'` não é único por internação: 35 internações em
março/2026 têm mais de um procedimento marcado como principal (até 5 em
um caso). Isso indica múltiplos avisos/episódios cirúrgicos legítimos na
mesma internação (reintervenções), não erro de cadastro — mas sem
`CD_AVISO_CIRURGIA` disponível (ver RQ-007), não havia como diferenciar
episódios distintos, causando fan-out ao juntar `silver_cirurgias` com
`gold_patient_journey` (linhas duplicadas por internação).

### Causa raiz

Combinação de dois fatores: granularidade de `silver_cirurgias` é por
procedimento, não por internação; e o campo que identificaria o episódio
(`CD_AVISO_CIRURGIA`) estava indisponível por causa do RQ-007.

### Decisão

Após a correção do RQ-007, `df_cirug_internacao` e `df_cirug_ambulatorial`
em `gold_patient_journey` passam por desempate via `row_number()`,
mantendo o procedimento principal mais recente por episódio quando há mais
de um `SN_PRINCIPAL = 'SIM'` — partição por `CD_INTERNACAO` (internação)
ou por `CD_ATENDIMENTO_AMBULATORIAL` (ambulatorial, após join com a
emergência, para não descartar episódios de pacientes com mais de uma
passagem pela emergência).

### Ação futura recomendada

Nenhuma correção adicional necessária no curto prazo. Se o volume de
reintervenções crescer com mais meses de histórico, avaliar se "mais
recente" continua sendo o critério certo, ou se a jornada deveria
representar a janela cirúrgica completa (primeira entrada + última saída)
em vez de um único procedimento.


## RQ-009 — Fonte de `ano_mes` sujeita a lacuna de totem em `emergencia_pura`

- **Tabela de origem:** `silver_atendimento_emergencia`
- **Campo afetado:** `DT_HR_TOTEM_RECEP` (origem de `ts_chegada` em `gold_patient_journey`)
- **Data do achado:** 2026-08-13
- **Contexto:** Sprint 4 — Fase 2 (validação do dataset `kpis_jornada_emergencia` após expansão do Bloco B)

### Achado

397 registros de `journey_type = 'emergencia_pura'` (ano_mes = 2026-03)
apresentaram `ano_mes` nulo em `gold_patient_journey`. Investigação
confirmou que `ts_chegada` (origem: `DT_HR_TOTEM_RECEP`) estava nulo
nesses 397 registros — todos concentrados em `emergencia_pura`, sem
internação vinculada, portanto sem `ts_entrada_internacao` para servir de
fallback no `COALESCE` original.

### Causa raiz

A ingestão de março/2026 usada neste projeto não passou pelo mesmo
tratamento de lacunas de totem já aplicado no projeto paralelo de
conversão (`pipeline-analytics-emergencia`), onde esse campo já chega
completo. Não é falha do pipeline Bronze→Silver→Gold — é uma diferença
entre a fonte de ingestão usada aqui e a fonte curada já tratada no outro
projeto.

### Decisão

`ano_mes` em `gold_patient_journey` passa a usar `DT_ATENDIMENTO` como
fonte primária no lugar de `ts_chegada` — `DT_ATENDIMENTO` é mais robusta
por não depender do equipamento de totem, e é suficiente porque `ano_mes`
só precisa do grão de mês, não da hora exata. `ts_chegada` continua sendo
a fonte usada em `duracao_total_min`, onde a hora exata é necessária.

Nenhum `COALESCE` adicional foi introduzido como rede de segurança — se a
fonte de ingestão futura vier incompleta novamente, `ano_mes` permanece
nulo, sinalizando o problema de forma visível em vez de mascará-lo.

### Ação futura recomendada

Nas próximas ingestões mensais, usar o mesmo arquivo/fonte já curada pelo
projeto `pipeline-analytics-emergencia` para os campos de totem, em vez da
extração direta usada em março/2026.