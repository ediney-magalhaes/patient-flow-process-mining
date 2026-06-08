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

### silver_atendimento_emergencia

- **Schema:** `hospital_santa_rosa.silver_fluxo`
- **Granularidade:** 1 linha por atendimento de emergência (deduplicada por CD_ATENDIMENTO)
- **Origem:** `bronze_atendimento_emergencia_raw`
- **Volume referência:** 6.236 registros (mar/2026)
- **Transformações aplicadas:**
  - Filtro por empresa (`EMPRESA = 'HSR'`)
  - Tipagem de 13 colunas de timestamp (string → timestamp)
  - Tipagem de data de atendimento (string → date)
  - Tipagem de colunas numéricas (`IDADE`, `COD_TRIAGEM`, `REGISTRO_ANS`, 
    `IDADE_CALCULADA` → integer)
  - Padronização de classificação de risco (`AMARELO1` → `AMARELO`)
  - 4 flags de consistência temporal: `flag_totem_classif`, `flag_classif_recep`, 
    `flag_recep_atend`, `flag_atend_alta`
  - Deduplicação por CD_ATENDIMENTO (ROW_NUMBER, mantém DT_HR_CLASSIF_RISCO 
    mais antiga)
  - Remoção de colunas financeiras, leito sem dados, metadados de ingestão
- **Expectations (monitoramento):** `flag_totem_classif`, `flag_classif_recep`, 
  `flag_recep_atend`, `flag_atend_alta`
- **Expectation (drop):** nenhuma

### silver_cirurgias

- **Schema:** `hospital_santa_rosa.silver_fluxo`
- **Granularidade:** 1 linha por procedimento cirúrgico (sem deduplicação — um 
  atendimento pode ter múltiplos procedimentos)
- **Origem:** `bronze_cirurgias_raw`
- **Volume referência:** 1.600 registros (mar/2026)
- **Transformações aplicadas:**
  - Correção de encoding (`MASCULIN0` → `MASCULINO`, `INTERNAC?O` → `INTERNACAO`)
  - Tipagem de 13 colunas de timestamp (string → timestamp)
  - Tipagem de colunas numéricas (`IDADE`, `CD_AVISO_CIRURGIA`, `CD_CIRURGIA_AVISO`, 
    `CODIGO_CIRURGIA`, `COD_FATURAMENTO` → integer)
  - 5 flags de consistência temporal: `flag_entrada_anestesia`, `flag_anestesia_cirurgia`, 
    `flag_cirurgia_fim`, `flag_fim_anestesia`, `flag_anestesia_saida`
  - Remoção de colunas calculadas, antibiótico, RPA sem dados, metadados de ingestão
- **Expectations (monitoramento):** `flag_entrada_anestesia`, `flag_anestesia_cirurgia`, 
  `flag_cirurgia_fim`, `flag_fim_anestesia`, `flag_anestesia_saida`
- **Nota:** coluna `SN_PRINCIPAL` identifica o procedimento principal de cada 
  sessão cirúrgica — usar na Gold para deduplicar por atendimento quando necessário
- **Pendente:** correção de encoding na coluna `DESCRICAO_CIRURGIA` (depende de 
  identificar encoding do CSV de origem)

### silver_epidemio

- **Schema:** `hospital_santa_rosa.silver_fluxo`
- **Granularidade:** 1 linha por internação (sem duplicatas)
- **Origem:** `bronze_epidemio_raw`
- **Volume referência:** 821 registros (mar/2026)
- **Papel:** base de enriquecimento — CIDs múltiplos, dados de UTI, complexidade, 
  procedimentos realizados
- **Transformações aplicadas:**
  - Tipagem de timestamps com formato brasileiro (`dd/MM/yyyy HH:mm` e `dd/MM/yyyy HH:mm:ss`)
  - Tipagem de timestamps formato ISO (`previsao_alta`, `dtsumario`)
  - Combinação de `dt_alta` + `hr_alta` em `dt_hr_alta`
  - Tipagem de dates com formato brasileiro (`dd/MM/yyyy` e `dd/MM/yy`)
  - Tipagem de 17 colunas numéricas (integer)
  - Remoção de colunas financeiras, colunas vazias, metadados de ingestão
- **Expectation (drop):** `atendimento_valido` — descarta linhas com atendimento nulo

### silver_exames_imagem

- **Schema:** `hospital_santa_rosa.silver_fluxo`
- **Granularidade:** 1 linha por exame de imagem por atendimento (deduplicada por CD_ATENDIMENTO + CODIGO_PROCEDIMENTO)
- **Origem:** `bronze_exames_imagem_raw`
- **Volume referência:** 5.308 registros (mar/2026)
- **Transformações aplicadas:**
  - Filtro por empresa (`Unidade = 'HSR'`)
  - Substituição de `//` por null (marcador de ausência do sistema de radiologia)
  - Tipagem de 22 colunas de timestamp formato brasileiro (`dd/MM/yyyy HH:mm`)
  - Tipagem de `DATA_HORA_PRESCRICAO` com inserção de espaço via `regexp_replace` antes da conversão (formato sem espaço na origem)
  - Tipagem de `DH_MAX` e `DH_MIN` formato ISO (`yyyy-MM-dd HH:mm:ss`)
  - Tipagem de `CODIGO_PROCEDIMENTO` (string → integer)
  - 4 flags de consistência temporal: `flag_prescricao_admissao`, `flag_admissao_inicio`, `flag_inicio_termino`, `flag_termino_liberado`
  - Deduplicação por CD_ATENDIMENTO + CODIGO_PROCEDIMENTO (ROW_NUMBER, mantém DH_MIN mais antigo)
  - Remoção de colunas redundantes e metadados de ingestão
- **Expectations (monitoramento):** `flag_prescricao_admissao`, `flag_admissao_inicio`, `flag_inicio_termino`, `flag_termino_liberado`
- **Nota:** `flag_termino_liberado` apresenta 100% de violações — laudo é liberado antes do término formal do exame no RIS. Comportamento a ser validado pelos gestores da área de imagem.

### silver_exames_laboratoriais

- **Schema:** `hospital_santa_rosa.silver_fluxo`
- **Granularidade:** 1 linha por exame laboratorial por atendimento (deduplicada por CD_ATENDIMENTO + CD_EXAME)
- **Origem:** `bronze_exames_laboratoriais_raw`
- **Volume referência:** 20K registros (mar/2026)
- **Transformações aplicadas:**
  - Renomeação de `ATEND` → `CD_ATENDIMENTO` (padronização com demais tabelas Silver)
  - Tipagem de 4 colunas de timestamp formato ISO (`yyyy-MM-dd HH:mm:ss`)
  - 2 flags de consistência temporal: `flag_pedido_coleta`, `flag_coleta_laudo`
  - Deduplicação por CD_ATENDIMENTO + CD_EXAME (ROW_NUMBER, mantém HR_PED_LAB mais antigo)
  - Remoção de metadados de ingestão
- **Expectations (monitoramento):** `flag_pedido_coleta`, `flag_coleta_laudo`

### silver_internacoes

- **Schema:** `hospital_santa_rosa.silver_fluxo`
- **Granularidade:** 1 linha por internação (deduplicada por CD_INTERNACAO)
- **Origem:** `bronze_internacoes_raw`
- **Volume referência:** 867 registros (mar/2026)
- **Transformações aplicadas:**
  - Renomeação de `ATENDIMENTO` → `CD_INTERNACAO` (diferencia do CD_ATENDIMENTO da emergência)
  - Tipagem de 2 colunas de timestamp formato ISO (`yyyy-MM-dd HH:mm:ss`)
  - Tipagem de colunas numéricas (`IDADE`, `CD_ORIGEM` → integer)
  - 1 flag de consistência temporal: `flag_atendimento_alta`
  - Deduplicação por CD_INTERNACAO (ROW_NUMBER, mantém DT_HR_ATENDIMENTO mais antigo)
  - Remoção de `CD_LEITO` (redundante com `LEITO`) e metadados de ingestão
- **Expectations (monitoramento):** `flag_atendimento_alta`
- **Nota:** `COD_PACIENTE` é o prontuário do paciente — identificador estável que permite rastrear a jornada entre emergência e internação na camada Gold

### silver_movimentacoes

- **Schema:** `hospital_santa_rosa.silver_fluxo`
- **Granularidade:** 1 linha por movimentação de leito por internação
- **Origem:** `bronze_movimentacoes_raw`
- **Volume referência:** 3.6K registros (mar/2026)
- **Transformações aplicadas:**
  - Renomeação de `ATEND` → `CD_INTERNACAO` (padronização com silver_internacoes)
  - Correção de encoding na coluna `UNIDADE` (`Âº` → `º`)
  - Combinação de `DATA` + `HORA` em timestamp único `DT_HR_MOVIMENTACAO`
  - Deduplicação por CD_INTERNACAO + DT_HR_MOVIMENTACAO + TIPO
  - Remoção de colunas `DATA` e `HORA` (substituídas por `DT_HR_MOVIMENTACAO`) e metadados de ingestão
- **Tipos de movimentação (`TIPO`):** `INTERNACAO`, `TRANSFER. DE`, `TRANSFER. PARA`, `ALTA`
- **Expectations:** nenhuma (tabela de eventos pontuais sem pares de timestamps para validar)

---

## Camada Gold

*A ser documentada no Sprint 2.*