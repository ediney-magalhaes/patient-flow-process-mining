# Changelog
 
Todas as mudanças notáveis deste projeto são documentadas neste arquivo.
 
O formato segue [Keep a Changelog 1.1.0](https://keepachangelog.com/pt-BR/1.1.0/), 
e o projeto adere ao [Versionamento Semântico 2.0.0](https://semver.org/lang/pt-BR/).
 
## Tipos de mudança
 
- `Adicionado` para novas funcionalidades
- `Alterado` para mudanças em funcionalidades existentes
- `Descontinuado` para funcionalidades que serão removidas em breve
- `Removido` para funcionalidades removidas
- `Corrigido` para correções de bugs
- `Segurança` para correções de vulnerabilidades
---
 
## [Não Lançado]

#### Sprint 4 — Entregáveis (em andamento)

#### Adicionado

- `gold_patient_journey` — tabela Gold cross-source com jornada completa do paciente,
  cobrindo seis tipos de jornada: `emergencia_pura`, `emergencia_cirurgia_ambulatorial`,
  `emergencia_internacao_clinica`, `emergencia_internacao_cirurgica`,
  `internacao_direta_clinica`, `internacao_direta_cirurgica`
- Cobertura de cirurgias ambulatoriais de emergência via anti join com `silver_internacoes`
  e join por `CD_PACIENTE` + janela temporal de 1 dia usando `DATA_INICIO_CIRURGIA`
- Métricas de UTI agregadas por episódio: `ts_primeira_entrada_uti`, `ts_ultima_saida_uti`,
  `qtd_passagens_uti`, `duracao_total_uti_min`
- `ts_primeiro_leito` excluindo unidades virtuais via coluna `UNIDADE`
- ADR-0011: design da `gold_patient_journey`
- RQ-006: `ORIGEM_ATEND` em `silver_internacoes` — campo com falhas de input manual
- View `gold_bi_jornada` criada no Unity Catalog (`hospital_santa_rosa.gold_fluxo`)
  como camada de abstração para BI — resolve join entre `gold_patient_journey` e
  `gold_events_emergencia` encapsulando a complexidade das famílias de identificador
- Dashboard AI/BI "Mapa Digital do Fluxo do Paciente" criado com datasets
  `gold_patient_journey` e `gold_bi_jornada` conectados; página "KPIs de Jornada"
  iniciada com filtro global `ano_mes` e primeiro contador validado (06/07/2026)

#### Corrigido

- Coluna `DT_CIRURGIA` em `silver_cirurgias` corrigida de `DT_ATENDIMENTO`
  (inexistente) para `DATA_INICIO_CIRURGIA`
- `ano_mes` ausente em todas as tabelas `gold_events_*` (`gold_events_altas`,
  `gold_events_cirurgias`, `gold_events_emergencia`, `gold_events_exames_imagem`,
  `gold_events_exames_laboratoriais`, `gold_events_internacoes`,
  `gold_events_movimentacoes`), coluna obrigatória do schema canônico Gold
  adicionada via `F.date_format(F.col("timestamp"), "yyyy-MM")` em cada função
  do `gold_transformation.py`. Pipeline reprocessado com Full Refresh em
  06/07/2026

#### Sprint 3 — Process Mining (concluído)

- PM4Py 2.7.22.4 instalado e validado no Databricks Free Edition (serverless)
- Notebook `03_process_mining.ipynb` criado — pipeline Gold → Pandas → PM4Py EventLog
- Algoritmo Inductive Miner selecionado para descoberta de processo (ADR-0009)
- Process Tree gerado para os fluxos de emergência e internação; visualização
  gerada localmente via Graphviz (bloqueado no Databricks serverless)
- Variant Analysis: 2.016 variantes identificadas e ranqueadas; persistido
  em `gold_variant_analysis`
- Bottleneck Detection: tempos de espera entre atividades calculados por
  fonte, com coeficiente de variação; persistido em `gold_bottleneck`
- Conformance Checking: token replay por fonte (fitness ≥ 0,99; precision
  0,06–0,18, atribuída à alta variedade de variantes); decisão documentada
  em ADR-0010; persistido em `gold_conformance`
- `gold_data_quality`: cobertura de timestamp por atividade e por caso
- Social Network Analysis (5 análises, escopo em ADR-0008):
  - Subcontracting setor↔setor, nível único
  - Handover e Subcontracting especialidade↔especialidade, segmentados por setor
  - Handover e Subcontracting setor↔setor, com especialidade como atributo
    da transição (construção manual em Pandas); persistidos em
    `gold_sna_handover` e `gold_sna_subcontracting`
- Performance Spectrum: análise de variação temporal de transições por mês
  e dia da semana; persistido em `gold_performance_spectrum`
- Dimensão `ano_mes` adicionada em `df_formatado`, propagada para Bottleneck,
  SNA e Conformance, suportando análise de tendência com histórico multi-período
- Exportação do event log completo para o formato padrão XES
  (IEEE 1849-2016), disponível em `hospital_santa_rosa.gold_fluxo.exports`
- Volume `exports` criado em `gold_fluxo` para artefatos de saída do projeto

### Corrigido
- RQ-004: causa raiz da perda de eventos entre `gold_event_log` e o
  EventLog do PM4Py confirmada — nulos de timestamp já presentes na
  Silver, não introduzidos pela transformação Gold.
- RQ-005: causa raiz da anomalia de timestamp (`Alta médica` antes de
  `Fim da Anestesia`) confirmada como erro de input operacional na
  origem, não falha de pipeline.

#### Sprint 2 — Gold (Event Log XES) — concluído

- Pipeline `gold_transformations` criado no Databricks apontando para `gold_transformation.py`
- Schema canônico do event log definido com 11 colunas: `case_id`, `activity`, `timestamp`,
  `lifecycle`, `event_type`, `case_type`, `outcome`, `resource`, `location`, `source`, `duration_minutes`
- Mapeamento de eventos por fonte concluído — 7 tabelas Silver mapeadas, 38 eventos distintos identificados
- Tabela `gold_events_movimentacoes` criada (3.6K registros)
- Tabela `gold_events_internacoes` criada (1.7K registros)
- Tabela `gold_events_altas` criada (2.7K registros)
- Tabela `gold_events_cirurgias` criada (19K registros) — padrão de iteração sobre lista de eventos
- Tabela `gold_events_emergencia` criada (50K registros)
- Tabela `gold_events_exames_imagem` criada (53K registros) — `case_type` dinâmico via `TIPO_ATENDIMENTO`
- Tabela `gold_events_exames_laboratoriais` criada (60K registros)
- Tabela `gold_event_log` criada (190K registros) — UNION ALL das 7 fontes com `duration_minutes`
- Tabela `gold_case_attributes` criada (7.1K registros) — 15 atributos clínicos e demográficos

#### Sprint 1 — Bronze + Silver (concluído)

- Volume `landing_zone` criado no Unity Catalog com subpastas por base
- Auto Loader (`cloudFiles`) validado na Free Edition com `trigger(availableNow=True)`
- Notebook `01_bronze_ingestion` — pipeline de ingestão Bronze via Auto Loader
- 8 tabelas Bronze criadas com dados reais de março/2026:
  - `bronze_altas_raw` (908 registros)
  - `bronze_atendimento_emergencia_raw` (8.730 registros)
  - `bronze_cirurgias_raw` (1.567 registros)
  - `bronze_epidemio_raw` (821 registros)
  - `bronze_exames_imagem_raw` (5.866 registros)
  - `bronze_exames_laboratoriais_raw` (20.479 registros)
  - `bronze_internacoes_raw` (867 registros)
  - `bronze_movimentacoes_raw` (3.613 registros)
- Metadados de ingestão: `_ingestion_timestamp` e `_source_file` em todas as tabelas
- Column Mapping habilitado para tabelas com caracteres especiais nos nomes de colunas
- Scripts de pré-processamento local para bases com estrutura de relatório:
  - `preprocess_exames_lab.py` — limpeza de paginação e normalização de timestamps
  - `preprocess_movimentacoes.py` — limpeza de paginação, normalização de layouts deslocados e propagação de unidade/data
- Integração das bases de exames laboratoriais e movimentações ao pipeline de anonimização
- Lakeflow Declarative Pipelines validado na Free Edition (confirma ADR-0003)
- Pipeline `silver_transformations` criado no Databricks
- Tabela `silver_altas` criada (895 registros) — tipada, deduplicada e limpa
- Tabela `silver_atendimento_emergencia` criada (6.236 registros) — tipada, deduplicada, com 4 flags de consistência temporal
- Tabela `silver_cirurgias` criada (1.600 registros) — tipada, com 5 flags de consistência temporal, granularidade por procedimento
- Tabela `silver_epidemio` criada (821 registros) — tipada, base de enriquecimento clínico
- Tabela `silver_exames_imagem` criada (5.308 registros) — tipada, deduplicada, com 4 flags de consistência temporal
- Tabela `silver_exames_laboratoriais` criada (20K registros) — tipada, deduplicada, com 2 flags de consistência temporal
- Tabela `silver_internacoes` criada (867 registros) — tipada, deduplicada, com 1 flag de consistência temporal
- Tabela `silver_movimentacoes` criada (3.6K registros) — tipada, deduplicada, event log de movimentações de leito
- Pipeline `silver_transformations` migrado para Git folder — código versionado no repositório
- `requirements.txt` com dependências do projeto

### Corrigido

- Anonimização da base epidemio: colunas `prestador1` e `prestador2` adicionadas ao `config.py` e dados re-ingeridos na Bronze
- Mapeamento de `especialidade` em `gold_events_exames_imagem` corrigido de `ESPECIALIDADE` para `ESPECIALIDADE_MEDICO`, coluna
  anterior não representava a especialidade do médico solicitante; bases de `exames_imagem` e `atendimento_emergencia` reingeridas (Bronze → Silver → Gold)

#### Sprint 0 — Fundação (concluído)

- Workspace Databricks Free Edition (AWS) configurado
- Repositório Git criado e conectado ao Databricks via Git folder
- `README.md` — visão geral, problema de negócio, solução, impacto esperado
- `ARCHITECTURE.md` — decisões arquiteturais e diagramas
- `CONTRIBUTING.md` — padrões de contribuição (Conventional Commits, 
  Trunk-Based Development)
- `SECURITY.md` — política de segurança e conformidade LGPD
- `CHANGELOG.md` — este arquivo
- `LICENSE` (MIT)
- `.gitignore` (Python)
- Unity Catalog configurado: catálogo `hospital_santa_rosa` com schemas 
  `bronze_fluxo`, `silver_fluxo`, `gold_fluxo` e `ml_fluxo`
- Script local de anonimização PII (SHA-256, remoção, generalização) com 
  configuração modular para 9 bases hospitalares
- ADRs iniciais (0001-0005): Lakehouse, Medallion, Declarative Pipelines, 
  PM4Py, anonimização local
- Estrutura de documentação (`docs/`) com 8 seções temáticas
---
 
## Roadmap de Versões
 
> Planejamento de releases futuros. Atualizado ao final de cada sprint.
 
### [0.1.0] — Sprint 0: Fundação

**Status:** concluído

- Setup completo do workspace e Unity Catalog
- Documentação base do repositório
- Script de anonimização local
- ADRs das decisões arquiteturais iniciais
### [0.2.0] — Sprint 1: Bronze + Silver

**Status:** concluído
 
- Ingestão dos dados de emergência e internação na camada Bronze
- Pipeline de transformação Bronze → Silver com validações de qualidade
- Tabelas Silver com event log padronizado
### [0.3.0] — Sprint 2: Gold (Event Log XES)

**Status:** concluído

- Pipeline `gold_transformations` criado no Databricks
- 7 tabelas `gold_events_*` — uma por fonte Silver, normalizando eventos
  para o schema canônico (`case_id`, `activity`, `timestamp`, `lifecycle`,
  `event_type`, `case_type`, `outcome`, `resource`, `location`, `source`)
- `gold_event_log` — event log unificado (UNION ALL das 7 tabelas) com
  `duration_minutes` calculado por caso
- `gold_case_attributes` — atributos do caso para enriquecimento analítico
  (dados clínicos via `silver_epidemio`)
### [0.4.0] — Sprint 3: Process Mining

**Previsão:** concluído

#### Fase 1 — Fundamentos e ambiente
- Instalação e configuração do PM4Py no Databricks Free Edition
- Conceitos fundamentais: event log, trace, variant, Petri net, process model
- Carregamento do `gold_event_log` do Delta Lake para o formato PM4Py

#### Fase 2 — Descoberta de processos
- Estudo comparativo dos algoritmos: Alpha Miner, Heuristic Miner, Inductive Miner
- Decisão arquitetural: qual algoritmo usar e por quê (ADR-0009)
- Geração do process model do fluxo de emergência
- Geração do process model do fluxo de internação

#### Fase 3 — Análises
- Variant analysis: identificação e ranking das variantes de processo
- Bottleneck detection: tempos de espera entre atividades
- Conformance checking: token replay vs alignment (ADR-0010)
- Social Network Analysis: Handover of Work (setor↔setor com especialidade
  como atributo da transição; especialidade ↔ especialidade segmentado por setor)
  e Subcontracting (mesmos dois níveis, mais a versão setor ↔ setor pura, sem especialidade);
  Working Together e Similar Activities avaliados e descartados (ADR-0008)
- Performance Spectrum: variação temporal do desempenho do processo

#### Fase 4 — Exportação
- Exportação do event log no formato XES
- Persistência dos modelos descobertos no schema `gold_fluxo`
### [0.5.0] — Sprint 4: Entregáveis
 
**Previsão:** em andamento

#### Fase 1 — gold_patient_journey

- ~~ Decisão arquitetural: como linkar `CD_ATENDIMENTO` ↔ `CD_INTERNACAO` para o mesmo episódio, pergunta de domínio antes de qualquer código~~
- ~~A tabela deve incluir `ano_mes` como dimensão obrigatória, seguindo o padrão estabelecido no Sprint 3 para suportar séries temporais quando o histórico for carregado~~
- ~~Implementação no `gold_transformation.py`~~
- ~~Entrada no dicionário de dados~~
- ~~ADR correspondente~~

#### Fase 2 — Dashboard AI/BI

**Passo 1 — View `gold_bi_jornada`** (pré-condição para Passos 2 e 3)
- Criar no Unity Catalog (`gold_fluxo`) uma view que resolve o join entre
  `gold_patient_journey` e `gold_events_atendimento`, encapsulando a lógica
  de família de identificador (CD_ATENDIMENTO) e expondo colunas com
  vocabulário de negócio
- Essa view é a única camada de abstração para BI — não serão criadas
  tabelas/views adicionais neste sprint

**Passo 2 — Dashboard único (AI/BI Dashboard)**
- Um único dashboard com quatro blocos organizados em seções visuais
  scrolláveis (sem navegação por abas — comportamento nativo da ferramenta)
- Filtro global de `ano_mes` e `tipo_jornada` aplicando sobre todos os blocos
- Seção 1 — KPIs de jornada agregada → fonte: `gold_patient_journey`
- Seção 2 — Análise de gargalos → fonte: `gold_patient_journey` +
  `gold_bi_jornada`
- Seção 3 — Conformance checking → fonte: `gold_patient_journey`
- Seção 4 — Handover / SNA → fonte: `gold_events_atendimento`
- Todos os visuais projetados com eixo temporal pronto para receber meses
  subsequentes — mesmo que no momento da entrega só exista março/2026

**Passo 3 — Genie Space**
- Escopo restrito: `gold_patient_journey` + `gold_bi_jornada` +
  `gold_events_atendimento`
  - `gold_patient_journey`: perguntas sobre jornada completa e métricas
    consolidadas
  - `gold_events_atendimento`: perguntas com granularidade de evento dentro
    da emergência (ex: tempo entre triagem e consulta)
  - Demais `gold_events_*` fora do escopo neste sprint — revisão após
    validação com stakeholders
- Configuração semântica: descrições de tabela/coluna (adaptadas do
  `data-dictionary.md`), instruções gerais para regras de negócio críticas
  (famílias de identificador, prefixos de UTI), ~10 consultas certificadas
  para perguntas de alta frequência
- Decisão sobre uso de metric views (camada semântica estruturada do Unity
  Catalog) a ser tomada durante a execução deste passo, após exploração
  da ferramenta

**Passo 4 — Permissões e publicação**
- Configurar acesso no Unity Catalog para os perfis de consumo (gestores
  do hospital) para Dashboard e Genie Space

**Passo 5 — Documentação**
- `docs/06-deliverables/dashboard.md` cobrindo Dashboard e Genie Space
- Os dois ADRs pendentes (escolha do AI/BI Dashboard e do Databricks App)
  ficam para a Fase 4 conforme planejado

#### Fase 3 — Databricks App

- Setup do service principal e permissões Unity Catalog
- Desenvolvimento direto no Databricks App (sem etapa local)
- Filtros da interface: source, `ano_mes` (range de meses, não só mês único),
  turno, threshold de ruído, o filtro de período deve aceitar seleção múltipla
  de meses desde o início, porque com histórico o usuário vai querer comparar janelas
- Visualizações: grafo de fluxo recalculável, performance spectrum, subcontracting
- Árvore de processo (Graphviz) — item represado do Sprint 3
- Deploy e validação
- Documentação em `docs/06-deliverables/app.md`

#### Fase 4 — ADRs e fechamento

- ADR: escolha do AI/BI Dashboard (decisão #2 de hoje)
- ADR: escolha do Databricks App (decisão #3 de hoje)
- ADR: design da `gold_patient_journey` (decisão #1 + solução da Fase 1)
- Atualização do `CHANGELOG.md`
- Atualização do `README.md` (roadmap Sprint 4 → concluído)

#### Resumo
- Dashboard executivo
- App interativo de Process Mining
- Documentação dos entregáveis
### [1.0.0] — Sprint 5: Release Oficial
 
**Previsão:** a definir
 
- CI/CD completo
- Documentação final
- Apresentação executiva
---
 
## Convenções deste Changelog
 
Cada entrada descreve brevemente a mudança. A partir da versão `1.0.0`, 
este changelog poderá ser gerado automaticamente a partir dos Conventional 
Commits. Até lá, a manutenção é manual ao final de cada sprint.
 
Releases lançadas terão correspondência em 
[GitHub Releases](../../releases) com tag SemVer (`v0.1.0`, `v0.2.0`, ...).
 
---
 
## Links de Comparação
 
[Não Lançado]: https://github.com/ediney-magalhaes/patient-flow-process-mining/compare/main...HEAD
