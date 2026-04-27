# Contribuindo para o Projeto Mapa Digital do Fluxo do Paciente
 
Obrigado pelo interesse em contribuir! Este documento define os padrões e 
processos para contribuições, garantindo qualidade, rastreabilidade e 
manutenibilidade do projeto.
 
> Antes de contribuir, leia também:
> - [README.md](README.md) — Visão geral do projeto
> - [ARCHITECTURE.md](ARCHITECTURE.md) — Decisões arquiteturais
> - [SECURITY.md](SECURITY.md) — Política de segurança e LGPD
 
---
 
## Tipos de Contribuição
 
| Tipo | Como contribuir |
|---|---|
| **Reportar bug** | Abra uma [issue](../../issues/new) |
| **Sugerir feature** | Abra uma [issue](../../issues/new) |
| **Melhorar documentação** | PR direto na pasta `docs/` |
| **Implementar código** | Siga o fluxo abaixo |
| **Tirar dúvida** | Use [Discussions](../../discussions) |
 
---
 
## Setup do Ambiente de Desenvolvimento
 
### Pré-requisitos
 
- Python 3.x
- Git
- Conta no Databricks Free Edition
- Editor recomendado: VS Code
> ⚠️ Ferramentas adicionais (Databricks CLI, pre-commit hooks, linters) 
> serão documentadas conforme forem configuradas ao longo dos sprints.
 
### Setup inicial
 
```bash
# Fork o repositório no GitHub, depois clone seu fork
git clone https://github.com/SEU-USUARIO/patient-flow-process-mining.git
cd patient-flow-process-mining
 
# Adicione o repositório original como upstream
git remote add upstream https://github.com/ediney-magalhaes/patient-flow-process-mining.git
 
# Crie ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
```
 
---
 
## Estratégia de Branches
 
Adotamos **Trunk-Based Development simplificado**:
 
```
main                    ← branch protegida, sempre deployable
├── feat/sprint-1-bronze-layer
├── fix/datetime-parsing-bug
├── docs/update-architecture
└── refactor/event-log-builder
```
 
### Regras
 
- **`main`** é sagrada — sempre passa nos testes, sempre deployable
- Branches feature são **curtas** (idealmente < 3 dias de trabalho)
- Sempre rebase com `main` antes de abrir PR
- Nunca commitar direto em `main`
- Nunca force-push em `main`
### Convenção de nomes de branch
 
```
<tipo>/<descrição-curta-em-kebab-case>
```
 
**Tipos válidos:**
 
- `feat/` — nova funcionalidade
- `fix/` — correção de bug
- `docs/` — alteração apenas em documentação
- `refactor/` — refatoração sem mudança de comportamento
- `test/` — adição/correção de testes
- `chore/` — manutenção (deps, configs, CI)
- `perf/` — melhoria de performance
**Exemplos:**
 
```
feat/sprint-2-event-log-xes
fix/silver-timestamp-utc
docs/adr-0004-pm4py
refactor/extract-anonymization-module
```
 
---
 
## Convenção de Commits
 
Adotamos **[Conventional Commits 1.0](https://www.conventionalcommits.org/pt-br/v1.0.0/)** 
— padrão usado por Angular, Vue, NestJS e milhares de projetos open source.
 
### Formato
 
```
<tipo>(<escopo opcional>): <descrição curta em minúscula>
 
[corpo opcional explicando o porquê]
 
[rodapé opcional: BREAKING CHANGE, refs, co-authors]
```
 
### Tipos válidos
 
| Tipo | Quando usar | Exemplo |
|---|---|---|
| `feat` | Nova funcionalidade | `feat(silver): adicionar deduplicação de eventos` |
| `fix` | Correção de bug | `fix(bronze): corrigir parse de datas brasileiras` |
| `docs` | Apenas documentação | `docs(adr): adicionar ADR-0004 PM4Py` |
| `style` | Formatação, sem mudança lógica | `style: aplicar black em src/` |
| `refactor` | Refatoração sem mudança de comportamento | `refactor(silver): extrair builder de event log` |
| `perf` | Melhoria de performance | `perf(gold): aplicar Liquid Clustering em fato` |
| `test` | Adição/correção de testes | `test(silver): cobrir caso de timestamp nulo` |
| `chore` | Manutenção (deps, CI, configs) | `chore: bump pm4py para 2.7.11` |
| `ci` | Mudanças em CI/CD | `ci: adicionar smoke test no GitHub Actions` |
| `build` | Mudanças em build/deploy | `build: adicionar target de produção` |
 
### Exemplos completos
 
**Commit simples:**
 
```
feat(pm4py): adicionar Inductive Miner para descoberta de processo
```
 
**Commit com corpo:**
 
```
fix(silver): corrigir ordenação de eventos por case_id
 
A ordenação anterior usava timestamp puro, o que causava inversão de
eventos com mesmo timestamp. Agora aplicamos sort estável por
(case_id, timestamp, sequence_id).
 
Refs: #42
```
 
**Commit com BREAKING CHANGE:**
 
```
feat(gold)!: alterar schema da tabela gold_event_log_xes
 
BREAKING CHANGE: a coluna actor foi renomeada para resource para
aderir ao padrão XES oficial. Dashboards e apps que consomem essa
tabela precisam ser atualizados.
 
Refs: ADR-0004
```
 
### Por que isso importa
 
- **Geração automática de CHANGELOG** a partir do histórico de commits
- **SemVer automático:** `feat` → minor, `fix` → patch, `BREAKING CHANGE` → major
- **Histórico legível** mesmo anos depois
- **Padrão de mercado** reconhecido por recrutadores e times técnicos
---
 
## Fluxo de Pull Request
 
### 1. Antes de começar
 
```bash
# Sincronize com upstream
git checkout main
git fetch upstream
git rebase upstream/main
 
# Crie branch
git checkout -b feat/sua-feature
```
 
### 2. Durante o desenvolvimento
 
- Commits pequenos e atômicos (1 commit = 1 ideia)
- Mensagens seguindo Conventional Commits
- Testes para código novo
- Documentação atualizada (README, ADR, dicionário)
### 3. Antes de abrir o PR
 
```bash
# Rebase com main atualizado
git fetch upstream
git rebase upstream/main
```
 
### 4. Abrindo o PR
 
- Título no formato Conventional Commits
- Descrição clara: **o quê**, **por quê**, **como testar**
- Linke a issue relacionada (`Closes #N`)
- Adicione screenshots quando aplicável (dashboards, diagramas)
- Marque como **Draft** se ainda em desenvolvimento
### 5. Checklist antes do merge
 
- [ ] Código tem testes (quando aplicável)
- [ ] Documentação atualizada
- [ ] CHANGELOG atualizado (se mudança visível ao usuário)
- [ ] ADR criado (se decisão arquitetural)
- [ ] Sem credenciais ou dados sensíveis no código
- [ ] Branch sincronizada com `main`
---
 
## Padrões de Código
 
### Python
 
- **Estilo:** [PEP 8](https://peps.python.org/pep-0008/)
- **Formatador:** [Black](https://black.readthedocs.io/) (será configurado)
- **Linter:** [Ruff](https://docs.astral.sh/ruff/) (será configurado)
- **Type hints:** obrigatórios em funções públicas
- **Docstrings:** padrão [Google Style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- **Tamanho de linha:** 100 caracteres
**Exemplo de função no padrão do projeto:**
 
```python
import polars as pl
 
 
def build_event_log(
    raw_events: pl.DataFrame,
    case_id_col: str = "case_id",
    timestamp_col: str = "timestamp",
) -> pl.DataFrame:
    """Constrói event log canônico no padrão XES.
 
    Args:
        raw_events: DataFrame com eventos brutos.
        case_id_col: Nome da coluna que identifica o caso.
        timestamp_col: Nome da coluna de timestamp.
 
    Returns:
        DataFrame ordenado por (case_id, timestamp), pronto para PM4Py.
 
    Raises:
        ValueError: Se colunas obrigatórias estiverem ausentes.
    """
    # implementação
```
 
### SQL
 
- **CTEs > subqueries** sempre que possível
- **Nomes em snake_case**
- **Colunas explícitas** (nunca `SELECT *` em produção)
- **Comentários** explicando lógica de negócio não óbvia
### Notebooks Databricks
 
- **Markdown no topo** explicando: objetivo, inputs, outputs, dependências
- **Células pequenas e focadas**
- **Sem dados sensíveis em outputs commitados**
---
 
## Documentação
 
Toda mudança de comportamento exige atualização de documentação:
 
| Mudança | Documento a atualizar |
|---|---|
| Decisão arquitetural | Novo ADR em `docs/02-architecture/adr/` |
| Nova tabela | `docs/03-data/data-dictionary.md` |
| Nova regra de qualidade | `docs/03-data/data-quality-rules.md` |
| Novo pipeline | `docs/04-pipelines/` |
| Mudança visível ao usuário | `CHANGELOG.md` |
 
---
 
## Versionamento
 
Adotamos [SemVer 2.0](https://semver.org/lang/pt-BR/):
 
```
MAJOR.MINOR.PATCH
│     │     │
│     │     └─ correções (fix)
│     └─────── novas features compatíveis (feat)
└───────────── breaking changes (BREAKING CHANGE)
```
 
---
 
## Dúvidas
 
- Discussões gerais: [GitHub Discussions](../../discussions)
- Bugs: [Issues](../../issues)
- Contato direto: edy.estatistica@gmail.com
---
 
**Obrigado por contribuir!**
