# Event log e padrão XES

## O que é

Event log é a matéria-prima de Process Mining: uma tabela em que cada linha é um **evento** (algo que aconteceu, quando, em qual caso). Os três campos mínimos são:

| Conceito | Pergunta que responde | Chave no padrão XES |
|---|---|---|
| **Caso** (case) | A que episódio o evento pertence? | `case:concept:name` |
| **Atividade** | O que aconteceu? | `concept:name` |
| **Timestamp** | Quando? | `time:timestamp` |

Os demais campos são **atributos**. Atributos de evento mudam de evento para evento (ex.: `resource`, `especialidade`, `location`). Atributos de caso valem para o caso inteiro (ex.: idade, sexo, convênio).

**XES** (eXtensible Event Stream, IEEE 1849-2016) é o formato padrão de troca. Um arquivo XES é um XML com traces (casos) e eventos, e qualquer ferramenta de Process Mining (ProM, Disco, Celonis) o lê. O projeto exporta o log completo em XES (7.643 traces em março/2026, no Volume `exports`).

## O event log deste projeto

A tabela central é `gold_event_log`: o `UNION ALL` das sete tabelas `gold_events_*`, uma por fonte Silver (ADR-0007). Cada `gold_events_*` transforma a sua fonte diretamente para o schema canônico, sem tabela intermediária. Para fontes com vários timestamps por linha, o código percorre uma lista de pares `(coluna_timestamp, nome_atividade)` e empilha um DataFrame por evento.

### Colunas

| Coluna | Papel | Observação |
|---|---|---|
| `case_id` | caso da fonte | identificador do atendimento ou da internação, conforme a fonte |
| `activity` | atividade | vocabulário fixado em ADR-0006 |
| `timestamp` | momento do evento | pode ser nulo na origem (ver Armadilhas) |
| `lifecycle` | fase do evento | hoje é `complete` em todos os eventos |
| `event_type`, `case_type` | categorias | ex.: `cirurgia`, `internacao` |
| `outcome` | desfecho | nulo em todas as fontes hoje |
| `resource` | médico (hash SHA-256) | cobertura varia por fonte (ADR-0008, RQ-001) |
| `especialidade` | especialidade | cobertura varia por fonte (ADR-0008, RQ-002) |
| `location` | unidade ou sala | nulo em emergência, imagem e laboratório |
| `source` | tabela Silver de origem | também é o ator das análises de handover |
| `ano_mes` | mês do **lote** de ingestão | propagado da Silver, não calculado pelo timestamp (ADR-0018) |
| `data_referencia` | data clínica real do caso | evita atribuir o caso ao mês de um evento administrativo |
| `case_id_jornada` | chave da jornada completa | une casos de fontes diferentes do mesmo paciente (ver abaixo) |
| `duration_minutes` | duração total do caso | calculada na `gold_event_log`, por `case_id` |

### Duas chaves de caso

`case_id` identifica o caso **dentro de uma fonte**. `case_id_jornada` identifica a **jornada**, que atravessa fontes. Em emergência e nos exames, a chave da jornada é o número da internação quando a emergência converteu, e o número do atendimento quando não converteu. Em março/2026 são 7.957 valores distintos de `case_id` e 7.512 de `case_id_jornada`, e nenhum `case_id` contém eventos de emergência e de internação ao mesmo tempo, enquanto 445 jornadas contêm (RQ-016).

**Regra:** a chave do caso define quem pode se encontrar na análise. Análise de caminho, gargalo e handover usa `case_id_jornada`. A descoberta de processo e a conformidade por fonte usam `case_id`, porque o modelo é por fonte.

### Atributos de caso

`gold_case_attributes` guarda os atributos que valem para o caso inteiro (idade, sexo, convênio, CID principal, motivo de alta, classificação de risco, entre outros), vindos de `silver_epidemio` e `silver_atendimento_emergencia`.

## Do Delta Lake ao PM4Py

1. `spark.table("...gold_event_log")` e `toPandas()`.
2. O timestamp recebe fuso UTC explícito (`tz_localize('UTC')`), porque o PM4Py exige.
3. `pm4py.format_dataframe(...)` renomeia as colunas para o padrão XES (`case:concept:name`, `concept:name`, `time:timestamp`) e **descarta linhas** com caso, atividade ou timestamp nulos.
4. `pm4py.convert_to_event_log(...)` produz o objeto `EventLog` usado nas análises.
5. `pm4py.write_xes(...)` exporta o arquivo.

## Armadilhas encontradas

**Linhas descartadas em silêncio.** O passo 3 remove linhas sem timestamp e só emite um aviso. Em exames de imagem, os nulos já estão na origem (RIS) e crescem nas etapas mais avançadas do exame, com o ditado do laudo como a mais afetada (RQ-004). O pipeline não introduz esses nulos.

**Tipo da coluna `ano_mes` depois do `format_dataframe`.** O PM4Py converte texto com aparência de data (`"2026-03"`) para timestamp. Antes de gravar, é preciso devolver ao formato `AAAA-MM` (RQ-015).

**Mês pelo timestamp do evento.** Eventos administrativos (como "Aviso de Cirurgia") caem em outro mês e vazam fragmentos do lote para meses vizinhos. A solução é o `ano_mes` de lote (ADR-0018).

**Evento duplicado.** `TRANSFER. DE` e `TRANSFER. PARA` descrevem o mesmo evento físico de movimentação. `gold_events_movimentacoes` deduplica os pares. Quem lê `silver_movimentacoes` diretamente precisa deduplicar também (RQ-017).

**Atividade com detalhe demais.** Em Movimentações, o nome da atividade inclui origem e destino (leito). Isso multiplica atividades e variantes. Para o grafo panorâmico, a atividade é reduzida ao tipo (ADR-0016).

**Inversões sistêmicas e timestamps incoerentes.** Em imagem, o término do exame vem depois da liberação (RQ-003). Em altas, "Alta médica" pode aparecer antes do fim da anestesia (RQ-005). São registros da origem, e o log não os corrige.

## Pendências

- ADR-0006 está desatualizado em três pontos: (1) lista a movimentação como "valor de `TIPO`", mas o código monta o nome com tipo, origem e destino (e normaliza as transferências para "TRANSFERÊNCIA: origem → destino"); (2) escreve "Prescricao de Alta" e "Alta Medica", e o código usa "Prescricao de alta" e "Alta médica"; (3) diz que `DATA_INICIO_CIRURGIA` foi descartada por redundância, mas ela é a base de `data_referencia` em cirurgias. Propor emenda.
- O dicionário descreve o schema canônico com 12 colunas. O código também grava `data_referencia` e `case_id_jornada`, e `gold_event_log` ainda tem `duration_minutes`. Atualizar o dicionário.
- A diferença entre 7.957 casos na `gold_event_log` e 7.643 traces no PM4Py é compatível com as linhas descartadas no `format_dataframe`, mas não foi verificada.
- `outcome` está nulo em todas as fontes. Decidir se tem uso ou se sai do schema.

## Referências

- IEEE 1849-2016, *Standard for eXtensible Event Stream (XES)*.
- Van der Aalst, W. (2016). *Process Mining: Data Science in Action*, capítulos sobre dados de eventos.
- Documentação do PM4Py: `format_dataframe`, `convert_to_event_log`, `write_xes`.
- ADR-0006, ADR-0007, ADR-0008, ADR-0018, RQ-003, RQ-004, RQ-005, RQ-015, RQ-016, RQ-017.