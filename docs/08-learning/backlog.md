# Backlog de Notas de Aprendizado

Lista de conceitos candidatos a uma nota dedicada em `docs/08-learning/`,
registrados no momento em que aparecem, para não depender de memória ou de
histórico de conversas.

## Pendentes

- [ ] Convenção de nomes da API de Organizational Mining do PM4Py (sufixo
  `_network`, ex: `discover_subcontracting_network`) e estrutura do objeto
  `SNA` (`.connections`, `.is_directed`) — 2026-06-24
- [ ] Filtro por evento (`attributes_filter.apply_events`) vs. filtro por
  caso (`attributes_filter.apply`) no PM4Py — 2026-06-24
- [ ] Imutabilidade do checkpoint do Auto Loader — trocar o arquivo na
  origem não é suficiente para reprocessamento; é necessário resetar
  checkpoint e tabela de destino — 2026-06-24
- [ ] `python -m` (execução como módulo) vs. execução direta de script —
  resolução de `sys.path` e por que imports absolutos (`from src...`)
  exigem o primeiro — 2026-06-24

## Nota sobre lacuna histórica

Em 22/06/2026, um levantamento retroativo identificou 10 conceitos
candidatos a nota de aprendizado, cobrindo os Sprints 0 a 2 (ex: Liquid
Clustering, Lakeflow vs. dbt, normalização inline). Essa lista nunca foi
registrada em arquivo — existiu apenas na conversa daquela sessão — e não
foi possível recuperá-la integralmente depois. Os 10 itens originais estão
perdidos como lista; será necessário refazer esse levantamento em sessão
dedicada, revisitando os Sprints 0–2, em vez de tentar reconstruir de
memória.