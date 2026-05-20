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

#### Sprint 1 — Bronze (em andamento)

- Volume `landing_zone` criado no Unity Catalog com subpastas por base
- Auto Loader (`cloudFiles`) validado na Free Edition com `trigger(availableNow=True)`
- Notebook `01_bronze_ingestion` — pipeline de ingestão Bronze via Auto Loader
- 6 tabelas Bronze criadas com dados reais de março/2026:
  - `bronze_altas_raw` (908 registros)
  - `bronze_atendimento_emergencia_raw` (8.730 registros)
  - `bronze_cirurgias_raw` (1.567 registros)
  - `bronze_epidemio_raw` (821 registros)
  - `bronze_exames_imagem_raw` (5.866 registros)
  - `bronze_internacoes_raw` (867 registros)
- Metadados de ingestão: `_ingestion_timestamp` e `_source_file` em todas as tabelas
- Column Mapping habilitado para tabelas com caracteres especiais nos nomes de colunas
- `requirements.txt` com dependências do projeto

#### Pendente neste sprint

- Script de pré-processamento para base de movimentações (estrutura de relatório)
- Base de exames laboratoriais (pendente confirmação de timestamps)
- Transformação Bronze → Silver
- Atualização do ARCHITECTURE.md com decisões validadas

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
 
**Previsão:** em andamento
 
- Setup completo do workspace e Unity Catalog
- Documentação base do repositório
- Script de anonimização local
- ADRs das decisões arquiteturais iniciais
### [0.2.0] — Sprint 1: Bronze + Silver
 
**Previsão:** a definir
 
- Ingestão dos dados de emergência e internação na camada Bronze
- Pipeline de transformação Bronze → Silver com validações de qualidade
- Tabelas Silver com event log padronizado
### [0.3.0] — Sprint 2: Gold (Event Log XES)
 
**Previsão:** a definir
 
- Tabela Gold com event log no formato canônico XES
- Tabelas de KPIs e métricas agregadas
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
