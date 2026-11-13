# Dashboard — Página 1: KPIs de Jornada

- **Local:** AI/BI Dashboard `Mapa Digital do Fluxo do Paciente`, aba "KPIs de Jornada"
- **Decisão arquitetural:** ADR-0014 (nomenclatura de negócio de `journey_type` e
  estrutura Bloco A / Bloco B)
- **Status:** publicado em 13/11/2026, com os dados de mar/2026, o único mês carregado

Este documento cobre artefatos que vivem **dentro do próprio Dashboard**
(datasets SQL salvos e campos calculados do Data Model), não versionados
como objetos do Unity Catalog. Diferente de `data-dictionary.md`, que cobre
tabelas e views reais do catálogo, o conteúdo aqui só existe dentro da
definição do Dashboard e não é consultável via notebook ou outro cliente SQL.

---

## Estrutura da página

Duas seções, cada uma com um título Markdown como divisor visual (fundo roxo/lavanda para "Jornada Emergência", azul para "Jornada Internação"), um filtro global `Período` (seleção múltipla, campo `ano_mes`) no topo e cards de KPI. A Emergência tem dois gráficos: distribuição por tipo de jornada e tendência mensal. A Internação tem quatro visuais: distribuição por tipo de jornada, tendência mensal, etapas até o leito e a tabela por unidade do 1º leito. Todos os visuais respondem ao filtro `Período`, exceto as duas tendências mensais, que mostram sempre a série completa.

### Seção "Jornada Emergência" (Bloco A)

**Cards** (todos filtrados a `Cd Atendimento Is Null = false`):

| Card | Fonte | Cálculo |
|---|---|---|
| Total de Atendimentos | `gold_patient_journey` | `COUNT DISTINCT(cd_atendimento)` |
| Taxa de Conversão (%) | `gold_patient_journey` | `AVG(Fl Conversao)`, formato % |
| Conversão cirúrgica (% dos atendimentos do PA) | `gold_patient_journey` | `AVG(Has Cirurgia Numerico)`, formato %. Base: todos os atendimentos do PA (6.236 em mar/2026, resultado 2,74%) |
| Conversão UTI (% dos atendimentos do PA) | `gold_patient_journey` | `AVG(Internou Em Uti Numerico)`, formato %. Base: todos os atendimentos do PA. Conta o atendimento que internou em UTI: o primeiro leito real da internação é de UTI, ou a internação foi registrada em leito de UTI (resultado 2,73% em mar/2026, ver `validacao-dashboard.md`) |
| Mediana do tempo até o leito (h) | `kpis_jornada_emergencia_cards` | Valor `mediana_formatada_leito` (mediana) e comparação `p90_formatado_leito` (P90), da espera real pelo leito. Nas internações clínicas, conta da abertura da internação até o 1º leito; nas cirúrgicas via emergência, da saída da sala até o 1º leito, só quando o 1º leito é posterior à saída da sala (297 casos em mar/2026: mediana de 3,1 h e P90 de 13,1 h). O recorte `cd_atendimento is not null` está na SQL do dataset, e o cartão responde ao filtro `Período` pelo parâmetro `periodo`. Padrão do ADR-0023 |
| Mediana da Jornada (h) | `kpis_jornada_emergencia_cards` | Valor `mediana_formatada_jornada` (mediana) e comparação `p90_formatado_jornada` (P90), dos atendimentos do PA com duração da emergência (`duracao_emergencia_min`: chegada até a alta da emergência ou, no convertido sem alta, até a abertura da internação, ADR-0025): 5.597 em mar/2026, mediana de 3,1 h e P90 de 6,6 h. Os 639 sem alta registrada ficam fora do cálculo e são contados na dica do gráfico por tipo de jornada. O cartão responde ao filtro `Período` pelo parâmetro `periodo`. Padrão do ADR-0023 |

**Gráfico "Mediana da Jornada por Tipo (Emergência)"** — barra,
dataset `kpis_jornada_emergencia_por_tipo`, eixo X `tipo_jornada`, eixo Y
`SUM(mediana_horas)` (título "Horas (mediana)"), ordenado decrescente. A dica
mostra P90 (h), Casos com duração e Casos sem duração. A barra mede a duração
da emergência (`duracao_emergencia_min`, ADR-0025), no mesmo padrão do cartão
"Mediana da Jornada (h)" (ADR-0023). Cobre as quatro categorias do Bloco A. Em
mar/2026, os 639 casos sem duração estão todos em Atendimento Emergência, e
Cirurgia Ambulatorial tem 1 caso, com mediana e P90 iguais.

**Gráfico "Tendência Mensal — Mediana e Percentil 90 da Jornada"** — linha,
dataset `kpis_jornada_emergencia`, eixo X `ano_mes`, eixo Y "Horas" com duas
séries, `SUM(mediana_horas)` (Mediana (h)) e `SUM(p90_horas)` (P90 (h)), da
duração da emergência (`duracao_emergencia_min`, ADR-0025; padrão do
ADR-0023). Configurado para **ignorar** o filtro
global `Período` — sempre mostra a série histórica completa, mesmo quando
um mês específico está selecionado nos cards.

### Seção "Jornada Internação" (hospital todo — Bloco A + Bloco B)

**Cards** (todos filtrados a `Cd Internacao Is Null = false`):

| Card | Fonte | Cálculo |
|---|---|---|
| Total de Internações | `gold_patient_journey` | `COUNT DISTINCT(cd_internacao)` |
| Internações via Emergência (%) | `gold_patient_journey` | `AVG(Is Internacao Via Emergencia)`, formato % |
| Internações cirúrgicas (% das internações) | `gold_patient_journey` | `AVG(Has Cirurgia Numerico)`, formato %. Base: todas as internações do hospital (867 em mar/2026, resultado 61,59%) |
| Internações com UTI (% das internações) | `gold_patient_journey` | `AVG(Has Uti Numerico)`, formato %. Base: todas as internações do hospital (resultado 28,72%) |
| Mediana da Jornada | `kpis_jornada_internacao_cards` | Valor `mediana_formatada_jornada` (mediana) e comparação `p90_formatado_jornada` (P90), das internações do Bloco B com alta: 1 d 4 h e P90 de 2 d 20 h em mar/2026. Mostra dias e horas a partir de 24 h. Responde ao filtro `Período` pelo parâmetro `periodo` |
| Mediana das Internações em Curso | `kpis_jornada_internacao_cards` | Valor `mediana_formatada_em_curso` (mediana) e comparação `qtd_em_curso_formatada`, das internações do Bloco B sem alta, medidas até o fim provisório: 4 d 12 h e 59 sem alta em mar/2026. Responde ao filtro `Período` pelo parâmetro `periodo` |

**Gráfico "Mediana da Jornada por Tipo (Internação)"** — barra, dataset `kpis_jornada_internacao_direta_por_tipo`, eixo X `tipo_jornada`, eixo Y `SUM(mediana_horas)`. A dica mostra P90 (h), Casos com duração e Casos sem duração (as internações sem alta, que ficam fora da mediana). Cobre as duas categorias do Bloco B (`internacao_cirurgica_eletiva`, `internacao_clinica_direta`). Responde ao filtro `Período` pelo parâmetro `periodo`.

**Gráfico "Tendência Mensal - Mediana e Percentil 90 da Jornada"** — linha, dataset `kpis_jornada_internacao_direta`, eixo X `ano_mes`, eixo Y "Horas" com duas séries, `SUM(mediana_horas)` (Mediana (h)) e `SUM(p90_horas)` (P90 (h)), da jornada das internações do Bloco B com alta, da entrada da internação até a alta final. Ignora o filtro global `Período`, mesma lógica da seção anterior: sempre mostra a série histórica completa.

**Gráfico "Mediana da Jornada por Tipo (Internação)"** — barra, dataset `internacao_etapas_leito`, eixo X `etapa`, eixo Y `MEDIAN(h)`, cor por `tipo_jornada`. A dica mostra o P90 (h). Mostra onde o tempo da internação até o 1º leito é gasto: internação até a sala, tempo na sala, saída da sala até o leito e o total. A regra da etapa 3 está na seção do dataset. Responde ao filtro `Período` por Fields (`ano_mes` do dataset).

**Tabela "Internações por unidade do 1º leito"** — dataset `internacao_por_unidade`, uma linha por unidade, ordenada por número de internações, decrescente. Colunas: unidade do 1º leito definitivo, `internacoes`, `casos_com_espera_h`, `mediana_espera_h` (com formatação condicional), `mediana_jornada` e `p90_jornada`, estas duas em dias e horas a partir de 24 h. Cobre todas as internações do hospital (13 unidades e 867 internações em mar/2026). Responde ao filtro `Período` pelo parâmetro `periodo`.

**Decisões de escopo descartadas** (registradas para não repetir a investigação): um card de "Tempo Médio até a Cirurgia" foi cogitado e descartado por fugir do escopo de visão geral da Página 1 (o tempo até a cirurgia difere fortemente por origem, 11,2 h para eletiva vs. 55,8 h para emergência, análise que pertence à Página 2, Análise de Gargalos). Um card de "Tempo Médio de UTI" foi descartado por medir permanência dentro da UTI, não tempo até chegar nela, fora do propósito pretendido. O card de jornada da Internação também foi descartado no início, porque o tempo até a alta exclui as internações ainda sem alta no mês de corte (~17% dos casos em mar/2026) e subestima a permanência real. Ele voltou como "Mediana da Jornada", que mede só as internações com alta, junto do card "Mediana das Internações em Curso", que mede as sem alta à parte.

**Bases dos percentuais de cirurgia e UTI (06 a 20/10/2026).** Os cards da seção Emergência medem conversão sobre todos os atendimentos do PA (2,74% de cirurgia e 2,73% de UTI). O de UTI conta o atendimento que internou em UTI (`internou_em_uti`). Os da seção Internação medem a proporção dentre as internações do hospital (61,59% e 28,72%), que incluem as sem passagem pela emergência, e o de UTI conta a passagem pela UTI em qualquer momento da internação (`has_uti`). A Página 4 usa uma terceira base, os internados da porta Emergência (41,2% de UTI, também por `has_uti`). Por isso os rótulos dos cards informam a base. Em 09/10/2026 mudaram só os títulos. Em 20/10/2026 o cálculo do card de UTI da Emergência passou de `has_uti` para `internou_em_uti` (ver `validacao-dashboard.md`).

---

## Datasets SQL do Dashboard

Os datasets que reagem ao filtro Período recebem o parâmetro `:periodo` (seleção múltipla) e aplicam no `where` a condição `(:periodo IS NULL OR array_contains(:periodo, 'Todos') OR array_contains(:periodo, ano_mes))`. A ligação com o filtro é feita na lista Parameters do widget do filtro. Os datasets sem o parâmetro, as duas tendências mensais, não reagem ao Período por desenho.

### `kpis_jornada_emergencia_cards`

Grão: 1 linha, sem group by, calculada sobre os atendimentos do PA no período selecionado no filtro Período.
Alimenta os dois cards de mediana da seção Emergência.

```sql
with j as (
    select
        *,
        -- minutos de espera pelo leito: da saída da sala nas cirúrgicas e da abertura da internação nas clínicas (nulo nos demais casos)
        case
         when journey_type = 'internacao_clinica' then (unix_timestamp(ts_primeiro_leito) - unix_timestamp(ts_entrada_internacao)) / 60
         when journey_type = 'internacao_cirurgica_emergencia' and ts_primeiro_leito >= ts_saida_cirurgia then (unix_timestamp(ts_primeiro_leito) - unix_timestamp(ts_saida_cirurgia)) / 60
        end as leito_min
    from hospital_santa_rosa.gold_fluxo.gold_patient_journey
    where cd_atendimento is not null
      and (:periodo IS NULL OR array_contains(:periodo, 'Todos') OR array_contains(:periodo, ano_mes))
),
base as (
    select
        round(sum(fl_conversao) * 100.0 / count(distinct cd_atendimento), 1) as tx_conversao,
        round(sum(case when has_cirurgia = true then 1 else 0 end) * 100.0 / count(distinct cd_atendimento), 1) as tx_conversao_cirurgica,
        round(sum(case when has_uti = true then 1 else 0 end) * 100.0 / count(distinct cd_atendimento), 1) as tx_conversao_uti,
        round(sum(duracao_total_min) / count(duracao_total_min) / 60.0, 1) as tempo_medio_jornada_horas,
        count(distinct cd_atendimento) as total_atendimento,
        percentile(leito_min, 0.5) as mediana_leito_min,
        percentile(leito_min, 0.9) as p90_leito_min,
        count(leito_min) as casos_leito,
        percentile(duracao_emergencia_min, 0.5) as mediana_jornada_min,
        percentile(duracao_emergencia_min, 0.9) as p90_jornada_min,
        count(duracao_emergencia_min) as casos_jornada
    from j
)
select
    *,
    concat(replace(cast(round(mediana_leito_min / 60, 1) as string), '.', ','), ' h') as mediana_formatada_leito,
    concat('P90 ', replace(cast(round(p90_leito_min / 60, 1) as string), '.', ','), ' h') as p90_formatado_leito,
    concat(casos_leito, ' casos') as casos_formatado_leito,
    concat(replace(cast(round(mediana_jornada_min / 60, 1) as string), '.', ','), ' h') as mediana_formatada_jornada,
    concat('P90 ', replace(cast(round(p90_jornada_min / 60, 1) as string), '.', ','), ' h') as p90_formatado_jornada,
    concat(casos_jornada, ' casos') as casos_formatado_jornada
from base
```

**Regra do tempo até o leito (`leito_min`).** Mede a espera real por leito. Nas internações clínicas, conta da abertura da internação até o 1º leito. Nas cirúrgicas via emergência, conta da saída da sala até o 1º leito, e só quando o 1º leito é posterior à saída da sala. Quem já tinha leito antes da cirurgia fica fora do cálculo, e os demais tipos de jornada ficam nulos.

### `kpis_jornada_emergencia`

Grão: 1 linha por `ano_mes`. Alimenta o gráfico de tendência da seção
Emergência, com a mediana e o P90 da duração da emergência por mês.

```sql
select
  ano_mes,
  count(distinct cd_atendimento) as total_atendimento,
  round(sum(fl_conversao) * 100.0 / count(distinct cd_atendimento), 1) as tx_conversao,
  round(sum(case when has_cirurgia = true then 1 else 0 end) * 100.0 / count(distinct cd_atendimento), 1) as tx_conversao_cirurgica,
  round(sum(case when has_uti = true then 1 else 0 end) * 100.0 / count(distinct cd_atendimento), 1) as tx_conversao_uti,
  round(percentile(duracao_emergencia_min, 0.5) / 60.0, 1) as mediana_horas,
  round(percentile(duracao_emergencia_min, 0.9) / 60.0, 1) as p90_horas
from hospital_santa_rosa.gold_fluxo.gold_patient_journey
where cd_atendimento is not null
group by ano_mes
order by ano_mes
```

**Nota:** esta query calcula proporções pré-agregadas por mês. Os cards
da Página 1 não usam este dataset para os percentuais — usam
`gold_patient_journey` diretamente com `AVG` sobre colunas 0/1, para evitar
o efeito de "média de médias" ao combinar múltiplos meses. Este dataset
serve exclusivamente ao gráfico de tendência mensal, onde o grão por mês é
o propósito.

### `kpis_jornada_emergencia_cards`

Grão: 1 linha (agregado). Parâmetro: `periodo` (`'Todos'` ou um `ano_mes`), ligado ao filtro `Período` da página. Alimenta os cartões "Mediana do tempo até o leito" e "Mediana da Jornada", no formato dos cartões da Página 2 (colunas de texto `*_formatado*`, com vírgula decimal). A mediana e o P90 são calculados na hora, sobre o filtro escolhido (ADR-0023).

```sql
with j as (
    select
        *,
        -- minutos da abertura da internação até o primeiro leito real (nulo para quem não internou)
        (unix_timestamp(ts_primeiro_leito) - unix_timestamp(ts_entrada_internacao)) / 60 as leito_min
    from hospital_santa_rosa.gold_fluxo.gold_patient_journey
    where cd_atendimento is not null
      and (:periodo = 'Todos' or ano_mes = :periodo)
),
base as (
    select
        round(sum(fl_conversao) * 100.0 / count(distinct cd_atendimento), 1) as tx_conversao,
        round(sum(case when has_cirurgia = true then 1 else 0 end) * 100.0 / count(distinct cd_atendimento), 1) as tx_conversao_cirurgica,
        round(sum(case when has_uti = true then 1 else 0 end) * 100.0 / count(distinct cd_atendimento), 1) as tx_conversao_uti,
        round(sum(duracao_total_min) / count(duracao_total_min) / 60.0, 1) as tempo_medio_jornada_horas,
        count(distinct cd_atendimento) as total_atendimento,
        percentile(leito_min, 0.5) as mediana_leito_min,
        percentile(leito_min, 0.9) as p90_leito_min,
        count(leito_min) as casos_leito,
        percentile(duracao_emergencia_min, 0.5) as mediana_jornada_min,
        percentile(duracao_emergencia_min, 0.9) as p90_jornada_min,
        count(duracao_emergencia_min) as casos_jornada
    from j
)
select
    *,
    concat(replace(cast(round(mediana_leito_min / 60, 1) as string), '.', ','), ' h') as mediana_formatada_leito,
    concat('P90 ', replace(cast(round(p90_leito_min / 60, 1) as string), '.', ','), ' h') as p90_formatado_leito,
    concat(casos_leito, ' casos') as casos_formatado_leito,
    concat(replace(cast(round(mediana_jornada_min / 60, 1) as string), '.', ','), ' h') as mediana_formatada_jornada,
    concat('P90 ', replace(cast(round(p90_jornada_min / 60, 1) as string), '.', ','), ' h') as p90_formatado_jornada,
    concat(casos_jornada, ' casos') as casos_formatado_jornada
from base
```

As colunas `tx_conversao`, `tx_conversao_cirurgica`, `tx_conversao_uti`, `tempo_medio_jornada_horas` e `total_atendimento` já existiam e não foram alteradas. As colunas `*_jornada` calculam a mediana e o P90 da duração da emergência (`duracao_emergencia_min`, ADR-0025), só dos atendimentos que têm duração.

### `kpis_jornada_emergencia_por_tipo`

Grão: 1 linha por `journey_type` (categoria de negócio, ver ADR-0014).
Alimenta o gráfico de distribuição da seção Emergência. Mediana e P90 da duração da emergência (`duracao_emergencia_min`, ADR-0025), com a contagem de jornadas com e sem duração. O `where` não filtra as jornadas sem duração, para que elas entrem na contagem.

```sql
select
  case journey_type when 'atendimento_emergencia' then 'Atendimento Emergência'
                    when 'cirurgia_ambulatorial' then 'Cirurgia Ambulatorial'
                    when 'internacao_clinica' then 'Internação Clínica'
                    when 'internacao_cirurgica_emergencia' then 'Internação Cirúrgica (Emergência)'
  end as tipo_jornada,
  round(percentile(duracao_emergencia_min, 0.5) / 60.0, 1) as mediana_horas,
  round(percentile(duracao_emergencia_min, 0.9) / 60.0, 1) as p90_horas,
  count(duracao_emergencia_min) as casos_com_duracao,
  count_if(duracao_emergencia_min is null) as casos_sem_duracao
  from hospital_santa_rosa.gold_fluxo.gold_patient_journey
  where journey_type in('atendimento_emergencia', 'cirurgia_ambulatorial', 'internacao_clinica', 'internacao_cirurgica_emergencia')
  and (:periodo IS NULL OR array_contains(:periodo, 'Todos') OR array_contains(:periodo, ano_mes))
  group by journey_type
  order by mediana_horas desc
```

### `kpis_jornada_internacao_direta`

Grão: 1 linha por `ano_mes`, escopado ao Bloco B (`cd_atendimento is null`, as internações sem passagem pela emergência). Alimenta o gráfico de tendência da seção Internação, com a mediana e o P90 da jornada, da entrada da internação até a alta final, só das internações que já tiveram alta. Não tem o parâmetro `:periodo`: a tendência mostra sempre a série completa.

```sql
select
    ano_mes,
    round(percentile(case when ts_alta_final is not null
        then (unix_timestamp(ts_alta_final) - unix_timestamp(ts_entrada_internacao)) / 3600 end, 0.5), 2) as mediana_horas,
    round(percentile(case when ts_alta_final is not null
        then (unix_timestamp(ts_alta_final) - unix_timestamp(ts_entrada_internacao)) / 3600 end, 0.9), 2) as p90_horas
from hospital_santa_rosa.gold_fluxo.gold_patient_journey
where cd_atendimento is null
group by ano_mes
order by ano_mes
```

### `kpis_jornada_internacao_direta_por_tipo`

Grão: 1 linha por tipo de jornada do Bloco B (`internacao_cirurgica_eletiva` e `internacao_clinica_direta`). Alimenta o gráfico de distribuição da seção Internação, com a mediana e o P90 da jornada, da entrada da internação até a alta final, e a contagem de internações com e sem alta. Reage ao filtro Período pelo parâmetro `:periodo`.

```sql
select
    case journey_type
        when 'internacao_cirurgica_eletiva' then 'Internação Cirúrgica Eletiva'
        else 'Internação Clínica Direta'
    end as tipo_jornada,
    round(percentile(case when ts_alta_final is not null
        then (unix_timestamp(ts_alta_final) - unix_timestamp(ts_entrada_internacao)) / 3600 end, 0.5), 2) as mediana_horas,
    round(percentile(case when ts_alta_final is not null
        then (unix_timestamp(ts_alta_final) - unix_timestamp(ts_entrada_internacao)) / 3600 end, 0.9), 2) as p90_horas,
    sum(case when ts_alta_final is not null then 1 else 0 end) as casos_com_duracao,
    sum(case when ts_alta_final is null then 1 else 0 end)     as casos_sem_duracao
from hospital_santa_rosa.gold_fluxo.gold_patient_journey
where cd_atendimento is null
  and cd_internacao is not null
  and (:periodo is null or array_contains(:periodo, 'Todos') or array_contains(:periodo, ano_mes))
group by 1
order by 1
```

### kpis_jornada_internacao_cards

Grão: 1 linha, sem group by, calculada sobre as internações do Bloco B (`internacao_cirurgica_eletiva` e `internacao_clinica_direta`) no período selecionado no filtro Período. Alimenta os dois cards de mediana da seção Internação: a jornada (com P90) e as internações em curso.

```sql
WITH ref AS (
  SELECT cast(last_day(to_date(concat(max(ano_mes), '-01'))) AS timestamp)
         + INTERVAL 1 DAY - INTERVAL 1 SECOND AS fim_provisorio
  FROM hospital_santa_rosa.gold_fluxo.gold_patient_journey
),
base AS (
  SELECT
    (unix_timestamp(coalesce(j.ts_alta_final, r.fim_provisorio))
       - unix_timestamp(j.ts_entrada_internacao)) / 3600 AS h,
    (j.ts_alta_final IS NULL) AS sem_alta
  FROM hospital_santa_rosa.gold_fluxo.gold_patient_journey j
  CROSS JOIN ref r
  WHERE j.cd_internacao IS NOT NULL
    AND j.journey_type IN ('internacao_cirurgica_eletiva', 'internacao_clinica_direta')
    AND (:periodo IS NULL OR array_contains(:periodo, 'Todos') OR array_contains(:periodo, j.ano_mes))
),

agg as(
  SELECT
  percentile(CASE WHEN NOT sem_alta THEN h END, 0.5) AS mediana_jornada_h,
  percentile(CASE WHEN NOT sem_alta THEN h END, 0.9) AS p90_jornada_h,
  percentile(CASE WHEN sem_alta THEN h END, 0.5) AS mediana_em_curso_h,
  sum(CASE WHEN sem_alta THEN 1 ELSE 0 END) AS qtd_em_curso
FROM base
)

select
  case
    when mediana_jornada_h >=24 then concat(floor(round(mediana_jornada_h) / 24), ' d ', cast(round(mediana_jornada_h) % 24 as int), ' h')
    else concat(replace(cast(round(mediana_jornada_h, 1) as string), '.', ','), ' h')
  end as mediana_formatada_jornada,
  concat('P90 ', case
    when p90_jornada_h >=24 then concat(floor(round(p90_jornada_h) / 24), ' d ', cast(round(p90_jornada_h) % 24 as int), ' h')
    else concat(replace(cast(round(p90_jornada_h, 1) as string), '.', ','), ' h')
  end) as p90_formatado_jornada,
  case
    when mediana_em_curso_h >=24 then concat(floor(round(mediana_em_curso_h) / 24), ' d ', cast(round(mediana_em_curso_h) % 24 as int), ' h')
    else concat(replace(cast(round(mediana_em_curso_h, 1) as string), '.', ','), ' h')
  end as mediana_formatada_em_curso,
  concat(qtd_em_curso, ' sem alta') as qtd_em_curso_formatada
from agg
```

**Internações em curso.** A internação sem alta (`ts_alta_final` nulo) não entra na mediana da jornada. Ela é medida à parte, da entrada da internação até um fim provisório, o último dia do mês mais recente carregado (CTE `ref`), e aparece no card como "sem alta".

### internacao_por_unidade

Grão: 1 linha por unidade do 1º leito definitivo (`unidade_primeiro_leito`; quando a internação não tem leito físico, usa `unidade_leito_inicial`). Cobre todas as internações do hospital e alimenta a tabela "Internações por unidade do 1º leito", com a mediana e o P90 da jornada e a mediana da espera pelo leito. Reage ao filtro Período pelo parâmetro `:periodo`.

```sql
with base as(
    select
    coalesce(unidade_primeiro_leito, unidade_leito_inicial) as unidade,
    (unix_timestamp(ts_alta_final) - unix_timestamp(ts_entrada_internacao)) / 3600 as h_jornada,
    case
    when journey_type = 'internacao_cirurgica_eletiva' and ts_primeiro_leito >= ts_saida_cirurgia then (unix_timestamp(ts_primeiro_leito) - unix_timestamp(ts_saida_cirurgia)) / 3600
    when journey_type = 'internacao_clinica_direta' then (unix_timestamp(ts_primeiro_leito) - unix_timestamp(ts_entrada_internacao)) / 3600
    end as h_espera_leito
    from hospital_santa_rosa.gold_fluxo.gold_patient_journey
    where cd_internacao is not null and
    (:periodo is null or array_contains(:periodo, 'Todos') or array_contains(:periodo, ano_mes))
),

agg as(
    select
        unidade,
        count(*) as internacoes,
        median(h_jornada) as mediana_jornada_h,
        percentile(h_jornada, 0.9) as p90_jornada_h,
        median(h_espera_leito) as mediana_espera_h,
        count(h_espera_leito) as casos_com_espera_h
    from base
    group by unidade
)

select
    unidade,
    internacoes,
    mediana_espera_h,
    casos_com_espera_h,
    case
     when mediana_jornada_h >=24 then concat(floor(round(mediana_jornada_h) / 24), ' d ', cast(round(mediana_jornada_h) % 24 as int), ' h')
     else concat(replace(cast(round(mediana_jornada_h, 1) as string), '.', ','), ' h')
    end as mediana_jornada,
    case
     when p90_jornada_h >=24 then concat(floor(round(p90_jornada_h) / 24), ' d ', cast(round(p90_jornada_h) % 24 as int), ' h')
     else concat(replace(cast(round(p90_jornada_h, 1) as string), '.', ','), ' h')
    end as p90_jornada
from agg
```

**Regra da espera pelo leito (`h_espera_leito`).** Nas cirúrgicas eletivas, conta da saída da sala até o 1º leito, e só quando o 1º leito é posterior à saída da sala. Nas clínicas diretas, conta da abertura da internação até o 1º leito. Os demais tipos ficam nulos, e `casos_com_espera_h` mostra quantas internações de cada unidade entram na mediana da espera.

### internacao_etapas_leito

Grão: 1 linha por internação e por etapa (até 4 linhas por internação), só das internações com 1º leito, do Bloco B. Alimenta o gráfico das etapas até o leito, que calcula a mediana e o P90 sobre a coluna `h`. Diferente dos outros, não tem o parâmetro `:periodo`: reage ao filtro Período por Fields, pelo campo `ano_mes` do dataset.

```sql
WITH base AS (
  SELECT
    CASE journey_type
      WHEN 'internacao_cirurgica_eletiva' THEN 'Internação Cirúrgica Eletiva'
      ELSE 'Internação Clínica Direta' END AS tipo_jornada,
    ano_mes,
    (unix_timestamp(ts_entrada_cirurgia) - unix_timestamp(ts_entrada_internacao)) / 3600 AS h_internacao_ate_sala,
    (unix_timestamp(ts_saida_cirurgia)   - unix_timestamp(ts_entrada_cirurgia))    / 3600 AS h_na_sala,
    case
     when ts_primeiro_leito >= ts_saida_cirurgia then (unix_timestamp(ts_primeiro_leito)   - unix_timestamp(ts_saida_cirurgia))      / 3600  end AS h_sala_ate_leito,
    (unix_timestamp(ts_primeiro_leito)   - unix_timestamp(ts_entrada_internacao))  / 3600 AS h_total
  FROM hospital_santa_rosa.gold_fluxo.gold_patient_journey
  WHERE cd_internacao IS NOT NULL
    AND ts_primeiro_leito IS NOT NULL
    AND journey_type IN ('internacao_cirurgica_eletiva', 'internacao_clinica_direta')
),
etapas AS (
  SELECT tipo_jornada, ano_mes, 1 AS ordem, '1. Internação até a sala'   AS etapa, h_internacao_ate_sala AS h FROM base
  UNION ALL SELECT tipo_jornada, ano_mes, 2, '2. Na sala cirúrgica',               h_na_sala        FROM base
  UNION ALL SELECT tipo_jornada, ano_mes, 3, '3. Saída da sala até o leito',       h_sala_ate_leito FROM base
  UNION ALL SELECT tipo_jornada, ano_mes, 4, 'Total (internação até o leito)',     h_total          FROM base
)
SELECT tipo_jornada, ano_mes, ordem, etapa, h
FROM etapas
WHERE h IS NOT NULL
```

**Regra da etapa 3 (`h_sala_ate_leito`).** Só é calculada quando o 1º leito é posterior à saída da sala. Se o paciente já tinha leito antes da cirurgia, a etapa fica nula e sai do gráfico, mas a internação continua no total (internação até o leito). As etapas 1 e 2 só existem para quem passou pela sala cirúrgica, por isso as clínicas diretas aparecem apenas no total.

---

## Campos calculados do Data Model

Campos criados na aba "Data" do Dashboard, sobre o Data Model
`gold_patient_journey`. Não existem como colunas na tabela real — são
expressões calculadas em tempo de consulta, específicas do Dashboard.

| Campo | Expressão | Propósito |
|---|---|---|
| `Cd Atendimento Is Null` | `ISNULL(cd_atendimento)` | Isola Bloco A (`false`) de Bloco B (`true`) para filtros de card |
| `Cd Internacao Is Null` | `ISNULL(cd_internacao)` | Isola linhas com internação real (`false`) |
| `Fl Conversao` | `source.fl_conversao` | Exposto como campo do Data Model — coluna existia na tabela mas não estava mapeada |
| `Fl Evasao` | `source.fl_evasao` | Idem |
| `Has Cirurgia Numerico` | `CASE WHEN source.has_cirurgia THEN 1 ELSE 0 END` | Converte boolean para 0/1, permitindo `AVG` (proporção) — o Data Model não suporta `AVG` direto sobre boolean |
| `Has Uti Numerico` | `CASE WHEN source.has_uti THEN 1 ELSE 0 END` | Idem, para `has_uti` |
| `Internou Em Uti Numerico` | `CASE WHEN source.internou_em_uti THEN 1 ELSE 0 END` | Converte `internou_em_uti` para 0/1, permitindo `AVG`. Base do cartão "Conversão UTI". O `Has Uti Numerico` continua nos visuais que medem passagem pela UTI |
| `Is Internacao Via Emergencia` | `CASE WHEN source.journey_type IN ('internacao_clinica', 'internacao_cirurgica_emergencia') THEN 1 ELSE 0 END` | Base do card "% Internações via Emergência" |
| `Duracao Total Horas` | `source.duracao_total_min / 60` | Duração total da jornada, chegada/entrada até alta, em horas. Sem uso na Página 1: era a base do antigo card "Tempo Médio da Jornada". |
| `Duracao Total Dias` | `source.duracao_total_min / 1440` | Idem, em dias — não usado nos cards finais, mantido pela investigação de permanência |
| `Duracao Internacao Leito Horas` | `(unix_timestamp(source.ts_primeiro_leito) - unix_timestamp(source.ts_entrada_internacao)) / 3600` | Tempo entre abertura da internação e chegada ao leito físico. Não depende de alta — livre do viés de exclusão de internações em curso. Sem uso na Página 1: era a base do antigo card "Tempo Médio até o Leito" e da antiga tendência da Internação. A espera real pelo leito passou a ser calculada nos datasets. |
| `Duracao Internacao Alta Dias` | `(unix_timestamp(coalesce(source.ts_alta_final, source.ts_alta_medica)) - unix_timestamp(source.ts_entrada_internacao)) / 86400` | Tempo de permanência (entrada até alta), em dias. **Sofre de viés conhecido**: exclui internações sem alta lançada no mês de corte (~17% em mar/2026) — não usado nos cards finais por esse motivo |

---

## Publicação e compartilhamento

Dashboard publicado com permissão de dados "Share data permission"
(credencial do publisher) — apropriado para o público-alvo (Diretoria
Assistencial, sem contas próprias no workspace Databricks). Acesso de
visualização concedido individualmente via e-mail na tela de
compartilhamento; não há grupo amplo configurado ainda.