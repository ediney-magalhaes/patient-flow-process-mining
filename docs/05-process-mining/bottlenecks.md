# Gargalos e tempos de espera (Bottleneck Analysis e Performance Spectrum)

## O que é

Análise de gargalos mede **quanto tempo passa entre duas atividades consecutivas** do mesmo caso e aponta onde o processo espera. Não pergunta "qual é o caminho" (descoberta) nem "o caminho segue o modelo" (conformance), e sim "onde o paciente fica parado". Duas visões complementares:

| Visão | Pergunta | Tabela do projeto |
|---|---|---|
| **Bottleneck** | Qual transição demora mais, e com que variabilidade? | `gold_bottleneck` |
| **Performance Spectrum** | Esse tempo muda conforme o dia da semana? | `gold_performance_spectrum` |

Uma terceira tabela, `gold_dfg_macro`, mede o tempo entre **marcos** escolhidos à mão, para o grafo panorâmico (ver abaixo).

## Como é calculado

Em `03_process_mining.ipynb`, os eventos são ordenados por `case_id_jornada` e horário. Com `shift(1)` (ou `shift(-1)` no Performance Spectrum) pegam-se a atividade e o horário do evento vizinho, e o tempo da transição é a diferença entre os dois. Depois agrega-se por transição.

Três decisões moldam o resultado:

**1. A chave é `case_id_jornada`, e não `case_id`.** A sequência atravessa as fontes (emergência → internação → cirurgia → movimentação → alta). Com `case_id`, a passagem entre processos não existe, o mesmo problema que o handover teve (RQ-016).

**2. A transição pertence a quem a originou.** `source`, `especialidade` e `ano_mes` são os do evento de **origem**. Filtrar por "Emergência" mostra as transições que começam na emergência, inclusive a saída dela para outro processo (ex.: `Fim da Consulta → Internação`).

**3. `ano_mes` vem de `data_referencia`, não do horário do evento.** Eventos administrativos, como "Aviso de Cirurgia", podem acontecer semanas antes do procedimento e distorcem a atribuição de mês. `data_referencia` é a data do evento clínico real, definida na Gold por fonte.

## O que cada tabela guarda

**`gold_bottleneck`**, uma linha por transição × fonte × mês × especialidade de origem: tempo médio, mediano, desvio padrão, frequência e coeficiente de variação (`cv_pct = desvio / média × 100`). Alto CV indica transição imprevisível, mesmo que a média seja baixa.

**`gold_performance_spectrum`**, mesma granularidade mais o dia da semana: mediana, P25 e P75. Transições com tempo negativo são removidas, porque indicam timestamps incoerentes (ver RQ-005). Esta tabela é **agregada**. O Performance Spectrum "clássico", com uma linha por caso colorida pela duração, exige granularidade de caso individual, que não existe hoje. Está reservado para o Databricks App.

**`gold_dfg_macro`**, uma linha por transição entre 15 marcos × mês × especialidade. O tempo é o **total decorrido entre dois marcos** e pode incluir passos intermediários omitidos (exames, etapas de cirurgia). Por isso **não é comparável** ao tempo de `gold_bottleneck` para o mesmo par de atividades. Detalhes em ADR-0016.

## Achados de março/2026

- **Maior gargalo:** `Aviso de Cirurgia → Internação`, com mediana da ordem de dias, mesmo após filtrar combinações de baixo volume (menos de 10 ocorrências). Não é artefato de pouco dado.
- **Sem sazonalidade semanal relevante** nos dias úteis. A leitura do notebook é que o gargalo é estrutural, e não operacional. Com um único mês, isso precisa ser reconferido com o histórico.

## Armadilhas encontradas

**Escolher a direção de uma transição pela frequência.** Na curadoria do DFG, `Alta da Emergência → Fim da Consulta` (5.056 casos) era muito mais frequente que `Fim da Consulta → Alta da Emergência` (467). A direção frequente era o artefato conhecido de **atraso de registro médico**, e o fluxo clínico correto era a outra. Frequência não decide direção neste domínio (ADR-0016).

**Reduzir o grafo por piso de frequência.** Com um único mês, frequência baixa não distingue "caminho irrelevante" de "caminho real ainda pouco amostrado". A lista de 15 marcos foi definida por revisão clínica.

**Média de médias.** Agregar médias de grupos de tamanhos diferentes distorce o resultado. Em `dfg_arestas` o tempo é recalculado com média ponderada por frequência (`sum(tempo × frequência) / sum(frequência)`), e na Página 1 a regra levou a campos calculados linha a linha.

**Tempo de transição não é tempo de espera.** A diferença entre dois horários inclui a duração do próprio procedimento. Onde há início e fim de atividade (ex.: consulta), "tempo entre `Início` e `Fim`" mede duração, e não espera.

**Timestamps incoerentes.** Casos com "Alta médica" antes do fim da anestesia (RQ-005) geram transições negativas ou falsos padrões. O erro está no registro da origem, e as tabelas não corrigem.

**Atividade de movimentação com o leito no nome.** Multiplica o número de combinações de transição. Para o DFG, a movimentação é reduzida ao tipo (`TIPO` puro).

## Como são usadas na Página 2

Cards de duração macro (Emergência → Internação, Internação → Cirurgia, Até o Leito), ranking de top gargalos por transição, heatmap de padrão por dia da semana e o DFG panorâmico. Os cards usam **P90** como métrica de dispersão, e não CV%. Detalhes em `dashboard-gargalos.md`.

## Pendências

- Reconferir o gargalo `Aviso de Cirurgia → Internação` e a ausência de sazonalidade com o histórico.
- Performance Spectrum por caso (granularidade de caso individual), previsto para o Databricks App.

## Referências

- Van der Aalst, W. (2016). *Process Mining: Data Science in Action*, capítulos sobre análise de desempenho.
- Denisov, V.; Fahland, D.; Van der Aalst, W. (2018). *Unbiased, Fine-Grained Description of Processes Performance from Event Data*. BPM 2018.
- ADR-0016 (`gold_dfg_macro`), RQ-005, RQ-016, `dashboard-gargalos.md`.