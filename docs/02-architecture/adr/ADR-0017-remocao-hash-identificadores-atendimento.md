# ADR-0017: Remoção de hash em identificadores de atendimento nas configs de anonimização

- **Status:** aceito
- **Data:** 2026-09-15
- **Decisores:** Ediney Magalhães

---

## Contexto

O número de atendimento (`CD_ATENDIMENTO`, `ATENDIMENTO`, `ATEND`, ou variantes por base, ver lista completa em Decisão) estava listado em `hash_columns` em praticamente todas as 10 configs de `src/anonymization/config.py`, sendo pseudonimizado via SHA-256 antes do upload para o Databricks, junto com os demais identificadores diretos de PII (nome, CPF, endereço).

Essa decisão criou um problema prático real: o número de atendimento é a chave primária operacional do hospital, usada para reaproveitamento entre projetos que já consomem os mesmos dados brutos do sistema hospitalar (HIS), incluindo o projeto de análise de conversão de emergência (`pipeline-analytics-emergencia`, BigQuery) já integrado a este projeto via `enrichment.py`. Hashear o número de atendimento localmente, com um salt específico deste projeto, produz um valor que não bate com o mesmo número de atendimento hasheado (ou em texto puro) em qualquer outro contexto — inviabilizando join direto entre bases que deveriam ser cruzáveis pela mesma chave de negócio.

O enriquecimento com `fl_conversao`/`fl_evasao` (curados no BigQuery) já contornava esse problema de um jeito específico: o `merge` acontecia usando `CD_ATENDIMENTO` em texto puro, **antes** do hash ser aplicado, dentro da própria função `anonymize_file`. Essa solução resolve o caso de uso já implementado, mas não resolve reaproveitamentos futuros — qualquer novo projeto que precise cruzar dados por número de atendimento exigiria a mesma solução pontual, replicada, com salt específico de cada join possível.

## Decisão

O número de atendimento deixa de ser hasheado em todas as 10 configs de anonimização, removido de `hash_columns` em:

| Config | Coluna removida |
|---|---|
| `atendimento_emergencia` | `CD_ATENDIMENTO` |
| `internacoes` | `ATENDIMENTO` |
| `movimentacoes` | `Atend.` |
| `cirurgias` | `ATENDIMENTO` |
| `exames_imagem` | `CD_ATENDIMENTO`, `NUMERO_ATENDIMENTO` |
| `atendimentos_box` | `CD_ATENDIMENTO` |
| `altas` | `ATENDIMENTO` |
| `epidemio` | `atendimento` |
| `exames_laboratoriais_limpo` | `ATEND` |
| `movimentacoes_limpo` | `ATEND` |

O número de atendimento passa a ser tratado como identificador operacional, não como PII direta, decisão consciente de que ele não identifica uma pessoa por si só (diferente de nome, CPF, endereço), mas sim um episódio de atendimento, análogo a um número de pedido ou protocolo. O risco de reidentificação através dele, cruzar de volta com o HIS ao vivo para localizar o paciente, é aceito como parte do modelo de ameaça do projeto, dado que o acesso ao Databricks já é restrito à equipe interna do hospital com acesso equivalente (ou maior) ao próprio HIS.

`atend_internacao` (coluna calculada em `atendimento_emergencia`, cópia hasheada de `CD_ATENDIMENTO` usada para bater com `CD_INTERNACAO` no join de `gold_patient_journey`) fica pendente de revisão em cascata, deixou de ter razão de ser hasheada, tratado como item separado.

## Alternativas consideradas

**Manter o hash e resolver o join via campo intermediário dedicado** (como já era feito para `atend_internacao`). Rejeitada como padrão geral: exigiria replicar essa solução pontual para cada novo cruzamento entre projetos que surgir no futuro, com salt específico de cada par de tabelas.

**Hash determinístico compartilhado entre projetos** (mesmo salt em todos os projetos do hospital que usam este HIS). Não avaliada a fundo nesta sessão, resolveria o reaproveitamento sem expor o número em texto puro, mas introduz gestão de segredo compartilhado entre projetos como novo risco operacional. Fica como alternativa a reconsiderar se o modelo de ameaça mudar.

## Consequências

- Os 9 arquivos de março/2026 precisaram ser reprocessados do zero (reingestão completa: Bronze dropada e recriada, checkpoints do Auto Loader limpos, novo upload).
- `atend_internacao` precisa de revisão em `gold_transformation.py`, pendência registrada, não resolvida por esta ADR.
- Reaproveitamento futuro do número de atendimento por outros projetos do hospital passa a ser direto, sem necessidade de solução pontual de join por projeto.