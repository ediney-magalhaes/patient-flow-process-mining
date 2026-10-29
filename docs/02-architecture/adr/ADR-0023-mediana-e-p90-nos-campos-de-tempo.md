# ADR-0023: Mediana e P90 como padrão dos campos de tempo do dashboard

- **Status:** aceito
- **Data:** 2026-10-26
- **Decisores:** Ediney Magalhães
- **Relacionado a:** ADR-0016, ADR-0021, ADR-0022

---

## Contexto

Ao validar a Página 1, os cartões de tempo apareceram sem medida de dispersão, contra a regra do projeto de que toda média vem acompanhada de CV% ou P90. Ao medir a dispersão, a média mostrou-se um mau valor principal para tempo.

Medição em março/2026, atendimentos do PA (único mês ingerido):

| Medida | Casos | Média | Mediana | P90 |
|---|---|---|---|---|
| Tempo da internação ao primeiro leito real | 412 | 5,97 h | 3,95 h | 13,37 h |
| Tempo da jornada (chegada até a alta) | 5.511 | 10,27 h | 3,33 h | 9,2 h |

Na jornada, a média fica acima do P90: poucos casos muito longos a puxam, e o atendimento típico dura 3,3 h. Dos 6.236 atendimentos do mês, 5.511 têm duração.

O dashboard também tinha convenções diferentes para a mesma natureza de campo: média sem dispersão (Página 1), média com P90 nos cartões, ranking e DFG e mediana no heatmap (Página 2), mediana com P90 na tabela dos caminhos mais comuns (Página 5).

## Decisão

1. **Todo campo de tempo do dashboard mostra a mediana como valor principal e o P90 como dispersão.** O P90 substitui o CV%, que descreve a dispersão da média.
2. **A mediana é calculada sobre as linhas de jornada, no grão do filtro escolhido**, e nunca sobre valores já agregados (mesma regra do ADR-0021, item 1: mediana de medianas é um número errado).
3. **Os rótulos deixam de dizer "médio"** nos campos que passam a mostrar mediana.
4. **A aplicação segue a validação de cada página.** A Página 1 é aplicada na validação de 26/10/2026. A Página 5 já segue o padrão. As Páginas 2, 3 e 4 são ajustadas quando forem validadas.

## Alternativas consideradas

- **Média + P90 (padrão que a Página 2 já usava).** Rejeitada: com a média acima do P90, o número principal não representa o caso típico.
- **Média + CV%.** Rejeitada: o CV% resume a dispersão de uma distribuição simétrica, e a distribuição de tempo aqui tem cauda longa.
- **Mediana + intervalo interquartil.** Rejeitada: o P90 já é usado nas Páginas 2 e 5, e mantê-lo evita uma terceira medida de dispersão.

## Consequências

- Os valores validados da Página 1 mudam: tempo até o leito vai de 5,97 h para 3,95 h e tempo da jornada de 10,27 h para 3,33 h (março/2026).
- Cartões e gráficos de tendência com mais de um mês precisam calcular a mediana sobre as linhas de jornada. Os datasets pré-agregados por mês (`kpis_jornada_emergencia` e os dois `*_por_tipo`) trocam `avg` por `percentile` e deixam de ser somados entre linhas.
- **Páginas 2, 3 e 4.** Gatilho: validação da página. Ação: trocar média por mediana nos campos de tempo e incluir o P90 onde faltar. Na Página 2 isso alcança os três cartões macro, o ranking de gargalos e as arestas do DFG.