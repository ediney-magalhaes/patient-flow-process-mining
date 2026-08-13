# Dashboard — Página 1: KPIs de Jornada

- **Local:** AI/BI Dashboard `Mapa Digital do Fluxo do Paciente`, aba "KPIs de Jornada"
- **Decisão arquitetural:** ADR-0014 (nomenclatura de negócio de `journey_type` e
  estrutura Bloco A / Bloco B)
- **Status:** publicado (versão inicial, mar/2026)

Este documento cobre artefatos que vivem **dentro do próprio Dashboard**
(datasets SQL salvos e campos calculados do Data Model), não versionados
como objetos do Unity Catalog. Diferente de `data-dictionary.md`, que cobre
tabelas e views reais do catálogo, o conteúdo aqui só existe dentro da
definição do Dashboard e não é consultável via notebook ou outro cliente SQL.

---

## Estrutura da página

Duas seções, cada uma com um título Markdown como divisor visual (fundo
roxo/lavanda para "Jornada Emergência", azul para "Jornada Internação"),
um filtro global `Período` (campo `ano_mes`) no topo, cards de KPI, e dois
gráficos por seção (tendência mensal + distribuição por categoria).

### Seção "Jornada Emergência" (Bloco A)

**Cards** (todos filtrados a `Cd Atendimento Is Null = false`):

| Card | Fonte | Cálculo |
|---|---|---|
| Total de Atendimentos | `gold_patient_journey` | `COUNT DISTINCT(cd_atendimento)` |
| Taxa de Conversão (%) | `gold_patient_journey` | `AVG(Fl Conversao)`, formato % |
| Taxa de Conversão Cirúrgica (%) | `gold_patient_journey` | `AVG(Has Cirurgia Numerico)`, formato % |
| Taxa de Conversão UTI (%) | `gold_patient_journey` | `AVG(Has Uti Numerico)`, formato % |
| Tempo até o Leito (h) | `gold_patient_journey` | `AVG(Duracao Internacao Leito Horas)` |
| Tempo Médio da Jornada (h) | `gold_patient_journey` | `AVG(Duracao Total Horas)` |

**Gráfico "Duração Média por Tipo de Jornada (Emergência)"** — barra,
dataset `kpis_jornada_emergencia_por_tipo`, eixo X `tipo_jornada`, eixo Y
`SUM(duracao_media_horas)`, ordenado decrescente, tooltip com
`coeficiente_variacao` (CV%, ver nota de formatação abaixo). Cobre as
quatro categorias do Bloco A.

**Gráfico "Tendência Mensal — Tempo Médio da Jornada"** — linha, dataset
`kpis_jornada_emergencia`, eixo X `ano_mes`, eixo Y
`SUM(tempo_medio_jornada_horas)`. Configurado para **ignorar** o filtro
global `Período` — sempre mostra a série histórica completa, mesmo quando
um mês específico está selecionado nos cards.

### Seção "Jornada Internação" (hospital todo — Bloco A + Bloco B)

**Cards** (todos filtrados a `Cd Internacao Is Null = false`):

| Card | Fonte | Cálculo |
|---|---|---|
| Total de Internações | `gold_patient_journey` | `COUNT DISTINCT(cd_internacao)` |
| Internações via Emergência (%) | `gold_patient_journey` | `AVG(Is Internacao Via Emergencia)`, formato % |
| Internações Cirúrgicas (%) | `gold_patient_journey` | `AVG(Has Cirurgia Numerico)`, formato % |
| Internações c/ UTI (%) | `gold_patient_journey` | `AVG(Has Uti Numerico)`, formato % |
| Tempo Médio até o Leito (h) | `gold_patient_journey` | `AVG(Duracao Internacao Leito Horas)` |

**Gráfico "Duração Média por Tipo de Jornada (Internação)"** — barra,
dataset `kpis_jornada_internacao_direta_por_tipo`, eixo X `tipo_jornada`,
eixo Y `SUM(duracao_media_horas)`, ordenado decrescente, tooltip com
`coeficiente_variacao`. Cobre as duas categorias do Bloco B
(`internacao_cirurgica_eletiva`, `internacao_clinica_direta`).

**Gráfico "Tendência Mensal — Tempo até o Leito"** — linha, dataset
`gold_patient_journey`, eixo X `Ano Mes`, eixo Y
`AVG(Duracao Internacao Leito Horas)`, filtro `Cd Internacao Is Null =
false`. Ignora o filtro global `Período`, mesma lógica da seção anterior.

**Decisões de escopo descartadas nesta sessão** (registradas para não
repetir a investigação): um card de "Tempo Médio da Jornada" para a
Internação foi cogitado e descartado — a métrica correta (tempo até a
alta) sofre de viés estrutural, pois exclui internações ainda sem alta
lançada no mês de corte (~17% dos casos em mar/2026), subestimando a
permanência real. Um card de "Tempo Médio até a Cirurgia" também foi
cogitado e descartado por fugir do escopo de visão geral da Página 1 (o
tempo até a cirurgia difere fortemente por origem — 11,2h para eletiva vs.
55,8h para emergência — análise que pertence à Página 2, Análise de
Gargalos). Um card de "Tempo Médio de UTI" foi descartado por medir
permanência dentro da UTI, não tempo até chegar nela, fora do propósito
pretendido.

---

## Datasets SQL do Dashboard

### `kpis_jornada_emergencia`

Grão: 1 linha por `ano_mes`. Alimenta os cards de percentual/tempo médio e
o gráfico de tendência da seção Emergência.

```sql
select
  ano_mes,
  count(distinct cd_atendimento) as total_atendimento,
  round(sum(fl_conversao) * 100.0 / count(distinct cd_atendimento), 1) as tx_conversao,
  round(sum(case when has_cirurgia = true then 1 else 0 end) * 100.0 / count(distinct cd_atendimento), 1) as tx_conversao_cirurgica,
  round(sum(case when has_uti = true then 1 else 0 end) * 100.0 / count(distinct cd_atendimento), 1) as tx_conversao_uti,
  round(avg(duracao_total_min) / 60.0, 1) as tempo_medio_jornada_horas
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

### `kpis_jornada_emergencia_por_tipo`

Grão: 1 linha por `journey_type` (categoria de negócio, ver ADR-0014).
Alimenta o gráfico de distribuição da seção Emergência.

```sql
select
  case journey_type when 'atendimento_emergencia' then 'Atendimento Emergência'
                    when 'cirurgia_ambulatorial' then 'Cirurgia Ambulatorial'
                    when 'internacao_clinica' then 'Internação Clínica'
                    when 'internacao_cirurgica_emergencia' then 'Internação Cirúrgica (Emergência)'
  end as tipo_jornada,
  round(avg(duracao_total_min) / 60.0, 1) as duracao_media_horas,
  round(stddev(duracao_total_min) / 60.0, 1) as desvio_padrao_horas,
  round((stddev(duracao_total_min) / avg(duracao_total_min)) * 100, 1) as coeficiente_variacao
from hospital_santa_rosa.gold_fluxo.gold_patient_journey
where duracao_total_min is not null
      and journey_type in('atendimento_emergencia', 'cirurgia_ambulatorial', 'internacao_clinica', 'internacao_cirurgica_emergencia')
group by journey_type
order by duracao_media_horas desc
```

### `kpis_jornada_internacao_direta`

Grão: 1 linha por `ano_mes`, escopado ao Bloco B (`cd_atendimento is
null`). Criado nesta sessão; hoje sem widget consumidor ativo na Página 1
(os cards de Internação migraram para escopo "hospital todo" via
`gold_patient_journey` direto). Mantido para uso futuro caso a seção volte
a precisar de uma visão exclusiva do Bloco B por mês.

```sql
select
  ano_mes,
  count(distinct cd_internacao) as total_internacoes,
  sum(case when has_cirurgia = true then 1 else 0 end) as total_cirurgias,
  round(avg(duracao_total_min) / 60.0, 1) as tempo_medio_jornada_horas,
  round(sum(case when has_uti = true then 1 else 0 end) * 100.0 / count(distinct cd_internacao), 1) as tx_uti,
  round((stddev(duracao_total_min) / avg(duracao_total_min)) * 100.0, 1) as coeficiente_variacao
from hospital_santa_rosa.gold_fluxo.gold_patient_journey
where cd_atendimento is null
group by ano_mes
order by ano_mes
```

### `kpis_jornada_internacao_direta_por_tipo`

Grão: 1 linha por `journey_type`, escopado às duas categorias do Bloco B.
Alimenta o gráfico de distribuição da seção Internação.

```sql
select
  case journey_type when 'internacao_cirurgica_eletiva' then 'Internação Cirúrgica Eletiva'
                    when 'internacao_clinica_direta' then 'Internação Clínica Direta'
  end as tipo_jornada,
  round(avg(duracao_total_min) / 60.0, 1) as duracao_media_horas,
  round(stddev(duracao_total_min) / 60.0, 1) as desvio_padrao_horas,
  round((stddev(duracao_total_min) / avg(duracao_total_min)) * 100, 1) as coeficiente_variacao
from hospital_santa_rosa.gold_fluxo.gold_patient_journey
where duracao_total_min is not null
      and journey_type in('internacao_cirurgica_eletiva', 'internacao_clinica_direta')
group by journey_type
order by duracao_media_horas desc
```

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
| `Is Internacao Via Emergencia` | `CASE WHEN source.journey_type IN ('internacao_clinica', 'internacao_cirurgica_emergencia') THEN 1 ELSE 0 END` | Base do card "% Internações via Emergência" |
| `Duracao Total Horas` | `source.duracao_total_min / 60` | Duração total da jornada, chegada/entrada até alta, em horas |
| `Duracao Total Dias` | `source.duracao_total_min / 1440` | Idem, em dias — não usado nos cards finais, mantido pela investigação de permanência |
| `Duracao Internacao Leito Horas` | `(unix_timestamp(source.ts_primeiro_leito) - unix_timestamp(source.ts_entrada_internacao)) / 3600` | Tempo entre abertura da internação e chegada ao leito físico. Não depende de alta — livre do viés de exclusão de internações em curso |
| `Duracao Internacao Alta Dias` | `(unix_timestamp(coalesce(source.ts_alta_final, source.ts_alta_medica)) - unix_timestamp(source.ts_entrada_internacao)) / 86400` | Tempo de permanência (entrada até alta), em dias. **Sofre de viés conhecido**: exclui internações sem alta lançada no mês de corte (~17% em mar/2026) — não usado nos cards finais por esse motivo |

---

## Publicação e compartilhamento

Dashboard publicado com permissão de dados "Share data permission"
(credencial do publisher) — apropriado para o público-alvo (Diretoria
Assistencial, sem contas próprias no workspace Databricks). Acesso de
visualização concedido individualmente via e-mail na tela de
compartilhamento; não há grupo amplo configurado ainda.