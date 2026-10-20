# ADR-0021: Variantes por jornada com tabela por jornada (`gold_variant_jornada`) e `activity_unidade` no event log

- **Status:** aceito
- **Data:** 2026-10-14
- **Decisores:** Ediney Magalhães
- **Relacionado a:** ADR-0014, ADR-0018, ADR-0020, RQ-016, RQ-019, RQ-020

---

## Contexto

A Página 5 do Dashboard (Variantes) foi construída sobre `gold_variant_analysis`, calculada por `case_id`. Ao olhar as maiores variantes, três problemas apareceram (RQ-019): fragmentos de uma fonte no topo do ranking, exames de pacientes externos e repetições de exame multiplicando caminhos.

Depois de corrigi-los, a análise de process mining pediu mais três coisas: tempo por caminho, caminhos raros e lentos, e filtro por especialidade. Cada uma criou uma decisão:

1. **Tempo não se agrega.** Mediana e P90 não se somam. Os datasets do dashboard somam linhas quando o usuário filtra por tipo ou especialidade, e uma mediana de medianas é um número errado, sem aviso.
2. **Nome da movimentação com o leito.** `INTERNACAO: Externo → EXENF02` e `INTERNACAO: Externo → EXENF04` contavam como etapas distintas, e jornadas clinicamente iguais viravam caminhos diferentes (RQ-020).
3. **Especialidade da jornada.** A especialidade é atributo de cada evento, e uma jornada passa por várias. Para filtrar variantes, cada jornada precisa de uma só.

## Decisão

### 1. Tabela por jornada como base única

Cria-se `gold_variant_jornada`, com **uma linha por jornada**: `case_id_jornada`, `ano_mes`, `journey_type`, `especialidade`, `sequencia`, `total_eventos` e `duracao_total_min`. O dashboard calcula mediana e P90 na hora, sobre o filtro escolhido. `gold_variant_analysis` é gravada **a partir da mesma base, na mesma célula** do notebook, para as duas nunca divergirem.

### 2. `activity_unidade` no event log (opção C)

`gold_event_log` ganha a coluna `activity_unidade`, com a unidade no lugar do leito nas movimentações. `activity` não muda. Nas outras seis fontes, `activity_unidade` é igual a `activity`. As variantes usam `activity_unidade`.

O mapa leito para unidade é calculado **por mês de lote** (`ano_mes` + leito), porque um leito pode mudar de unidade entre anos. A unidade `GINECOLOGIA/OBSTETRICIA` (nome usado antes de 2025) é unificada em `TERREO`.

### 3. Especialidade da jornada

| Tipo de jornada | Especialidade |
|---|---|
| `atendimento_emergencia` | a da emergência |
| `internacao_cirurgica_emergencia`, `internacao_cirurgica_eletiva`, `cirurgia_ambulatorial` | a da cirurgia |
| `internacao_clinica`, `internacao_clinica_direta` | a da alta (`DS_ESPECIALID`); sem alta, a da internação |

Sem nenhuma, vale a primeira especialidade preenchida nos eventos da jornada e, por fim, "Sem especialidade". A regra para internação clínica foi definida por Ediney: a alta define o "dono" do paciente internado.

### 4. Duração ausente

Jornadas sem `duracao_total_min` ficam com o valor nulo, e a mediana e o P90 as ignoram. A tabela dos caminhos mostra quantas jornadas entraram na conta. A revisão das causas está no checklist de ingestão.

## Alternativas consideradas

**Guardar mediana e P90 em `gold_variant_analysis`.** Rejeitada: não se recompõem ao filtrar, e o número sairia errado sem aviso.

**Guardar só a duração média por variante.** Rejeitada: a média é distorcida por poucos casos longos (na internação clínica, P90 de 170 h contra mediana de 61 h) e perde o P90.

**Trocar o leito pela unidade na origem (`activity`).** Rejeitada: perde o leito no event log, altera resultados já publicados (Páginas 2 e 3) e obriga a regravar todas as tabelas do notebook.

**Trocar só no cálculo de variantes, lendo o texto no pandas.** Rejeitada: frágil com mais leitos, e cria dois vocabulários sem lineage.

**Mapa leito-unidade global, sem o mês.** Rejeitada: com o histórico, um leito pode mudar de unidade, e um `max` arbitrário erraria sem avisar.

## Consequências

- Uma lógica de variante só, com duas tabelas que não divergem.
- A mediana e o P90 corretos para qualquer combinação de filtros do dashboard.
- Variantes distintas em mar/2026: de 1.525 para 1.328. A queda foi menor que a esperada, porque boa parte da pulverização vem da combinação de exames.
- O leito continua no `gold_event_log` (`activity`), disponível para o Databricks App.
- `gold_event_log` ganha uma coluna, e o pipeline `gold_transformations` exige Full Refresh.
- A regra de especialidade vive no notebook e depende de `gold_patient_journey` e de `silver_altas`. As jornadas sem correspondência em `gold_patient_journey` (231 em mar/2026) usam o fallback pelos eventos.
- Com o histórico, o mapa leito-unidade e os nomes de unidade por ano precisam ser reconferidos (checklist de ingestão).
- A conformidade por variante depende do histórico e está no checklist de ingestão.