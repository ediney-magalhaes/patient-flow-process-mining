# Organizational Mining — o que aprendi

## O que é

Organizational Mining é a parte do Process Mining que olha para os atores do
processo (pessoas, especialidades, setores) em vez do fluxo de atividades em
si. A pergunta deixa de ser "o que acontece" (descoberta, conformance,
bottleneck) e passa a ser "quem faz, e como essas partes se relacionam".

A teoria completa — as quatro métricas, quando usar cada uma — está em
`docs/05-process-mining/social-network-analysis.md`. Esta nota é sobre o
processo de decisão que vivi para chegar no escopo aplicado ao projeto, e os
erros que cometi (e que o Claude cometeu) no caminho.

## A armadilha da granularidade trivial

Minha primeira tentativa de aplicar Similar Activities foi com `source`
(emergência, cirurgia, internação...) como ator. Parecia razoável, mas o
resultado seria sempre trivial: cada fonte já executa, por desenho do schema,
um conjunto de atividades exclusivo e não sobreposto. Qualquer correlação ali
sairia próxima de zero sempre — não porque há uma descoberta real, mas porque
o próprio jeito que organizamos a Gold já garante isso de antemão.

A mesma armadilha apareceu de novo com `location` (setor): o exemplo inicial
de correlação entre unidades de internação não revelava nada, porque toda
unidade convencional *precisa* gerar o mesmo trio de eventos administrativos
(internar, transferir, alta) — não é uma característica que distingue um
setor do outro, é estrutural ao processo.

**Lição:** antes de rodar uma métrica de similaridade, perguntar se o ator
escolhido tem variedade real de atividades entre suas instâncias, ou se o
próprio schema já garante que o perfil vai ser parecido (ou idêntico) por
construção.

## A diferença entre "ter a coluna" e "a coluna sustentar a pergunta"

Levei um tempo para separar duas coisas que pareciam a mesma: ter um campo de
"especialidade" ou "médico" na tabela, e esse campo realmente sustentar a
métrica que eu queria calcular.

Exemplo concreto: `exames_imagem` tem seis campos de médico diferentes
(solicitante, executante, e quatro de laudo). Ter a coluna não significa que
ela está pronta para uso — duas delas (`MEDICO_LAUDO_DEFINITIVO` e
`MEDICO_LAUDO_ULTIMAMODIFICACAO`) tinham cobertura de ~35%, com um padrão
suspeito de cobertura quase idêntica entre as duas, sugerindo preenchimento
sistemicamente parcial (talvez por modalidade de exame ou janela de tempo), não
ausência aleatória. Usar esses campos teria introduzido exclusão silenciosa de
65% dos casos em qualquer rede — sem nenhum sinal visível de que isso estava
acontecendo.

**Lição:** verificar cobertura antes de usar qualquer campo como ator, e
desconfiar de cobertura parcial com padrão repetido entre colunas — geralmente
não é dado faltando aleatoriamente, é comportamento sistêmico de captura.

## Hierarquia de atores não é uma escolha única

A virada na discussão foi perceber que "setor" e "especialidade" não são
alternativas concorrentes — são dois níveis que podem se combinar de duas
formas diferentes, e cada combinação responde a uma pergunta diferente:

- **Especialidade como atributo da transição entre setores** — o ator
  continua sendo o setor, mas cada handover é enriquecido com qual
  especialidade conduzia o caso naquele momento.
- **Especialidade como ator dentro de um setor** — o setor passa a ser um
  filtro de contexto, e a rede é calculada entre especialidades que atuam
  *dentro* daquele setor especificamente.

Isso fez ressuscitar métricas que eu tinha descartado isoladamente (Handover
e Subcontracting por setor puro pareciam redundantes com colunas já existentes
em `movimentações`) — combinadas com especialidade, deixaram de ser
redundantes e passaram a responder uma pergunta nova.

## Resource ficou no schema desde o Sprint 2, mas nunca foi usado

A coluna `resource` foi pensada desde a definição do schema canônico da Gold,
exatamente prevendo esse tipo de análise — mas nenhuma das sete tabelas
`gold_events_*` chegou a popular ela de fato. Ficou nula por padrão até essa
investigação, mesmo em `cirurgias`, que é a única fonte com múltiplos atores
reais (cirurgião, anestesista, assistentes) já anonimizados via hash desde o
Sprint 0.

**Lição:** um campo "reservado para o futuro" no schema não significa que ele
está pronto para uso — é fácil esquecer de popular algo que não bloqueia
nenhum pipeline no curto prazo, até o dia em que a análise que depende dele
aparece.