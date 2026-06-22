# ADR-0010: Adoção de Token Replay para Conformance Checking

## Status

**Aceito**

**Data:** 2026-06-16

**Decisores:** Ediney Magalhães (Analytics Engineer)

**Sprint:** 3

**Relacionado a:** [ADR-0009](0009-inductive-miner.md)

---

## Contexto

A Fase 3 do Sprint 3 exige medir o quanto o comportamento real registrado
no `gold_event_log` adere ao model descoberto pelo Inductive Miner
(ADR-0009). O PM4Py oferece duas famílias de algoritmo para essa medição:
token replay e alignment-based conformance checking.

Diferente do ADR-0009, a escolha aqui não nasceu de uma comparação
formal extensa entre as duas abordagens antes da implementação — token
replay foi adotado diretamente, por ser o algoritmo introduzido junto com
os conceitos fundamentais de fitness/precision no início da Fase 3. Este
ADR formaliza retroativamente a justificativa técnica da escolha e
documenta a alternativa não explorada, para que a decisão fique
rastreável mesmo sem ter passado por um comparativo prévio explícito.

## Decisão

**Adotar token replay (`pm4py.fitness_token_based_replay`,
`pm4py.precision_token_based_replay`) como método de Conformance
Checking.**

### Mecanismo

Token replay simula a execução de cada trace real sobre a Petri Net
derivada do Process Tree (ADR-0009), movendo tokens entre os lugares da
rede a cada evento. Quando um evento do trace não encontra um token
disponível no lugar esperado, o algoritmo registra uma violação (token
"faltante" ou "sobrando"). Ao final, agrega essas violações em duas
métricas: fitness (quanto do comportamento real o model explica) e
precision (quão restritivo o model é em relação aos dados reais).

### Por que token replay foi suficiente para o objetivo da Fase 3

1. **Soundness do model já garantida.** O Inductive Miner (ADR-0009)
   garante um Process Tree sem deadlocks ou livelocks. Token replay é
   especialmente sensível a inconsistências estruturais do model — sobre
   um model sound, o risco de resultado não confiável que motivaria a
   alternativa (alignment) é baixo.

2. **Custo computacional.** Token replay é significativamente mais
   barato que alignment-based checking, que precisa resolver um problema
   de otimização (menor custo de edição) para cada trace. Sobre ~7.6K
   traces, essa diferença de custo é relevante para execução repetida
   durante desenvolvimento iterativo.

3. **Suficiência para o objetivo diagnóstico do sprint.** O objetivo da
   Fase 3 é quantificar fitness/precision por fonte e identificar onde o
   processo real diverge do esperado — não localizar o ponto exato de
   desvio dentro de cada trace individual com precisão milimétrica.
   Alignment-based checking se destaca exatamente nesse segundo cenário
   (diagnóstico fino, trace a trace), que não era o requisito desta fase.

## Alternativa considerada

**Alignment-based conformance checking** — não implementado. Resolve, para
cada trace, a sequência de movimentos no model que minimiza o custo de
edição em relação ao trace real, produzindo um diagnóstico mais preciso
de onde exatamente o desvio ocorre. Teria valor se o objetivo fosse
auditoria detalhada de casos individuais ou refinamento fino do model —
não era o objetivo desta fase. Permanece como opção válida para uma
investigação futura mais granular, caso a análise por fonte (já entregue)
revele a necessidade de diagnosticar desvios trace a trace.

## Consequências

- Resultados obtidos por fonte (fitness ≥ 0.9929 em todas, precision
  entre 0.06–0.18): fitness alto indica que os Process Trees descobertos
  explicam bem o comportamento real; precision baixa é atribuída à alta
  variedade de variantes por fonte (entre 605 e 5.922 traces, múltiplos
  caminhos clínicos legítimos), não a problema de qualidade de dado —
  consistente com o que já era esperado a partir da Variant Analysis.
- Conformance checking executado por fonte (`source`), não sobre o
  `gold_event_log` misturado — mesma decisão de isolamento aplicada em
  Bottleneck Detection e na descoberta de processo (ADR-0009).
- Resultados não persistidos como tabela Gold — tratados como análise
  diagnóstica ad-hoc do notebook, recalculada a cada execução. Ver nota
  de decisão equivalente para Bottleneck Detection.
- Se uma necessidade futura de diagnóstico trace a trace surgir (ex:
  auditoria de casos específicos para apresentação à diretoria),
  alignment-based checking deve ser reavaliado como ADR específico, não
  assumido como extensão automática deste.