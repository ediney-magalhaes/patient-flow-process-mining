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

### bronze_exames_laboratoriais_raw

- **Schema:** `hospital_santa_rosa.bronze_fluxo`
- **Granularidade:** 1 linha por exame laboratorial
- **Origem:** `exames_laboratoriais_limpo_anonimizado.csv` (pré-processado localmente)
- **Volume referência:** 20.479 registros (mar/2026)
- **Pré-processamento:** `preprocess_exames_lab.py` — remoção de paginação de 
  relatório (621 páginas), normalização de timestamps com dia/mês invertido 
  pelo pandas, padronização de separador CSV

### bronze_internacoes_raw

- **Schema:** `hospital_santa_rosa.bronze_fluxo`
- **Granularidade:** 1 linha por internação
- **Origem:** `internacoes_anonimizado.csv`
- **Volume referência:** 867 registros (mar/2026)
- **Column Mapping:** habilitado

### bronze_movimentacoes_raw

- **Schema:** `hospital_santa_rosa.bronze_fluxo`
- **Granularidade:** 1 linha por movimentação de leito
- **Origem:** `movimentacoes_limpo_anonimizado.csv` (pré-processado localmente)
- **Volume referência:** 3.613 registros (mar/2026)
- **Pré-processamento:** `preprocess_movimentacoes.py` — remoção de estrutura 
  de relatório agrupado por unidade/data, normalização de 3 layouts de colunas 
  deslocadas, propagação de unidade de internação e data para cada linha

---

## Camada Silver

Dados tipados, limpos e deduplicados. Transformações executadas via 
Lakeflow Declarative Pipelines (pipeline `silver_transformations`).

### silver_altas

- **Schema:** `hospital_santa_rosa.silver_fluxo`
- **Granularidade:** 1 linha por alta hospitalar (deduplicada por atendimento)
- **Origem:** `bronze_altas_raw`
- **Volume referência:** 895 registros (mar/2026)
- **Transformações aplicadas:**
  - Correção de encoding (`1? ANDAR` → `1o ANDAR`)
  - Combinação de data + hora em timestamps únicos (`DT_HR_ATENDIMENTO`, 
    `DT_HR_ALTA_MEDICA`, `DT_HR_ALTA_FINAL`, `DT_HR_PRE_MED`)
  - Tipagem de colunas numéricas (`COD_CONVENIO`, `QTD_DIARIAS_UTI`, 
    `QTD_DIARIAS_UNID_ABERTA` → integer)
  - Deduplicação por atendimento (ROW_NUMBER, mantém registro mais recente)
  - Remoção de colunas originais de data/hora separadas e metadados de ingestão
- **Expectation:** `atendimento_valido` — descarta linhas com ATENDIMENTO nulo

---

## Camada Gold

*A ser documentada no Sprint 2.*