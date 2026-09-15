# Idempotência com MERGE INTO — o que aprendi

## O que é

Um pipeline é idempotente quando executá-lo duas vezes produz o mesmo
resultado que executá-lo uma vez, reprocessar não duplica nem corrompe o
que já existe. Em Delta Lake, `MERGE INTO` é o mecanismo padrão para isso:
em vez de decidir de antemão "isso é um insert ou um update" (que é o que
`append` força você a assumir), você declara uma chave de correspondência e
deixa o motor decidir por linha, `WHEN MATCHED THEN UPDATE`, `WHEN NOT
MATCHED THEN INSERT`. dbt já faz exatamente isso por baixo dos panos quando
você configura um modelo incremental com `strategy='merge'`, a diferença
aqui foi escrever o `MERGE` direto, sem o dbt como intermediário.

## `append` funciona até alguém rodar a célula fora de ordem

A célula que persistia a linha de exceção "Alta da Emergência → Fim" em
`gold_dfg_macro` usava `.mode("append")`, e funcionava, mas só porque
dependia de uma convenção implícita, nunca escrita em lugar nenhum: rodar
sempre depois da célula de `overwrite` das outras 14 transições, que
reconstrói a tabela inteira e "limpa o terreno" antes do append acontecer.
Não havia nada no código que garantisse essa ordem. Reexecutar só a célula
do append, cenário comum ao depurar um notebook, sem rodar tudo de novo do
zero, duplicaria a linha por `ano_mes`, sem lançar nenhum erro visível.

**Lição:** `append` sem chave de deduplicação não é "mais simples que
`MERGE`", é uma aposta na ordem de execução. Em notebook, onde reexecutar
uma célula isolada é o modo normal de trabalhar (não uma exceção), essa
aposta quebra com frequência maior do que em um pipeline batch que sempre
roda do início ao fim.

## Idempotência não se declara, se testa

Corrigir o código para `MERGE INTO` não foi o suficiente para considerar o
problema resolvido, a correção só virou fato confirmado depois de rodar a
célula duas vezes seguidas e comparar a contagem por `ano_mes` antes e
depois. Documentar "corrigido para MERGE" sem esse teste seria a mesma
falha de documentar um risco sem resolvê-lo: parece fechado, mas ninguém
verificou de fato.

**Lição:** o teste de idempotência é sempre o mesmo, independente do
pipeline, rodar a operação duas vezes seguidas, sem tocar em mais nada
entre uma execução e outra, e conferir se o resultado é idêntico. Se a
contagem mudar na segunda rodada, a chave de `MERGE` está errada ou
incompleta.

## O schema de origem precisa bater com o schema de destino, não só a operação de escrita

Corrigir `append` para `MERGE` resolveu a idempotência, mas expôs um
segundo problema que estava escondido atrás do primeiro: o `SELECT` que
gerava a linha de exceção produzia 5 colunas, enquanto a tabela de destino
(alimentada pela `overwrite` das outras 14 transições) tem 7,
`especialidade` e `tempo_mediano_min` estavam faltando. Provavelmente
estava sendo preenchido como `NULL` por coerção implícita, sem ninguém ter
decidido isso conscientemente.

**Lição:** ao adicionar uma linha de exceção a uma tabela já existente,
conferir o schema de destino explicitamente antes de escrever a query de
origem, o tipo de escrita (`append`, `overwrite`, `MERGE`) e a
compatibilidade de schema são dois problemas independentes, e corrigir um
não garante ter visto o outro.