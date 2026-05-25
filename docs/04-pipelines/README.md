# Pipelines

Documentação dos pipelines de ingestão, transformação e orquestração.

## Pipelines implementados

- **`01_bronze_ingestion`** — Ingestão de 8 bases hospitalares via Auto Loader 
  para tabelas Delta na camada Bronze. Notebook no Workspace do Databricks.
- **`silver_transformations`** — Pipeline Lakeflow Declarative Pipelines para 
  transformações Bronze → Silver. Materializa tabelas tipadas, limpas e 
  deduplicadas no schema `silver_fluxo`. Pipeline no Workspace do Databricks.

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