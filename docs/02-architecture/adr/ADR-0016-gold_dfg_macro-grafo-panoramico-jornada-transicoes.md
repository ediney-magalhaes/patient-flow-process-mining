# ADR-0016: `gold_dfg_macro` — Grafo Panorâmico da Jornada com Curadoria Manual de Transições

- **Status:** aceito
- **Data:** 2026-08-25
- **Decisores:** Ediney Magalhães

---

## Contexto

Durante a construção da Página 2 do Dashboard, identificou-se que `gold_bottleneck` e `gold_performance_spectrum`, mesmo após a correção que os fez cruzar fontes via `case_id_jornada`, não servem de fonte direta para um DFG (Directly-Follows Graph) visual: cada nó de um DFG precisa de posição x/y fixa, e o event log completo tem ~38 atividades clínicas distintas mais centenas de combinações de leito específico em Movimentação, volume incompatível com qualquer grafo desenhável manualmente.

Uma primeira tentativa de reduzir esse volume por **frequência** (manter só as transições mais comuns) foi rejeitada: a base atual é de um único mês de teste, e frequência neste estágio não distingue "caminho clinicamente irrelevante" de "caminho real mas ainda pouco amostrado", a mesma lição já aprendida com a especialidade Cardiologia (baixo volume, achado real) se aplicaria aqui.

Adicionalmente, a tentativa de resolver pares de transições recíprocas (ex: `Alta da Emergência → Fim da Consulta`, 5.056 casos, vs. `Fim da Consulta → Alta da Emergência`, 467 casos) escolhendo a direção de maior frequência **produziu um erro real**: a direção de maior frequência era o artefato conhecido de atraso de registro médico (já documentado como dor operacional), não o fluxo clínico verdadeiro. Isso confirmou que frequência não é critério válido para decidir direção de fluxo neste domínio.

## Decisão

### 1. Nova tabela, separada de `gold_bottleneck`/`gold_performance_spectrum`

`gold_dfg_macro` é calculada a partir do mesmo `df_formatado` (PM4Py), mas com um filtro adicional: só sobrevivem eventos cuja atividade pertence a uma **lista fechada de 15 marcos**, definida por curadoria manual (não por frequência), cobrindo os pontos de transição entre processos. A atividade de Movimentação é simplificada para o rótulo genérico (`TIPO` puro, sem código de leito) antes do filtro.

Ao remover do meio da sequência qualquer evento que não pertença aos 15 marcos, o `.shift()` conecta automaticamente os marcos entre si, pulando os passos intermediários (exames, etapas detalhadas de cirurgia), o tempo resultante é o **tempo total decorrido entre marcos**, não tempo entre passos consecutivos reais. Essa é uma métrica deliberadamente diferente da de `gold_bottleneck`, documentada como tal.

### 2. Curadoria manual da direção e da lista final de transições

Das transições possíveis entre os 15 marcos, a lista final foi definida por revisão clínica direta (usuário), não por regra estatística:

- Pares com clara predominância de volume (diferença ≥ ~5x) tiveram a direção minoritária descartada do grafo por decisão editorial de legibilidade, permanece disponível em `gold_bottleneck` para quem precisar da granularidade completa.
- Pares com volume próximo (empate estatístico) foram decididos individualmente pelo usuário, com um caso descartado por ambiguidade real (`Aviso de Cirurgia ↔ Fim da Cirurgia`).
- A direção de `Alta da Emergência ↔ Fim da Consulta Médica` foi corrigida manualmente para `Fim da Consulta → Alta da Emergência`, a direção logicamente correta, não a de maior volume (que reflete o atraso de registro já documentado).
- A estrutura final tem **duas entradas convergentes** (via Emergência, via Cirurgia eletiva) que se encontram em `Internação`, seguidas de um caminho único até `Alta Hospitalar`, incluindo uma transição (`Agendamento de Cirurgia → Aviso de Cirurgia`) que não tem sustentação estatística no mês atual (abaixo do piso de frequência ≥10) mas é mantida por ser logicamente correta; ganhará volume real com a carga histórica.

### 3. `especialidade` incluída, com aceitação de dado esparso

Diferente do filtro de Processo (que não se aplica, o grafo é definido justamente como a visão "sem processo"), o filtro de Especialidade foi mantido, seguindo a mesma regra de "dono é quem originou a transição" já usada em `gold_bottleneck`. Isso fragmenta as 15 transições em 78 combinações transição × especialidade, nem toda especialidade tem volume em toda transição, e o widget consumidor precisa tratar ausência de dado como estado válido ("sem dado suficiente para este recorte"), não como erro.

## Alternativas consideradas

**Reduzir o grafo por piso de frequência, sem curadoria manual.** Rejeitada, já demonstrou produzir erro real (escolher o artefato de atraso de registro em vez do fluxo correto) quando aplicada sem julgamento clínico.

**Grafo único cobrindo todas as ~38 atividades, sem lista fechada.** Rejeitada, inviável de desenhar manualmente (posição x/y por nó), mesmo problema que motivou a descoberta desta necessidade.

**Matriz (heatmap de/para) no lugar de grafo de nós e setas.** Avaliada e rejeitada para este caso de uso, tecnicamente preserva todos os dados sem exigir escolha de direção, mas o usuário considerou não interpretável para o público executivo (diretoria), que não decodifica matriz de transição com a mesma facilidade que um fluxograma.

## Consequências

- `gold_dfg_macro`: 78 linhas (15 transições × especialidades com volume suficiente), `ano_mes` pronto para histórico multi-mês.
- A tabela é normativa e requer manutenção manual: se o processo clínico do hospital mudar (nova etapa, novo protocolo), a lista de 15 marcos e a lista de transições aprovadas precisam ser revisadas, não se atualiza sozinha com a chegada de novo dado, diferente das demais tabelas Gold do projeto.
- `Fim da Consulta Médica` aparece no grafo sem nenhuma transição de saída própria (a leitura de "vai para Alta da Emergência" já é coberta a partir dela mesma), isso é esperado, reflexo direto da correção de direção aplicada.
- Pendência não resolvida: implementação do widget Vega-Lite no AI/BI Dashboard consumindo esta tabela, próxima etapa após este ADR.