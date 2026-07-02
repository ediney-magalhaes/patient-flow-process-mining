# ADR-0008: Escopo de Social Network Analysis e Extensão do Schema Canônico

- **Status:** aceito
- **Data:** 2026-06-24
- **Decisores:** Ediney Magalhães

---

## Contexto

O Sprint 3 definiu Social Network Analysis (Organizational Mining) como entrega
obrigatória da Fase 3. O schema canônico da Gold (ADR implícito do Sprint 2)
já reservava a coluna `resource` para esse propósito, mas ela nunca foi
populada em nenhuma das sete tabelas `gold_events_*` — ficou como
placeholder nulo desde a implementação original.

A família de métricas de Organizational Mining do PM4Py contém quatro
métricas distintas: Handover of Work, Subcontracting, Working Together e
Similar Activities (Resource Profile Similarity). Cada uma responde a uma
pergunta de negócio diferente e exige um tipo de relação diferente entre
atores (sequencial, de retorno, de coocorrência, ou de similaridade de
perfil).

Investigação das Silver confirmou que campos de médico (já com hash SHA-256
aplicado, decisão de anonimização do Sprint 0) e de especialidade existem
nativamente em `silver_atendimento_emergencia`, `silver_altas`,
`silver_internacoes`, `silver_exames_imagem` e `silver_cirurgias` — porém
com nomes de coluna inconsistentes entre fontes, e com granularidade
heterogênea: algumas fontes têm um único par médico/especialidade por
linha, outras têm múltiplos pares (ex: `altas` tem prescritor e médico de
alta; `cirurgias` tem cirurgião e dois assistentes; `exames_imagem` tem
solicitante e múltiplos médicos de laudo com cobertura variável).

## Decisão

**Métricas implementadas**, com `source` (setor/processo) e `especialidade`
como atores — não o indivíduo:

| # | Métrica | Ator | Nível |
|---|---|---|---|
| 1 | Handover of Work | Setor → Setor | Especialidade como atributo da transição |
| 2 | Handover of Work | Especialidade → Especialidade | Segmentado dentro de cada setor |
| 3 | Subcontracting | Setor → Setor | Especialidade como atributo da transição |
| 4 | Subcontracting | Especialidade → Especialidade | Segmentado dentro de cada setor |
| 5 | Subcontracting | Setor → Setor | Nível único, sem especialidade |

**Métricas descartadas:** Working Together (pressupõe coocorrência
simultânea de atores no mesmo caso, inexistente entre setores distintos —
um paciente ocupa uma unidade física por vez) e Similar Activities entre
setores ou entre especialidades nas granularidades disponíveis (perfis de
atividade tendem a ser triviais ou redundantes com o desenho do próprio
schema, sem variedade suficiente para gerar correlação informativa).
Documentados como conceitos estudados em `docs/08-learning/`.

**Extensão do schema canônico** — duas novas colunas, ambas string e
nullable, populadas inline em cada `gold_events_*` (consistente com
ADR-0007 — normalização inline na Gold, sem alterar a Silver):

`especialidade`:

| Fonte | Coluna de origem | Cobertura nos eventos |
|---|---|---|
| `atendimento_emergencia` | `ESPECIALIDADE` | todos os 8 eventos |
| `internacoes` | `ESPECIALID_ATEND` | todos os eventos |
| `altas` | `DS_ESPECIALID` | todos os 3 eventos |
| `exames_imagem` | `ESPECIALIDADE_MEDICO` | todos os 10 eventos |
| `cirurgias` | `ESPECIALIDADE` (cirurgião principal) | todos os 12 eventos |

`resource` (hash do médico, reativando coluna do schema original):

| Fonte | Coluna de origem | Cobertura nos eventos |
|---|---|---|
| `atendimento_emergencia` | `PRESTADOR` | todos os 8 eventos |
| `internacoes` | `PRESTADOR` | todos os eventos |
| `altas` | `PREST_ALTA` | somente `Prescrição de Alta` |
| `exames_imagem` | `MEDICO_SOLICITANTE` | somente `Prescrição do Exame de Imagem` |
| `cirurgias` | `ANESTESISTA_01` / `CIRURGIAO_01` | somente eventos de anestesia / cirurgia, respectivamente |

## Alternativas consideradas

**Propagação de especialidade via join com tabela de referência
médico→especialidade.** Descartada — investigação confirmou que todas as
fontes relevantes já têm a coluna nativamente, eliminando a necessidade de
join externo.

**Valor único de médico/especialidade por linha, aplicado uniformemente a
todos os eventos daquela linha, em `cirurgias` e `exames_imagem`.**
Descartada para `cirurgias` — o procedimento tem atores fisicamente
distintos (cirurgião, anestesista, assistentes) e um mapeamento
evento-a-evento preserva a granularidade necessária para handover
individual futuro. Aceita parcialmente para `exames_imagem`, onde a
maioria dos eventos não tem ator individual claro na Silver.

**Mapeamento de `MEDICO_LAUDO_DEFINITIVO` e
`MEDICO_LAUDO_ULTIMAMODIFICACAO` em `exames_imagem`.** Descartada — cobertura
de 34,6% e 36,2%, respectivamente, com padrão sugerindo preenchimento
sistemicamente parcial (possivelmente por modalidade de exame ou janela de
tempo), não ausência aleatória. Popular `resource` com esses campos
introduziria exclusão silenciosa de ~65% dos casos em qualquer análise de
rede que dependa deles.

**Handover of Work puro por setor, sem especialidade.** Descartada —
redundante com as colunas `ORIGEM`/`DESTINO` já existentes em
`silver_movimentacoes`, sem valor analítico incremental.

**Working Together e Similar Activities como análises obrigatórias.**
Descartadas pelos motivos detalhados na seção de Decisão.

**Correção pós-implementação (24/06):** a coluna `ESPECIALIDADE` em
`exames_imagem` não representa a especialidade do médico solicitante —
é outro campo, semanticamente diferente. Identificado durante a
implementação de SNA (Handover especialidade↔especialidade), quando o
PM4Py quebrou ao comparar valores nulos/inconsistentes. Corrigido para
`ESPECIALIDADE_MEDICO`, que tem cobertura real de 96%.

## Consequências

- `especialidade` e `resource` passam a ser colunas obrigatórias de
  inspecionar no schema canônico, ainda que nullable — toda nova fonte
  futura precisa decidir explicitamente seu mapeamento, não herdar null
  por omissão.
- Assimetria intencional em `altas` e `exames_imagem`: `especialidade`
  cobre todos os eventos da fonte, `resource` cobre apenas um evento
  específico — por limitação real da Silver, não inconsistência de
  implementação. Documentado para evitar interpretação equivocada por
  quem consumir a tabela depois.
- Com `resource` populado via hash estável, análises de handover e
  subcontracting no nível de indivíduo (não apenas setor/especialidade)
  ficam disponíveis para uso futuro, caso a diretoria solicite esse
  aprofundamento, sem necessidade de reprocessamento desde a origem.
- A limitação de cobertura em `MEDICO_LAUDO_DEFINITIVO` e
  `MEDICO_LAUDO_ULTIMAMODIFICACAO` é registrada como item de melhoria de
  captura na origem, não como pendência deste sprint.
- O nome de coluna de especialidade permanece divergente em cada Silver
  (`ESPECIALIDADE`, `DS_ESPECIALID`, `ESPECIALID_ATEND`) — a padronização
  ocorre apenas na tradução para o schema canônico da Gold, sem alterar a
  Silver, mantendo um único ponto de normalização no projeto.