# Process Mining

Documentação da disciplina de Process Mining aplicada ao fluxo hospitalar. A intenção é que esta pasta funcione como um mini-livro: cada capítulo explica o conceito, a decisão tomada no projeto e as armadilhas encontradas, com ligação para os ADRs, as regras de qualidade (RQ) e os dashboards.

## Capítulos

Ordem de leitura sugerida:

| Capítulo | Status | Conteúdo | Ligações |
|---|---|---|---|
| `fundamentals.md` | Escrito | Tipos, perspectivas e particularidades do dado hospitalar | ADR-0004 |
| `event-log.md` | Escrito | Estrutura do event log, padrão XES, chaves de caso | ADR-0006, ADR-0007, ADR-0018, `gold_event_log` |
| `discovery.md` | Escrito | Algoritmos de descoberta: Alpha, Heuristic, Inductive | ADR-0009 |
| `conformance.md` | Escrito | Conformance Checking: token replay, modelo de referência | ADR-0010, ADR-0019, RQ-014, `dashboard-conformidade.md` |
| `bottlenecks.md` | Escrito | Gargalos, tempos de espera e Performance Spectrum | ADR-0016, `dashboard-gargalos.md` |
| `variants.md` | Escrito | Variant Analysis e clustering de traces | `gold_variant_analysis` |
| `social-network-analysis.md` | Escrito | Organizational Mining: handover, subcontracting, escolha do ator, chave do caso | ADR-0008, ADR-0020, RQ-015, RQ-016, `dashboard-handover.md` |

## Pendências dos capítulos

Cada capítulo tem uma seção "Pendências" própria. As que dependem do histórico (cerca de 2 anos) ou de validação com a área assistencial ficam abertas até a ingestão.