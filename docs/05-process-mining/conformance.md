# Conformance Checking

## O que é

Conformance Checking compara o comportamento **observado** (o event log) com o comportamento **esperado** (um modelo de processo) e responde a duas perguntas diferentes:

- **Fitness:** quanto do que aconteceu o modelo consegue reproduzir? Valor 1,0 significa que todos os casos cabem no modelo.
- **Precision:** quanto do que o modelo permite aparece de fato no log? Precision baixa significa que o modelo aceita muito mais caminhos do que ocorrem.

Um modelo muito permissivo tem fitness alto e precision baixa. Um modelo muito restrito tem o contrário. As duas métricas precisam ser lidas juntas.

## Token replay e alignment

| Método | Como funciona | Quando usar |
|---|---|---|
| **Token replay** | Executa cada trace sobre a Petri Net, movendo tokens a cada evento, e conta tokens faltantes e sobrando | Medida agregada (fitness e precision por fonte), custo baixo |
| **Alignment** | Para cada trace, acha a sequência de movimentos do modelo com menor custo de edição | Diagnóstico trace a trace: onde exatamente o caso desviou |

Adotado o **token replay** (ADR-0010): o modelo do Inductive Miner é sound, o custo é baixo para repetir durante o desenvolvimento, e o objetivo era quantificar por fonte, e não auditar caso a caso. O alignment fica como opção para um diagnóstico granular (ver Pendências).

## O que o projeto mede

Por `source` e por `ano_mes`: fitness, precision e `total_traces`, gravados em `gold_conformance` e mostrados na Página 3 do dashboard (`dashboard-conformidade.md`). O processo é medido por fonte porque misturar processos clinicamente distintos no mesmo modelo gera precision baixa por mistura, e não por desvio.

## Modelo de referência (ADR-0019)

Medir o mês contra um modelo descoberto dele mesmo mede o quanto o modelo descreve o log, e não o desvio do processo. Por isso o mês testado é comparado a um **período de referência**, definido por fonte e reavaliado a cada execução:

1. Se o ano anterior está inteiro ingerido (12 meses), ele é a referência.
2. Se não, a referência é tudo o que foi ingerido antes do mês testado.
3. Se não existe nada anterior, o próprio mês é a referência. Só neste caso o modelo é self-referential.

**Estado atual:** só existe março/2026, então todas as fontes caem no caso 3. Os números da Página 3 hoje medem o quanto o modelo descreve o log, e **não** o desvio do processo. O fitness 1,0 em seis fontes é esperado nesse cenário. A medida de desvio real só passa a existir com histórico.

## Resultados de março/2026

| Fonte | Fitness | Precision | Traces |
|---|---|---|---|
| Altas | 1,0 | 0,073 | 895 |
| Emergência | 1,0 | 0,3044 | 5.922 |
| Cirurgias | 1,0 | 0,0983 | 605 |
| Exames de imagem | 1,0 | 0,087 | 3.411 |
| Exames laboratoriais | 1,0 | 0,4133 | 2.734 |
| Internações | 1,0 | 0,1057 | 867 |
| Movimentações | 0,9738 | 0,0237 | 939 |

A precision baixa é esperada: a variedade de caminhos clínicos legítimos é alta (2.016 variantes no mês), e um modelo que cobre todas elas aceita muito mais do que aparece em qualquer mês. Não indica erro de processo. O fitness de 0,9738 em Movimentações, a única fonte abaixo de 1,0, não foi investigado.

## Armadilhas encontradas

**Checagem de histórico global em vez de por fonte (RQ-014).** A checagem rodava fora do laço por fonte e, com fragmentos de `ano_mes` contaminados (ADR-0018), quatro fontes receberam log de referência vazio. O modelo degenerado produziu fitness e precision exatamente 1,0, que parecia resultado bom. **Valor exatamente 1,0 em conformidade é sinal para investigar.**

**Chave de mês derivada do timestamp do evento.** Quando um evento administrativo cai em outro mês (como "Aviso de Cirurgia"), o `ano_mes` por timestamp espalha fragmentos de um lote em vários meses. O `ano_mes` correto é o do lote de ingestão (ADR-0018, RQ-015).

**Persistência por `replaceWhere`.** `gold_conformance` é gravada com `overwrite` e `replaceWhere ano_mes = mês corrente`, e preserva os meses anteriores. Reexecutar um mês sobrescreve só aquele mês.

## Como ler a Página 3

- Fitness alto e precision baixa é o padrão esperado, e o texto da página explica isso.
- Com um único mês não há tendência. O gráfico de linha só mostra segmentos a partir da segunda ingestão.
- A média simples entre fontes engana, porque os volumes são muito diferentes (5.922 contra 605 traces). Se for preciso um valor global, ponderar por `total_traces`.

## Pendências

- Reavaliar os números quando houver ao menos um ano fechado: aí a Conformance passa a medir desvio de fato.
- Alignment-based checking, se surgir a necessidade de diagnóstico caso a caso (ADR-0010 já prevê um ADR próprio).
- Investigar o fitness de 0,9738 em Movimentações.

## Referências

- Rozinat, A.; Van der Aalst, W. (2008). *Conformance Checking of Processes Based on Monitoring Real Behavior*. Information Systems.
- Van der Aalst, W. (2016). *Process Mining: Data Science in Action*, capítulos sobre conformance.
- Documentação do PM4Py: `fitness_token_based_replay`, `precision_token_based_replay`.
- ADR-0010 (token replay), ADR-0019 (modelo de referência), ADR-0018 (`ano_mes` de lote), RQ-014, RQ-015, `dashboard-conformidade.md`.