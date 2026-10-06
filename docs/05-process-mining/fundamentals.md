# Fundamentos de Process Mining

## O que é

Process Mining é a disciplina que extrai conhecimento sobre processos a partir dos **registros de eventos** que os sistemas de informação já produzem. Ela fica entre a ciência de dados (que olha para os dados) e a gestão de processos (que olha para o fluxo de trabalho). Em vez de perguntar a quem executa "como o processo funciona", pergunta-se ao registro "como o processo aconteceu".

Quem formalizou grande parte da área foi Wil van der Aalst, que também propôs o Alpha Miner (2004, ver `discovery.md`) e escreveu o livro de referência, *Process Mining: Data Science in Action* (2016).

## Os três tipos

| Tipo | Entrada | Saída | Pergunta | Capítulo |
|---|---|---|---|---|
| **Descoberta** | event log | modelo de processo | Qual é o processo real? | `discovery.md` |
| **Conformidade** | event log + modelo | desvios, fitness, precision | O processo real segue o esperado? | `conformance.md` |
| **Melhoria** (enhancement) | event log + modelo | modelo enriquecido (tempos, gargalos, recursos) | Onde o processo pode melhorar? | `bottlenecks.md` |

## As perspectivas

Uma mesma análise pode olhar o processo por ângulos diferentes:

| Perspectiva | Pergunta | Neste projeto |
|---|---|---|
| **Fluxo de controle** | Em que ordem as coisas acontecem? | Process Tree, variantes, desenho da jornada (Página 4) |
| **Tempo** | Quanto demora, onde espera? | Gargalos, Performance Spectrum, DFG (Página 2) |
| **Organizacional** | Quem passa o trabalho para quem? | Handover e subcontracting (Página 4, `social-network-analysis.md`) |
| **Caso / dados** | O que distingue um caso do outro? | `gold_case_attributes`, porta de entrada, especialidade |

## Do dado ao insight, no projeto

1. **Event log** (`event-log.md`): `gold_event_log`, com uma linha por evento.
2. **Descoberta** (`discovery.md`): Inductive Miner sobre o log.
3. **Conformidade** (`conformance.md`): fitness e precision por fonte e mês.
4. **Desempenho** (`bottlenecks.md`): tempo entre atividades e entre marcos.
5. **Variantes** (`variants.md`): caminhos reais, com a contagem de casos de cada um.
6. **Organizacional** (`social-network-analysis.md`): handover e subcontracting.
7. **Entrega:** quatro páginas de dashboard (KPIs, Gargalos, Conformidade, Handover).

## Por que PM4Py

ADR-0004: custo zero, programável, versionável e reproduzível, com os algoritmos modernos e suporte ao padrão XES. Celonis foi descartado por custo e por ser fechado, Disco por ser uma ferramenta de interface gráfica sem versionamento, e Apromore Community pelo menor encaixe com o resto do projeto. Foi validado em 15/06/2026 que o PM4Py 2.7.22.4 instala no compute serverless da Free Edition.

## Particularidades de dado hospitalar

**O "caso" não é óbvio.** O mesmo paciente aparece com identificadores diferentes em cada sistema (atendimento de emergência, internação, cirurgia). A escolha da chave do caso muda o que cada análise consegue enxergar (RQ-016).

**Alta variedade legítima.** Cada paciente é diferente, então há muitas variantes e a precision é baixa. Isso é característica do domínio, e não defeito do processo.

**Registro tardio e inversões.** Há eventos registrados depois do que aconteceu, e timestamps incoerentes (RQ-003, RQ-005). Frequência não decide a ordem correta de um fluxo (ADR-0016).

**Dado ausente na origem.** Etapas do exame de imagem sem timestamp (RQ-004), e a base de laboratório que cobre só emergência (RQ-018). Process Mining expõe essas lacunas, o que também é um resultado.

**Privacidade.** O ator das análises é o processo de origem e a especialidade, nunca a pessoa (ADR-0008). O dado é anonimizado localmente antes de subir ao Databricks (LGPD).

## Armadilhas gerais

**Confundir modelo com realidade.** O modelo descoberto é uma simplificação do log. Um modelo permissivo aceita quase tudo, e um muito restrito rejeita casos legítimos.

**Medir o modelo contra o log que o gerou.** O resultado diz o quanto o modelo descreve o log, e não o quanto o processo desvia (ADR-0019).

**Valores perfeitos.** Fitness ou precision exatamente 1,0 é sinal para investigar, e não para comemorar (RQ-014).

**Um mês de dado.** Sem histórico não há tendência, e contagens pequenas oscilam. Vários resultados deste projeto ficam pendentes da ingestão dos cerca de 2 anos de histórico.

## Referências

- Van der Aalst, W. (2016). *Process Mining: Data Science in Action* (2ª ed.). Springer.
- Berti, A.; Van Zelst, S.; Van der Aalst, W. (2019). *Process Mining for Python (PM4Py): Bridging the Gap Between Process- and Data Science*. ICPM Demo.
- IEEE 1849-2016 (XES).
- ADR-0004, ADR-0008, ADR-0016, ADR-0019, RQ-003, RQ-004, RQ-005, RQ-014, RQ-016, RQ-018.