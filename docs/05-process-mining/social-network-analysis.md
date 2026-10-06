# Social Network Analysis (Organizational Mining)

## O que é

Social Network Analysis, dentro de Process Mining, é o conjunto de técnicas que
analisa como diferentes atores — pessoas, papéis, setores — se relacionam dentro
da execução de um processo. Van der Aalst trata essa disciplina sob o nome mais
amplo de **Organizational Mining**: enquanto descoberta de processo (Inductive
Miner) responde "qual é o caminho do processo", Organizational Mining responde
"quem está envolvido, e como essas partes interagem entre si".

A pré-condição estrutural para qualquer análise dessa família é a existência de
um atributo de **ator** por evento — no padrão XES, `org:resource`. Sem esse
atributo, não há rede para calcular: a limitação não é de ferramenta, é de dado.

## As quatro métricas

O PM4Py implementa quatro métricas clássicas de Organizational Mining, divididas
em duas naturezas distintas.

### Métricas de interação

**Handover of Work** — mede transições sequenciais dentro do mesmo caso: se o
evento N foi executado pelo ator A e o evento N+1 pelo ator B, há um handover de
A para B. É uma relação direcionada — A entrega para B, não o contrário.

**Subcontracting** — mede o padrão A → B → A dentro do mesmo caso: o ator A
executa uma atividade, o controle passa para B, e depois **retorna** para A.
Captura "delegação com retorno" — diferente do handover simples, que não
distingue uma transferência definitiva de uma passagem temporária.

**Working Together** — mede coocorrência: dois atores presentes no mesmo caso,
independente de ordem ou sequência. Não é direcionada — A e B trabalharam juntos
nesse caso, ponto. Exige que os atores apareçam **simultaneamente** vinculados
ao mesmo caso (ex: cirurgião + anestesista no mesmo procedimento).

### Métrica de similaridade

**Similar Activities (Resource Profile Similarity)** — não mede interação
nenhuma entre atores. Constrói uma matriz ator × atividade (frequência de cada
atividade por ator) e calcula correlação entre as linhas. Responde "esses dois
atores desempenham o mesmo tipo de trabalho?" — útil para identificar atores
substituíveis ou papéis equivalentes.

## Quando usar cada uma

| Métrica | Pergunta de negócio | Pré-requisito de dado |
|---|---|---|
| Handover of Work | Quem passa o caso para quem, em que ordem | Ator com timestamp de evento, sequência clara |
| Subcontracting | Quem delega e retoma o controle do caso | Mesmo que handover, mais profundidade de trace |
| Working Together | Quem colabora no mesmo caso, simultaneamente | Múltiplos atores vinculados ao mesmo evento/caso |
| Similar Activities | Quais atores têm perfil de trabalho parecido | Variedade de atividades por ator — perfis idênticos por desenho do schema geram resultado trivial |

## Armadilhas comuns

**Escolher o ator sem verificar se ele sustenta a pergunta.** A escala de
granularidade do ator (indivíduo, especialidade, setor, processo) muda
completamente o que cada métrica revela. Um ator mal escolhido não gera erro —
gera um resultado "limpo" e sem significado, porque confirma algo que já é
verdade por construção do dado (ex: correlacionar setores que nunca produzem
volumes comparáveis entre si, ou que executam atividades estruturalmente
idênticas por desenho).

**Confundir existência de coluna com aplicabilidade da métrica.** Ter um campo
de "ator" na fonte não garante que a métrica é informativa — Working Together
exige simultaneidade real, não apenas presença do ator no caso.

**Ignorar cobertura parcial do dado.** Um campo de ator com cobertura baixa
(ex: 35%) introduz exclusão silenciosa de uma fatia relevante da rede sem
nenhum sinal de que isso está acontecendo — a rede resultante parece completa,
mas não é.

## Aplicação neste projeto

### Escolha do ator

O ator das análises é o **processo de origem do evento** (`source`, a tabela Silver de onde o evento vem) e a **especialidade**, nunca a pessoa (ADR-0008). Duas razões: LGPD, e evitar que o dashboard vire ranking de desempenho individual. Consequência: `source` é tabela de origem, e não setor físico. "Alta" e "Internação" são registros de sistemas diferentes, e não locais do hospital.

### As cinco análises

| # | Análise | Construção | Resultado |
|---|---|---|---|
| 1 | Handover setor↔setor, com especialidade como atributo | manual em Pandas | persistida (`gold_sna_handover`), alimenta a Página 4 |
| 2 | Handover especialidade↔especialidade, por setor | nativa do PM4Py | sem valor executivo, só metodológico |
| 3 | Subcontracting setor↔setor, com especialidade como atributo | manual em Pandas | persistida (`gold_sna_subcontracting`), alimenta a Página 4 |
| 4 | Subcontracting especialidade↔especialidade, por setor | nativa do PM4Py | sem valor executivo |
| 5 | Subcontracting setor↔setor puro | nativa do PM4Py | dominada por pares (A, A), sem informação |

Working Together e Similar Activities foram avaliadas e descartadas (ADR-0008).

### Por que a construção é manual nas análises 1 e 3

A função nativa agrupa por ator e descarta o atributo da transição. Para manter a especialidade na aresta, o handover é calculado com `shift(1)` e o subcontracting com `shift(1)` e `shift(2)` sobre os eventos ordenados por jornada e horário. Só entram mudanças de `source`: passagens dentro do mesmo processo ficam de fora (o Handover não mostra, por exemplo, as idas e vindas de UTI, que vivem dentro de Movimentações).

### A chave do caso muda o resultado

A primeira versão agrupava por `case_id`, e o handover não tinha a passagem Emergência → Internação, a mais importante do hospital: nenhum `case_id` continha eventos das duas fontes, enquanto 445 jornadas (`case_id_jornada`) continham. Trocar a chave levou o handover de 216 para 263 combinações, e a passagem passou a ter 370 transições (RQ-016). **Lição:** em Organizational Mining, a chave do caso define quais atores podem se encontrar. Se a chave separa o que o negócio considera um mesmo caso, a rede mostra só os atores que coexistem dentro de cada fragmento.

### Como ler o resultado

- **Handover** aqui é a sucessão de eventos por horário dentro da jornada, e não fluxo clínico direcional. "Alta → Internação" (708) corresponde a "Alta médica", "Alta Hospitalar" ou "Prescrição de alta" seguidas de "Alta da Internação", registros de alta do mesmo episódio em tabelas diferentes.
- **Subcontracting** descreve uma sequência observada por horário. O caso dominante, Exames de Imagem → Emergência → Exames de Imagem (203), pode ser exame de controle, e os dados não provam delegação nem retrabalho.
- Com sete atores, a rede cabe numa **matriz de adjacência 7×7**, e não num sociograma: com posições fixas, a distância entre nós não significa nada e o olho lê proximidade.
- A especialidade do handover é a do evento de **destino**, e a do subcontracting é a do processo **intermediário**.

### Uso nos dashboards

Página 4 (`dashboard-handover.md`): matriz de handover, heatmap de percentual da saída de cada processo, gráfico de especialidade por passagem e sequências A → B → A.

## Referências

- Van der Aalst, W. (2016). *Process Mining: Data Science in Action*, capítulo sobre Organizational Mining.
- Van der Aalst, W.; Song, M. (2004). Mining Social Networks: Uncovering Interaction Patterns in Business Processes. BPM 2004
- Documentação oficial do PM4Py — módulo `pm4py.algo.organizational_mining`.
