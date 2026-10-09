# Análise de variantes (Variant Analysis)

## O que é

Uma **variante** é uma sequência distinta de atividades seguida por um ou mais casos. Dois casos estão na mesma variante quando passam pelas mesmas atividades, na mesma ordem. A análise de variantes conta quantos casos seguem cada sequência e responde a perguntas como: quão padronizado é o processo? Quantos caminhos cobrem a maior parte dos casos? O que é caminho comum e o que é exceção?

Ela complementa as outras análises. A descoberta mostra o modelo que descreve o log, a conformidade mede o quanto o log cabe nele, e as variantes mostram os caminhos reais, um a um.

## Como é calculada neste projeto

Em `03_process_mining.ipynb`, seção Variant Analysis, sobre o `df_formatado` (e não sobre o `event_log` do PM4Py):

1. **Chave:** `case_id_jornada`, e não `case_id`. A variante é o caminho da jornada do paciente, atravessando emergência, exames, internação e cirurgia (RQ-016, RQ-019).
2. **Exclusão:** jornadas cuja única fonte é `silver_exames_imagem` e cujo `case_type` é `Externo` ficam de fora. A base de imagem inclui pacientes externos, que nunca tiveram atendimento nem internação no hospital.
3. **Ordenação** por horário do evento (ordenação estável).
4. **Colapso:** repetições **consecutivas** da mesma atividade viram uma só. Repetições não consecutivas permanecem.
5. **Mês:** `ano_mes` vem de `data_referencia` do primeiro evento da jornada, a data clínica real, e não do horário do primeiro evento.
6. **Tipo de jornada:** `journey_type` vem de `gold_patient_journey`, pela mesma chave (`coalesce(cd_internacao, cd_atendimento)`). Jornadas sem correspondência ficam como `sem_jornada_classificada` (231 em mar/2026, quatro populações explicadas na RQ-019).
7. **Ranking** calculado dentro de cada `ano_mes` e de cada `journey_type`, e não de forma global.
8. O resultado é gravado em `gold_variant_analysis`, com uma linha por variante, mês e tipo de jornada (1.531 linhas em mar/2026).

## O que a tabela guarda

| Coluna | Significado |
|---|---|
| `rank` | posição da variante dentro do mês e do tipo de jornada (1 = mais frequente) |
| `sequencia` | atividades separadas por `→`, já colapsadas |
| `total_eventos` | tamanho da sequência colapsada |
| `ano_mes` | mês da jornada, derivado de `data_referencia` |
| `journey_type` | tipo de jornada, vindo de `gold_patient_journey`; `sem_jornada_classificada` quando a jornada não existe lá (ver RQ-019) |
| `total_casos` | jornadas que seguem exatamente essa variante no mês e no tipo |
| `cobertura_perc` | `total_casos` sobre o total de jornadas do mesmo mês e tipo |

`rank` e `cobertura_perc` valem **dentro do tipo de jornada**. A visão "todos os tipos" é somada no SQL do dashboard: `total_casos` se soma, mas `rank` e `cobertura_perc` precisam ser recalculados sobre a soma, e não somados. Para saber quanto as N variantes mais comuns cobrem juntas, soma-se a cobertura em ordem de rank. Essa curva acumulada é o Pareto da Página 5.

## Resultado de março/2026

| Medida | Por `case_id` | Por jornada, colapsado | Sem exames externos (atual) |
|---|---|---|---|
| Unidades | 7.643 | 7.202 | 6.577 |
| Variantes | 2.359 | 1.586 | 1.525 |
| Maior variante | 2.015 | 1.949 | 1.949 (29,6%) |
| Variantes de 1 caso | 2.008 (85,1%) | 1.375 (86,7%) | 1.338 (87,7%) |

A cauda longa persiste: cerca de 88% das variantes têm um único caso. É característica do domínio, porque cada paciente tem um conjunto próprio de exames e etapas, e é a mesma razão da precision baixa na conformidade (`conformance.md`). Os números são de um único mês e vão mudar com o histórico.

## Armadilhas

**Chave do caso.** Com `case_id`, as maiores variantes eram fragmentos de uma fonte (3 das 10 maiores eram só exame de imagem), sem a passagem por internação ou cirurgia.

**População fora de escopo.** Exames de pacientes externos aparecem no topo do ranking se não forem excluídos. Exclui-se pela combinação "só imagem" e "Externo", para que um exame de paciente internado sem vínculo continue visível como sinal de problema.

**Repetição de exames.** Cada quantidade de pedidos, coletas e laudos criava uma variante nova (uma tinha 26 eventos). O colapso de repetições consecutivas reduz esse efeito, mas não o elimina quando a repetição não é consecutiva.

**Mês pelo primeiro evento.** Em casos cirúrgicos atribuía a jornada ao mês do agendamento. A correção usa `data_referencia`.

**Ranking global.** Um ranking único acumulado mistura meses e esconde mudança de padrão.

**Ordem dos eventos.** "Alta da Emergência → Fim da Consulta Médica" e "Fim da Consulta Médica → Alta da Emergência" são variantes distintas, e não foram normalizadas: dar a alta antes de encerrar a consulta é a prática real dos médicos.

## Limitações

- **Um único mês.** Os números são de março/2026. A distribuição das variantes, o tamanho da cauda e as faixas de frequência vão mudar com o histórico.
- **Jornadas sem correspondência em `gold_patient_journey`.** 231 jornadas ficam como `sem_jornada_classificada`: 177 com alta e/ou movimentações de leito, 52 de cirurgia e 2 de emergência convertida. Nenhuma tem internação em `silver_internacoes`. A explicação de cada grupo e a hipótese de internações anteriores a março estão na RQ-019.
- **Variante "Alta médica → Alta Hospitalar"** (78 casos, 9ª maior): pertence ao grupo acima. Aparece no ranking de `sem_jornada_classificada`, e não no de nenhum tipo de jornada real.
- **Cauda longa.** Cerca de 88% das variantes têm um único caso. Cada paciente tem um conjunto próprio de exames e etapas.
- **Repetições não consecutivas** (pedido, coleta e laudo, e depois outro pedido) continuam gerando variantes distintas.

## Referências

- Van der Aalst, W. (2016). *Process Mining: Data Science in Action*, capítulos sobre análise de variantes e filtragem de logs.
- Documentação do PM4Py: `pm4py.get_variants` (usada só na exploração do notebook).
- `gold_variant_analysis` em `data-dictionary.md`, RQ-004, RQ-015, RQ-016, RQ-019, `conformance.md`.