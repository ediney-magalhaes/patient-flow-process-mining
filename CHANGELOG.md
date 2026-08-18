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
  cobrindo seis tipos de jornada com vocabulário de negócio (ADR-0014):
  `atendimento_emergencia`, `internacao_clinica`, `internacao_cirurgica_emergencia`,
  `internacao_cirurgica_eletiva`, `internacao_clinica_direta`, `cirurgia_ambulatorial`
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
  - Integração com dados curados do BigQuery (`pipeline-analytics-emergencia.marts.atendimentos_pa`)
  via `enrichment.py`: colunas `fl_conversao`, `fl_evasao` e `atend_internacao` incorporadas
  a `silver_atendimento_emergencia` como fonte de verdade para conversão emergência→internação,
  substituindo o join algorítmico por aproximação temporal (`CD_PACIENTE` + janela de 1 dia)
- `gold_patient_journey` expandida com Bloco B (internações sem origem em
  emergência) via `left_anti` contra emergências convertidas, unificada ao
  Bloco A por `unionByName` antes da cadeia de enriquecimento (UTI, cirurgia,
  altas, primeiro leito) — reaproveitada sem duplicação de lógica
- ADR-0014: expansão do Bloco B e nomenclatura de negócio de `journey_type`,
  emendado com a sexta categoria (`internacao_clinica_direta`), confirmada
  por investigação de dado real (RQ-010) após refutar a hipótese original de
  inexistência clínica
- RQ-009: fonte de `ano_mes` em `gold_patient_journey` migrada de `ts_chegada`
  para `DT_ATENDIMENTO` — lacuna de totem na ingestão de mar/2026 (não
  presente na fonte já curada usada pelo projeto de conversão)
- RQ-010: investigação e confirmação de `internacao_clinica_direta` como
  padrão operacional real (internação sem consulta prévia na emergência e
  sem cirurgia), ~14% do Bloco B em mar/2026
- Dashboard "Mapa Digital do Fluxo do Paciente", página "KPIs de Jornada"
  (Página 1) concluída e publicada — duas seções (Jornada Emergência,
  Jornada Internação), 11 cards, 4 gráficos, 4 datasets SQL e ~15 campos
  calculados no Data Model; documentado em
  `docs/06-deliverables/dashboard-kpis-jornada.md`

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
  - `gold_patient_journey`: coluna `has_internacao` removida — critério de classificação de
  `journey_type` migrado do join algorítmico (`CD_INTERNACAO IS NOT NULL`) para `fl_conversao`
  curado, mais confiável para casos de coincidência temporal sem relação clínica real
- `gold_patient_journey`: fan-out corrigido em `df_cirug_internacao` e `df_cirug_ambulatorial` —
  internações/atendimentos com múltiplos procedimentos cirúrgicos duplicavam a linha da jornada;
  filtro por `SN_PRINCIPAL = 'SIM'` com desempate por `CD_AVISO_CIRURGIA`/data quando há mais de
  um procedimento principal na mesma internação (RQ pendente de numeração)
- `silver_cirurgias`: cast indevido de `CD_AVISO_CIRURGIA` para `int` removido — coluna é
  anonimizada via hash SHA-256 (string), o cast zerava o valor silenciosamente sem lançar erro
- Dataset `kpis_jornada` do Dashboard: métrica de conversão migrada de `pct_internacao`
  (`has_internacao`) para `tx_conversao` (`fl_conversao`)
- `gold_patient_journey`: chave de join do Bloco B corrigida de
  `CD_ATENDIMENTO` (inexistente em `df_intern`) para `CD_INTERNACAO`
- `gold_patient_journey`: `fl_conversao`/`fl_evasao` do Bloco B corrigidos de
  `F.lit(None).cast(0)` (sintaxe inválida) para `F.lit(0)`, conforme decisão
  de modelagem (internação direta tratada como "não convertida", não como
  "não aplicável")
- Data Model do Dashboard (`gold_bi_jornada` e `gold_patient_journey`):
  campo `has_internacao`, removido da tabela desde a Fase 1, ainda estava
  mapeado como Field no Data Model, quebrando o preview dos dois datasets
  com `UNRESOLVED_COLUMN` — campo removido, sem impacto em widgets (nenhum
  os referenciava ainda)

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

**Passo 1 — View `gold_bi_jornada`** (pré-condição para Passos 2 e 3) — ~~concluído~~
- ~~Criar no Unity Catalog (`gold_fluxo`) uma view que resolve o join entre `gold_patient_journey` e `gold_events_emergencia`, encapsulando a lógica de família de identificador (CD_ATENDIMENTO) e expondo colunas com vocabulário de negócio~~
- Essa view é a única camada de abstração para BI — não serão criadas
  tabelas/views adicionais neste sprint

**Passo 2 — Dashboard (AI/BI Dashboard)**
- **Decisão revisada (13/08/2026):** dashboard estruturado em abas por página (uma aba por seção), não em scroll único como planejado originalmente — decisão tomada durante a construção da Página 1, mantida para as páginas seguintes por consistência
- **Decisão revisada (18/08/2026):** reprogramação completa de fonte→página, motivada pela conclusão retroativa do Sprint 3 (Bottleneck, Conformance, SNA e Performance Spectrum persistidos como tabelas Gold, fato não refletido no roadmap anterior). Nº de páginas passou de 4 para 5 — inclusão da Página de Variantes, ausente do desenho original apesar de ter fonte pronta desde o fechamento do Sprint 3
- Filtro `ano_mes` (Período) implementado na Página 1. Filtro de `tipo_jornada` **não implementado** — não fez parte do desenho final da Página 1; avaliar necessidade ao construir as páginas seguintes
- Página 1 — KPIs de jornada agregada → fonte: `gold_patient_journey` — ~~concluída e publicada~~ (ver `docs/06-deliverables/dashboard-kpis-jornada.md`)
- Página 2 — Gargalos → cards de duração macro + ranking top gargalos + heatmap dia-da-semana + DFG (grafo de fluxo colorido por frequência/tempo) → fontes: `gold_patient_journey` + `gold_bi_jornada` + `gold_bottleneck` + `gold_performance_spectrum`
  - **Pendência técnica não resolvida:** viabilidade de embutir o DFG (renderizado via networkx/matplotlib, mesmo padrão usado no SNA) como imagem estática dentro do AI/BI Dashboard ainda não validada, Databricks AI/BI não executa Python nativamente. Primeira tarefa da construção desta página, não decisão fechada.
- Página 3 — Conformidade → fitness/precision por fonte, tendência por `ano_mes` → fonte: `gold_conformance` *(corrigido — roadmap anterior apontava incorretamente para `gold_patient_journey`)*
- Página 4 — Handover / SNA → sociograma setor↔setor (grafo, `gold_sna_handover` #1) + ranking de subcontracting por especialidade (`gold_sna_subcontracting` #3) → fontes: `gold_sna_handover` + `gold_sna_subcontracting` *(corrigido — roadmap anterior apontava incorretamente para `gold_events_emergencia`, tabela bruta)*
- Página 5 (nova) — Variantes de Processo → ranking + gráfico de Pareto (frequência + % cobertura acumulada) → fonte: `gold_variant_analysis`
- **Fora do escopo do Dashboard, decisão consciente:** `gold_data_quality` — tabela de governança de dado (cobertura de timestamp), audiência de TI/operação, não de gestão executiva. Sem tabela nova nem página alocada; revisar escopo se a diretoria pedir explicitamente.
- Todos os visuais projetados com eixo temporal pronto para receber meses subsequentes — mesmo que no momento da entrega só exista março/2026
- **Nota (18/08/2026):** três capacidades de granularidade micro (case-level) foram identificadas como incompatíveis com o Dashboard por volume/renderização — Performance Spectrum real, diagnóstico de Conformance por caso, Process Tree/BPMN interativo. Detalhadas e reservadas na Fase 3 — Databricks App, abaixo.

**Decisão revisada (18/08/2026, tarde) — Auditoria de completude de filtro por página**

Motivada por: filtro "Processo" nos cards macro da Página 2 revelou que o
roadmap original definiu páginas sem verificar se as tabelas Gold sustentam
as dimensões de filtro necessárias. Auditoria completa das 5 páginas contra
4 dimensões candidatas (Período, Processo, Tipo de Jornada, Especialidade)
antes de retomar qualquer construção.

**Correções de engenharia necessárias (reabre o notebook `03_process_mining.ipynb`):**
- `gold_bottleneck`: reconstruir agregação a partir de `gold_event_log`
  incluindo `especialidade` (campo já existe na origem, perdido no
  `groupby` atual) e `journey_type` (via join com `gold_patient_journey`
  por `case_id`/`cd_atendimento`, feito antes do `groupby` final)
- `gold_performance_spectrum`: mesma correção, mesmo motivo
- `gold_variant_analysis`: adicionar `ano_mes` real (hoje só tem
  `data_referencia` — viola o princípio de dimensão temporal obrigatória
  em toda tabela Gold) e `journey_type` (via mesmo mecanismo de join por
  `case_id`, rastreado antes da agregação de variante)

**Decisões de design (sem correção de dado — granularidade não sustenta a dimensão):**
- `gold_conformance`: sem `especialidade`/`journey_type`. Fitness/precision
  são propriedades de Petri Net descoberta — segmentar exigiria discovery
  separado por segmento (custo metodológico desproporcional ao valor).
  Fica em `source` × `ano_mes`.
- `gold_sna_handover`/`gold_sna_subcontracting`: sem filtro de Processo.
  Cada linha relaciona DOIS processos (`source_anterior`/`source`) —
  filtro de processo único quebraria a leitura do sociograma.
- Variant Analysis: sem filtro de Processo, mesma lógica de SNA — variante
  é caminho completo do caso, atravessa processos por definição.

**Filtros finais por página, após auditoria:**
| Página | Período | Processo | Tipo de Jornada | Especialidade |
|---|---|---|---|---|
| 1 — KPIs de Jornada | ✅ | — (n/a, jornada agregada) | ✅ já é a dimensão nativa da página | — (decisão de design, 18/08: especialidade não é estável em nível de jornada — caso pode atravessar múltiplas especialidades) |
| 2 — Gargalos (cards macro) | ✅ | — | 🔲 a implementar | — (mesma decisão de design da Página 1 — cards macro também são nível de jornada) |
| 2 — Gargalos (ranking/heatmap/DFG) | ✅ | ✅ implementado | 🔲 a implementar (pós-correção) | 🔲 a implementar (pós-correção) |
| 3 — Conformidade | ✅ | ✅ | — (decisão de design) | — (decisão de design) |
| 4 — Handover/SNA | ✅ | — (decisão de design) | — (decisão de design) | ✅ já disponível |
| 5 — Variantes | 🔲 a corrigir (falta `ano_mes` real) | — (decisão de design) | 🔲 a implementar (pós-correção) | — (decisão de design, mesma lógica das Páginas 1 e 2-macro) |

**Passo 3 — Genie Space**
- **Pendência de revisão (18/08/2026):** escopo definido abaixo foi fechado
  antes da auditoria de completude de filtro que revelou que `gold_event_log`
  carrega `especialidade` e `case_id` de forma mais rica que
  `gold_events_emergencia` isolada. Revisar este escopo depois que as
  correções de Gold (Bottleneck, Performance Spectrum, Variant Analysis)
  estiverem implementadas — pode haver fonte melhor disponível para as
  perguntas conversacionais do que a listada abaixo.
- Escopo restrito: `gold_patient_journey` + `gold_bi_jornada` + `gold_events_emergencia`
  - `gold_patient_journey`: perguntas sobre jornada completa e métricas consolidadas
  - `gold_events_emergencia`: perguntas com granularidade de evento dentro da emergência (ex: tempo entre triagem e consulta)
  - Demais `gold_events_*` fora do escopo neste sprint — revisão após validação com stakeholders
- Configuração semântica: descrições de tabela/coluna (adaptadas do `data-dictionary.md`), instruções gerais para regras de negócio críticas (famílias de identificador, prefixos de UTI), ~10 consultas certificadas para perguntas de alta frequência
- Decisão sobre uso de metric views (camada semântica estruturada do Unity Catalog) a ser tomada durante a execução deste passo, após exploração da ferramenta

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
- Visualizações:
  - Grafo de fluxo recalculável (DFG interativo, por período/filtro)
  - Performance Spectrum real — uma linha por atendimento, colorida por duração da transição; requer tabela nova, granularidade caso × transição × timestamps, ainda não existe
  - Subcontracting (exploração livre, sem o recorte curado que foi para o Dashboard)
  - Diagnóstico de Conformance Checking por caso — quais atendimentos específicos desviaram do modelo e onde; token replay já calcula isso, nunca foi persistido
  - Árvore de processo (Graphviz) — item represado do Sprint 3, já gerado localmente (pasta `temp/`), nunca integrado a nenhum entregável
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
