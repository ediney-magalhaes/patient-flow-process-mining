# ADR-0024: Fonte da emergência é a mart curada do projeto de conversão

- **Status:** aceito
- **Data:** 2026-10-29
- **Decisores:** Ediney Magalhães
- **Relacionado a:** ADR-0012, ADR-0017, ADR-0018, RQ-009

---

## Contexto

Até aqui, a base de emergência do Databricks vinha do export mensal bruto do sistema hospitalar. O `enrichment.py` acrescentava a esse export quatro colunas curadas do projeto `pipeline-analytics-emergencia` (BigQuery): `atend_PA`, `atend_internacao`, `fl_conversao` e `fl_evasao`.

Os dois projetos partem do mesmo export, mas só o do BigQuery passa pelo tratamento de qualidade: `stg_atendimentos` exige `DT_HR_TOTEM_RECEP` não nulo, e a curadoria corrige horários, idade e demais campos antes da `marts.atendimentos_pa`. Em mar/2026, a consequência foi:

| Medida | Export bruto (Databricks) | Mart (BigQuery) |
|---|---|---|
| Atendimentos | 6.236 | 6.236 |
| Sem horário de chegada (`DT_HR_TOTEM_RECEP`) | 397 | 0 |
| Sem horário de alta (`DT_HR_ALTA`) | 639 | 643 |

Sem a chegada não há duração da jornada da emergência. Manter duas versões do mesmo atendimento, uma tratada e outra não, produz números diferentes entre os projetos para a mesma pergunta (RQ-009).

## Decisão

1. **Fonte única.** A emergência do Databricks passa a ser a tabela `pipeline-analytics-emergencia.marts.atendimentos_pa`, inteira, uma competência por arquivo. O export bruto de emergência deixa de ser importado.
2. **Extração local.** O `enrichment.py` deixa de enriquecer: passa a consultar a mart por competência, sem `merge` com outro arquivo. A anonimização e o upload continuam locais, antes de qualquer dado chegar ao Databricks.
3. **Anonimização.** Valem as regras atuais da configuração `atendimento_emergencia`: hash SHA-256 em `PRESTADOR` e descarte de `CEP`, `CIDADE` e `UF`. A mart não traz nome, endereço nem data de nascimento.
4. **Arquivo e Bronze.** O arquivo segue o padrão `atendimento_emergencia_AAAA_MM`. A Bronze lê o que a mart entrega, sem schema fixo (Auto Loader com `schemaLocation` e `mergeSchema`), e nada muda na ingestão.
5. **Silver e Gold.** Ajustes mínimos, sem lógica nova:

| Camada | Ajuste | Motivo |
|---|---|---|
| Silver | `atend_PA` renomeada para `CD_ATENDIMENTO` | a mart usa outro nome para a mesma chave |
| Silver | removidas as referências a `EMPRESA`, `COD_TRIAGEM`, `REGISTRO_ANS`, `DT_HR_TRANF_LEITO` e `DT_HR_SAIDA_LEITO` | colunas que a mart não entrega; o filtro `HSR` já é feito na ingestão do projeto de conversão |
| Silver | `IDADE` deixa de ser descartada | a Gold passa a usar a idade da mart, já corrigida pela curadoria |
| Gold | `IDADE` no lugar de `IDADE_CALCULADA` na tabela de features | a mart traz a idade já corrigida pela curadoria |
| Gold | `location` nulo nos eventos de emergência | `LOCAL_PROCED` não vem na mart (ver Alternativas) |

6. **Reingestão de março.** O Auto Loader não relê arquivo já registrado, e linhas novas somadas às antigas duplicariam o mês na Bronze. O procedimento é apagar o arquivo antigo do Volume, recriar `bronze_atendimento_emergencia_raw` com o checkpoint dela, subir o arquivo novo e executar Full Refresh em `silver_transformations` e `gold_transformations`.

## Alternativas consideradas

**Manter o export bruto e trazer mais colunas curadas.** Rejeitada: replica, coluna a coluna, regras de curadoria que já existem no outro projeto, e as duas bases continuam divergindo onde a cópia não alcança.

**Reproduzir no Databricks o tratamento de chegada ausente.** Rejeitada: duplica lógica de outro projeto e abre uma segunda fonte de verdade para o mesmo campo.

**Ler as camadas anteriores à mart (`raw` ou `staging`).** Rejeitada: elas não trazem as correções da curadoria, que são aplicadas na `int_curadoria_correcoes` e consumidas pela mart.

**Incluir `LOCAL_PROCED` no `stg_atendimentos` do projeto de conversão.** Rejeitada: o campo indica a procedência do paciente, e não onde o evento ocorreu. Em mar/2026, 99,4% dos registros são `PRONTO ATENDIMENTO`, e os 0,6% restantes (ambulatório, consultório, domicílio, laboratório, imagem, UTI, via urbana) não sustentam nenhuma análise da jornada. Alterar o outro projeto por esse campo não se justifica.

## Consequências

- Os dois projetos passam a contar os mesmos atendimentos com os mesmos horários de chegada: em mar/2026, 6.236 atendimentos e nenhum sem chegada.
- A emergência de uma competência só sobe ao Databricks depois que a mart do mês estiver carregada e curada no projeto de conversão.
- Atendimentos sem alta registrada na mart (643 em mar/2026) continuam sem duração da jornada da emergência.
- `location` fica nulo na emergência, como já descreve `docs/05-process-mining/event-log.md`.
- `IDADE` passa a refletir a curadoria, e não o cálculo a partir da data de nascimento.
- `atend_internacao`, `fl_conversao` e `fl_evasao` continuam vindo da mart, como antes; deixam de ser colunas acrescentadas ao export e passam a ser colunas da própria fonte.
- As demais bases (internações, movimentações, cirurgias, altas, exames, epidemiologia) não mudam.
- A conferência mensal contra o BigQuery (atendimentos e nulos de chegada por competência) entra no checklist de ingestão.