# Análise de variantes (Variant Analysis)

## O que é

Uma **variante** é uma sequência distinta de atividades seguida por um ou mais casos. Dois casos estão na mesma variante quando passam pelas mesmas atividades, na mesma ordem. A análise de variantes conta quantos casos seguem cada sequência e responde a perguntas como: quão padronizado é o processo? Quantos caminhos cobrem 80% dos casos? O que é caminho comum e o que é exceção?

Ela complementa as outras análises. A descoberta mostra o modelo que descreve o log, a conformidade mede o quanto o log cabe nele, e as variantes mostram os caminhos reais, um a um.

## Como é calculada neste projeto

Em `03_process_mining.ipynb`:

1. `pm4py.get_variants(event_log)` agrupa os traces por sequência de atividades.
2. Cada variante é ordenada pelo número de casos.
3. Cada caso recebe o `ano_mes` de `data_referencia`, a data do evento clínico real, e não o horário do primeiro evento. O primeiro evento de um caso cirúrgico costuma ser "Aviso de Cirurgia", um agendamento administrativo que pode ocorrer semanas antes do procedimento.
4. O ranking é calculado **dentro de cada `ano_mes`**, e não de forma global.
5. O resultado é gravado em `gold_variant_analysis`, com uma linha por variante e mês.

## O que a tabela guarda

| Coluna | Significado |
|---|---|
| `rank` | posição da variante no mês (1 = mais frequente) |
| `sequencia` | atividades separadas por `→` |
| `total_eventos` | tamanho da sequência |
| `ano_mes` | mês do caso, derivado de `data_referencia` |
| `total_casos` | casos que seguem exatamente essa variante no mês |
| `cobertura_perc` | `total_casos` sobre o total de casos do mês |

A coluna `cobertura_perc` é por variante. Para saber quanto os N caminhos mais comuns cobrem juntos, soma-se a cobertura em ordem de rank. Essa curva acumulada é o gráfico de Pareto previsto para a Página 5 do dashboard.

## Resultado de março/2026

Foram 2.016 variantes distintas para 7.643 traces, ou seja, em média menos de quatro casos por variante. O volume é alto porque o log mistura sete fontes e porque o cuidado clínico tem muitas combinações legítimas de exames, consultas e etapas. É a mesma razão da precision baixa na conformidade (ver `conformance.md`).

## Armadilhas

**Mês pelo primeiro evento do caso.** Em casos cirúrgicos, atribuía o caso ao mês do agendamento. Em uma versão anterior, 112 de 117 casos com mês incorreto vinham dessa distorção. A correção usa `data_referencia`, definida na Gold por fonte.

**Ranking global.** Um ranking único acumulado mistura meses e esconde mudança de padrão. Com o ranking por mês, dá para comparar a variante dominante de um mês com a de outro.

**Muitas variantes não significam processo desorganizado.** A cauda longa de variantes de um caso só é esperada em ambiente hospitalar. O que importa é a cobertura das variantes mais frequentes e o que mudou ao longo do tempo.

**Variante depende do nível de detalhe das atividades.** Atividades muito granulares (como cada leito em Movimentações) multiplicam variantes sem informação nova. Se a Página 5 ficar ilegível, o primeiro ajuste é agrupar atividades.

## Pendências

- **Chave do caso.** O `event_log` do notebook é montado por `case_id` e não por `case_id_jornada`, então a variante é o caminho dentro de uma fonte e de seus vizinhos de `case_id`, e não a jornada inteira entre emergência, internação e cirurgia. Hoje a análise de variantes é a única que não usa a chave da jornada (ver RQ-016). Decidir se muda antes de construir a Página 5.
- **Filtros da Página 5.** A auditoria de 18/08 previu `ano_mes` real (já corrigido) e `journey_type` para variantes. O `journey_type` ainda não está em `gold_variant_analysis`.
- **Descrição de `total_eventos`.** O dicionário diz "número de atividades distintas na sequência", mas o código usa o comprimento da sequência (`len(sequencia)`), que conta repetições. Ajustar o texto do dicionário, ou o código, depois de conferir.
- **Contagem de 2.016 variantes** vem do dicionário e do CHANGELOG. Não foi remedida depois das correções de `ano_mes` (RQ-015).
- **Página 5** (ranking e Pareto) ainda não construída.

## Referências

- Van der Aalst, W. (2016). *Process Mining: Data Science in Action*, capítulos sobre análise de variantes e filtragem de logs.
- Documentação do PM4Py: `pm4py.get_variants`.
- `gold_variant_analysis` em `data-dictionary.md`, RQ-015, RQ-016, `conformance.md`.