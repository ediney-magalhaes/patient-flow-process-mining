# Process Mining

Documentação da disciplina de Process Mining aplicada ao fluxo hospitalar. A intenção é que esta pasta funcione como um mini-livro: cada capítulo explica o conceito, a decisão tomada no projeto e as armadilhas encontradas, com ligação para os ADRs, as regras de qualidade (RQ) e os dashboards.

## Capítulos

| Capítulo | Status | Conteúdo | Ligações |
|---|---|---|---|
| `social-network-analysis.md` | Escrito | Organizational Mining: handover, subcontracting, escolha do ator, chave do caso | ADR-0008, ADR-0020, RQ-015, RQ-016, `dashboard-handover.md` |
| `fundamentals.md` | Planejado | Conceitos fundamentais e histórico | ADR-0004 |
| `event-log.md` | Planejado | Estrutura do event log e padrão XES | ADR-0006, `gold_event_log` |
| `discovery.md` | Planejado | Algoritmos de descoberta: Alpha, Heuristic, Inductive | ADR-0009 |
| `conformance.md` | Planejado | Conformance Checking: token replay, modelo de referência | ADR-0010, ADR-0019, RQ-014, `dashboard-conformidade.md` |
| `bottlenecks.md` | Planejado | Gargalos, tempos de espera e Performance Spectrum | ADR-0016, `dashboard-gargalos.md` |
| `variants.md` | Planejado | Variant Analysis e clustering de traces | `gold_variant_analysis` |

## Ordem de escrita

Os capítulos são escritos conforme o projeto tem material consolidado: `discovery`, `conformance`, `bottlenecks`, `variants`, `event-log` e `fundamentals`.