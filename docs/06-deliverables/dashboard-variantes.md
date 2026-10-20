# Dashboard, Página 5: Variantes

- **Local:** AI/BI Dashboard `Mapa Digital do Fluxo do Paciente`, aba "Variantes"
- **Decisões arquiteturais:** ADR-0021 (variantes por jornada, `gold_variant_jornada` e `activity_unidade`)
- **Regras de qualidade relacionadas:** RQ-016, RQ-019, RQ-020
- **Status:** publicado (14/10/2026)

Este documento cobre artefatos que vivem **dentro do Dashboard** (datasets SQL salvos e configuração dos widgets). Tabelas e views do catálogo estão em `data-dictionary.md`.

---

## Pergunta da página

Quão padronizado é o processo, quantos caminhos distintos existem, quanto os mais comuns cobrem, quanto tempo cada um leva e como isso varia por tipo de jornada e por especialidade.

**Termos usados na página:**

- **Jornada** = um atendimento (uma passagem pelo PS ou uma internação), e não um paciente. O mesmo paciente pode ter mais de uma jornada: em mar/2026, 6.657 jornadas do `gold_patient_journey` vêm de 5.628 pacientes distintos.
- **Caminho** = a sequência de etapas que a jornada percorre (o que o notebook chama de variante).

---

## Estrutura da página

Três filtros no topo, aplicados a todos os visuais:

| Filtro | Tipo | Valores | Observação |
|---|---|---|---|
| Período | multi-select | `dim_periodo` | bypass `IS NULL` |
| Tipo de jornada | multi-select | `dim_tipo_jornada` (7 rótulos de negócio) | |
| Especialidade (de entrada da jornada) | multi-select | `dim_especialidade` (compartilhado com as Páginas 2 e 4) | A especialidade da jornada segue a regra do ADR-0021, e não a do evento de destino, como na Página 4. "Sem especialidade" (86 jornadas) não está na lista, então entra só com o filtro vazio |

Quatro visuais, nesta ordem:

1. **Perfil das jornadas por combinação de etapas** (barras): quantas jornadas há em cada combinação de etapas (emergência, imagem, laboratório, internação, cirurgia). O tooltip traz os caminhos distintos e as jornadas por caminho.
2. **Caminhos distintos x jornadas, por frequência do caminho** (barras agrupadas): em cada faixa de frequência (um caso, de 2 a 5, de 6 a 20, de 21 a 100, mais de 100), o % dos caminhos e o % das jornadas. É o retrato da cauda longa.
3. **Os 10 caminhos mais comuns** (tabela): jornadas, % das jornadas, % acumulado, jornadas com tempo, mediana e P90 em horas e o caminho. A setinha ao lado do caminho expande o texto completo, e parar o mouse sobre a célula mostra uma caixa com ele inteiro.
4. **Caminhos raros com jornadas lentas** (tabela): caminhos com até 5 jornadas que têm pelo menos uma jornada acima do P90 do tipo.

## Resultados de referência (mar/2026, medidos em 14 e 20/10/2026)

| Medida | Valor |
|---|---|
| Jornadas | 6.577 |
| Caminhos distintos | 1.328 |
| Caminho mais comum | 1.949 jornadas (29,63%), mediana de 1,9 h e P90 de 5,3 h |
| 10 caminhos mais comuns | 58,74% das jornadas |

| Faixa (jornadas por caminho) | Caminhos | % dos caminhos | Jornadas | % das jornadas |
|---|---|---|---|---|
| um caso | 1.092 | 82,2 | 1.092 | 16,6 |
| de 2 a 5 | 157 | 11,8 | 417 | 6,3 |
| de 6 a 20 | 52 | 3,9 | 538 | 8,2 |
| de 21 a 100 | 20 | 1,5 | 903 | 13,7 |
| mais de 100 | 7 | 0,5 | 3.627 | 55,1 |

Os números são de um único mês e vão mudar com o histórico.


---

## Datasets SQL do Dashboard

Todos os datasets de dado têm três parâmetros multi-select (`periodo`, `tipo_jornada` e `especialidade`), com **Allow multiple selections** marcado, e ligados aos três filtros da página em **Parameters**. O rótulo de negócio do tipo de jornada é montado por um `case` no SQL, e a especialidade é traduzida com `vw_dim_especialidade` (nome traduzido quando existe, nome bruto quando não).

### `variantes_perfis`

Grão: 1 linha por perfil (combinação de etapas). Alimenta o gráfico de perfis. Lê de `gold_variant_analysis`.

O perfil é classificado por busca de texto na sequência (maiúsculas e minúsculas diferenciadas), então as atividades de movimentação, escritas em maiúsculas, não entram na classificação. `variantes` conta sequências distintas depois do filtro, e por isso a mesma sequência que aparece em dois tipos de jornada conta uma vez só.

Valores de referência (mar/2026, sem filtros, medidos em 20/10/2026):

| Perfil | Jornadas | Caminhos | Jornadas por caminho |
|---|---|---|---|
| Emergência | 2.286 | 11 | 207,8 |
| Emergência + imagem + laboratório | 1.381 | 356 | 3,9 |
| Emergência + laboratório | 1.016 | 29 | 35,0 |
| Emergência + imagem | 711 | 140 | 5,1 |
| Sem emergência + internação + cirurgia | 299 | 147 | 2,0 |
| Sem emergência | 213 | 25 | 8,5 |

```sql
with base as (
    select
        g.sequencia,
        g.total_casos,
        coalesce(v.especialidade_label, g.especialidade) as especialidade,
        case g.journey_type
            when 'atendimento_emergencia' then 'Atendimento de emergência'
            when 'internacao_clinica' then 'Internação clínica (via emergência)'
            when 'internacao_cirurgica_emergencia' then 'Internação cirúrgica (via emergência)'
            when 'internacao_cirurgica_eletiva' then 'Internação cirúrgica eletiva'
            when 'internacao_clinica_direta' then 'Internação clínica direta'
            when 'cirurgia_ambulatorial' then 'Cirurgia ambulatorial'
            else 'Sem jornada classificada'
        end as tipo_jornada
    from hospital_santa_rosa.gold_fluxo.gold_variant_analysis g
    left join hospital_santa_rosa.gold_fluxo.vw_dim_especialidade v
        on g.especialidade = v.especialidade_origem
    where (:periodo is null or array_contains(:periodo, g.ano_mes))
),
filtrado as (
    select * from base
    where (:tipo_jornada is null or array_contains(:tipo_jornada, tipo_jornada))
      and (:especialidade is null or array_contains(:especialidade, especialidade))
),
perfil as (
    select
        sequencia,
        total_casos,
        case when sequencia like '%Pronto-Socorro%' then 'Emergência' else 'Sem emergência' end as inicio,
        concat_ws(' + ',
            case when sequencia like '%Exame de Imagem%' then 'imagem' end,
            case when sequencia like '%Exame Laboratorial%' then 'laboratório' end,
            case when sequencia like '%Internacao%' then 'internação' end,
            case when sequencia like '%Cirurgia%' then 'cirurgia' end
        ) as etapas
    from filtrado
)
select
    case when length(etapas) > 0 then concat(inicio, ' + ', etapas) else inicio end as perfil,
    sum(total_casos) as jornadas,
    count(distinct sequencia) as variantes,
    round(sum(total_casos) * 1.0 / count(distinct sequencia), 1) as jornadas_por_variante
from perfil
group by 1
order by jornadas desc
```


### `variantes_faixas`

Grão: 1 linha por faixa de frequência do caminho. Alimenta o gráfico de barras agrupadas. Lê de `gold_variant_analysis`. A soma por `sequencia` no `filtrado` junta de volta a mesma sequência quando ela aparece em mais de um tipo de jornada ou especialidade, e por isso cada caminho conta uma vez só.

Valores de referência (mar/2026, sem filtros, medidos em 20/10/2026):

| Faixa | Caminhos | % dos caminhos | Jornadas | % das jornadas |
|---|---|---|---|---|
| 1. um caso | 1.092 | 82,2 | 1.092 | 16,6 |
| 2. de 2 a 5 | 157 | 11,8 | 417 | 6,3 |
| 3. de 6 a 20 | 52 | 3,9 | 538 | 8,2 |
| 4. de 21 a 100 | 20 | 1,5 | 903 | 13,7 |
| 5. mais de 100 | 7 | 0,5 | 3.627 | 55,1 |

```sql
with base as (
    select
        g.sequencia,
        g.total_casos,
        coalesce(v.especialidade_label, g.especialidade) as especialidade,
        case g.journey_type
            when 'atendimento_emergencia' then 'Atendimento de emergência'
            when 'internacao_clinica' then 'Internação clínica (via emergência)'
            when 'internacao_cirurgica_emergencia' then 'Internação cirúrgica (via emergência)'
            when 'internacao_cirurgica_eletiva' then 'Internação cirúrgica eletiva'
            when 'internacao_clinica_direta' then 'Internação clínica direta'
            when 'cirurgia_ambulatorial' then 'Cirurgia ambulatorial'
            else 'Sem jornada classificada'
        end as tipo_jornada
    from hospital_santa_rosa.gold_fluxo.gold_variant_analysis g
    left join hospital_santa_rosa.gold_fluxo.vw_dim_especialidade v
        on g.especialidade = v.especialidade_origem
    where (:periodo is null or array_contains(:periodo, g.ano_mes))
),
filtrado as (
    select sequencia, sum(total_casos) as total_casos
    from base
    where (:tipo_jornada is null or array_contains(:tipo_jornada, tipo_jornada))
      and (:especialidade is null or array_contains(:especialidade, especialidade))
    group by 1
)
select
    case when total_casos = 1 then '1. um caso'
         when total_casos <= 5 then '2. de 2 a 5'
         when total_casos <= 20 then '3. de 6 a 20'
         when total_casos <= 100 then '4. de 21 a 100'
         else '5. mais de 100' end as faixa,
    count(*) as caminhos,
    sum(total_casos) as jornadas,
    round(count(*) * 100.0 / sum(count(*)) over (), 1) as pct_dos_caminhos,
    round(sum(total_casos) * 100.0 / sum(sum(total_casos)) over (), 1) as pct_das_jornadas
from filtrado
group by 1
order by 1
```


### `variantes_top10`

Grão: 1 linha por caminho, limitada aos 10 mais comuns. Alimenta a tabela dos 10 caminhos mais comuns. Lê de `gold_variant_jornada`, e não de `gold_variant_analysis`, porque a mediana e o P90 são calculados na hora, sobre o filtro escolhido (ADR-0021). `com_duracao` é o número de jornadas que entraram no cálculo do tempo. Jornadas sem duração ficam fora da mediana e do P90.

Valores de referência (mar/2026, sem filtros, medidos em 14/10/2026):

| Posição | Caminho (resumo) | Jornadas | % das jornadas | % acumulado | Jornadas com tempo | Mediana (h) | P90 (h) |
|---|---|---|---|---|---|---|---|
| 01 | Consulta e alta | 1.949 | 29,63 | 29,63 | 1.949 | 1,9 | 5,3 |
| 02 | Consulta com laboratório | 796 | 12,10 | 41,73 | 794 | 3,7 | 6,7 |
| 03 | Consulta com imagem e laboratório | 269 | 4,09 | 45,82 | 269 | 3,8 | 6,6 |
| 04 | Consulta com imagem, alta antes da liberação do exame | 190 | 2,89 | 48,71 | 190 | 1,6 | 2,5 |
| 05 | Consulta, fim da consulta antes da alta | 174 | 2,65 | 51,36 | 174 | 1,9 | 5,3 |
| 06 | Consulta sem registro de alta | 133 | 2,02 | 53,38 | 0 | sem tempo | sem tempo |
| 07 | Consulta com imagem, laboratório e laudo aprovado | 116 | 1,76 | 55,14 | 116 | 4,2 | 7,2 |
| 08 | Igual ao 07, com preparo do exame | 93 | 1,41 | 56,55 | 93 | 4,9 | 7,2 |
| 09 | Alta médica e Alta Hospitalar, sem internação na base (RQ-019) | 78 | 1,19 | 57,74 | 0 | sem tempo | sem tempo |
| 10 | Consulta com laboratório, fim da consulta antes da alta | 66 | 1,00 | 58,74 | 66 | 3,8 | 6,1 |

```sql
with base as (
    select
        j.sequencia,
        j.duracao_total_min,
        coalesce(v.especialidade_label, j.especialidade) as especialidade,
        case j.journey_type
            when 'atendimento_emergencia' then 'Atendimento de emergência'
            when 'internacao_clinica' then 'Internação clínica (via emergência)'
            when 'internacao_cirurgica_emergencia' then 'Internação cirúrgica (via emergência)'
            when 'internacao_cirurgica_eletiva' then 'Internação cirúrgica eletiva'
            when 'internacao_clinica_direta' then 'Internação clínica direta'
            when 'cirurgia_ambulatorial' then 'Cirurgia ambulatorial'
            else 'Sem jornada classificada'
        end as tipo_jornada
    from hospital_santa_rosa.gold_fluxo.gold_variant_jornada j
    left join hospital_santa_rosa.gold_fluxo.vw_dim_especialidade v
        on j.especialidade = v.especialidade_origem
    where (:periodo is null or array_contains(:periodo, j.ano_mes))
),
filtrado as (
    select * from base
    where (:tipo_jornada is null or array_contains(:tipo_jornada, tipo_jornada))
      and (:especialidade is null or array_contains(:especialidade, especialidade))
),
agg as (
    select
        sequencia,
        count(*) as total_casos,
        count(duracao_total_min) as com_duracao,
        round(percentile_approx(duracao_total_min, 0.5) / 60.0, 1) as mediana_h,
        round(percentile_approx(duracao_total_min, 0.9) / 60.0, 1) as p90_h
    from filtrado
    group by 1
),
ranqueado as (
    select
        *,
        row_number() over (order by total_casos desc, sequencia) as posicao,
        round(total_casos * 100.0 / sum(total_casos) over (), 2) as cobertura_perc
    from agg
)
select
    concat('Caminho ', lpad(cast(posicao as string), 2, '0')) as caminho,
    posicao,
    total_casos,
    cobertura_perc,
    round(sum(cobertura_perc) over (order by posicao), 2) as cobertura_acumulada,
    mediana_h,
    p90_h,
    com_duracao,
    replace(
        sequencia,
        'Chegada ao Pronto-Socorro → Início da Triagem → Classificação de Risco → Início do Cadastro → Fim do Cadastro → Início da Consulta Médica',
        '[Entrada no PS → início da consulta]'
    ) as descricao
from ranqueado
where posicao <= 10
order by posicao
```


### `variantes_raras_lentas`

Grão: 1 linha por caminho raro (até 5 jornadas no filtro escolhido) que tem pelo menos uma jornada lenta. Alimenta a tabela de caminhos raros com jornadas lentas. Lê de `gold_variant_jornada`.

- **Caminho raro:** até 5 jornadas no filtro escolhido, o mesmo corte das faixas "um caso" e "de 2 a 5".
- **Jornada lenta:** duração acima do P90 das jornadas do mesmo tipo. O P90 é calculado sobre o que sobra depois dos filtros de Período e Especialidade, então muda quando eles mudam. Jornadas sem duração não entram.
- **Ordem:** número de jornadas lentas e, depois, maior tempo.
- Limite de 20 linhas.

Leitura de referência (mar/2026, sem filtros, medida em 14/10/2026):

- Os 8 primeiros caminhos são de emergência: de 2 a 5 jornadas, todas lentas, com tempo máximo entre 7,6 e 22,9 h.
- Os seguintes são de internação: cada um com 1 jornada e de 340 a 660 h (14 a 27 dias).
- Na internação quase todo caminho é único, então "raro" não distingue nada ali, e a lista mostra só jornadas longas. Com o filtro de tipo de jornada, cada leitura fica separada.

```sql
with base as (
    select
        j.sequencia,
        j.duracao_total_min,
        coalesce(v.especialidade_label, j.especialidade) as especialidade,
        case j.journey_type
            when 'atendimento_emergencia' then 'Atendimento de emergência'
            when 'internacao_clinica' then 'Internação clínica (via emergência)'
            when 'internacao_cirurgica_emergencia' then 'Internação cirúrgica (via emergência)'
            when 'internacao_cirurgica_eletiva' then 'Internação cirúrgica eletiva'
            when 'internacao_clinica_direta' then 'Internação clínica direta'
            when 'cirurgia_ambulatorial' then 'Cirurgia ambulatorial'
            else 'Sem jornada classificada'
        end as tipo_jornada
    from hospital_santa_rosa.gold_fluxo.gold_variant_jornada j
    left join hospital_santa_rosa.gold_fluxo.vw_dim_especialidade v
        on j.especialidade = v.especialidade_origem
    where (:periodo is null or array_contains(:periodo, j.ano_mes))
),
filtrado as (
    select * from base
    where (:tipo_jornada is null or array_contains(:tipo_jornada, tipo_jornada))
      and (:especialidade is null or array_contains(:especialidade, especialidade))
),
p90_tipo as (
    select tipo_jornada, percentile_approx(duracao_total_min, 0.9) as p90_min
    from filtrado
    where duracao_total_min is not null
    group by 1
),
caminhos as (
    select sequencia, count(*) as total_casos
    from filtrado
    group by 1
),
lentas as (
    select
        f.sequencia,
        count(*) as jornadas_lentas,
        round(max(f.duracao_total_min) / 60.0, 1) as maior_tempo_h,
        concat_ws(', ', sort_array(collect_set(f.tipo_jornada))) as tipos
    from filtrado f
    join p90_tipo p on f.tipo_jornada = p.tipo_jornada
    where f.duracao_total_min > p.p90_min
    group by 1
)
select
    c.total_casos,
    l.jornadas_lentas,
    l.maior_tempo_h,
    l.tipos,
    replace(
        c.sequencia,
        'Chegada ao Pronto-Socorro → Início da Triagem → Classificação de Risco → Início do Cadastro → Fim do Cadastro → Início da Consulta Médica',
        '[Entrada no PS → início da consulta]'
    ) as descricao
from caminhos c
join lentas l on c.sequencia = l.sequencia
where c.total_casos <= 5
order by l.jornadas_lentas desc, l.maior_tempo_h desc
limit 20
```


### Datasets auxiliares dos filtros

Sem parâmetros. Populam os dropdowns, ligados em **Fields**.

- `dim_periodo`: compartilhado com as outras páginas (`select distinct ano_mes from hospital_santa_rosa.gold_fluxo.gold_patient_journey order by ano_mes`).
- `dim_especialidade`: compartilhado com as Páginas 2 e 4. Aplica `vw_dim_especialidade` e lê de `gold_bottleneck`. Cobre todas as especialidades reais de `gold_variant_analysis` (41 em 14/10/2026). Só "Sem especialidade" (86 jornadas em mar/2026) fica fora da lista, então essas jornadas entram nos visuais apenas com o filtro de especialidade vazio.
- `dim_tipo_jornada`: criado para esta página, com os 7 rótulos de negócio, os mesmos do `case` dos datasets de dado.

```sql
select 'Atendimento de emergência' as tipo_jornada
union all select 'Internação clínica (via emergência)'
union all select 'Internação cirúrgica (via emergência)'
union all select 'Internação cirúrgica eletiva'
union all select 'Internação clínica direta'
union all select 'Cirurgia ambulatorial'
union all select 'Sem jornada classificada'
```

### Datasets excluídos

`variantes_tabela` (tabela de sequências completas, ilegível, substituída pela tabela dos 10 caminhos) e `variantes_ordem` (indicador de caminhos que só trocam a ordem, removido da página porque o conceito não se comunica bem num cartão; o achado está em `variants.md`).

### Widgets descartados durante a construção

| Widget | Motivo | Substituto |
|---|---|---|
| Tabela de sequências completas (20 variantes) | Sequências de 8 a 20 eventos, com os mesmos 6 primeiros, ilegíveis | Tabela dos 10 caminhos, com a setinha que expande o texto |
| Pareto das 10 variantes com "Caminho 01...10" | O tooltip corta a descrição do caminho | Tabela dos 10 caminhos, com cobertura acumulada |
| Cartão "caminhos que só trocam a ordem" (39,5%) | Número que exige esforço para ser compreendido, e o aviso de limite não cabe num cartão | Achado documentado em `variants.md` |

### Como configurar (aprendido na construção)

- **Barras agrupadas:** em Y axis, ⋮ e **Layout**, **Group**. O padrão empilha, e somar dois percentuais não faz sentido.
- **Texto longo na tabela:** a setinha ao lado da célula expande o caminho com quebra de linha, e parar o mouse mostra uma caixa com o texto inteiro.
- **Título com duas linhas em cards:** Shift + Enter.
- **Dropdown de filtro que lista só uma opção** logo depois de criar e ligar a três datasets: voltou ao normal com **Reset all to default**. A causa não foi identificada.