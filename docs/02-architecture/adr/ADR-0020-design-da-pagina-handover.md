# ADR-0020: Design da Página 4 do Dashboard (Handover) — duas camadas, portas de entrada e cálculo no SQL

- **Status:** aceito
- **Data:** 2026-10-02
- **Decisores:** Ediney Magalhães

---

## Contexto

A Página 4 foi planejada como "Handover / SNA": sociograma setor↔setor e ranking de subcontracting. Ao construí-la, três fatos mudaram o desenho.

1. O `gold_sna_handover` não continha a passagem Emergência → Internação, porque o handover era calculado por `case_id` e não por `case_id_jornada` (RQ-016).
2. O AI/BI não tem visual nativo de grafo, e a rede tem só 7 nós (`source`, que é tabela de origem do evento e não setor físico). Um sociograma com posições fixas sugeriria proximidade que não existe.
3. A diretoria precisa saber o caminho esperado do paciente e onde ele sai dele, e o handover (volume entre processos) não responde isso sozinho. As idas e vindas de UTI vivem dentro de Movimentações, e o handover descarta por construção as passagens dentro do mesmo `source`.

## Decisão

### Duas camadas na mesma página

- **Jornada por porta de entrada:** desenho Custom Viz (Vega-Lite) com fluxo principal, desvios e apoio diagnóstico, alimentado por `gold_patient_journey`, `gold_event_log` e `silver_movimentacoes`.
- **Handover entre processos:** matriz de handover, heatmap de percentual da saída de cada processo, sequências A → B → A e gráfico de especialidade de destino por passagem, alimentados por `gold_sna_handover` e `gold_sna_subcontracting`.

As duas camadas respondem a perguntas diferentes, com fontes e bases diferentes. Elas ficam juntas porque uma dá referência à outra: o desenho mostra o que é normal, e a matriz mostra entre quais processos o trabalho passa. Cada camada tem banner próprio, e cada filtro fica perto do que controla.

### Portas de entrada, e não tipos de jornada

O desenho é filtrado por três portas: **Emergência** (`atendimento_emergencia`, `internacao_clinica`, `internacao_cirurgica_emergencia`), **Cirurgia Eletiva** (`internacao_cirurgica_eletiva`) e **Internação Clínica** (`internacao_clinica_direta`). Filtrar por `journey_type` deixaria o fluxo degenerado, porque o tipo já define se houve cirurgia. A antiga "Direta" foi dividida em duas portas porque misturava duas populações: 86% passavam por cirurgia e 14% não.

A cirurgia é **desvio** na Emergência (37,6% dos internados) e **fluxo principal** na Cirurgia Eletiva (caminho esperado).

### UTI em ramos cronológicos

A UTI é dividida por momento em relação à cirurgia (antes, após, sem cirurgia), porque um único ramo sugeriria uma ordem que os dados não sustentam: na Cirurgia Eletiva, 69% das entradas são pós-operatórias. A reentrada na UTI aparece só nas jornadas sem cirurgia. Nas jornadas cirúrgicas, a volta após a operação é a UTI pós-operatória esperada, e não é possível separá-la de um retorno real com os dados atuais (ver RQ-017). Fica como pendência para a ingestão do histórico.

### Cálculo no SQL, JSON só mapeia campos

No Custom Viz, `transform` com `calculate` ou `filter` dentro do JSON fez o desenho aparecer em branco, sem mensagem de erro. Tipo da seta, posição do rótulo e texto do rótulo são calculados no SQL do dataset `espinha_arestas`. Mudar uma posição ou uma regra é mudar o SQL, e não o JSON.

### Matriz de adjacência no lugar do sociograma

A matriz 7×7 mostra a rede inteira sem sobreposição. O grafo interativo fica reservado para o Databricks App (Fase 3 do Sprint 4), onde há Python livre e bibliotecas de grafo.

### Filtros

| Filtro | Controla | Não controla, e por quê |
|---|---|---|
| Período | todos os widgets de dado | — |
| Porta de entrada | desenho | os de handover, que não têm porta |
| Especialidade (do processo de destino) | matriz e heatmap de percentual | sequências (a especialidade do subcontracting é a do intermediário, e o mesmo rótulo significaria duas coisas) e gráfico de especialidades (a especialidade é o eixo) |
| Passagem | gráfico de especialidades | os demais |

### Textos curtos nos widgets

A Description de cada widget só existe quando evita uma leitura errada (por exemplo, ler "Alta → Internação" como erro, ou comparar linhas de bases diferentes). O detalhe fica em `dashboard-handover.md`.

## Alternativas consideradas

**Sociograma em Custom Viz com nós em círculo.** Rejeitada: com posições fixas, a distância entre nós não tem significado e o olho lê proximidade. Custo alto para pouca informação.

**Desenho em gráfico de barras por etapa (funil).** Rejeitada: é um funil de contagens, e não um desenho de caminho. A base de cada barra mistura jornadas da porta e internados, e o desvio não aparece como ramo.

**Uma única espinha, sem filtro de porta.** Rejeitada: mentiria para a cirurgia eletiva e para a internação direta, que não passam pela emergência.

**Gráfico de funil para a especialidade de destino.** Rejeitada: as especialidades são categorias paralelas. Funil sugere perda entre etapas que não existe. Barras horizontais ordenadas têm a mesma silhueta sem a leitura errada.

**Duas páginas (jornada e handover).** Rejeitada por ora: a página fica com seis widgets de dado e cabe numa tela com banners. Reavaliar se a validação com a diretoria mostrar a página carregada.

**Manter os gráficos de barras por tipo de jornada (UTI, reentrada, apoio diagnóstico) e o ranking de handover.** Rejeitada: repetiam o desenho e a matriz, com bases diferentes (36,2% contra 39,6% no apoio, 8,2% contra a omissão proposital da reentrada cirúrgica), e dois números para a mesma coisa confundem.

## Consequências

- A página responde "que caminho o paciente fez", "para onde vai a saída de cada processo" e "para qual especialidade vai uma passagem", e não só "quanto passa entre processos".
- **Dívida técnica:** a regra de UTI ("entrada vinda de fora da UTI" e os prefixos de unidade) existe em dois lugares, `gold_transformation.py` (`qtd_passagens_uti`) e a CTE `ent` de `espinha_arestas`. Se uma mudar sem a outra, os números divergem sem aviso. Avaliar levar a contagem antes/depois da cirurgia para o `gold_patient_journey`.
- **Percentuais com bases diferentes:** Emergência → Internação é 7,2% no desenho (base: jornadas da porta) e 10,5% no heatmap de percentual (base: transições que saem da Emergência, dominadas por exames). As Descriptions avisam.
- **Laboratório "sem dado"** nas portas sem emergência é a ausência estrutural da base (RQ-018), e o desenho muda sozinho quando a base passar a cobrir internados.
- **Nomes de especialidade brutos:** a Página 4 não aplica `vw_dim_especialidade`, então `MEDICO PEDIATRA` e `PEDIATRIA` aparecem separados. Correção pendente (ver RQ-018).
- **Validação clínica pendente:** Internação Clínica como porta (caso raro, RQ-010), UTI antes da cirurgia eletiva (27% dos pacientes de UTI) e UTI "durante" a cirurgia (6 pacientes).
- Mudar posições ou regras do desenho exige mexer no SQL de `espinha_arestas` e conferir as três portas, porque as posições são fixas e compartilhadas.