# Dicionário de Dados

Este documento descreve as tabelas do projeto por camada do Medallion.
Atualizado conforme novas tabelas são criadas.

---

## Camada Bronze

Dados brutos ingeridos via Auto Loader, preservados como vieram da origem.
Todas as tabelas incluem as colunas de metadados `_ingestion_timestamp`, 
`_source_file` e `_rescued_data`.

### bronze_altas_raw

- **Schema:** `hospital_santa_rosa.bronze_fluxo`
- **Granularidade:** 1 linha por alta hospitalar
- **Origem:** `altas_anonimizado.csv` (exportação mensal do HIS)
- **Volume referência:** 908 registros (mar/2026)
- **Column Mapping:** habilitado

### bronze_atendimento_emergencia_raw

- **Schema:** `hospital_santa_rosa.bronze_fluxo`
- **Granularidade:** 1 linha por atendimento de emergência
- **Origem:** `atendimento_emergencia_anonimizado.csv`
- **Volume referência:** 8.730 registros (mar/2026)

### bronze_cirurgias_raw

- **Schema:** `hospital_santa_rosa.bronze_fluxo`
- **Granularidade:** 1 linha por cirurgia realizada
- **Origem:** `cirurgias_anonimizado.csv`
- **Volume referência:** 1.567 registros (mar/2026)
- **Column Mapping:** habilitado (colunas com espaços e caracteres especiais)

### bronze_epidemio_raw

- **Schema:** `hospital_santa_rosa.bronze_fluxo`
- **Granularidade:** 1 linha por caso epidemiológico
- **Origem:** `epidemio_anonimizado.csv`
- **Volume referência:** 821 registros (mar/2026)
- **Column Mapping:** habilitado

### bronze_exames_imagem_raw

- **Schema:** `hospital_santa_rosa.bronze_fluxo`
- **Granularidade:** 1 linha por exame de imagem
- **Origem:** `exames_imagem_anonimizado.csv`
- **Volume referência:** 5.866 registros (mar/2026)
- **Column Mapping:** habilitado

### bronze_internacoes_raw

- **Schema:** `hospital_santa_rosa.bronze_fluxo`
- **Granularidade:** 1 linha por internação
- **Origem:** `internacoes_anonimizado.csv`
- **Volume referência:** 867 registros (mar/2026)
- **Column Mapping:** habilitado

### bronze_movimentacoes_raw (pendente)

- **Schema:** `hospital_santa_rosa.bronze_fluxo`
- **Granularidade:** 1 linha por movimentação de leito
- **Origem:** `movimentacoes_anonimizado.csv`
- **Status:** pendente — arquivo de origem requer script de pré-processamento 
  (estrutura de relatório agrupado por unidade/data)

---

## Camada Silver

*A ser documentada no Sprint 1.*

---

## Camada Gold

*A ser documentada no Sprint 2.*