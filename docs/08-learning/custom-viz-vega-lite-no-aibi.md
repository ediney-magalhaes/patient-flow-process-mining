# Custom Viz (Vega-Lite) no AI/BI Dashboard — o que aprendi

## O que é

O AI/BI Dashboard do Databricks não tem visual nativo de grafo ou de fluxo. Para desenhar um, existe o **Custom Viz**: um widget que recebe um dataset e uma especificação **Vega-Lite** (JSON) e desenha o que a especificação descrever. Foi assim que o DFG da Página 2 e o desenho da jornada da Página 4 foram feitos.

Vega-Lite descreve o gráfico em camadas (`layer`). Cada camada tem uma marca (`rule` para linha, `circle` para nó, `text` para texto) e um `encoding`, que liga campos do dataset a posição, cor e espessura.

## Como o desenho é montado

Cada linha do dataset é uma **seta**, com posição fixa: `x_de`, `y_de`, `x_para`, `y_para`. Não há algoritmo de layout. As posições são escolhidas à mão, no SQL, o que funciona porque o número de nós é pequeno e a ordem tem sentido (da esquerda para a direita, o tempo corre).

As camadas, de baixo para cima: linhas das setas, rótulo de cada seta, círculos dos nós de origem e de destino, nome dos nós.

**Lição:** com poucos nós e uma ordem natural, posição fixa no SQL é mais simples e legível que um grafo calculado. Com uma rede sem ordem natural, a mesma abordagem sugere proximidade que não existe.

## Os campos precisam ser declarados no widget

O widget só enxerga os campos que foram adicionados em **Fields**, um por vez. Campo no dataset e fora de Fields não chega ao Vega-Lite, e o painel avisa "Unused fields" para o que foi declarado e não é usado.

**Lição:** ao acrescentar uma coluna ao SQL, lembrar de declará-la no widget.

## Cálculo no SQL, JSON só mapeia campos

O desenho apareceu **em branco, sem mensagem de erro**, quando o JSON usava `transform` com `calculate`. Isolando passo a passo, a versão mínima (só linhas) funcionava, a cor por um campo existente funcionava, e a cor por um campo calculado no `transform` quebrava, no topo do JSON e também dentro da camada. A expressão usava `indexOf` e `||`. Não descobri qual detalhe exato quebra, só que o `calculate` com essa expressão não funcionou aqui.

A solução foi mover todo cálculo para o SQL do dataset: o tipo da seta, a posição do rótulo e o texto do rótulo. O JSON só liga campos a propriedades visuais.

**Lição:** quando um Custom Viz fica em branco sem erro, reduzir ao mínimo e somar uma parte por vez. E manter a lógica no SQL, que é testável com uma tabela de resultado, e não dentro do JSON, que não mostra erro.

## Texto legível sobre linhas: duas camadas

Rótulo sobre uma linha grossa fica ilegível. A solução é duplicar a camada de texto: uma por baixo, com `stroke` branco grosso, e outra por cima, com a cor final. O contorno branco apaga a linha atrás do texto.

**Lição:** o contorno é um efeito de duas camadas, e não uma propriedade única da marca de texto.

## Espessura proporcional: escala de raiz quadrada

Espessura proporcional ao percentual com escala linear deixou a passagem mais importante, com 7,2%, como a linha mais fina do desenho. A escala `sqrt` suaviza a diferença e mantém os valores pequenos visíveis.

**Lição:** o que a escala esconde também é decisão. Escolher a escala pelo que precisa continuar visível.

## O JSON não redimensiona o widget

`width` e `height` do JSON definem o tamanho do desenho dentro do widget. O container do Canvas continua com o tamanho que foi desenhado, e é preciso arrastar a borda dele à mão. Um `width` maior (de 700 para 1000) afastou nomes de nós que se encostavam.

**Lição:** ajustar o desenho e o container em separado, e conferir nas três portas, porque as posições são compartilhadas.

## Posição do rótulo no SQL

Rótulo no meio da seta cai em cima do nome do nó. No SQL, rótulos de setas que descem da linha central ficam a 65% do caminho, e os de setas curtas que descem de uma linha secundária ficam deslocados à direita.

**Lição:** quando muitos rótulos disputam o mesmo espaço, afastar cada um do nó de origem, e não do centro da seta.

## Filtros e Custom Viz

O filtro precisa estar ligado em **Parameters** ao dataset do widget, como nos outros gráficos. No Custom Viz, a seção **Parameters** do próprio widget aparece vazia e não precisa ser preenchida.

**Lição:** se o Custom Viz não reage ao filtro, olhar o vínculo no filtro, e não no widget.

## Quando usar

| Situação | Custom Viz | Alternativa |
|---|---|---|
| Fluxo com poucos nós e ordem natural | sim | — |
| Rede densa ou sem ordem | não | matriz de adjacência (heatmap), ou grafo no Databricks App |
| Interatividade (arrastar, destacar vizinhos) | não | Databricks App |

## Referências

- Documentação do Vega-Lite (`layer`, `rule`, `circle`, `text`, `scale`).
- ADR-0016 (DFG da Página 2), ADR-0020 (desenho da Página 4), `dashboard-gargalos.md`, `dashboard-handover.md`.