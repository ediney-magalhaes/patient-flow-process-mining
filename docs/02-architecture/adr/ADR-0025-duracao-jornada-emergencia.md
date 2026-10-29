# ADR-0025: Duração da Jornada Emergência e atendimentos sem alta registrada

- **Status:** aceito
- **Data:** 2026-10-29
- **Decisores:** Ediney Magalhães
- **Relacionado a:** ADR-0021, ADR-0023, ADR-0024, RQ-009

---

## Contexto

O cartão "Tempo Médio da Jornada" da seção Emergência (Página 1 do dashboard) precisa de uma duração por atendimento do pronto-socorro. A coluna `duracao_total_min` de `gold_patient_journey` mede a jornada inteira e, para quem internou, vai até a alta da internação, que pertence à jornada da seção Internação.

A Jornada Emergência é definida como **a chegada ao pronto-socorro até a alta da emergência**, para todos os atendimentos do PA, inclusive os que internaram.

Com a mart curada como fonte (ADR-0024), todos os atendimentos de mar/2026 têm horário de chegada. Restam **643 sem `DT_HR_ALTA`**, todos com `MOTIVO_ALTA` igual a `NÃO INFORMADO`:

| Grupo | Casos | Horário médico registrado |
|---|---|---|
| Não convertidos, não evadidos | 639 | 315 com fim, 12 só com início, 312 sem nenhum |
| Convertidos | 4 | nenhum |

## Decisão

1. **Fim da emergência, por prioridade:**

| Prioridade | Fim usado | `origem_fim_emergencia` |
|---|---|---|
| 1 | `DT_HR_ALTA` (alta da emergência) | `alta` |
| 2 | abertura da internação, para o convertido sem alta, quando há internação vinculada | `internacao` |
| 3 | nenhum: a duração fica nula | `sem_alta_registrada` |

2. **Colunas novas em `gold_patient_journey`:** `ts_alta_emergencia` (hoje existe só no intermediário), `duracao_emergencia_min` e `origem_fim_emergencia`. `duracao_emergencia_min` é `fim - ts_chegada`, em minutos. `duracao_total_min` não muda.
3. **Visibilidade.** Atendimentos sem alta registrada não são excluídos em silêncio. A coluna `origem_fim_emergencia` os identifica, e o cartão mostra quantos casos ficaram nessa situação ao lado da mediana e do P90.
4. **Estatística.** O cartão usa mediana e P90 (ADR-0023), calculados sobre as linhas de jornada no grão do filtro (ADR-0021), apenas dos casos com duração.

## Alternativas consideradas

**Usar o último horário registrado no PA como fim.** Rejeitada: o resultado é um mínimo, e não a permanência. Em cerca de 82% dos casos o projeto de conversão observa `DT_HR_ALTA` antes de `FIM_ATD_MEDICO`, então o fim do atendimento médico superestimaria a alta. Nos 312 atendimentos sem nenhum horário médico, o último registro pode ser a própria chegada, e a duração sairia zero. Nenhuma referência consultada adota essa prática.

**Imputar o horário de alta por modelo estocástico do processo** (Rogge-Solti, Mans, van der Aalst e Weske, 2013). Rejeitada: o método pressupõe que o dado falte ao acaso e exige um modelo do processo. Nos 643 casos, nenhum tem desfecho informado, o que não permite sustentar essa premissa.

**Excluir os casos sem alta sem sinalizar.** Rejeitada: o cartão passaria a descrever apenas os atendimentos com alta, sem informar a proporção que ficou de fora.

## Consequências

- A duração da emergência é a mesma convenção do projeto de conversão, onde `minutos_permanencia_total` é nulo quando não há alta. A medida de referência do CMS (mediana de chegada a saída) também define a duração como saída menos chegada.
- Em mar/2026, 639 atendimentos ficam sem duração (`sem_alta_registrada`), e os 4 convertidos usam a abertura da internação quando há internação vinculada.
- A proporção de `sem_alta_registrada` passa a ser indicador de qualidade do registro e entra na conferência mensal de ingestão.
- O cartão da seção Internação não é afetado: a alta da internação segue na jornada dela.