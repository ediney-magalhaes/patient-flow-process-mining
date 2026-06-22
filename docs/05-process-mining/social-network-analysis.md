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

## Referências

- Van der Aalst, W. (2016). *Process Mining: Data Science in Action*, capítulo
  sobre Organizational Mining.
- Documentação oficial do PM4Py — módulo `pm4py.algo.organizational_mining`.