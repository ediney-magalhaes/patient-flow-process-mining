# Dashboard — Página 3: Conformidade

- **Local:** AI/BI Dashboard `Mapa Digital do Fluxo do Paciente`, aba "Conformidade"
- **Decisão arquitetural:** ADR-0019 (modelo de referência da Conformance Checking) e RQ-014 (checagem de histórico por fonte)
- **Status:** construída e publicada (29/09/2026)

Mesmo escopo de `dashboard-gargalos.md`: cobre artefatos que vivem dentro do próprio Dashboard (datasets SQL salvos, filtros, widgets), não objetos do Unity Catalog, isso já está em `data-dictionary.md`.

---
## Estrutura da página

Dois filtros globais no topo:

| Filtro | Parâmetro | Tipo | Bypass |
|---|---|---|---|
| Período | `periodo` | multi-select | `IS NULL` (campo vazio) |
| Processo | `source_filtro` | single value | texto `'Todos'` |

**Vínculo por widget:** cada filtro precisa ser ligado individualmente a cada dataset que ele controla, via **Parameters**. Não há herança automática entre widgets.

**Filtro Período, lista de valores:** o campo `ano_mes` do dataset auxiliar `dim_periodo` entra em **Fields** apenas para popular o dropdown. O vínculo com `conformance_tendencia` é feito em **Parameters**. Sem o campo em Fields, o dropdown só oferece "All".

---
## Widgets

Todos os widgets usam o dataset `conformance_tendencia`.

### Gráficos de linha: Fitness e Precision

Dois gráficos lado a lado, mesma configuração, mudando só a métrica:

| Configuração | Fitness | Precision |
|---|---|---|
| Título | Fitness por processo ao longo do tempo - Aderência ao fluxo esperado | Precision por processo ao longo do tempo - Especificidade do fluxo esperado |
| Eixo X | `ano_mes` | `ano_mes` |
| Eixo Y | `SUM(fitness)` | `SUM(precision)` |
| Cor | `source` | `source` |
| Faixa do eixo Y | Custom, 0 a 1 | Custom, 0 a 1 |

**Por que `SUM` é seguro aqui:** o dataset já vem no grão `(ano_mes, source)`, então cada ponto agrega exatamente uma linha. Se `ano_mes` ou `source` forem removidos do gráfico, o `SUM` passa a somar linhas e o valor deixa de fazer sentido (fitness acima de 1).

**Por que o eixo fixo em 0 a 1:** fitness e precision são métricas normalizadas. Com escala automática, variações pequenas parecem dramáticas.

**Limitação atual:** com um único mês de ingestão (2026-03), cada fonte tem um ponto só e a linha não é desenhada. Os valores aparecem no tooltip. O gráfico passa a mostrar tendência a partir da segunda ingestão mensal.

### Caixa de texto: "Como ler estes gráficos"

Texto fixo abaixo dos gráficos, explicando em linguagem executiva o que são fitness e precision e por que precision baixa é esperada em ambiente hospitalar (alta variedade legítima de caminhos clínicos, não erro de modelo). Conteúdo conceitual em `docs/05-process-mining/`.

### Tabela: "Comparativo de conformidade por processo"

| Coluna original | Nome exibido |
|---|---|
| `ano_mes` | Período |
| `source` | Processo |
| `fitness` | Fitness (aderência) |
| `precision` | Precision (especificidade) |
| `total_traces` | Total de atendimentos (traces) |

Uma linha por fonte. Sem formatação condicional na precision, decisão deliberada: colorir valores baixos de vermelho contradiria o texto explicativo da página.

---
## Datasets SQL do Dashboard

### `conformance_tendencia`

Grão: 1 linha por `(ano_mes, source)`. Parâmetros: `periodo` (multi-select), `source_filtro` (single value). Alimenta os dois gráficos e a tabela.

```sql
select
    ano_mes,
    source,
    fitness,
    precision,
    total_traces
from hospital_santa_rosa.gold_fluxo.gold_conformance
where (:periodo is null or array_contains(:periodo, ano_mes))
  and (:source_filtro = 'Todos' or source = :source_filtro)
order by ano_mes, source
```

### `dim_periodo`

Grão: 1 linha por `ano_mes`. Sem parâmetros. Usado só para popular o dropdown do filtro Período.

```sql
select distinct ano_mes
from hospital_santa_rosa.gold_fluxo.gold_patient_journey
order by ano_mes
```

**Por que `gold_patient_journey` e não `gold_event_log`:** o `gold_patient_journey` tem grão de caso, com `ano_mes` vindo do lote (ADR-0018). O `gold_event_log` tem grão de evento e, antes da correção, vazava meses fantasma.

---

## Pendências

- Validação dos números desta página, adiada para depois que o dashboard inteiro estiver pronto (mesma decisão da Página 2)
- Com a segunda ingestão mensal, conferir se os gráficos de linha passam a desenhar tendência e se os filtros continuam corretos com mais de um período