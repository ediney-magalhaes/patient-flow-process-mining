# ADR-0013: Substituição do Linking Algorítmico por `atend_internacao` Curado em `gold_patient_journey`

- **Status:** aceito
- **Data:** 2026-08-04
- **Decisores:** Ediney Magalhães
- **Amenda:** ADR-0012 (escopo de colunas consumidas do BigQuery),
  ADR-0011 (critério de classificação de `journey_type`)

---

## Contexto

O ADR-0012 estabeleceu a integração com a tabela curada do BigQuery
(`atendimentos_pa`), consumindo apenas `fl_conversao` e `fl_evasao`. A
lógica de vínculo físico entre emergência e internação em
`gold_patient_journey` (ADR-0011) permaneceu independente, usando
`CD_PACIENTE` + janela temporal de 1 dia, a mesma aproximação que a
curadoria do outro projeto existe justamente para corrigir.

Na prática, isso mantinha duas fontes de verdade convivendo sem
necessidade: `fl_conversao` (curado) decidindo a métrica de conversão
exibida nos KPIs, e `CD_INTERNACAO IS NOT NULL` (algorítmico, via
`has_internacao`) decidindo a classificação estrutural de `journey_type`.
As duas podem divergir, um paciente pode ter uma internação vinculada
pelo algoritmo por coincidência de janela temporal, sem que a curadoria
considere isso uma conversão real; ou o inverso.

Investigação da tabela curada (`atendimentos_pa`) revelou que ela já
disponibiliza `atend_internacao`, o identificador de internação
correspondente a cada conversão, resolvido pela mesma lógica de curadoria
que produz `fl_conversao`. Essa coluna não estava sendo consumida.

## Decisão

1. **Consumir `atend_internacao`** adicionalmente a `fl_conversao`/
   `fl_evasao` na integração já estabelecida pelo ADR-0012, com o mesmo
   tratamento de hash SHA-256 aplicado a identificadores de atendimento.

2. **Substituir o critério de classificação de `journey_type`**: as
   condições que usavam `CD_INTERNACAO IS NULL`/`IS NOT NULL` passam a
   usar `fl_conversao == 0`/`== 1`. A coluna `has_internacao` é removida,
   sua função é inteiramente absorvida por `fl_conversao`.

3. **Substituir o join emergência↔internação**: de `CD_PACIENTE` +
   janela temporal de 1 dia para join direto por
   `atend_internacao == CD_INTERNACAO`. O join deixa de decidir se houve
   conversão (isso já é resolvido por `fl_conversao`) e passa a ser
   puramente busca de dado de enriquecimento (timestamps, UTI, cirurgia)
   para os atendimentos já sabidamente convertidos.

## Alternativas consideradas

**Manter `has_internacao` e `fl_conversao` como colunas paralelas**
descartada. Definida inicialmente como caminho mais seguro (permitiria
auditar divergência entre as duas fontes), mas rejeitada porque o
objetivo da integração com a curadoria é justamente parar de confiar no
critério algorítmico, não mantê-lo como alternativa. O join por
`CD_PACIENTE` + janela também segue sendo uma fonte legítima de falso
positivo (paciente internado por outro motivo, coincidência temporal),
problema que a curadoria já resolve.

**Manter o join por `CD_PACIENTE` + janela, usando `fl_conversao` apenas
para a métrica dos KPIs** — descartada. Deixaria a classificação de
`journey_type` (usada em Dashboard, Genie Space e Process Mining)
dependente do critério menos confiável, mesmo com o critério correto
disponível e já integrado.

## Consequências

- `has_internacao` removida de `gold_patient_journey` e de
  `gold_bi_jornada` (view) — qualquer consulta ou visual que a referencie
  precisa ser atualizado para usar `fl_conversao`.
- Atendimentos com `fl_conversao = 1` mas sem `atend_internacao`
  preenchida (curadoria confirma conversão sem vincular internação
  física — ~1% dos casos em mar/2026) ficam classificados corretamente
  como convertidos, porém sem os timestamps de internação/UTI/cirurgia
  na jornada. Comportamento esperado, não é falha de join.
- Granularidade de `silver_cirurgias` (1 linha por procedimento) exigia
  filtro por `SN_PRINCIPAL` e desempate adicional para não duplicar
  linhas da jornada quando há múltiplos procedimentos por internação, 
  detalhado em RQ-007 e RQ-008.
- Query do Dashboard (`kpis_jornada`) migrada de
  `SUM(CASE WHEN has_internacao...)` para `SUM(fl_conversao)`.
- Reforça a dependência já registrada no ADR-0012: mudanças na estrutura
  de `atendimentos_pa` (incluindo remoção ou renomeação de
  `atend_internacao`) agora afetam também a classificação estrutural da
  jornada, não só a métrica de conversão exibida.