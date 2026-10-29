# Validação do dashboard

Cada valor exibido no dashboard é conferido contra uma consulta que não passa pelo dataset do widget. A base é março/2026, o único mês ingerido. Validação iniciada em 20/10/2026.

## Fontes de conferência

- **Cadeia Databricks:** consulta direta às tabelas Silver e Gold, sem o dataset do widget. Detecta perda ou duplicação entre as camadas.
- **Projeto `pipeline-analytics-emergencia` (BigQuery):** trata a base de emergência separadamente. Detecta divergência entre o que o projeto ingeriu e o que o pipeline de emergência conta.

---

## Página 1 — KPIs de Jornada

### Total de Atendimentos (seção Emergência)

- **Valor no cartão:** 6.236
- **Conferência:** `silver_atendimento_emergencia` 6.236, `gold_patient_journey` 6.236, `gold_events_emergencia` 6.236 e BigQuery (competência 2026-03) 6.236.
- **Resultado:** confere.

### Diferença entre a Página 1 (6.236) e a porta Emergência da Página 4 (6.235)

- **Conferência:** a porta Emergência soma `atendimento_emergencia` (5.783), `internacao_clinica` (282) e `internacao_cirurgica_emergencia` (170), total 6.235. A jornada restante é `cirurgia_ambulatorial` (1), que tem `cd_atendimento`.
- **Causa:** a Página 1 conta todo `cd_atendimento` não nulo. A Página 4 exclui `cirurgia_ambulatorial` da porta por desenho.
- **Resultado:** explicada, sem correção.

### Taxa de Conversão (seção Emergência)

- **Valor no cartão:** 7,25%
- **Conferência:** BigQuery (competência 2026-03), 452 convertidos em 6.236 atendimentos, 7,25%.
- **Resultado:** confere.

### Conversão cirúrgica (% dos atendimentos do PA)

- **Valor no cartão:** 2,74%
- **Regra:** `has_cirurgia` é verdadeiro quando existe procedimento principal (`SN_PRINCIPAL = 'SIM'`) com entrada em sala registrada, sem limite de tempo depois da internação. Dois caminhos: cirurgia da internação (`ATENDIMENTO = CD_INTERNACAO`) e cirurgia ambulatorial (mesmo paciente, no dia do atendimento ou no seguinte).
- **Conferência:** Silver, 170 atendimentos convertidos com cirurgia na internação e 1 com cirurgia ambulatorial (não convertido). Total 171 de 6.236, ou 2,74%.
- **Resultado:** confere.
- **Decisão:** regra mantida. A revisão depende da validação com a diretoria.

### Conversão UTI (% dos atendimentos do PA)

- **Valor no cartão:** 2,73% (antes da correção, 2,98%)
- **Regra:** o atendimento internou em UTI quando o primeiro leito real da internação é de UTI, ou quando a própria internação foi registrada em leito de UTI. Unidades virtuais (`OBSERVACAO PA`, `EXTRA INTERNACAO`, `HEMODINAMICA`, `BERCARIO - ALOJAMENTO CONJUNTO`) e registros de `ALTA` não contam como primeiro leito: passar por elas e ser transferido para a UTI conta. Coluna `internou_em_uti` da `gold_patient_journey`.
- **Divergência encontrada:** o cartão media `has_uti`, que é passagem pela UTI em qualquer momento da internação (186 atendimentos, 2,98% em mar/2026). Isso inclui 16 atendimentos cujo primeiro leito real não era de UTI e que passaram por ela depois. Os 170 que internaram em UTI estão todos entre os 186.
- **Conferência:** Silver, 170 atendimentos com a UTI como primeiro leito real. O de internação registrada direto em leito de UTI entra por esta regra, pela movimentação `INTERNACAO`, e o caminho pelo leito da internação não acrescenta casos em mar/2026. Total 170 de 6.236, ou 2,73%.
- **Correção:** coluna nova `internou_em_uti`, campo `Internou Em Uti Numerico` no Data Model e cartão apontado para ele. O `has_uti` foi mantido, porque a Página 4, o cartão "Internações com UTI" e a view `gold_bi_jornada` usam "passou pela UTI".
- **Resultado:** confere depois da correção.

### Tempo até o leito (seção Emergência)

- **Valor no cartão:** mediana de 4,0 h e P90 de 13,4 h, sobre 412 casos (antes, média de 5,97 h).
- **Regra:** tempo entre o registro da internação e o primeiro leito real, dos atendimentos do PA que internaram. Unidades virtuais e registros de `ALTA` não contam como primeiro leito.
- **Conferência:** Silver, consulta independente do dataset do widget. Mediana de 3,95 h (237 min), P90 de 13,37 h e 412 casos.
- **Divergências encontradas:**
  - A média não representava o caso típico: 5,97 h de média contra 3,95 h de mediana e 13,37 h de P90. O padrão passou a ser mediana e P90 (ADR-0023).
  - Um dos 412 casos (e 2 das 732 internações com registro em mar/2026) tinha o primeiro leito anterior ao registro, com tempo negativo. O `ts_primeiro_leito` tomava a menor data entre as movimentações de unidade real sem olhar o tipo, e um registro de `ALTA` com data anterior ao registro da internação virava o primeiro leito. No caso `1631623`: `ALTA` em 23/03 11:12, `INTERNACAO` em 23/03 21:32 (mesmo minuto do registro) e `ALTA` em 27/03 11:12.
  - O cartão lia `gold_patient_journey` sem ligação com o parâmetro `periodo`, então não responderia ao filtro `Período` depois do segundo mês ingerido.
- **Correção:** `df_primeiro_leito` e o primeiro leito de `internou_em_uti` passaram a ignorar `ALTA` (commit `35eaf0c`, com Full Refresh). O caso `1631623` foi de −10,3 h para 0 h, e não restam tempos negativos nas 732 internações. O cartão passou a ler `kpis_jornada_emergencia_cards`, no mesmo formato dos cartões da Página 2: valor `mediana_formatada_leito`, comparação `p90_formatado_leito` e filtro `Período` pelo parâmetro `periodo`.
- **Resultado:** confere depois da correção.