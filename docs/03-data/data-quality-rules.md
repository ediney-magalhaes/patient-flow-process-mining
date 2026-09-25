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


## RQ-010 — Confirmação de `internacao_clinica_direta` como categoria de negócio real

- **Tabela de origem:** `gold_patient_journey`
- **Campo afetado:** `journey_type`
- **Data do achado:** 2026-08-13
- **Contexto:** Sprint 4 — Fase 2 (validação do Bloco B em `gold_patient_journey`
  após implementação do ADR-0014)

### Achado

Na primeira execução com Full Refresh após a implementação do Bloco B, 58 dos
422 registros (~14%) caíram na branch de investigação temporária da
classificação de `journey_type` — o caso que o ADR-0014 original havia
caracterizado, por hipótese, como clinicamente inexistente: internação sem
consulta prévia na emergência e sem cirurgia vinculada.

### Investigação

Duas rodadas de cruzamento contra `silver_atendimento_emergencia`, por
`cd_paciente`, descartaram explicações de erro de pipeline:

1. Join com janela de 1 dia antes da internação, restrito a registros com
   `origem_atendimento` indicando vínculo com emergência: nenhuma
   correspondência encontrada para os casos testados.
2. Join sem filtro de data nem de `origem_atendimento` (removido da
   investigação por não ser campo confiável para decisão, conforme já
   estabelecido no ADR-0014): 53 dos 58 casos não têm nenhum registro de
   emergência associado ao paciente em nenhum momento; os outros 5 têm
   emergências, mas todas posteriores à data de entrada da internação em
   questão — episódios não relacionados, prováveis reinternações do mesmo
   paciente ao longo do mês.

Nenhum indício de gap de curadoria, erro de vínculo ou falha de janela
temporal. O padrão é consistente com um tipo de entrada hospitalar real, não
mapeado antes da investigação.

### Decisão

Confirmado como categoria de negócio legítima: **internação clínica sem
consulta na emergência**. Nomeada `internacao_clinica_direta` pelo usuário,
substituindo o rótulo temporário de investigação em `gold_transformation.py`.
Passa a ser a sexta categoria oficial de `journey_type`, documentada no
ADR-0014 (emenda de 2026-08-13) e em `data-dictionary.md`.

### Ação futura recomendada

Nenhuma correção de pipeline necessária — o `otherwise` da classificação já
capturava esses casos corretamente, faltava apenas o nome de negócio. Ao
processar novos meses, monitorar se o volume proporcional de
`internacao_clinica_direta` se mantém próximo dos ~14% do Bloco B observados
em março/2026, ou se essa proporção era específica desse mês.

## RQ-011: `fl_conversao = 1` sem `cd_internacao` correspondente em `internacao_clinica`

**Contexto:** Durante a extensão de `gold_patient_journey` com colunas de
especialidade por segmento (18/08/2026), identificados 7 casos (de 282,
~2,5%) classificados como `journey_type = internacao_clinica`
(`fl_conversao = 1`) sem `cd_internacao` correspondente em
`silver_internacoes` — logo, sem `ts_entrada_internacao` nem
`especialidade_internacao` preenchidos, apesar da categoria implicar
internação real.

**Investigação:** `fl_conversao` é curada externamente (BigQuery,
`pipeline-analytics-emergencia`), fonte de verdade única de conversão
por decisão de governança do projeto. Os 7 casos têm a flag de conversão
vinda dessa fonte externa, mas o registro de internação correspondente
não existe (ou não bate) em `silver_internacoes` — sistemas de origem
diferentes, sincronização não garantida entre eles.

**Decisão:** Não corrigido neste projeto. `fl_conversao` não é
recalculada nem validada aqui — é consumida como está, por princípio já
estabelecido (single source of truth, `fl_conversao`/`fl_evasao` do
BigQuery curado prevalecem sobre lógica local). Divergência de
sincronização entre a fonte de conversão e `silver_internacoes` é
responsabilidade do pipeline de origem, fora do escopo deste projeto.
Sem ação corretiva — registrado para rastreabilidade caso o padrão
cresça em volume nas próximas cargas.


## RQ-012 — Persistência não idempotente e schema divergente na linha de exceção de `gold_dfg_macro`

- **Tabela de origem:** `gold_dfg_macro`
- **Célula/campo afetado:** célula de persistência da linha "Alta da Emergência → Fim" (`03_process_mining.ipynb`)
- **Data do achado:** 2026-09-15
- **Contexto:** ADR-0016 (fechamento da dívida de documentação da Página 2 do Dashboard)

### Achado

Ao revisar a ADR-0016 para fechar pendências abertas, dois problemas foram
identificados na célula que persiste a linha de exceção "Alta da Emergência
→ Fim" (a 16ª linha da tabela, calculada separadamente das outras 15 via
`.shift()`):

1. **Persistência via `.mode("append")` sem chave de deduplicação.** A célula
   anterior, que persiste as 14 transições principais, usa `.mode("overwrite")`
   e reconstrói a tabela inteira a cada execução, o `append` da linha de
   exceção só produzia resultado correto porque dependia implicitamente dessa
   ordem de execução (overwrite antes, append depois, sempre juntos).
   Reexecutar a célula de `append` isoladamente (cenário comum em depuração)
   duplicaria a linha por `ano_mes`, sem nenhum erro visível.
2. **Schema divergente do `SELECT` de origem.** O `df_dfg_final` (persistido
   via overwrite) tem 7 colunas: `ano_mes, especialidade, de, para,
   tempo_medio_min, tempo_mediano_min, frequencia`. O `SELECT` que gerava a
   linha de exceção produzia apenas 5, faltavam `especialidade` e
   `tempo_mediano_min`.

### Causa raiz

A linha de exceção foi adicionada depois da lógica principal das 14
transições, como ajuste pontual, sem revisão cruzada contra o schema final
da tabela nem contra o padrão de persistência (`overwrite`) já em uso no
resto da célula.

### Decisão

Célula reescrita para usar `MERGE INTO` (Delta Lake) na chave
`(ano_mes, de, para)`, com `especialidade` explicitamente `NULL` e
`tempo_mediano_min` calculado via `percentile_approx`. Idempotência
confirmada por teste manual: duas execuções consecutivas da célula produzem
a mesma contagem por `ano_mes`. Decisão completa e código final documentados
em ADR-0016, item 4.

### Ação futura recomendada

Ao adicionar uma linha de exceção ou ajuste pontual a uma tabela Gold já
existente, conferir o schema de destino explicitamente antes de escrever o
`SELECT` de origem, e preferir `MERGE INTO` a `append` sempre que a célula
puder ser reexecutada isoladamente do restante do notebook, não assumir
ordem de execução como garantia de correção.


## RQ-013 — `atend_internacao` permaneceu hasheada após remoção de hash de `CD_ATENDIMENTO`

- **Tabela de origem:** `atendimento_emergencia` (config de anonimização)
- **Campo afetado:** `atend_internacao`
- **Data do achado:** 2026-09-15
- **Contexto:** ADR-0017 (remoção de hash de identificadores de atendimento)

### Achado

Ao aplicar a ADR-0017 (remoção de hash de `CD_ATENDIMENTO` e equivalentes
por base, para viabilizar reaproveitamento entre projetos), a coluna
`atend_internacao` — cópia de `CD_INTERNACAO` de `silver_internacoes`,
incorporada via `enrichment.py` durante o join com o BigQuery curado —
permaneceu listada em `hash_columns` da config `atendimento_emergencia`.
A remoção de hash foi aplicada em `CD_ATENDIMENTO`, mas não em
`atend_internacao`, apesar das duas colunas precisarem bater entre si no
join central de `gold_patient_journey` (`atend_internacao == CD_INTERNACAO`).

Como `CD_INTERNACAO` (config `internacoes`) também teve seu hash removido
na mesma ADR, o resultado seria duas colunas que deveriam ser idênticas
para o mesmo caso — uma em texto puro (`CD_INTERNACAO`), outra ainda
hasheada (`atend_internacao`), quebrando silenciosamente o join central
da jornada do paciente.

### Causa raiz

A lista de colunas a corrigir na ADR-0017 foi montada olhando `config.py`
por nome de coluna óbvio (`CD_ATENDIMENTO`, `ATENDIMENTO`, `ATEND`), sem
mapear explicitamente colunas derivadas/calculadas que dependem da mesma
decisão, `atend_internacao` não tem "atendimento" nem "atend" como nome
que remetesse imediatamente à mesma categoria de identificador, na
varredura inicial.

### Decisão

`atend_internacao` removida de `hash_columns` na config `atendimento_emergencia`.
Reprocessamento completo desta base exigido (mesmo procedimento da ADR-0017:
regenerar CSV local, subir ao Volume, dropar Bronze, limpar checkpoint,
reingerir). Confirmado por consulta direta pós-correção: valores de
`atend_internacao` em formato numérico reconhecível, compatível com
`CD_INTERNACAO`.

### Ação futura recomendada

Ao remover hash de um identificador, mapear explicitamente qualquer coluna
derivada dele (cópias, chaves de join calculadas) antes de considerar a
correção completa, não basta buscar pelo nome da coluna original.

## RQ-014 — Checagem de disponibilidade de histórico global, não por fonte, em `gold_conformance`

- **Tabela de origem:** `gold_event_log` (via notebook `03_process_mining.ipynb`)
- **Célula afetada:** determinação do período de referência na seção de
  Conformance Checking
- **Data do achado:** 2026-09-22
- **Contexto:** ADR-0019 (modelo de referência para Conformance Checking)

### Achado

A primeira implementação da lógica de referência (ADR-0019) calculava a
disponibilidade de histórico (`quantidade_meses_anterior`,
`quantidade_meses_anteriores_qualquer`) uma única vez, fora do laço `for
source in ...`, consultando `gold_event_log` sem filtro de `source`. Como
existiam fragmentos residuais de contaminação de `ano_mes` (ver ADR-0018,
não corrigida ainda no momento desta execução) em 3 das 7 fontes
(`silver_altas`: 3 eventos, `silver_atendimento_emergencia`: 7,
`silver_cirurgias`: 316), a checagem global via essa contaminação como
"existe histórico disponível" e aplicava o mesmo `periodo_referencia` às 7
fontes igualmente.

As 4 fontes sem nenhum fragmento residual (`silver_exames_imagem`,
`silver_exames_laboratoriais`, `silver_internacoes`, `silver_movimentacoes`)
receberam log de referência **vazio** ao aplicar esse `periodo_referencia`.
Descobrir um Process Tree a partir de um `EventLog` vazio produz um modelo
degenerado; testar o log real do mês contra esse modelo produziu fitness e
precision artificiais, exatamente 1.0 para as 4 fontes afetadas, valor que
passou despercebido numa primeira leitura por parecer um resultado "bom",
não um sintoma de erro.

### Causa raiz

A checagem de disponibilidade de histórico foi implementada pensando na
tabela como uma unidade só, sem considerar que cada `source` pode ter
disponibilidade de dado completamente diferente das demais, inclusive
diferença criada artificialmente pela contaminação de `ano_mes` (ADR-0018),
que não distribui fragmentos igualmente entre fontes.

### Decisão

A checagem de referência (as duas contagens e a decisão de
`periodo_referencia`) movida para dentro do laço `for source in ...`, com
`source` incluído em cada consulta SQL. Cada fonte passa a decidir sua
própria disponibilidade de histórico de forma independente. Correção
completa descrita em ADR-0019.

### Ação futura recomendada

Ao implementar lógica condicional que decide comportamento por fonte
dentro de um pipeline com laço `for source`, sempre verificar se a
condição em si também precisa ser avaliada por fonte, não só a ação
tomada com base nela, uma condição calculada fora do laço, aplicada a
resultados dentro do laço, é um padrão fácil de errar silenciosamente
quando fontes têm disponibilidade de dado heterogênea.