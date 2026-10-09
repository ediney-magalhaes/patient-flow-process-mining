# Dashboard — Página 4: Handover

- **Local:** AI/BI Dashboard `Mapa Digital do Fluxo do Paciente`, aba "Handover"
- **Decisões e achados relacionados:** RQ-015 (contaminação de `ano_mes` no notebook de Process Mining), RQ-016 (handover e subcontracting calculados por `case_id_jornada`) e RQ-017 (contagem em dobro de entradas na UTI)
- **Status:** construída e publicada (02/10/2026). A validação dos números e da leitura clínica depende do histórico (cerca de 2 anos) e das conversas de validação com a área assistencial (ver Pendências)

Mesmo escopo de `dashboard-conformidade.md`: cobre artefatos que vivem dentro do próprio Dashboard (datasets SQL salvos, filtros, widgets, Custom Viz), não objetos do Unity Catalog, isso já está em `data-dictionary.md`.

**Propósito:** responder três perguntas, em duas camadas.

1. Que caminho o paciente fez e onde saiu do esperado? (camada Jornada, desenho por porta de entrada)
2. Para onde vai a saída de cada processo? (camada Handover, heatmap de percentual)
3. Para qual especialidade vai uma passagem escolhida? (camada Handover, gráfico de especialidades)

Além delas, a matriz e as sequências A → B → A mostram o volume do handover entre processos (perspectiva organizacional do Process Mining).

---

## Estrutura da página

Cada camada tem um banner de seção e o filtro dela ao lado.

| Camada | Fonte | Widgets |
|---|---|---|
| Jornada por porta de entrada | `gold_patient_journey`, `gold_event_log`, `silver_movimentacoes` | Desenho (Custom Viz) e nota "Como ler este bloco" |
| Handover entre processos | `gold_sna_handover`, `gold_sna_subcontracting` | Matriz de handover, sequências A → B → A, heatmap de percentual da saída e gráfico de especialidade por passagem |

### Filtros

| Filtro | Parâmetro | Tipo | Controla | Não controla |
|---|---|---|---|---|
| Período | `periodo` | multi-select, bypass `IS NULL` | desenho, matriz, sequências, heatmap de percentual, gráfico de especialidades | — |
| Porta de entrada | `porta` | single value, padrão `Emergência` | desenho | todos os de handover |
| Especialidade (do processo de destino) | `especialidade_filtro` | multi-select, bypass `IS NULL` | matriz e heatmap de percentual | desenho, sequências e gráfico de especialidades |
| Passagem | `passagem` | single value, padrão `Emergência → Internação` | gráfico de especialidades | todos os outros |

**Vínculo por widget:** cada filtro precisa ser ligado individualmente a cada dataset que ele controla, via **Parameters**. Os valores dos dropdowns vêm de datasets auxiliares sem parâmetro (`dim_periodo`, `dim_porta`, `dim_especialidade`, `dim_passagem`), ligados em **Fields**.

**Ao excluir um widget, remover também o vínculo do filtro:** os datasets de gráficos apagados (`handover_ranking`, `desvios_uti`, `apoio_exames`) não podiam ser excluídos enquanto estavam listados em **Parameters** dos filtros. Primeiro remove-se o vínculo, depois o dataset.

**Filtro de Especialidade e as sequências:** o filtro não reage no gráfico de sequências, por decisão. A especialidade do handover é a do evento de **destino**, e no subcontracting é a do processo **intermediário** (B). Ligar o mesmo filtro faria o rótulo significar duas coisas na mesma página. Se for necessário filtrar as sequências, o certo é um filtro separado ("especialidade do processo intermediário").

**Filtro de Especialidade e o gráfico de especialidades:** não se aplica, porque a especialidade é o eixo do gráfico.

### Portas de entrada

A porta é definida pelo `journey_type` de `gold_patient_journey`:

| Porta | `journey_type` incluídos | Jornadas (mar/2026) |
|---|---|---|
| Emergência | `atendimento_emergencia`, `internacao_clinica`, `internacao_cirurgica_emergencia` | 6.235 |
| Cirurgia Eletiva | `internacao_cirurgica_eletiva` | 364 |
| Internação Clínica | `internacao_clinica_direta` | 58 |

`cirurgia_ambulatorial` (1 jornada) fica fora. A porta "Internação Clínica" é um caso raro e vai para discussão na validação dos dados.

---

## Widgets

Textos de Description curtos por decisão: o texto fica no gráfico só se evita uma leitura errada. O detalhe fica aqui.

### Desenho da jornada (Custom Viz Vega-Lite)

- **Dataset:** `espinha_arestas`. Filtros ligados: `porta` e `periodo`.
- **Fields declarados no widget:** `seta`, `de`, `para`, `x_de`, `y_de`, `x_para`, `y_para`, `valor`, `base`, `pct`, `tipo`, `sem_dado`, `x_mid`, `y_mid`, `rotulo`.
- **Título:** "Handover da jornada por porta de entrada: etapas, desvios e apoio diagnóstico (jornadas e % sobre a base de cada seta)".
- **Description:** "Base do %: jornadas da porta (alta sem internação, internação e apoio), internados (cirurgia, UTI e alta) ou pacientes de UTI (reentrada)."
- **Tamanho:** `width` 1000 e `height` 480 no JSON. O container precisa ser ajustado manualmente no Canvas, porque o `height` do JSON não redimensiona o widget (mesma limitação do DFG da Página 2).

**Construção:** cada linha do dataset é uma seta com posição fixa (`x_de`, `y_de`, `x_para`, `y_para`), como no `dfg_arestas`. As camadas são: linhas (`rule`), rótulo da seta, círculos dos nós e nome dos nós. Os textos têm contorno branco (camada duplicada, uma com `stroke` branco por baixo e outra com a cor final por cima) para não ficarem ilegíveis sobre as linhas.

| Elemento | Regra |
|---|---|
| Cor | `tipo`: Fluxo principal `#00799B`, Desvio `#D85A30`, Apoio diagnóstico `#EF9F27` |
| Espessura | proporcional a `pct`, escala de raiz quadrada (sem ela, Emergência → Internação, com 7,2%, ficava a linha mais fina) |
| Legenda | no topo, horizontal, título "Tipo de fluxo" |
| Rótulo da seta | `rotulo` = valor e percentual; "sem dado" quando o apoio vem zerado |
| Nó | círculo com nome (`de` e `para`) |

**Armadilha do Custom Viz:** `transform` com `calculate` ou `filter` dentro do JSON fez o desenho aparecer em branco, sem mensagem de erro. Todo cálculo (tipo da seta, posição e texto do rótulo) foi movido para o SQL do dataset, e o JSON só mapeia campos. Ao mexer no desenho, mudar o SQL e não o JSON.

**Posição dos rótulos (no SQL):** seta que desce da linha central (y=50): rótulo a 65% do caminho, longe do nome do nó de origem. Seta que desce de y=20 para y=0: rótulo deslocado 0,6 para a direita.

| Porta | Fluxo principal | Desvios | Apoio |
|---|---|---|---|
| Emergência | Emergência → Internação → Alta; Emergência → Alta sem internação | Cirurgia; UTI antes da cirurgia; UTI após a cirurgia; UTI sem cirurgia; Reentrada na UTI | Imagem e laboratório, ligados à Emergência |
| Cirurgia Eletiva | Internação → Cirurgia → Alta | UTI antes da cirurgia; UTI após a cirurgia | Imagem e laboratório, ligados à Internação |
| Internação Clínica | Internação → Alta | UTI; Reentrada na UTI | Imagem e laboratório, ligados à Internação |

A cirurgia é desvio na Emergência (bifurcação de uma minoria dos internados) e fluxo principal na Cirurgia Eletiva (caminho esperado).

**Base dos percentuais:** setas que saem da Emergência (alta sem internação, internação e apoio) usam todas as jornadas da porta. Cirurgia, UTI e alta usam os internados. Reentrada usa os pacientes que passaram pela UTI. Nas portas sem emergência, a base é o total de internados, e o apoio usa as jornadas da porta.

**Contagens de UTI em jornadas cirúrgicas (mar/2026):** na Cirurgia Eletiva, 12 antes, 35 depois e 2 nos dois grupos. Na Emergência, 56 antes, 19 depois e 2 nos dois.

**Caixa "Como ler este bloco"** (ao lado do desenho): laboratório "sem dado" não significa ausência de exame; um paciente pode estar em dois ramos de UTI, então os ramos podem somar mais que o total com UTI; reentrada na UTI não aparece nas jornadas cirúrgicas, onde a volta após a operação está em "UTI após a cirurgia".

### Matriz de handover (heatmap)

- **Dataset:** `handover_matriz`. Filtros ligados: `periodo` e `especialidade_filtro`.
- **Eixos:** linhas = `origem` ("De (processo de origem)"), colunas = `destino` ("Para (processo de destino)").
- **Cor:** `SUM(frequencia)`, nome de exibição "Transições". Rótulos de valor ligados.
- **Description:** "Sucessão de eventos por horário na mesma jornada, e não fluxo clínico. Ex.: 'Alta → Internação' são registros de alta do mesmo episódio."
- **Leitura:** 7 processos nas linhas e 5 nas colunas. Exame Laboratorial e Movimentações nunca aparecem como destino. Idas e vindas dentro do mesmo processo (como as movimentações de UTI) não aparecem.

### Heatmap de percentual da saída

- **Dataset:** `handover_pct`. Filtros ligados: `periodo` e `especialidade_filtro`.
- **Título:** "Para onde vai a saída de cada processo (% das transições de cada linha)".
- **Eixos:** mesmos da matriz. Cor: `SUM(pct_da_saida)`, nome de exibição "% da saída". Rótulos de valor ligados.
- **Description:** "Cada linha soma 100%. Linhas com poucas transições oscilam (ex.: Internação, 34): confira a matriz acima. Difere do desenho da jornada, que usa outra base."
- **Percentual dentro do filtro:** a função de janela recalcula 100% para o que sobra depois do filtro.
- **Diferença para o desenho:** Emergência → Internação é 10,5% aqui (base: transições que saem da Emergência, dominadas por exames) e 7,2% no desenho (base: jornadas da porta). Bases diferentes, por isso a Description avisa.

### Sequências A → B → A

- **Dataset:** `subcontracting_sequencias`. Filtro ligado: `periodo`.
- **Gráfico:** barras horizontais, top 10, ordenadas por frequência decrescente, com rótulos de valor.
- **Description:** "Ordem observada por horário: não prova delegação nem retrabalho. O filtro de Especialidade não se aplica."

### Especialidade de destino da passagem escolhida

- **Dataset:** `handover_especialidade`. Filtros ligados: `periodo` e `passagem` (valor único).
- **Título:** "Especialidade de destino da passagem escolhida (número de transições)".
- **Gráfico:** barras horizontais ordenadas, eixo X "Número de transições", eixo Y "Especialidade do processo de destino", rótulos de valor.
- **Tooltip:** `SUM(pct_da_passagem)`, nome de exibição "% da passagem". O percentual fica no tooltip para não poluir o gráfico.
- **Description:** "O filtro de Especialidade do topo não se aplica a este gráfico."
- **Referência (mar/2026), Emergência → Internação:** Clínica Médica 132, Generalista 63, Geriatria 51, Pediatria 42, Cirurgia Geral 33, Cardiologia 29, Ortopedia 13, total 370.
- **Por que barras e não funil:** as especialidades são categorias paralelas, não etapas em que cada uma é subconjunto da anterior. Funil sugeriria uma perda entre etapas que não existe.
- **Passagens sem especialidade:** Laboratório e Movimentações não têm especialidade, então passagens que partem ou chegam nesses processos podem mostrar poucas especialidades.

### Banners

Dois banners de seção (caixas de texto com fundo azul-claro): "Jornada por porta de entrada" e "Handover entre processos".

### Widgets removidos durante a construção

| Widget removido | Motivo | Substituto |
|---|---|---|
| Ranking de handover por especialidade | Repetia a matriz com o filtro de Especialidade | Matriz e gráfico de especialidade por passagem |
| Gráfico "UTI por tipo de jornada" | Repetia o desenho, por tipo de jornada e não por porta | Desenho |
| Gráfico "Reentrada na UTI por tipo de jornada" | Mostrava 8,2% na cirúrgica via emergência, enquanto o desenho deixa essas reentradas de fora de propósito (ver RQ-017) | Desenho |
| Gráfico "Apoio diagnóstico por tipo de jornada" | Bases diferentes das do desenho (36,2% contra 39,6%) | Desenho |

**Funil avaliado e descartado (06/10/2026).** Nem na Página 1 nem na Página 4. Só a cadeia emergência, internação e alta final é de subconjuntos encadeados (6.235, 452 e 358 em mar/2026). Cirurgia e UTI são ramos paralelos, e um funil sugeriria ordem e perda que não existem. A conversão (7,2%) já está nos cards da Página 1 e a passagem no desenho da Página 4. A alta final sofre do viés de internações sem alta no corte do mês.

---

## Datasets SQL do Dashboard

### `espinha_arestas`

Grão: 1 linha por seta do desenho. Parâmetros: `porta` (valor único, sem *Allow multiple selections*) e `periodo` (multi-select). Alimenta o desenho.

Linhas por porta: Emergência 10, Cirurgia Eletiva 6, Internação Clínica 5. Valores de referência (mar/2026) estão na seção Widgets.

```sql
with jr as (
    select
        ts_alta_final, has_cirurgia, has_uti, qtd_reentradas_uti, journey_type, ts_entrada_cirurgia,
        coalesce(cd_internacao, cd_atendimento) as chave
    from hospital_santa_rosa.gold_fluxo.gold_patient_journey
    where case
              when journey_type in ('atendimento_emergencia', 'internacao_clinica', 'internacao_cirurgica_emergencia') then 'Emergência'
              when journey_type = 'internacao_cirurgica_eletiva' then 'Cirurgia Eletiva'
              when journey_type = 'internacao_clinica_direta' then 'Internação Clínica'
          end = :porta
      and (:periodo is null or array_contains(:periodo, ano_mes))
),
ev as (
    select
        case_id_jornada,
        max(case when source = 'silver_exames_imagem' then 1 else 0 end) as tem_imagem,
        max(case when source = 'silver_exames_laboratoriais' then 1 else 0 end) as tem_lab
    from hospital_santa_rosa.gold_fluxo.gold_event_log
    group by 1
),
ent as (
    select distinct CD_INTERNACAO, DT_HR_MOVIMENTACAO as ts
    from hospital_santa_rosa.silver_fluxo.silver_movimentacoes
    where DESTINO rlike '^(UTIA1|UTIA2|UTIB|UCO|UNP)'
      and not coalesce(ORIGEM rlike '^(UTIA1|UTIA2|UTIB|UCO|UNP)', false)
),
uc as (
    select
        count(distinct case when e.ts < jr.ts_entrada_cirurgia then jr.chave end) as uti_pre,
        count(distinct case when e.ts >= jr.ts_entrada_cirurgia then jr.chave end) as uti_pos
    from jr join ent e on e.CD_INTERNACAO = jr.chave
    where jr.has_cirurgia
),
m as (
    select
        count(*) as jornadas,
        sum(case when jr.journey_type <> 'atendimento_emergencia' then 1 else 0 end) as internaram,
        sum(case when jr.journey_type <> 'atendimento_emergencia' and jr.ts_alta_final is not null then 1 else 0 end) as com_alta_final,
        sum(case when jr.journey_type <> 'atendimento_emergencia' and jr.has_cirurgia then 1 else 0 end) as cirurgia,
        sum(case when jr.has_uti then 1 else 0 end) as uti,
        sum(case when jr.qtd_reentradas_uti > 0 then 1 else 0 end) as reentrada_uti,
        sum(case when jr.has_uti and not jr.has_cirurgia then 1 else 0 end) as uti_sem_cir,
        sum(case when jr.qtd_reentradas_uti > 0 and not jr.has_cirurgia then 1 else 0 end) as reentrada_sem_cir,
        sum(coalesce(ev.tem_imagem, 0)) as com_imagem,
        sum(coalesce(ev.tem_lab, 0)) as com_lab
    from jr left join ev on jr.chave = ev.case_id_jornada
),
setas as (
    -- Emergência: desfecho sem internação e passagem para a internação
    select 'Emergência → Alta sem internação' as seta, 'Emergência' as de, 'Alta sem internação' as para,
           1 as x_de, 50 as y_de, 1 as x_para, 20 as y_para,
           jornadas - internaram as valor, jornadas as base, 'Fluxo principal' as tipo
    from m where :porta = 'Emergência'
    union all
    select 'Emergência → Internação', 'Emergência', 'Internação', 1, 50, 4, 50, internaram, jornadas, 'Fluxo principal'
    from m where :porta = 'Emergência'
    union all
    -- Internação → Alta (Emergência e Internação Clínica)
    select 'Internação → Alta', 'Internação', 'Alta',
           case when :porta = 'Emergência' then 4 else 1 end, 50, 7, 50,
           com_alta_final, internaram, 'Fluxo principal'
    from m where :porta <> 'Cirurgia Eletiva'
    union all
    -- Emergência: a cirurgia é desvio
    select 'Internação → Cirurgia', 'Internação', 'Cirurgia', 4, 50, 4, 20, cirurgia, internaram, 'Desvio'
    from m where :porta = 'Emergência'
    union all
    -- Emergência: UTI em três ramos, em ordem cronológica da esquerda para a direita
    select 'Internação → UTI antes da cirurgia', 'Internação', 'UTI antes da cirurgia', 4, 50, 2.2, 20, uc.uti_pre, m.internaram, 'Desvio'
    from m cross join uc where :porta = 'Emergência'
    union all
    select 'Cirurgia → UTI após a cirurgia', 'Cirurgia', 'UTI após a cirurgia', 4, 20, 4, 0, uc.uti_pos, m.internaram, 'Desvio'
    from m cross join uc where :porta = 'Emergência'
    union all
    select 'Internação → UTI sem cirurgia', 'Internação', 'UTI sem cirurgia', 4, 50, 6, 20, uti_sem_cir, internaram, 'Desvio'
    from m where :porta = 'Emergência'
    union all
    select 'UTI sem cirurgia → Reentrada na UTI', 'UTI sem cirurgia', 'Reentrada na UTI', 6, 20, 6, 0, reentrada_sem_cir, uti_sem_cir, 'Desvio'
    from m where :porta = 'Emergência'
    union all
    -- Cirurgia Eletiva: a cirurgia faz parte do fluxo principal
    select 'Internação → Cirurgia', 'Internação', 'Cirurgia', 1, 50, 4, 50, cirurgia, internaram, 'Fluxo principal'
    from m where :porta = 'Cirurgia Eletiva'
    union all
    select 'Cirurgia → Alta', 'Cirurgia', 'Alta', 4, 50, 7, 50, com_alta_final, internaram, 'Fluxo principal'
    from m where :porta = 'Cirurgia Eletiva'
    union all
    select 'Internação → UTI antes da cirurgia', 'Internação', 'UTI antes da cirurgia', 1, 50, 2, 20, uc.uti_pre, m.internaram, 'Desvio'
    from m cross join uc where :porta = 'Cirurgia Eletiva'
    union all
    select 'Cirurgia → UTI após a cirurgia', 'Cirurgia', 'UTI após a cirurgia', 4, 50, 5, 20, uc.uti_pos, m.internaram, 'Desvio'
    from m cross join uc where :porta = 'Cirurgia Eletiva'
    union all
    -- Internação Clínica: UTI e reentrada
    select 'Internação → UTI', 'Internação', 'UTI', 1, 50, 2.5, 20, uti, internaram, 'Desvio'
    from m where :porta = 'Internação Clínica'
    union all
    select 'UTI → Reentrada na UTI', 'UTI', 'Reentrada na UTI', 2.5, 20, 2.5, 0, reentrada_uti, uti, 'Desvio'
    from m where :porta = 'Internação Clínica'
    union all
    -- Apoio diagnóstico (as três portas), sempre ligado ao nó de entrada em x=1
    select 'Apoio: Exames de imagem', 'Exames de imagem',
           case when :porta = 'Emergência' then 'Emergência' else 'Internação' end,
           0, 95, 1, 50, com_imagem, jornadas, 'Apoio diagnóstico'
    from m
    union all
    select 'Apoio: Laboratório', 'Laboratório',
           case when :porta = 'Emergência' then 'Emergência' else 'Internação' end,
           2, 95, 1, 50, com_lab, jornadas, 'Apoio diagnóstico'
    from m
)
select
    seta, de, para, x_de, y_de, x_para, y_para, valor, base,
    round(valor * 100.0 / nullif(base, 0), 1) as pct,
    (seta like 'Apoio%' and valor = 0) as sem_dado,
    tipo,
    case when y_de = 20 and y_para = 0 then (x_de + x_para) / 2.0 + 0.6
         when y_de = 50 and y_para < 50 then x_de + 0.65 * (x_para - x_de)
         else (x_de + x_para) / 2.0 end as x_mid,
    case when y_de = 50 and y_para < 50 then y_de + 0.65 * (y_para - y_de)
         else (y_de + y_para) / 2.0 end as y_mid,
    case
        when seta like 'Apoio%' and valor = 0 then 'sem dado'
        else concat(cast(valor as string), ' (', cast(round(valor * 100.0 / nullif(base, 0), 1) as string), '%)')
    end as rotulo
from setas
```

**Como a UTI é contada:** `ent` lista cada entrada na UTI vinda de **fora** da UTI, a partir de `silver_movimentacoes` (`SELECT DISTINCT` deduplica os pares `TRANSFER. DE` e `TRANSFER. PARA`, ver RQ-017). `uti_pre` e `uti_pos` contam pacientes com entrada antes ou a partir da entrada na sala cirúrgica. Um paciente pode estar nos dois grupos.

**Sobre as posições:** as coordenadas (x, y) são fixas no SQL, como no `dfg_arestas` da Página 2. Mudar uma posição é mudar o SQL, não o JSON.

**Custom Viz do desenho (JSON publicado em 02/10/2026):**

```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "data": {"name": "databricks_query"},
  "layer": [
    {
      "mark": {"type": "rule", "opacity": 0.85},
      "encoding": {
        "x": {"field": "x_de", "type": "quantitative", "axis": null, "scale": {"domain": [-1, 8]}},
        "y": {"field": "y_de", "type": "quantitative", "axis": null, "scale": {"domain": [-20, 110]}},
        "x2": {"field": "x_para"},
        "y2": {"field": "y_para"},
        "color": {"field": "tipo", "type": "nominal", "scale": {"domain": ["Fluxo principal", "Desvio", "Apoio diagnóstico"], "range": ["#00799B", "#D85A30", "#EF9F27"]}, "title": "Tipo de fluxo", "legend": {"orient": "top", "direction": "horizontal", "titleFontSize": 12, "symbolStrokeWidth": 4}},
        "strokeWidth": {"field": "pct", "type": "quantitative", "scale": {"type": "sqrt", "range": [1.5, 9], "domain": [0, 100]}, "legend": null}
      }
    },
    {
      "mark": {"type": "text", "fontSize": 10, "color": "white", "stroke": "white", "strokeWidth": 4, "dy": -10},
      "encoding": {
        "x": {"field": "x_mid", "type": "quantitative", "axis": null, "scale": {"domain": [-1, 8]}},
        "y": {"field": "y_mid", "type": "quantitative", "axis": null, "scale": {"domain": [-20, 110]}},
        "text": {"field": "rotulo", "type": "nominal"}
      }
    },
    {
      "mark": {"type": "text", "fontSize": 10, "color": "#52514E", "dy": -10},
      "encoding": {
        "x": {"field": "x_mid", "type": "quantitative", "axis": null, "scale": {"domain": [-1, 8]}},
        "y": {"field": "y_mid", "type": "quantitative", "axis": null, "scale": {"domain": [-20, 110]}},
        "text": {"field": "rotulo", "type": "nominal"}
      }
    },
    {
      "mark": {"type": "circle", "size": 700, "color": "#F1EFE8", "stroke": "#52514E", "strokeWidth": 1.5, "opacity": 1},
      "encoding": {
        "x": {"field": "x_de", "type": "quantitative", "axis": null, "scale": {"domain": [-1, 8]}},
        "y": {"field": "y_de", "type": "quantitative", "axis": null, "scale": {"domain": [-20, 110]}}
      }
    },
    {
      "mark": {"type": "circle", "size": 700, "color": "#F1EFE8", "stroke": "#52514E", "strokeWidth": 1.5, "opacity": 1},
      "encoding": {
        "x": {"field": "x_para", "type": "quantitative", "axis": null, "scale": {"domain": [-1, 8]}},
        "y": {"field": "y_para", "type": "quantitative", "axis": null, "scale": {"domain": [-20, 110]}}
      }
    },
    {
      "mark": {"type": "text", "fontSize": 11, "fontWeight": "bold", "color": "white", "stroke": "white", "strokeWidth": 4, "dy": 22},
      "encoding": {
        "x": {"field": "x_de", "type": "quantitative", "axis": null, "scale": {"domain": [-1, 8]}},
        "y": {"field": "y_de", "type": "quantitative", "axis": null, "scale": {"domain": [-20, 110]}},
        "text": {"field": "de", "type": "nominal"}
      }
    },
    {
      "mark": {"type": "text", "fontSize": 11, "fontWeight": "bold", "color": "#042C53", "dy": 22},
      "encoding": {
        "x": {"field": "x_de", "type": "quantitative", "axis": null, "scale": {"domain": [-1, 8]}},
        "y": {"field": "y_de", "type": "quantitative", "axis": null, "scale": {"domain": [-20, 110]}},
        "text": {"field": "de", "type": "nominal"}
      }
    },
    {
      "mark": {"type": "text", "fontSize": 11, "fontWeight": "bold", "color": "white", "stroke": "white", "strokeWidth": 4, "dy": 22},
      "encoding": {
        "x": {"field": "x_para", "type": "quantitative", "axis": null, "scale": {"domain": [-1, 8]}},
        "y": {"field": "y_para", "type": "quantitative", "axis": null, "scale": {"domain": [-20, 110]}},
        "text": {"field": "para", "type": "nominal"}
      }
    },
    {
      "mark": {"type": "text", "fontSize": 11, "fontWeight": "bold", "color": "#042C53", "dy": 22},
      "encoding": {
        "x": {"field": "x_para", "type": "quantitative", "axis": null, "scale": {"domain": [-1, 8]}},
        "y": {"field": "y_para", "type": "quantitative", "axis": null, "scale": {"domain": [-20, 110]}},
        "text": {"field": "para", "type": "nominal"}
      }
    }
  ],
  "width": 1000,
  "height": 480
}
```

### `handover_matriz`

Grão: 1 linha por par origem × destino. Parâmetros: `periodo` e `especialidade_filtro`, ambos multi-select. Alimenta a matriz.

```sql
select
    o.source_label as origem,
    d.source_label as destino,
    sum(h.frequencia) as frequencia
from hospital_santa_rosa.gold_fluxo.gold_sna_handover h
join hospital_santa_rosa.gold_fluxo.vw_dim_source o on h.source_anterior = o.source
join hospital_santa_rosa.gold_fluxo.vw_dim_source d on h.source = d.source
left join hospital_santa_rosa.gold_fluxo.vw_dim_especialidade e on h.especialidade = e.especialidade_origem
where (:periodo is null or array_contains(:periodo, h.ano_mes))
  and (:especialidade_filtro is null or array_contains(:especialidade_filtro, coalesce(e.especialidade_label, h.especialidade)))
group by 1, 2
```

### `handover_pct`

Grão: 1 linha por par origem × destino, com o percentual dentro da origem. Parâmetros: `periodo` e `especialidade_filtro`, ambos multi-select. Alimenta o heatmap de percentual. A função de janela recalcula o 100% depois do filtro.

```sql
select
    o.source_label as origem,
    d.source_label as destino,
    sum(h.frequencia) as transicoes,
    round(sum(h.frequencia) * 100.0 / sum(sum(h.frequencia)) over (partition by o.source_label), 1) as pct_da_saida
from hospital_santa_rosa.gold_fluxo.gold_sna_handover h
join hospital_santa_rosa.gold_fluxo.vw_dim_source o on h.source_anterior = o.source
join hospital_santa_rosa.gold_fluxo.vw_dim_source d on h.source = d.source
left join hospital_santa_rosa.gold_fluxo.vw_dim_especialidade e on h.especialidade = e.especialidade_origem
where (:periodo is null or array_contains(:periodo, h.ano_mes))
  and (:especialidade_filtro is null or array_contains(:especialidade_filtro, coalesce(e.especialidade_label, h.especialidade)))
group by 1, 2
```

### `handover_especialidade`

Grão: 1 linha por especialidade, para a passagem escolhida. Parâmetros: `passagem` (valor único, sem *Allow multiple selections*) e `periodo` (multi-select). Alimenta o gráfico de especialidades. Não tem `especialidade_filtro`, porque a especialidade é o eixo do gráfico.

```sql
select
    coalesce(e.especialidade_label, h.especialidade, 'Sem especialidade') as especialidade,
    sum(h.frequencia) as transicoes,
    round(sum(h.frequencia) * 100.0 / sum(sum(h.frequencia)) over (), 1) as pct_da_passagem
from hospital_santa_rosa.gold_fluxo.gold_sna_handover h
join hospital_santa_rosa.gold_fluxo.vw_dim_source o on h.source_anterior = o.source
join hospital_santa_rosa.gold_fluxo.vw_dim_source d on h.source = d.source
left join hospital_santa_rosa.gold_fluxo.vw_dim_especialidade e on h.especialidade = e.especialidade_origem
where concat(o.source_label, ' → ', d.source_label) = :passagem
  and (:periodo is null or array_contains(:periodo, h.ano_mes))
group by 1
order by transicoes desc
```

### `subcontracting_sequencias`

Grão: 1 linha por sequência A → B → A (top 10). Parâmetro: `periodo` (multi-select). Alimenta o gráfico de sequências.

```sql
select
    concat(a.source_label, ' → ', b.source_label, ' → ', a.source_label) as sequencia,
    sum(s.frequencia) as frequencia
from hospital_santa_rosa.gold_fluxo.gold_sna_subcontracting s
join hospital_santa_rosa.gold_fluxo.vw_dim_source a on s.source = a.source
join hospital_santa_rosa.gold_fluxo.vw_dim_source b on s.source_1_atras = b.source
where (:periodo is null or array_contains(:periodo, s.ano_mes))
group by 1
order by frequencia desc
limit 10
```

### Datasets auxiliares dos filtros

Sem parâmetros. Populam os dropdowns, ligados em **Fields**.

- `dim_periodo`: `select distinct ano_mes from hospital_santa_rosa.gold_fluxo.gold_patient_journey order by ano_mes`
- `dim_porta`:

```sql
select 'Emergência' as porta
union all
select 'Cirurgia Eletiva' as porta
union all
select 'Internação Clínica' as porta
```

- `dim_passagem` (27 passagens, o mesmo número de pares da matriz):

```sql
select distinct concat(o.source_label, ' → ', d.source_label) as passagem
from hospital_santa_rosa.gold_fluxo.gold_sna_handover h
join hospital_santa_rosa.gold_fluxo.vw_dim_source o on h.source_anterior = o.source
join hospital_santa_rosa.gold_fluxo.vw_dim_source d on h.source = d.source
order by 1
```

- `dim_especialidade`: dataset já existente, compartilhado com a Página 2. Aplica `vw_dim_especialidade` (nome traduzido quando existe, nome bruto quando não) e lê de `gold_bottleneck`. Cobre todas as especialidades de `gold_sna_handover` (conferido em 06/10/2026), mas se uma especialidade nova aparecer só no handover, ela não entrará no filtro até existir no bottleneck.

```sql
SELECT DISTINCT COALESCE(v.especialidade_label, b.especialidade) AS especialidade
FROM hospital_santa_rosa.gold_fluxo.gold_bottleneck b
LEFT JOIN hospital_santa_rosa.gold_fluxo.vw_dim_especialidade v
  ON b.especialidade = v.especialidade_origem
WHERE b.especialidade IS NOT NULL
ORDER BY especialidade
```

### Datasets excluídos

`espinha_jornada` (passo intermediário, substituído por `espinha_arestas`), `handover_ranking`, `desvios_uti` e `apoio_exames` (gráficos removidos, ver Widgets). Os três últimos só puderam ser excluídos depois de remover o vínculo em **Parameters** dos filtros.

---

## Pendências

Todos os visuais previstos para a página foram construídos. O que segue aberto depende do histórico (cerca de 2 anos) ou de validação com a área assistencial. Hoje só existe 2026-03, então não há tendência temporal e as contagens pequenas oscilam.

### Reavaliar com o histórico

- **Reentrada na UTI nas jornadas cirúrgicas.** O desenho não mostra reentrada na Cirurgia Eletiva (2 jornadas com `qtd_reentradas_uti > 0`, ambas UTI pós-operatória já contada no ramo "UTI após a cirurgia"). Na Emergência, as 6 reentradas de pacientes cirúrgicos ficaram fora, porque não se separa UTI pós-operatória esperada de retorno real (4 dessas 6 têm alguma entrada pós-operatória). Separar exige contar entradas por paciente depois da cirurgia.
- **Filtro de especialidade das sequências.** Não reage por decisão (ver Estrutura da página). Se for necessário, criar filtro próprio, "especialidade do processo intermediário".

### Para discussão clínica

- **Internação Clínica (58 jornadas)** como porta de entrada. Internação clínica sem passagem pela emergência é caso raro e vai para a validação dos dados (ver RQ-010).
- **UTI antes da cirurgia eletiva (12 de 45 pacientes com UTI, 27%).** Pode ser estabilização pré-operatória ou problema de registro.
- **UTI "durante" a cirurgia (6 pacientes no total).** A primeira entrada na UTI cai entre a entrada e a saída da sala cirúrgica. Suspeita de timestamp inconsistente, como na RQ-005. Não investigado.
- **Internados sem alta final registrada (94 na Emergência, 60 nas demais portas).** A hipótese é que ainda estavam internados no fim de março. Não conferido.

### Limitações de dado

- **Laboratório "sem dado"** nas portas sem emergência: a base de exames laboratoriais só cobre pacientes de emergência. Quando passar a cobrir internados, o desenho muda sem alterar a query. `valor = 0` não distingue "sem dado" de "ninguém fez exame".
- **Handover não mostra passagens dentro do mesmo processo.** As idas e vindas de UTI vivem dentro de Movimentações e só aparecem no desenho da jornada.
- **Percentuais com bases diferentes.** Emergência → Internação é 7,2% no desenho (base: jornadas da porta) e 10,5% no heatmap de percentual (base: transições que saem da Emergência). Avisado nas Descriptions.
- **2 jornadas de internação clínica via emergência** não têm eventos no `gold_event_log` (ficam sem apoio diagnóstico). Causa não investigada.

### Dívida técnica

- **Lógica de UTI duplicada.** Os prefixos de unidade de UTI (`UTIA1`, `UTIA2`, `UTIB`, `UCO`, `UNP`) e a regra "entrada vinda de fora da UTI" estão em dois lugares: `gold_transformation.py` (`qtd_passagens_uti`) e o dataset `espinha_arestas` (CTE `ent`). Se uma mudar sem a outra, os números divergem sem aviso. Avaliar levar a contagem de UTI antes/depois da cirurgia para o `gold_patient_journey`.