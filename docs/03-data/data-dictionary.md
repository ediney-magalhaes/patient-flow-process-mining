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

Event log canônico para Process Mining e atributos de caso para enriquecimento analítico.
Todas as tabelas `gold_events_*` seguem o schema canônico XES com 10 colunas obrigatórias.

### Schema canônico — tabelas gold_events_*

| Coluna | Tipo | Obrigatoriedade | Descrição |
|---|---|---|---|
| `case_id` | string | obrigatório | Identificador do atendimento (hash SHA-256) |
| `activity` | string | obrigatório | Nome da atividade do evento |
| `timestamp` | timestamp | obrigatório | Momento em que o evento ocorreu |
| `lifecycle` | string | obrigatório | Fase do evento (`start` ou `complete`) |
| `event_type` | string | obrigatório | Categoria do evento (ex: `internacao`, `cirurgia`) |
| `case_type` | string | obrigatório | Tipo de jornada do caso (ex: `internacao`, `cirurgico`) |
| `outcome` | string | nullable | Desfecho do caso |
| `resource` | string | nullable | Profissional ou sistema que executou a atividade |
| `location` | string | nullable | Unidade ou sala onde o evento ocorreu |
| `source` | string | obrigatório | Tabela Silver de origem do evento |
| `duration_minutes` | int | nullable | Duração total do caso em minutos (diferença entre primeiro e último evento) |

### gold_events_movimentacoes

- **Schema:** `hospital_santa_rosa.gold_fluxo`
- **Granularidade:** 1 linha por evento de movimentação de leito
- **Origem:** `silver_movimentacoes`
- **Volume referência:** 3.6K registros (mar/2026)
- **Eventos:** `INTERNACAO`, `TRANSFER. DE`, `TRANSFER. PARA`, `ALTA`
- **location:** coluna `UNIDADE` da Silver

### gold_events_internacoes

- **Schema:** `hospital_santa_rosa.gold_fluxo`
- **Granularidade:** 1 linha por evento de internação (2 eventos por atendimento)
- **Origem:** `silver_internacoes`
- **Volume referência:** 1.7K registros (mar/2026)
- **Eventos:** `Internacao`, `Alta da Internacao`
- **location:** coluna `UNIDADE` da Silver

### gold_events_altas

- **Schema:** `hospital_santa_rosa.gold_fluxo`
- **Granularidade:** 1 linha por evento de alta (3 eventos por atendimento)
- **Origem:** `silver_altas`
- **Volume referência:** 2.7K registros (mar/2026)
- **Eventos:** `Prescricao de Alta`, `Alta Medica`, `Alta Hospitalar`
- **location:** coluna `UNID_INT` da Silver

### gold_events_cirurgias

- **Schema:** `hospital_santa_rosa.gold_fluxo`
- **Granularidade:** 1 linha por evento cirúrgico (12 eventos por procedimento)
- **Origem:** `silver_cirurgias`
- **Volume referência:** 19K registros (mar/2026)
- **Eventos:** `Aviso de Cirurgia`, `Agendamento de Cirurgia`, `Inicio Programado da Cirurgia`,
  `Fim Programado da Cirurgia`, `Entrada na Sala Cirurgica`, `Inicio da Anestesia`,
  `Inicio da Cirurgia`, `Fim da Cirurgia`, `Fim da Anestesia`, `Saida da Sala Cirurgica`,
  `Inicio da Limpeza da Sala`, `Fim da Limpeza da Sala`
- **location:** coluna `SALA_CIRURGIA` da Silver

### gold_events_emergencia

- **Schema:** `hospital_santa_rosa.gold_fluxo`
- **Granularidade:** 1 linha por evento de emergência (8 eventos por atendimento)
- **Origem:** `silver_atendimento_emergencia`
- **Volume referência:** 50K registros (mar/2026)
- **Eventos:** `Chegada ao Pronto-Socorro`, `Início da Triagem`, `Classificação de Risco`,
  `Início do Cadastro`, `Fim do Cadastro`, `Início da Consulta Médica`,
  `Fim da Consulta Médica`, `Alta da Emergência`
- **location:** null — sem coluna de localização física disponível na Silver
- **Nota:** CID registrado nesta tabela representa hipótese diagnóstica de entrada,
  não diagnóstico confirmado

### gold_events_exames_imagem

- **Schema:** `hospital_santa_rosa.gold_fluxo`
- **Granularidade:** 1 linha por evento de exame de imagem (10 eventos por exame)
- **Origem:** `silver_exames_imagem`
- **Volume referência:** 53K registros (mar/2026)
- **Eventos:** `Prescrição do Exame de Imagem`, `Admissão no RIS`,
  `Liberação para Início do Exame`, `Início do Preparo`, `Fim do Preparo`,
  `Início do Exame`, `Término do Exame de Imagem`, `Ditado do Laudo`,
  `Laudo Registrado no Sistema`, `Laudo Aprovado`
- **case_type:** dinâmico via coluna `TIPO_ATENDIMENTO` da Silver (`Internação`,
  `Urgência`, `Ambulatório`, `Externo`)
- **location:** null — sem coluna de localização física disponível na Silver

### gold_events_exames_laboratoriais

- **Schema:** `hospital_santa_rosa.gold_fluxo`
- **Granularidade:** 1 linha por evento de exame laboratorial (3 eventos por exame)
- **Origem:** `silver_exames_laboratoriais`
- **Volume referência:** 60K registros (mar/2026)
- **Eventos:** `Pedido de Exame Laboratorial`, `Coleta do Exame Laboratorial`,
  `Laudo do Exame Laboratorial`
- **case_type:** `emergencia` — todos os exames laboratoriais desta base são
  de pacientes de emergência (confirmado pela presença de `CLASSI_RISCO` em todos os registros)
- **location:** null — sem coluna de localização física disponível na Silver

### gold_event_log

- **Schema:** `hospital_santa_rosa.gold_fluxo`
- **Granularidade:** 1 linha por evento (UNION ALL de todas as tabelas `gold_events_*`)
- **Origem:** `gold_events_movimentacoes`, `gold_events_internacoes`, `gold_events_altas`,
  `gold_events_cirurgias`, `gold_events_emergencia`, `gold_events_exames_imagem`,
  `gold_events_exames_laboratoriais`
- **Volume referência:** 190K registros (mar/2026)
- **Colunas adicionais:** `duration_minutes` — duração total do caso em minutos,
  calculada via Window function particionada por `case_id`
- **Nota:** tabela central do projeto — fonte primária para análises de Process Mining
  com PM4Py no Sprint 3

### gold_case_attributes

- **Schema:** `hospital_santa_rosa.gold_fluxo`
- **Granularidade:** 1 linha por atendimento
- **Origem:** `silver_epidemio` (casos de internação) + `silver_atendimento_emergencia` (casos de emergência)
- **Volume referência:** 7.1K registros (mar/2026)
- **Colunas:**

| Coluna | Tipo | Fonte internação | Fonte emergência | Descrição |
|---|---|---|---|---|
| `case_id` | string | `atendimento` | `CD_ATENDIMENTO` | Identificador do caso |
| `case_type` | string | `tp_atendimento` | `"emergencia"` | Tipo de jornada |
| `idade` | int | `idade` | `IDADE_CALCULADA` | Idade do paciente |
| `sexo` | string | `sexo` | `SEXO` | Sexo do paciente |
| `convenio` | string | `convenio` | `CONVENIO` | Convênio do paciente |
| `especialidade` | string | `especialidade` | `ESPECIALIDADE` | Especialidade médica |
| `cid_principal` | string | `cid_1_principal` | `CID` | CID principal — para internação é diagnóstico confirmado; para emergência é hipótese diagnóstica de entrada |
| `motivo_alta` | string | `motivo_alta` | `MOTIVO_ALTA` | Motivo da alta |
| `classificacao_risco` | string | null | `COR_CLASSIF` | Classificação de risco (somente emergência) |
| `tipo_internacao` | string | `tipo_internacao` | null | Tipo de internação (somente internação) |
| `nr_dias` | int | `nr_dias` | null | Número de dias de internação |
| `qtd_passagens_uti` | int | `qtd_passagens_uti` | null | Quantidade de passagens pela UTI |
| `complexidade` | string | `PREVISAO_COMPLEXIDADE` | null | Complexidade prevista do caso |
| `grupo_diagnostico` | string | `PREVISAO_GRUPO` | null | Grupo diagnóstico previsto |
| `teve_cirurgia` | string | `cirurgia` | null | Indica se houve cirurgia |