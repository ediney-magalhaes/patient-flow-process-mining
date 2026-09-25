# ADR-0019: Modelo de referência para Conformance Checking — ano anterior fechado, com fallback incremental

- **Status:** aceito
- **Data:** 2026-09-22
- **Decisores:** Ediney Magalhães

---

## Contexto

O notebook `03_process_mining.ipynb`, na seção de Conformance Checking, originalmente descobria o Process Tree de cada fonte a partir do próprio mês sendo testado, o mesmo log servia de base para o modelo e de log de teste contra esse modelo. Isso produz uma medida válida de o quão bem um modelo *pode* descrever o comportamento observado, mas não uma medida de desvio real: um modelo descoberto a partir do próprio dado testado tende a se ajustar bem a ele quase por definição, mascarando mudanças de processo mês a mês, porque a régua de comparação também muda a cada execução.

O padrão mais correto, alinhado ao que a literatura de Process Mining chama de Conformance Checking no sentido canônico (Van der Aalst): comparar o log observado contra um modelo de referência fixo, análogo ao padrão de champion/challenger já usado em MLOps, um "processo esperado" estável, contra o qual desvios reais podem ser medidos, em vez de um modelo que se redefine a cada execução.

Decisão de negócio: o ano anterior fechado (janeiro a dezembro) foi escolhido como unidade de referência, com uma regra de exceção explícita para quando não existir histórico suficiente. Enquanto o histórico multi-mês do projeto ainda não existir, cada mês de 2026 seria comparado contra si mesmo, e a régua mudaria mês a mês de qualquer forma, a arquitetura precisa suportar essa transição sem intervenção manual.

## Decisão

### Regra de referência

Para processar o mês M do ano Y:

1. Verifica se o ano Y-1 está **inteiro** ingerido (os 12 meses presentes em `gold_event_log`, por fonte).
2. Se sim, usa Y-1 consolidado como referência.
3. Se não (ano anterior parcial ou inexistente), usa **tudo que já foi ingerido antes do mês M** como referência (janela crescente, não um recorte fixo de N meses).
4. Se não existir nenhum dado anterior ao mês M (caso do primeiro mês do projeto), usa o próprio mês M como referência, único caso em que o comportamento é self-referential, e só porque não há alternativa.

Essa regra é permanente, não um bootstrap de uma vez só: a checagem "o ano anterior está fechado?" se repete a cada execução, para qualquer ano.

### Implementação: checagem por fonte, não global

A implementação original calculava a checagem de "existe histórico" uma vez, fora do laço de iteração por fonte (`for source in ...`), usando `gold_event_log` sem filtro de `source`. Isso causou um bug real na primeira execução com dado de produção: fragmentos residuais de contaminação de `ano_mes` (ver ADR-0018) existiam em 3 das 7 fontes, mas a checagem global via essa contaminação como "existe histórico" e aplicava o mesmo `periodo_referencia` (janela incremental) às 7 fontes igualmente, incluindo as 4 fontes que não tinham nenhum fragmento e ficaram com log de referência **vazio**. Descobrir um Process Tree a partir de um `EventLog` vazio produz um modelo degenerado; testar o log real do mês contra esse modelo produziu fitness e precision artificiais (exatamente 1.0 para as fontes com log vazio), mascarados como resultado válido até uma auditoria manual dos números.

Correção: a checagem de referência (contagem de meses do ano anterior, contagem de meses anteriores de qualquer ano, e a decisão de `periodo_referencia`) foi movida para **dentro** do laço `for source in ...`, com `source` incluído em cada consulta SQL. Cada fonte decide sua própria disponibilidade de histórico e sua própria referência, independente das demais.

### Persistência

`gold_conformance` é escrita via `overwrite` com `option("replaceWhere", f"ano_mes = '{mes_atual}'")`, reescreve só a partição do mês corrente a cada execução, preservando meses anteriores já persistidos. Ver detalhamento do mecanismo `replaceWhere` na nota de aprendizado correspondente (`docs/08-learning/`).

## Alternativas consideradas

**Continuar com modelo self-referential (mês testado = mês da Discovery), sem período de referência.** Rejeitada: não distingue "processo mudou" de "modelo mudou porque foi redescoberto", tornando qualquer tendência de fitness/precision ao longo do tempo estatisticamente questionável.

**Janela móvel de 12 meses (sempre os últimos 12 meses antes do mês corrente, não o ano civil fechado).** Rejeitada em favor do ano civil fechado: mais estável (o mesmo modelo serve a todos os meses de um ano corrente, sem redescoberta a cada execução) e mais fácil de comunicar à diretoria ("comparado contra 2026").

## Consequências

- `gold_conformance` agora reflete Conformance Checking no sentido canônico, modelo de referência distinto do log testado, a partir do momento em que existir ao menos um ano civil fechado no histórico; até lá, opera em modo self-referential por necessidade, não por design ideal.
- A regra de referência é reavaliada a cada execução do notebook, sem necessidade de ajuste manual conforme o histórico cresce mês a mês.
- Checagem de disponibilidade de histórico é por fonte, não global, decisão que corrigiu o bug descrito, e que deve ser mantida em qualquer refatoração futura desta lógica.
- Reprocessamento de `gold_event_log` com `ano_mes` de lote correto (ADR-0018) era pré-requisito para este notebook funcionar corretamente, as duas ADRs são interdependentes na prática, ainda que architecturalmente distintas.