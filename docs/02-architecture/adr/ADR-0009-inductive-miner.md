# ADR-0009: Adoção do Inductive Miner para Descoberta de Processo

## Status

**Aceito**

**Data:** 2026-06-16

**Decisores:** Ediney Magalhães (Analytics Engineer)

**Sprint:** 3

**Relacionado a:** [ADR-0004](0004-why-pm4py.md)

---

## Contexto

A Fase 2 do Sprint 3 exige escolher um algoritmo de descoberta de processo
para construir o model a partir do `gold_event_log`. O PM4Py oferece três
algoritmos clássicos disponíveis nativamente: Alpha Miner, Heuristic Miner
e Inductive Miner. Cada um tem estratégia e garantias distintas, e a
escolha影响 diretamente a qualidade do conformance checking que viria
depois (ADR-0009 original do roadmap — hoje formalizado como ADR-0010).

O `gold_event_log` tem volume de ~190K eventos / ~7.6K traces, com ruído
real conhecido — timestamps nulos concentrados em `exames_imagem` (ver
RQ-001), variantes raras decorrentes da variabilidade clínica genuína de
cada paciente.

## Decisão

**Adotar o Inductive Miner como algoritmo de descoberta de processo.**

### Comparativo dos três algoritmos avaliados

**Alpha Miner** — o primeiro algoritmo formal de Process Mining, proposto
por Van der Aalst em 2004. Analisa relações de ordem absolutas entre
atividades ("A sempre precede B") e constrói uma Petri Net a partir
delas. Elegante matematicamente, mas não lida bem com loops, não tolera
ruído nos dados, e falha com paralelismo complexo. Estudado
academicamente, raramente usado em produção.

**Heuristic Miner** — evolução prática do Alpha Miner. Trabalha com
frequências em vez de relações absolutas ("A precede B em 87% dos
casos"), com um threshold manual que ignora relações raras como ruído.
Mais robusto que o Alpha Miner em logs ruidosos, mas o threshold exige
calibração manual e os resultados variam conforme o valor escolhido —
introduz um parâmetro subjetivo sem garantia formal sobre o resultado.

**Inductive Miner** — proposto por Sander Leemans em 2013, é o algoritmo
recomendado pelo próprio Van der Aalst para uso geral. Funciona
recursivamente: divide o log em sublogs menores usando cortes lógicos
(sequência, escolha, paralelismo, loop) e repete o processo em cada
sublog até não conseguir mais dividir. O resultado é sempre um Process
Tree **garantidamente sound** — sem deadlocks, sem livelocks, sem
caminhos que nunca terminam.

### Razões da escolha

1. **Tolerância a ruído real.** O `gold_event_log` tem ruído documentado
   (timestamps nulos, variantes raras de baixa frequência). O parâmetro
   `noise_threshold` do Inductive Miner permite controlar essa tolerância
   de forma explícita e parametrizada, sem o ajuste manual subjetivo que
   o Heuristic Miner exigiria.

2. **Soundness necessária para Conformance Checking.** A Fase 3 do
   sprint depende de comparar o model descoberto contra o comportamento
   real via token replay (ver ADR-0010). Token replay sobre um model que
   não é sound produz resultados não confiáveis — deadlocks e livelocks
   no model geram artefatos de medição, não achados reais sobre o
   processo. A garantia de soundness do Inductive Miner é pré-condição
   para um Conformance Checking válido.

3. **Volume de dados confortável para o algoritmo.** ~190K eventos é um
   volume tratável pelo Inductive Miner em tempo de execução aceitável,
   sem necessidade de otimização adicional.

## Alternativas consideradas

**Alpha Miner** — descartado. Sem tolerância a ruído, o model resultante
sobre dados hospitalares reais (com timestamps nulos e variantes raras)
provavelmente seria desconectado ou non-sound, invalidando qualquer
conformance checking posterior.

**Heuristic Miner** — descartado. Resolveria parcialmente o problema de
ruído, mas não oferece garantia de soundness, e introduz um parâmetro de
calibração manual (threshold de frequência) sem justificativa clínica
clara para qualquer valor escolhido.

## Consequências

- O parâmetro `noise_threshold` do Inductive Miner fica disponível para
  ajuste fino futuro — a primeira execução usa o default (`0.0`, sem
  simplificação) para visualizar o model completo antes de qualquer
  decisão de simplificação.
- A descoberta de processo é feita **por fonte** (`source`), não sobre o
  `gold_event_log` misturado — decisão tomada durante a implementação do
  Bottleneck Detection e reaplicada aqui pelo mesmo motivo: misturar
  processos clinicamente distintos (emergência, cirurgia, internação...)
  no mesmo model produz uma Petri Net excessivamente permissiva, com
  precision baixa não por problema de qualidade de dado, mas por mistura
  indevida de processos.
- Toda análise subsequente de Process Mining no projeto (Variant
  Analysis, Bottleneck Detection, Conformance Checking) herda essa
  decisão — o Process Tree do Inductive Miner é o model de referência.