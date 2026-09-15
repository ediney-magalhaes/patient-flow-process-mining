# Dashboard — Página 2: Gargalos

- **Local:** AI/BI Dashboard `Mapa Digital do Fluxo do Paciente`, aba "Gargalos"
- **Decisão arquitetural:** ADR-0016 (design de `gold_dfg_macro`, curadoria
  manual de transições, exceção metodológica e resolução visual do nó
  "Transferência" duplicado)
- **Status:** construída e com layout fechado (15/09/2026). Validação dos
  números/dados desta página foi deliberadamente adiada para depois que
  o dashboard inteiro estiver pronto, decisão explícita, não pendência
  esquecida (ver Pendências, abaixo)

Mesmo escopo de `dashboard-kpis-jornada.md`: cobre artefatos que vivem
dentro do próprio Dashboard (datasets SQL salvos, Custom Viz, filtros),
não objetos do Unity Catalog, isso já está em `data-dictionary.md`.

---

## Estrutura da página

Três filtros globais no topo:

| Filtro | Campo | Tipo | Bypass |
|---|---|---|---|
| Período | `periodo` | single value | texto `'Todos'` |
| Processo | `source_filtro` | single value | texto `'Todos'` |
| Especialidade | `especialidade_filtro` | multi-select | `IS NULL` (campo vazio) |

**Vínculo por widget:** cada filtro precisa ser ligado individualmente a
cada dataset que ele controla, não há herança automática entre widgets
de uma mesma página.

### Layout (fechado em 15/09/2026)

Linha 1, largura cheia: os 3 cards macro, lado a lado, cada um esticado
até a borda da própria coluna do grid.

Linha 2: DFG à esquerda, ocupando toda a altura da linha (~30–35% da
largura); Ranking e Heatmap empilhados à direita, cada um com metade da
altura do DFG. Essa foi a opção escolhida entre três arranjos avaliados
(empilhamento total; redesenho do DFG para orientação horizontal;
divisão de Ranking/Heatmap ao lado do DFG), a única que preenche o
espaço sem tocar na calibração já feita do Custom Viz do DFG nem
transformar a página numa lista de blocos.

### Cards macro

Três cards, mesmo padrão de formatação (tempo em min/h/dias conforme
magnitude, P90 como métrica de dispersão não CV%, decisão específica
desta página):

| Card | Transição coberta |
|---|---|
| Emergência → Internação | `Alta da Emergência` → `Internacao` |
| Internação → Cirurgia | `Internacao` → `Entrada na Sala Cirurgica` |
| Até o Leito | `Internacao` → primeiro leito físico |

### Ranking — "Top Gargalos por Transição"

Gráfico de barras. Quando `source_filtro = 'Todos'`, mostra Top 1 por
processo (Movimentações excluída desse modo, não comparável); com um
processo específico selecionado, mostra Top 8 daquele processo.

### Heatmap — "Padrão de Gargalos por Dia da Semana"

Matriz de/para × dia da semana. Filtra `frequencia >= 10` e `de != para`
(remove autolaços). Agregação `None` no widget (não `Sum`).

### DFG — "Fluxo da Jornada — Visão Panorâmica"

Custom Viz Vega-Lite, alimentado por `gold_dfg_macro` (ADR-0016). Duas
colunas visuais (Emergência à esquerda, Cirúrgico à direita), gradiente
verde→laranja→vermelho por tempo, espessura de linha proporcional ao
tempo, rótulos com unidade (min/h/dias). Nota de rodapé explica a
transição de retorno "Fim da Cirurgia → Transferência", não desenhada
como aresta própria (ver ADR-0016, item 5, para o porquê da duplicação
visual do nó "Transferência").

---

## Datasets SQL do Dashboard

### `cards_gargalos_macro`

Grão: 1 linha (agregado). Parâmetros: `periodo`, `especialidade_filtro`
(multi). **Sem `source_filtro`**, decisão de design, especialidade
instável por processo na jornada agregada.

> **Lacuna:** SQL completa não capturada nesta sessão de documentação,
> pendente de registro; consultar diretamente no editor do dataset se
> precisar da query exata.

### `ranking_gargalos_chart`

Grão: 1 linha por transição. Parâmetros: `periodo`, `source_filtro`,
`especialidade_filtro` (multi). Coluna `tempo_medio_horas`; `transicao`
formatada para exibição.

> **Lacuna:** SQL completa não capturada nesta sessão de documentação.

### `heatmap_performance_spectrum`

Grão: 1 linha por transição × dia da semana. Parâmetros: `periodo`,
`source_filtro`, `especialidade_filtro` (multi). Filtro
`frequencia >= 10 and de != para`. Coluna `tempo_mediano_horas`.

> **Lacuna:** SQL completa não capturada nesta sessão de documentação.

### `dfg_arestas`

Grão: 1 linha por aresta (transição entre marcos). Parâmetros: `periodo`,
`especialidade_filtro` (multi). **Sem `source_filtro`**, decisão
arquitetural (ADR-0016): o DFG é a visão panorâmica da jornada completa.

```sql
WITH nos AS (
    SELECT * FROM VALUES
        ('Chegada ao Pronto-Socorro', 1, 140, 'Chegada ao PS'),
        ('Início da Triagem', 1, 120, 'Início da Triagem'),
        ('Início do Cadastro', 1, 100, 'Início do Cadastro'),
        ('Início da Consulta Médica', 1, 80, 'Início da Consulta'),
        ('Fim da Consulta Médica', 1, 60, 'Fim da Consulta'),
        ('Alta da Emergência', 1, 40, 'Alta da Emergência'),
        ('Fim', 1, 20, 'Fim (sem internação)'),
        ('Agendamento de Cirurgia', 5, 160, 'Agendamento'),
        ('Aviso de Cirurgia', 5, 140, 'Aviso de Cirurgia'),
        ('Internacao', 5, 120, 'Internação'),
        ('TRANSFERÊNCIA', 5, 100, 'Transferência'),
        ('Entrada na Sala Cirurgica', 5, 80, 'Entrada na Sala'),
        ('Fim da Cirurgia', 5, 60, 'Fim da Cirurgia'),
        ('Prescricao de alta', 5, 40, 'Prescrição de alta'),
        ('Alta médica', 5, 20, 'Alta médica'),
        ('Alta Hospitalar', 5, 0, 'Alta Hospitalar')
    AS t(no_bruto, x, y, no_label)
),
filtrado AS (
    SELECT de, para, tempo_medio_min, frequencia
    FROM hospital_santa_rosa.gold_fluxo.gold_dfg_macro d
    WHERE (:periodo = 'Todos' or d.ano_mes = :periodo)
      AND (:especialidade_filtro is null or array_contains(:especialidade_filtro, d.especialidade))
),
agregado AS (
    SELECT
        de,
        para,
        sum(frequencia) as frequencia,
        sum(tempo_medio_min * frequencia) / sum(frequencia) as tempo_medio_min
    FROM filtrado
    GROUP BY de, para
)
SELECT
    a.de,
    a.para,
    a.tempo_medio_min,
    a.frequencia,
    CASE WHEN a.de = 'TRANSFERÊNCIA' AND a.para = 'Prescricao de alta' THEN 7 ELSE n_de.x END AS x_de,
    CASE WHEN a.de = 'TRANSFERÊNCIA' AND a.para = 'Prescricao de alta' THEN 50 ELSE n_de.y END AS y_de,
    CASE WHEN a.de = 'TRANSFERÊNCIA' AND a.para = 'Prescricao de alta' THEN 'Transferência (pós-cirurgia)' ELSE n_de.no_label END AS label_de,
    CASE WHEN a.de = 'Fim da Cirurgia' AND a.para = 'TRANSFERÊNCIA' THEN 7 ELSE n_para.x END AS x_para,
    CASE WHEN a.de = 'Fim da Cirurgia' AND a.para = 'TRANSFERÊNCIA' THEN 50 ELSE n_para.y END AS y_para,
    CASE WHEN a.de = 'Fim da Cirurgia' AND a.para = 'TRANSFERÊNCIA' THEN 'Transferência (pós-cirurgia)' ELSE n_para.no_label END AS label_para
FROM agregado a
JOIN nos n_de ON a.de = n_de.no_bruto
JOIN nos n_para ON a.para = n_para.no_bruto
```

**Fields obrigatórios do Custom Viz** (declarar em "Fields" além do JSON):
`x_de`, `y_de`, `label_de`, `x_para`, `y_para`, `label_para`,
`tempo_medio_min`, `frequencia`.

**Nota de renderização:** o widget precisa ser redimensionado manualmente
no Canvas para ~900px+ de altura, o `height` do JSON não redimensiona o
container automaticamente.

JSON Vega-Lite completo: ver ADR-0016 (item 5) e o código-fonte publicado
do Custom Viz no editor do widget, não duplicado aqui por já estar
versionado em dois lugares.

---

## Campos calculados do Data Model

Nenhum campo novo foi necessário no Data Model para esta página, a
formatação de tempo (min/h/dias) e o cálculo de P90 já são feitos
diretamente nas queries dos datasets, diferente da Página 1, onde a
regra de "média de médias" exigiu campos calculados sobre
`gold_patient_journey` linha a linha.

---

## Pendências

- Validação dos números e dados desta página, adiada para depois que o
  dashboard inteiro estiver pronto (decisão explícita)