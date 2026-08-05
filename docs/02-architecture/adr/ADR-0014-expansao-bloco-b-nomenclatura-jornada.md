# ADR-0014: Expansão de `gold_patient_journey` com Jornadas sem Origem em Emergência (Bloco B) e Nomenclatura de Negócio de `journey_type`

- **Status:** aceito
- **Data:** 2026-08-04
- **Decisores:** Ediney Magalhães
- **Amenda:** ADR-0011 (critério original de classificação de `journey_type`, que cobria apenas jornadas originadas em emergência)

---

## Contexto

`gold_patient_journey` (ADR-0011, expandido pelo ADR-0013) hoje é construído a partir de um único ponto de partida: `df_emerg`, com `LEFT JOIN` contra `df_intern` por `atend_internacao` (curado via BigQuery, conforme ADR-0013). Esse desenho captura corretamente toda jornada que **passa pela emergência**, convertida ou não.

Ele não captura, por construção, internações que **não têm origem em emergência convertida**, pacientes que internam por indicação médica direta, cirurgia eletiva agendada, ou outro fluxo que não passa pelo pronto-socorro. Essas internações existem em `silver_internacoes` mas nunca aparecem em `gold_patient_journey`, porque a tabela nasce de um `LEFT JOIN` partindo do lado da emergência, o que sobra do lado da internação simplesmente não é lido.

O volume real desse grupo ainda não foi medido (estimativa inicial do usuário: abaixo de 1% do total mensal), mas o gap é estrutural, não um caso de borda a ignorar: qualquer jornada que comece por essa porta hoje é invisível ao Dashboard, ao Genie Space e a qualquer análise de Process Mining sobre `gold_patient_journey`.

Adicionalmente, a nomenclatura de `journey_type` usada até aqui (`emergencia_pura`, `emergencia_internacao_clinica`, `emergencia_internacao_cirurgica`, e os nomes mortos no código `internacao_direta_clinica`/`internacao_direta_cirurgica`) reflete vocabulário de engenharia, a lógica do join que originou a classificação, não o vocabulário usado pelo hospital. Como `journey_type` é a coluna que aparece diretamente no Dashboard executivo e alimenta o Genie Space (BI conversacional), esse descompasso de vocabulário é um risco de adoção: quem consome a informação não deveria precisar traduzir mentalmente o rótulo técnico para o termo clínico equivalente.

---

## Decisão

### 1. Estrutura: união de dois blocos

`gold_patient_journey` passa a ser construída em dois blocos, unidos por `UNION`:

- **Bloco A (existente):** `df_emerg` completo -> `LEFT JOIN` com `df_intern` por `atend_internacao` -> jornadas com origem em emergência.
- **Bloco B (novo):** `df_intern` filtrado por `LEFT ANTI JOIN` contra `df_emerg` restrito a `fl_conversao = 1` -> internações sem nenhuma emergência convertida correspondente.

O Bloco B reaproveita integralmente a cadeia de enriquecimento já existente para o Bloco A, agregação de UTI (ORIGEM/DESTINO com prefixos UTIA1/UTIA2/UTIB/UCO/UNP), vínculo com cirurgia via `silver_cirurgias` por `CD_INTERNACAO`, identificação de primeiro leito físico, e cálculo de altas, porque todos esses joins são feitos por `CD_INTERNACAO`, agnósticos à origem da internação. A única lógica nova é a base de partida do Bloco B e a classificação de `journey_type` resultante.

No Bloco B, `CD_ATENDIMENTO` é `NULL` (coerente com o schema existente, que já tolera esse campo nulo em jornadas sem emergência).

`ORIGEM_ATEND` permanece como atributo informativo, nunca decisório: a classificação depende exclusivamente da presença ou ausência de vínculo de conversão (`atend_internacao` casado com `fl_conversao = 1`), não do preenchimento manual desse campo.

### 2. Nomenclatura de `journey_type` — vocabulário de negócio, não de engenharia

Os rótulos de `journey_type` passam a refletir os termos usados no hospital, substituindo os nomes técnicos anteriores:

| `journey_type` (novo) | Origem | Critério |
|---|---|---|
| `atendimento_emergencia` | Bloco A | Passa pela emergência, sem conversão (nem internação, nem cirurgia) |
| `internacao_clinica` | Bloco A | Converteu na emergência (`fl_conversao = 1`), sem cirurgia vinculada |
| `internacao_cirurgica_emergencia` | Bloco A | Converteu na emergência (`fl_conversao = 1`), com cirurgia vinculada |
| `internacao_cirurgica_eletiva` | Bloco B | Sem consulta prévia na emergência, com cirurgia vinculada |
| `cirurgia_ambulatorial` | — (regra já existente) | Cirurgia sem internação vinculada (`LEFT ANTI JOIN` contra `silver_internacoes`) |

Nota de negócio explícita: **não existe, na prática clínica do hospital, internação clínica eletiva** (internação sem cirurgia e sem passagem por emergência). O Bloco B, por construção (`LEFT ANTI JOIN` puro, sem checar cirurgia), é estruturalmente capaz de produzir esse caso caso ele apareça no dado real. Nenhuma regra de tratamento automático foi definida para essa hipótese, qualquer registro fora das cinco categorias acima será investigado e nomeado no momento em que aparecer durante a construção e validação do Bloco B, não tratado retroativamente nem via mecanismo de quarentena automatizado. Essa decisão é deliberadamente escopada ao volume e à maturidade atuais do projeto (uma base de teste, carga mensal manual); se o padrão se tornar recorrente em produção, um ADR específico tratará da automação do tratamento de exceção.

Os nomes mortos `internacao_direta_clinica`/`internacao_direta_cirurgica`, presentes no código-fonte sem nunca terem sido populados, são removidos e substituídos pelos nomes desta tabela.

---

## Alternativas consideradas

**Join invertido (`RIGHT JOIN` ou `FULL OUTER JOIN`) em vez de `UNION` de dois blocos.** Inverter a direção do join original faria `df_emerg_intern` nascer já cobrindo os dois lados, mas exigiria revisar cada `.withColumn()` posterior que assume a existência de `CD_ATENDIMENTO`, incluindo a própria lógica de classificação de `journey_type` e os cálculos de duração, para o caso em que nenhum dos dois lados está preenchido do jeito esperado hoje. Rejeitada por reescrever uma superfície de código maior para o mesmo resultado que o `UNION` de blocos entrega com risco de regressão menor sobre o Bloco A já validado.

**Manter os nomes técnicos de `journey_type`.** Caminho de menor esforço (nomes já existiam, mesmo que mortos, no código). Rejeitada porque o público consumidor de `journey_type` (Diretoria Assistencial via Dashboard, Genie Space) não é o mesmo público que escreve o pipeline, e o vocabulário técnico não é o vocabulário usado no hospital, risco de adoção maior que o custo de renomear.

**Tratamento automatizado de exceção (quarentena ou rótulo `nao_classificado`) para casos fora das cinco categorias.** Avaliado e descartado nesta fase, não há ainda volume de produção real que justifique a automação, e a decisão foi adiar esse mecanismo para quando (e se) o padrão se mostrar recorrente, tratando qualquer ocorrência agora de forma pontual e investigativa.

---

## Consequências

**Positivas:**
- `gold_patient_journey` passa a cobrir 100% das internações do hospital, não apenas as originadas em emergência, fecha um gap estrutural de cobertura que hoje é invisível a qualquer análise downstream.
- `journey_type` passa a ser diretamente legível por stakeholders não técnicos, reduzindo fricção de adoção do Dashboard e do Genie Space.
- Toda a cadeia de enriquecimento (UTI, cirurgia, altas, primeiro leito) é reaproveitada sem duplicação de lógica.

**Negativas / trade-offs:**
- Renomear `journey_type` é uma mudança de schema com efeito cascata: Dashboard (Seções 2–4, já mapeadas como impactadas), Genie Space, e qualquer notebook ou análise de Process Mining que hoje filtra por `journey_type` usando os nomes antigos precisa ser atualizado.
- O caso "clínico eletivo" (teoricamente inexistente) fica sem tratamento automatizado, se aparecer com volume maior que o esperado em produção real, será necessário revisitar esta decisão com um ADR dedicado.
- O volume real do Bloco B ainda não foi validado contra dado, a estimativa de "abaixo de 1%" é uma hipótese do usuário, a confirmar durante a implementação.

**Ação decorrente:** atualizar `docs/03-data/data-dictionary.md` (entrada de `gold_patient_journey`, coluna `journey_type`) e o Dashboard AI/BI (Seções 2–4) após a implementação do Bloco B, antes de fechar a sessão.