# ADR-0011: Design da gold_patient_journey — Jornada Cross-Source do Paciente

## Status

Aceito

## Contexto

O projeto possui sete fontes Silver de eventos, divididas em duas famílias de
identificador de episódio: `CD_ATENDIMENTO` (emergência, exames, cirurgias
ambulatoriais e altas de emergência) e `CD_INTERNACAO` (internações,
movimentações e altas de internação). Nenhuma das cinco tabelas Gold do Sprint 3
modela a jornada completa do paciente atravessando essas duas famílias, todas
operam dentro de uma única fonte. O Sprint 4 exige uma visão macro do episódio
completo para alimentar o dashboard executivo e o app interativo.

## Decisão

Criar a tabela `hospital_santa_rosa.gold_fluxo.gold_patient_journey` como uma
tabela wide com uma linha por episódio completo, cobrindo os seguintes tipos de
jornada:

- `emergencia_pura`: atendimento de emergência sem internação ou cirurgia
- `emergencia_cirurgia_ambulatorial`: emergência com procedimento cirúrgico sem internação
- `emergencia_internacao_clinica`: emergência que converte em internação sem cirurgia
- `emergencia_internacao_cirurgica`: emergência que converte em internação com cirurgia
- `internacao_direta_clinica`: internação eletiva sem cirurgia
- `internacao_direta_cirurgica`: internação eletiva com cirurgia

### Estratégia de junção entre famílias

A ligação entre `CD_ATENDIMENTO` e `CD_INTERNACAO` é feita via `COD_PACIENTE`
(identificador único e estável do cadastro do paciente no HIS, consistente entre
todos os módulos após anonimização SHA-256) combinado com janela temporal de 1
dia, internação deve ocorrer entre a data do atendimento de emergência e a data
seguinte. O campo `ORIGEM_ATEND` de `silver_internacoes` foi avaliado como
alternativa mas descartado como critério de join por ter falhas conhecidas de
input manual sem processo de curadoria equivalente ao existente no projeto
BigQuery. O campo é mantido na tabela como atributo informativo.

### Separação de cirurgias por tipo

Cirurgias de internação e ambulatoriais são distinguidas pela presença de
`CD_INTERNACAO` correspondente em `silver_internacoes`, não pelo campo
`TIPO_ATENDIMENTO` nem por `ORIGEM_ATENDIMENTO`, ambos com baixa confiabilidade
por dependência de input manual. Cirurgias com internação são joinadas por
`CD_INTERNACAO`. Cirurgias ambulatoriais de emergência são identificadas por
anti join com `silver_internacoes` e linkadas à emergência via `CD_PACIENTE` +
janela temporal de 1 dia usando `DATA_INICIO_CIRURGIA` como âncora temporal.

### Métricas de UTI

Passagens pela UTI são identificadas via colunas `ORIGEM` e `DESTINO` de
`silver_movimentacoes`, usando prefixos de leito (`UTIA1`, `UTIA2`, `UTIB`,
`UCO`, `UNP`). Transferências entre unidades intensivas são tratadas como
continuação da mesma passagem. A tabela armazena métricas agregadas por episódio:
`ts_primeira_entrada_uti`, `ts_ultima_saida_uti`, `qtd_passagens_uti` e
`duracao_total_uti_min`. Timestamps individuais de cada movimento estão
disponíveis no `gold_event_log` via `silver_movimentacoes`.

### Primeiro leito físico

O timestamp `ts_primeiro_leito` exclui movimentações para unidades consideradas
leitos virtuais: `BERCARIO - ALOJAMENTO CONJUNTO`, `HEMODINAMICA`,
`OBSERVACAO PA` e `EXTRA INTERNACAO`. A exclusão é feita pela coluna `UNIDADE`
(não por prefixo de leito) por ser mais estável diante de criação de novos
leitos no HIS.

## Alternativas consideradas

**Junção por `ORIGEM_ATEND`:** descartada por falhas de input manual sem curadoria.

**Junção por `TIPO_ATENDIMENTO` em cirurgias:** descartada pelo mesmo motivo.

**Tabela no formato longo (uma linha por evento):** o `gold_event_log` já cumpre
esse papel. A `gold_patient_journey` é complementar, no formato wide, para
alimentar KPIs executivos sem reprocessamento de eventos.

**Processamento incremental via `dlt.read_stream()`:** avaliado e deferido para
sprint futuro. O volume atual (~6.5K registros/mês) torna o reprocessamento
full viável em cada execução.

## Consequências

- A tabela é recalculada integralmente a cada execução do pipeline
  `gold_transformations`, cobrindo automaticamente novos meses à medida que
  o histórico é carregado
- `ORIGEM_ATEND` permanece na tabela como atributo informativo com ressalva de
  qualidade documentada em `data-quality-rules.md`
- Cirurgias ambulatoriais sem correspondência em `silver_atendimento_emergencia`
  (ex: ambulatório eletivo puro) não aparecem na tabela — estão fora do escopo
  do projeto


---

## Emenda (06/10/2026)

Quatro pontos deste ADR foram superados pelo Sprint 4. A decisão de criar uma tabela wide com uma linha por episódio **continua válida**.

1. **Tipos de jornada.** Os seis `journey_type` listados na Decisão (`emergencia_pura`, `internacao_direta_clinica` etc.) foram substituídos pelo vocabulário de negócio do ADR-0014: `atendimento_emergencia`, `internacao_clinica`, `internacao_cirurgica_emergencia`, `internacao_cirurgica_eletiva`, `internacao_clinica_direta` e `cirurgia_ambulatorial`. O ADR-0014 também acrescentou o Bloco B (internações sem emergência convertida), que este ADR não cobria.
2. **Estratégia de junção.** A junção emergência → internação por `COD_PACIENTE` com janela de 1 dia foi substituída pela junção direta `atend_internacao == CD_INTERNACAO`, com a conversão curada no BigQuery (ver ADR-0013 e a atualização de 04/08/2026 na RQ-006). `ORIGEM_ATEND` continua só como atributo informativo.
3. **Métricas de UTI.** Este ADR diz que transferências entre unidades intensivas são tratadas como continuação da mesma passagem, mas o código não fazia isso: cada destino em UTI contava como passagem, e os pares `TRANSFER. DE` e `TRANSFER. PARA` contavam em dobro. A regra descrita aqui passou a valer de fato em 29/09/2026 (RQ-017), e a tabela ganhou a coluna `qtd_reentradas_uti`.
4. **Identificadores.** A menção a "hash SHA-256" para `CD_ATENDIMENTO` e `CD_INTERNACAO` deixou de valer com a ADR-0017: números de atendimento não são mais hasheados.

Chave de caso: `gold_patient_journey` é a base de `case_id_jornada`, que as análises de gargalo, performance e handover usam desde a RQ-016.