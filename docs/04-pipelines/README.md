# Pipelines

Documentação dos pipelines de ingestão, transformação e orquestração.

## Pipelines implementados

- **`01_bronze_ingestion`** — Ingestão de 8 bases hospitalares via Auto Loader 
  para tabelas Delta na camada Bronze. Notebook no Workspace do Databricks.
- **`silver_transformations`** — Pipeline Lakeflow Declarative Pipelines para 
  transformações Bronze → Silver. Materializa 8 tabelas tipadas, limpas e 
  deduplicadas no schema `silver_fluxo`. Código versionado no Git folder 
  (`my_transformation.py`) a partir de 08/06/2026. Tabelas implementadas:
  - `silver_altas` (895 registros)
  - `silver_atendimento_emergencia` (6.236 registros, 4 flags temporais)
  - `silver_cirurgias` (1.600 registros, 5 flags temporais)
  - `silver_epidemio` (821 registros, enriquecimento clínico)
  - `silver_exames_imagem` (5.308 registros, 4 flags temporais)
  - `silver_exames_laboratoriais` (20K registros, 2 flags temporais)
  - `silver_internacoes` (867 registros, 1 flag temporal)
  - `silver_movimentacoes` (3.6K registros, event log de leitos)
- **`gold_transformations`** — Pipeline Lakeflow Declarative Pipelines para
  transformações Silver → Gold. Materializa tabelas de eventos normalizados
  no schema canônico XES e o event log unificado no schema `gold_fluxo`.
  Código versionado no Git folder (`gold_transformation.py`) a partir de
  11/06/2026. Tabelas implementadas:
  - `gold_events_movimentacoes` (3.6K registros)
  - `gold_events_internacoes` (1.7K registros)
  - `gold_events_altas` (2.7K registros)
  - `gold_events_cirurgias` (19K registros)
  - `gold_events_emergencia` — pendente
  - `gold_events_exames_imagem` — pendente
  - `gold_events_exames_laboratoriais` — pendente
  - `gold_event_log` — pendente
  - `gold_case_attributes` — pendente

## Scripts de pré-processamento local

- **`preprocess_exames_lab.py`** — Limpeza de paginação e normalização de 
  timestamps para base de exames laboratoriais
- **`preprocess_movimentacoes.py`** — Limpeza de estrutura de relatório agrupado, 
  normalização de layouts deslocados e propagação de unidade/data para base 
  de movimentações

## Documentos planejados

- `ingestion.md` — Estratégia de ingestão (método, frequência, formato)
- `bronze-to-silver.md` — Transformações Bronze → Silver
- `silver-to-gold.md` — Transformações Silver → Gold
- `orchestration.md` — Orquestração e agendamento