# ADR-0015: Propagação de `data_referencia` para `gold_event_log` e Correção de `ano_mes` em Tabelas Analíticas de Process Mining

- **Status:** aceito
- **Data:** 2026-08-18
- **Decisores:** Ediney Magalhães
- **Relacionado a:** RQ-009 (origem da decisão de usar `DT_ATENDIMENTO` como referência de `ano_mes` em `gold_patient_journey`)

---

## Contexto

Durante a auditoria de completude de filtro do Dashboard (Sprint 4, Fase 2), identificou-se que `gold_variant_analysis`, `gold_bottleneck` e `gold_performance_spectrum`, as três tabelas analíticas construídas a partir de `gold_event_log` no notebook `03_process_mining.ipynb`, calculavam `ano_mes` a partir de `time:timestamp` (o timestamp cru de cada evento), sem tratamento de dois problemas reais:

1. **Eventos administrativos de agendamento distorcendo a data de referência do caso.** Em cirurgias, o primeiro evento de um trace é frequentemente `Aviso de Cirurgia`, marcação administrativa que pode ocorrer meses antes do procedimento real. Usar "o primeiro evento do trace" como proxy de `ano_mes` atribuiu 112 dos 117 casos de `gold_variant_analysis` a meses incorretos (ex: caso com cirurgia em março classificado como janeiro, por conta do aviso).

2. **Timestamps próximos da virada de meia-noite empurrando o caso para o mês seguinte.** Mesmo após corrigir (1), 4 casos remanescentes (emergência e altas) tinham eventos legítimos ocorrendo em horários como 23:43 do último dia do mês, o cálculo baseado em timestamp completo (com hora) atribuiu esses casos ao mês seguinte por diferença de minutos.

O RQ-009 já havia resolvido um problema estruturalmente idêntico para `gold_patient_journey`, usando `DT_ATENDIMENTO` (coluna de data, não timestamp) em vez de `ts_chegada`. Esse precedente foi aplicado aqui, generalizado para as sete fontes que compõem `gold_event_log` — que, diferente de `gold_patient_journey`, nunca teve uma coluna de data pura própria.

Paralelamente, a mesma auditoria identificou que nenhuma das três tabelas suportava filtro de Especialidade, necessário para a Página 2 do Dashboard (Gargalos), decisão de negócio definida como "especialidade do evento que originou a transição" (quem estava conduzindo o caso quando o gargalo começou, não quem o recebeu).

## Decisão

### 1. Nova coluna `data_referencia` em todas as 7 funções `gold_events_*`

Adicionada em `gold_transformation.py`, uma coluna `data_referencia` (tipo `date`, sem hora) por fonte, usando a coluna de origem mais adequada em cada caso:

| Fonte | Coluna de origem | Observação |
|---|---|---|
| `gold_events_emergencia` | `DT_ATENDIMENTO` | Mesma coluna já validada pelo RQ-009 |
| `gold_events_internacoes` | `DT_HR_ATENDIMENTO` (truncada) | Timestamp combinado na Silver; truncamento recupera a data pura equivalente à extração original |
| `gold_events_altas` | `DT_HR_ALTA_FINAL` (truncada) | Mesma lógica — colunas de data e hora separadas na extração, combinadas no Silver |
| `gold_events_cirurgias` | `DATA_INICIO_CIRURGIA` (truncada) | Mesma coluna já usada em `gold_patient_journey` como `DT_CIRURGIA` — reaproveita decisão já validada, evita usar o primeiro evento do trace (`Aviso de Cirurgia`), que é administrativo |
| `gold_events_exames_imagem` | `DATA_HORA_PRESCRICAO` (truncada) | Primeiro evento real da cadeia; colunas de data pura originais (`DIA`, `MES`, `MES_ANO`) não sobrevivem à transformação Silver |
| `gold_events_exames_laboratoriais` | `HR_PED_LAB` (truncada) | Primeiro evento real da cadeia; sem coluna de data pura separada nesta fonte |
| `gold_events_movimentacoes` | `DT_HR_MOVIMENTACAO` (truncada) | Única coluna de timestamp disponível; `DATA`/`HORA` originais foram removidas na transformação Silver |

`data_referencia` é propagada para `gold_event_log` via `unionByName`, disponível para qualquer consumidor downstream.

### 2. `ano_mes` recalculado nas três tabelas analíticas, a partir de `data_referencia`

`gold_variant_analysis`, `gold_bottleneck` e `gold_performance_spectrum` passam a derivar `ano_mes` de `data_referencia` (constante por caso dentro da mesma fonte), em vez de `time:timestamp`. Elimina os dois problemas descritos no Contexto sem exigir lógica de exclusão de atividades administrativas no notebook, a correção mora na origem (pipeline), não em cada consumidor.

`gold_variant_analysis` teve adicionalmente sua granularidade alterada: de ranking único global para ranking segmentado por `ano_mes` (`rank` calculado dentro de cada mês, não globalmente), necessário para que o filtro de Período no Dashboard tenha efeito real sobre a página de Variantes, em vez de `ano_mes` ser uma coluna decorativa com valor idêntico em todas as linhas.

### 3. Coluna `especialidade` adicionada a `gold_bottleneck` e `gold_performance_spectrum`

Populada com a especialidade do evento de **origem** da transição (via `.shift(1)` sobre o evento anterior no caso, mesma técnica já usada para `activity_anterior`/`timestamp_anterior`). Decisão de negócio: ao buscar por especialidade, a referência é quem iniciou a transição, não quem a recebeu.

## Alternativas consideradas

**Truncar `time:timestamp` no notebook (`.normalize()`), sem alterar `gold_transformation.py`.** Resolveria o problema (2), virada de meia-noite, mas não o (1): eventos administrativos continuariam distorcendo qual timestamp é usado como referência. Rejeitada por ser correção parcial, e por colocar a lógica de correção no notebook consumidor em vez de na origem, obrigando qualquer novo consumidor de `gold_event_log` a reimplementar a mesma correção.

**Manter Especialidade fora de `gold_bottleneck`/`gold_performance_spectrum`, tratando como decisão de design (como feito para `gold_conformance` e SNA).** Rejeitada, diferente de `gold_conformance` (onde segmentar exigiria descoberta de processo separada por especialidade, custo desproporcional) e SNA (ambiguidade estrutural de "qual dos dois processos da relação"), aqui não há ambiguidade técnica que justifique a exclusão: cada transição tem uma única especialidade de origem, direta de capturar.

## Consequências

- `gold_variant_analysis`: 2.016 linhas (variante × mês, mar/2026, volume idêntico ao ranking global anterior, porque só há um mês carregado; volume vai crescer com carga histórica multi-mês).
- `gold_bottleneck`: 1.662 linhas (fragmentação por `especialidade` frente às 63 combinações curadas anteriores).
- `gold_performance_spectrum`: 7.621 linhas (fragmentação por `especialidade` frente às 2.089 combinações anteriores).
- Qualquer notebook, dashboard ou query que já consumia essas três tabelas antes desta correção precisa ser revisado, o schema mudou (`especialidade` nova em duas tabelas; `data_referencia`/`rank` com semântica diferente em `gold_variant_analysis`) e o volume de linhas aumentou.
- `data_referencia` fica disponível em `gold_event_log` para qualquer análise futura que precise de data de referência confiável por caso, sem repetir esta investigação.
- Pendência não resolvida por este ADR: Performance Spectrum em granularidade de caso individual (uma linha por atendimento, colorida por duração) continua exigindo tabela nova, fora do escopo desta correção — reservado ao Databricks App.