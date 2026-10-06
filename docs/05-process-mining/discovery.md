# Descoberta de processo (Process Discovery)

## O que é

Descoberta de processo é a técnica que recebe um event log e devolve um **modelo de processo**, sem que ninguém o desenhe antes. Em vez de perguntar ao hospital "como o fluxo deveria ser", pergunta-se ao dado "como o fluxo foi". O modelo descoberto serve de base para as outras análises: Conformance Checking compara o log contra ele, e as demais análises usam o mesmo vocabulário de atividades.

## Os três algoritmos clássicos

| Algoritmo | Estratégia | Ponto forte | Limitação |
|---|---|---|---|
| **Alpha Miner** (Van der Aalst et al., 2004) | Relações absolutas de ordem ("A sempre precede B") | Elegante e fácil de explicar | Não tolera ruído, falha com loops e paralelismo complexo. Mais acadêmico que prático |
| **Heuristic Miner** | Frequências ("A precede B em 87% dos casos") com limiar manual | Robusto a ruído | O limiar é subjetivo e o resultado muda com ele. Sem garantia formal sobre o modelo |
| **Inductive Miner** (Leemans et al., 2013) | Divide o log recursivamente por cortes lógicos (sequência, escolha, paralelismo, loop) | Modelo sempre *sound*, tolerância a ruído parametrizada | Pode produzir modelo permissivo, que aceita mais comportamento do que o log tem |

**Soundness** significa que o modelo não tem deadlock, não tem livelock e todo caminho termina. É pré-condição para Conformance Checking: token replay sobre um modelo que não é sound mede defeito do modelo, e não desvio do processo.

## Process Tree e Petri Net

O Inductive Miner devolve um **Process Tree**, uma árvore cujos nós são operadores (sequência, escolha exclusiva, paralelismo, loop) e cujas folhas são atividades. O PM4Py converte a árvore em **Petri Net** (`convert_to_petri_net`) para o token replay. A árvore é a forma mais legível para humanos, e a Petri Net é a forma executável.

## Decisão no projeto

Adotado o **Inductive Miner** (ADR-0009). Razões, resumidas:

1. O `gold_event_log` tem ruído conhecido (timestamps nulos concentrados em exames de imagem, RQ-004, e variantes raras de variabilidade clínica genuína). O `noise_threshold` permite tratar isso de forma explícita.
2. A Conformance Checking depende de um modelo sound.
3. O volume (cerca de 190 mil eventos, 7,6 mil traces) é tratável sem otimização.

Alpha Miner foi descartado por não tolerar ruído. Heuristic Miner, por não garantir soundness e exigir um limiar sem justificativa clínica.

## Como é usado no código

Em `03_process_mining.ipynb`:

- **Descoberta geral:** `pm4py.discover_process_tree_inductive(event_log)` sobre o log inteiro, com os parâmetros padrão (`noise_threshold = 0`, sem simplificação). Serve de visão panorâmica.
- **Descoberta por fonte, na Conformance Checking:** para cada `source`, o Process Tree é descoberto a partir de um **período de referência**, e não do mês testado (ADR-0019). Cada fonte decide a própria referência.
- A visualização do Process Tree é gerada localmente com Graphviz, porque o ambiente serverless do Databricks Free Edition bloqueia a renderização.

## Armadilhas encontradas

**Misturar processos clinicamente distintos no mesmo modelo.** Emergência, cirurgia e internação no mesmo Process Tree produzem um modelo excessivamente permissivo, com precision baixa, e a causa é a mistura, e não a qualidade do dado. Por isso a Conformance Checking é feita por fonte.

**Modelo descoberto do próprio log testado.** Com o Inductive Miner sem ruído, o modelo reproduz o log que o gerou, então o fitness sai próximo de 1,0 por construção. Foi o que a primeira versão da Conformance Checking fez (modelo self-referential), e por isso passou a usar um modelo de referência separado (ADR-0019).

**Log de referência vazio.** Descobrir um Process Tree a partir de um log vazio produz um modelo degenerado, e o fitness e a precision saem em 1,0 exato, com cara de resultado bom. Aconteceu em 4 das 7 fontes (RQ-014). Valor exatamente igual a 1,0 em uma métrica de conformidade é sinal para investigar, e não para comemorar.

**Precision baixa não é erro do algoritmo.** Em ambiente hospitalar, a variedade de caminhos clínicos legítimos (2.016 variantes em março/2026) faz o modelo aceitar muito mais do que aparece em um único mês.

## Referências

- Van der Aalst, W.; Weijters, T.; Maruster, L. (2004). *Workflow Mining: Discovering Process Models from Event Logs*. IEEE TKDE.
- Leemans, S.; Fahland, D.; Van der Aalst, W. (2013). *Discovering Block-Structured Process Models from Event Logs: A Constructive Approach*. Petri Nets 2013.
- Van der Aalst, W. (2016). *Process Mining: Data Science in Action*, capítulos sobre descoberta de processo.
- Documentação do PM4Py: `pm4py.discover_process_tree_inductive`, `pm4py.convert_to_petri_net`.
- ADR-0009 (escolha do algoritmo), ADR-0019 (modelo de referência), RQ-004, RQ-014.