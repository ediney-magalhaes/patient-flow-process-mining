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

### Adicionado

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
 
**Previsão:** a definir
 
- Descoberta automatizada de processos com PM4Py
- Análise de variantes, gargalos e conformidade
### [0.5.0] — Sprint 4: Entregáveis
 
**Previsão:** a definir
 
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
