# ADR-0007: Normalização Inline na Gold vs Camada Intermediária Física

- **Status:** aceito
- **Data:** 2026-06-12
- **Decisores:** Ediney Magalhães

---

## Contexto

As tabelas Silver têm estruturas heterogêneas — algumas têm uma linha por
atendimento com múltiplos timestamps em colunas (`silver_atendimento_emergencia`,
`silver_cirurgias`), outras já têm uma linha por evento (`silver_movimentacoes`).
Para construir o event log canônico, todas precisam ser normalizadas para o
formato `case_id / activity / timestamp`. A questão é onde fazer essa
normalização: em uma camada intermediária física ou inline na Gold.

## Decisão

Normalização inline na Gold — cada função `gold_events_*` faz a transformação
diretamente da Silver para o schema canônico sem persistir tabelas intermediárias.

## Alternativas consideradas

**Camada intermediária física** — criar tabelas Silver refinadas já no formato
canônico, e a Gold fazer apenas o UNION ALL. Vantagem: isolamento por fonte,
mais fácil de depurar cada fonte individualmente. Desvantagem: tabelas
intermediárias sem valor analítico direto, maior complexidade operacional,
custo de armazenamento adicional.

**Normalização inline na Gold** — cada tabela `gold_events_*` encapsula a
transformação da sua fonte. Vantagem: arquitetura mais simples, cada tabela
Gold é testável e inspecionável individualmente, sem camadas desnecessárias.
Desvantagem: se um evento específico estiver errado, é preciso inspecionar
a tabela `gold_events_*` correspondente em vez de uma tabela intermediária
dedicada.

## Consequências

- Cada tabela `gold_events_*` é a unidade de isolamento e depuração — erros
  em eventos de uma fonte são investigados diretamente nela
- O padrão de loop sobre lista de tuplas `(coluna_timestamp, nome_atividade)`
  foi adotado para fontes com múltiplos eventos, tornando o código extensível
  para novas fontes sem alteração estrutural
- Se o volume de dados crescer significativamente, a decisão pode ser revisada
  para introduzir materialização intermediária — registrar como débito técnico