# Análise de variantes (Variant Analysis)

## O que é

Uma **variante** (na página do dashboard, um **caminho**) é uma sequência distinta de atividades seguida por uma ou mais jornadas. Duas jornadas estão na mesma variante quando passam pelas mesmas atividades, na mesma ordem. A análise conta quantas jornadas seguem cada sequência e responde a perguntas como: quão padronizado é o processo? Quantos caminhos cobrem a maior parte das jornadas? Quanto tempo cada caminho leva? O que é comum e o que é exceção?

Ela complementa as outras análises. A descoberta mostra o modelo que descreve o log, a conformidade mede o quanto o log cabe nele, e as variantes mostram os caminhos reais, um a um.

## Como é calculada neste projeto

Em `03_process_mining.ipynb`, seção Variant Analysis, sobre o `df_formatado` (e não sobre o `event_log` do PM4Py):

1. **Chave:** `case_id_jornada`, e não `case_id`. A variante é o caminho da jornada do paciente, atravessando emergência, exames, internação e cirurgia (RQ-016, RQ-019).
2. **Exclusão:** jornadas cuja única fonte é `silver_exames_imagem` e cujo `case_type` é `Externo` ficam de fora (625 em mar/2026). A base de imagem inclui pacientes externos, que nunca tiveram atendimento nem internação no hospital.
3. **Ordenação** por horário do evento (ordenação estável).
4. **Atividade:** `activity_unidade`, e não `concept:name`. Nas movimentações, a unidade substitui o leito no nome (RQ-020, ADR-0021).
5. **Colapso:** repetições **consecutivas** da mesma atividade viram uma só. Repetições não consecutivas permanecem.
6. **Mês:** `ano_mes` vem de `data_referencia` do primeiro evento da jornada, a data clínica real, e não do horário do primeiro evento.
7. **Tipo de jornada:** `journey_type` vem de `gold_patient_journey`, pela chave `coalesce(cd_internacao, cd_atendimento)`. Jornadas sem correspondência ficam como `sem_jornada_classificada`.
8. **Especialidade da jornada:** emergência usa a da emergência; cirurgias usam a da cirurgia; internações clínicas usam a da alta e, sem alta, a da internação. Sem nenhuma, vale a primeira dos eventos; por fim, "Sem especialidade" (ADR-0021).
9. **Duas tabelas, gravadas na mesma célula:** `gold_variant_jornada` (uma linha por jornada, com a duração) e `gold_variant_analysis` (uma linha por variante, mês, tipo e especialidade). A segunda é gravada a partir da primeira, para as duas nunca divergirem.

## O que as tabelas guardam

`gold_variant_analysis` guarda `rank`, `sequencia`, `total_eventos`, `ano_mes`, `journey_type`, `especialidade`, `total_casos` e `cobertura_perc`. `rank` e `cobertura_perc` valem **dentro de mês, tipo e especialidade**. A visão "todos" é somada no SQL do dashboard: `total_casos` se soma, mas `rank` e `cobertura_perc` são recalculados sobre a soma, e não somados.

`gold_variant_jornada` existe porque mediana e P90 não se somam. Ela guarda a duração de cada jornada, e o dashboard calcula o tempo na hora, sobre o filtro escolhido. Os campos estão em `data-dictionary.md`.

## Resultado de março/2026

| Medida | Por `case_id` | Por jornada, colapsado | Sem exames externos | Com unidade no lugar do leito (atual) |
|---|---|---|---|---|
| Unidades | 7.643 | 7.202 | 6.577 | 6.577 |
| Variantes | 2.359 | 1.586 | 1.525 | 1.328 |
| Maior variante | 2.015 | 1.949 | 1.949 | 1.949 (29,6%) |
| Variantes de 1 caso | 2.008 (85,1%) | 1.375 (86,7%) | 1.338 (87,7%) | 1.092 (82,2%) |

Distribuição atual por faixa de jornadas por caminho:

| Faixa | Caminhos | % dos caminhos | Jornadas | % das jornadas |
|---|---|---|---|---|
| um caso | 1.092 | 82,2 | 1.092 | 16,6 |
| de 2 a 5 | 157 | 11,8 | 417 | 6,3 |
| de 6 a 20 | 52 | 3,9 | 538 | 8,2 |
| de 21 a 100 | 20 | 1,5 | 903 | 13,7 |
| mais de 100 | 7 | 0,5 | 3.627 | 55,1 |

Os 10 caminhos mais comuns cobrem 58,74% das jornadas, e todos são de emergência. O caminho mais comum (consulta e alta) tem mediana de 1,9 h e P90 de 5,3 h. Com exame laboratorial sobe para 3,7 h e 6,7 h, e com imagem e laboratório a mediana fica entre 3,8 e 4,9 h.

A cauda longa persiste: 82% dos caminhos têm uma jornada só. É característica do domínio, porque cada paciente tem um conjunto próprio de exames e etapas, e é a mesma razão da precision baixa na conformidade (`conformance.md`). Na emergência simples, 2.286 jornadas seguem 11 caminhos (207,8 jornadas por caminho). Nos perfis com internação e cirurgia, a razão é de 2,0 ou menos, ou seja, quase cada jornada tem um caminho próprio. Os números são de um único mês.

## Variantes que diferem só pela ordem

Ignorando a ordem dos eventos, os 1.328 caminhos distintos viram 803 conjuntos de etapas: 39,5% dos caminhos têm as mesmas atividades de outro caminho, só em outra ordem. Na emergência a proporção é 62,7%, e na internação cirúrgica eletiva, 57,1%.

A medida é um limite superior do efeito clínico, porque inclui qualquer diferença de ordem, inclusive a de eventos administrativos. O caso conhecido é "Alta da Emergência" antes ou depois de "Fim da Consulta Médica": os médicos dão a alta e depois encerram a consulta, e as duas ordens continuam como variantes distintas, sem normalização.

O indicador foi testado como cartão da página e removido, porque o conceito não se comunica bem em um número só. O achado fica aqui.

## Armadilhas

**Chave do caso.** Com `case_id`, as maiores variantes eram fragmentos de uma fonte (3 das 10 maiores eram só exame de imagem), sem a passagem por internação ou cirurgia.

**População fora de escopo.** Exames de pacientes externos aparecem no topo do ranking se não forem excluídos. Exclui-se pela combinação "só imagem" e "Externo", para que um exame de paciente internado sem vínculo continue visível como sinal de problema.

**Repetição de exames.** Cada quantidade de pedidos, coletas e laudos criava uma variante nova (uma tinha 26 eventos). O colapso reduz esse efeito, mas não o elimina quando a repetição não é consecutiva.

**Leito no nome da movimentação.** `INTERNACAO: Externo → EXENF02` e `INTERNACAO: Externo → EXENF04` contavam como etapas distintas. Com a unidade no lugar do leito, as atividades de movimentação caíram de 1.167 para 111 e as variantes de 1.525 para 1.328 (RQ-020).

**Mês pelo primeiro evento.** Em casos cirúrgicos atribuía a jornada ao mês do agendamento. A correção usa `data_referencia`.

**Ranking global.** Um ranking único acumulado mistura meses e esconde mudança de padrão.

**Mediana de medianas.** Mediana e percentil não se somam ao filtrar por tipo ou especialidade. Por isso o tempo é calculado a partir de `gold_variant_jornada`, jornada a jornada.

**Jornadas sem nenhum timestamp.** O `gold_event_log` tem 7.512 valores de `case_id_jornada`, e a análise parte de 7.202. As 310 de diferença são jornadas em que nenhum evento tem timestamp, descartadas pelo `format_dataframe`. É dado ausente na origem (RQ-004), e não perda de pipeline.

## Limitações

- **Um único mês.** A distribuição das variantes, o tamanho da cauda e as faixas de frequência vão mudar com o histórico.
- **Jornadas sem correspondência em `gold_patient_journey`.** 231 jornadas ficam como `sem_jornada_classificada`: 177 com alta e/ou movimentações de leito, 52 de cirurgia e 2 de emergência convertida. Nenhuma tem internação em `silver_internacoes`. A explicação de cada grupo está na RQ-019.
- **Variante "Alta médica → Alta Hospitalar"** (78 jornadas): pertence ao grupo acima e aparece no ranking de `sem_jornada_classificada`, e não no de um tipo de jornada real.
- **Repetições não consecutivas** (pedido, coleta e laudo, e depois outro pedido) continuam gerando variantes distintas.
- **Nomes de movimentação:** leito sem unidade no mapa mantém o leito no nome (4 de 2.640 eventos em mar/2026).

## Referências

- Van der Aalst, W. (2016). *Process Mining: Data Science in Action*, capítulos sobre análise de variantes e filtragem de logs.
- Documentação do PM4Py: `pm4py.get_variants` (usada só na exploração do notebook).
- `gold_variant_analysis` e `gold_variant_jornada` em `data-dictionary.md`, ADR-0021, RQ-004, RQ-015, RQ-016, RQ-019, RQ-020, `dashboard-variantes.md`, `conformance.md`.