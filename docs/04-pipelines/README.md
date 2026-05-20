# Pipelines

Documentação dos pipelines de ingestão, transformação e orquestração.

## Pipelines implementados

- **`01_bronze_ingestion`** — Ingestão de 6 bases hospitalares via Auto Loader 
  para tabelas Delta na camada Bronze. Notebook no repositório raiz.

## Documentos planejados

- `ingestion.md` — Estratégia de ingestão (método, frequência, formato)
- `bronze-to-silver.md` — Transformações Bronze → Silver
- `silver-to-gold.md` — Transformações Silver → Gold
- `orchestration.md` — Orquestração e agendamento