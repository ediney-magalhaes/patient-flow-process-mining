# ADR-0018: Origem de `ano_mes` migrada do timestamp de evento para o nome do arquivo de origem

- **Status:** aceito
- **Data:** 2026-09-15
- **Decisores:** Ediney Magalhães
- **Última atualização:** 2026-09-22 (propagação da coluna de lote até `gold_event_log` implementada, a pendência descrita originalmente na seção Consequências está resolvida)

---

## Contexto

Ao investigar por que o filtro de Período da Página 3 (Conformidade) do Dashboard oferecia meses além de março/2026, a causa raiz revelou um problema estrutural na origem da coluna `ano_mes` em `gold_event_log`.

Hoje, `ano_mes` em cada tabela `gold_events_*` é calculado como `F.date_format(F.col("timestamp"), "yyyy-MM")`, o mês do timestamp de cada evento individual, não um mês de referência único por caso ou por lote de ingestão. Como um mesmo caso clínico gera múltiplos eventos ao longo do tempo (ex: `Agendamento de Cirurgia` registrado semanas antes da internação em si), consultar `distinct ano_mes` em `gold_event_log` retornou fragmentos de outros meses (`2025-12`, `2026-01`, `2026-02`, `2026-04`) e um volume expressivo de `null` (23.334 linhas em `exames_imagem`, já rastreado à causa raiz confirmada em RQ-004), mesmo com um único mês de dado real ingerido. Nenhum desses fragmentos representa uma ingestão real — são eventos pontuais de casos de março cujo timestamp específico caiu fora da fronteira do mês.

Investigação confirmou que `gold_patient_journey.ano_mes` não sofre do mesmo problema, é 1 valor fixo por caso completo (hoje derivado de `DT_ATENDIMENTO`, correção de RQ-009), não por evento. A pergunta que `gold_event_log.ano_mes` deveria responder ("a que lote de ingestão esse dado pertence") é estruturalmente diferente da pergunta que ele responde hoje ("em que mês esse evento específico aconteceu").

Verificação de alternativas de origem para um "mês de referência do lote" confirmado por dado real:

- **`_source_file`** (metadado de ingestão, já existente em toda tabela Bronze): já carrega o padrão `nome_AAAA_MM.extensão` em um caso isolado (`atendimento_2026_03.xlsx`), mas não nas outras 8 bases — não é uma convenção consistente hoje, foi acidental (renomeação manual durante integração com o projeto BigQuery).
- **Campo de data dentro do dado bruto** (ex: `DT_ALTA_FINAL` em `altas`): testado com zero nulos na base de altas, mas rejeitado como estratégia geral, não há garantia de que o mesmo padrão se sustente nas outras 8 bases ou em meses futuros, e alguns campos candidatos já têm viés de cobertura conhecido e documentado (ex: mesmo `DT_ALTA_FINAL`, ~17% de exclusão em internações sem alta lançada, registrado na Página 1 do Dashboard).
- **Parâmetro manual na execução do script** (`--ano-mes` como argumento de linha de comando): rejeitado, o projeto não prevê execução manual assistida por humano na operação real; a ingestão mensal precisa funcionar sem intervenção de alguém digitando um valor a cada execução.
- **Cálculo automático pela data do sistema no momento da execução** (ex: "mês anterior ao mês de execução"): não escolhida, depende de uma suposição implícita sobre quando o script roda em relação ao mês que representa, que pode não se sustentar sempre.

## Decisão

O nome do arquivo de entrada passa a ser a fonte oficial e obrigatória do período de referência, seguindo o padrão `nome-base_AAAA_MM.extensão` para as 9 bases (incluindo as duas com pré-processamento próprio, `exames_laboratoriais_limpo` e `movimentacoes_limpo`), sem exceção.

Em `src/anonymization/processor.py`, `anonymize_file` extrai `ano_mes` do `filepath` via regex (`r"(\d{4})_(\d{2})"`), falhando explicitamente (`ValueError`) se o padrão não for encontrado, falha visível, não mascarada, mesmo princípio já adotado em RQ-009. O valor extraído é gravado como coluna `ano_mes` no DataFrame, antes de `drop_columns` (para não correr risco de ser descartada por config futura), e também incorporado ao nome do arquivo de saída (`nome-base_AAAA_MM_anonimizado.csv`), mantendo rastreabilidade visual no Volume além da coluna em si.

Em `src/anonymization/run.py`, a busca de configuração por nome de arquivo (`find_config`) passou a separar o sufixo de período do nome-base antes de comparar contra `ANONYMIZATION_CONFIGS` (via `re.match(r"^(.+)_\d{4}_\d{2}$", ...)`), as 10 configs continuam com `name` fixo, sem data, evitando que precisem ser editadas a cada mês.

### Propagação até `gold_event_log` (implementada em 22/09/2026)

A coluna de lote chega íntegra até a Silver desde a implementação original desta ADR, mas as 7 funções `gold_events_*` em `gold_transformation.py` continuavam recalculando `ano_mes` por timestamp de evento (`F.date_format(F.col("timestamp"), "yyyy-MM")`), ignorando a coluna de lote já disponível em `df` desde a leitura da Silver. Isso não era um risco teórico: a contaminação por fragmento de mês, sem correção, causou um bug real na Página 3 do Dashboard (ver ADR-0019) — a lógica de determinação de período de referência do notebook de Conformance usava `distinct ano_mes` sobre `gold_event_log` para decidir se existia histórico disponível, e os fragmentos residuais dessa contaminação foram lidos como se fossem meses de ingestão reais.

Correção aplicada nas 7 funções: a coluna `ano_mes` de `df` (lida da Silver) passa a ser preservada nos `.select(...)` intermediários de cada sub-DataFrame de evento, e a linha que recalculava por `F.date_format` foi removida. `gold_events_movimentacoes` (única função sem `.select()` intermediário nem `unionByName`) teve só a linha de recálculo removida. `gold_patient_journey` não foi tocada — seu `ano_mes` já é derivado por caso via `DT_ATENDIMENTO` (RQ-009), não sofre desta limitação.

Reprocessamento completo exigido após a correção: `gold_transformations` (Full Refresh) e, em seguida, o notebook `03_process_mining.ipynb` (que lê `gold_event_log` para uma variável em memória, `event_log`, que não se atualiza sozinha quando a tabela muda no Unity Catalog).

## Alternativas consideradas

Ver as quatro alternativas descartadas na seção Contexto, com a justificativa de rejeição de cada uma.

## Consequências

- Os 9 arquivos brutos de março/2026 precisaram ser renomeados manualmente (`nome_2026_03.extensão`) antes do reprocessamento.
- `data/anonymized` precisou ser limpa e regenerada, nomes de saída antigos (sem período) não coincidem com os novos, os dois conjuntos coexistiriam sem sobrescrita automática.
- Reingestão completa exigida: tabelas Bronze dropadas, checkpoints do Auto Loader limpos (Auto Loader rastreia por caminho de arquivo, um arquivo com nome novo não é reconhecido como "já processado", mas também não substitui a linha antiga automaticamente; sem dropar a tabela, o resultado seria duplicação de volume, não correção).
- Toda ingestão mensal futura depende, a partir de agora, do nome do arquivo seguir o padrão exato, se um arquivo for renomeado sem esse sufixo, ou o padrão mudar sem atualizar o regex de extração, a anonimização falha explicitamente (por design), não silenciosamente.
- `gold_event_log.ano_mes` agora reflete o mês do lote de ingestão em todas as 7 fontes `gold_events_*`, íntegro, sem fragmentos residuais de outros meses, confirmado por consulta direta pós-correção (`select ano_mes, count(*) from gold_event_log group by ano_mes` retornando uma única linha, `2026-03`).