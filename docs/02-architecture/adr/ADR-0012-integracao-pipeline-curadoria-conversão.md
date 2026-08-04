# ADR-0012: Integração com Pipeline de Curadoria de Conversão (BigQuery) como Fonte de Verdade

- **Status:** aceito
- **Data:** 2026-07-30
- **Decisores:** Ediney Magalhães
- **Superado parcialmente por:** ADR-0013 (2026-08-04) — escopo de colunas
  consumidas e lógica de linking revisados

---

## Contexto

O projeto mantém, em paralelo, um segundo pipeline (`pipeline-analytics-emergencia`,
BigQuery + dbt) dedicado especificamente ao monitoramento de conversão de
atendimentos de emergência em internação. Esse pipeline conta com uma camada
de curadoria humana — uma assistente administrativa revisa mensalmente os
casos que a lógica automática de vínculo não resolve com confiança (`fl_suspeito_conversao`),
produzindo um resultado de conversão mais fiel do que qualquer cálculo
puramente algorítmico.

A `gold_patient_journey`, deste projeto, também precisa expor uma taxa de
conversão como parte dos KPIs de jornada. Calculá-la de forma independente,
sem a mesma curadoria, criaria duas versões divergentes da mesma métrica de
negócio expostas em dois dashboards diferentes para a mesma diretoria —
problema de governança de dado (métrica não conformada, no sentido Kimball),
não apenas de precisão técnica.

O processo de curadoria roda inteiramente dentro do outro projeto, operado
por uma pessoa não técnica. Qualquer integração entre os dois projetos precisa
preservar essa restrição: nenhum passo manual, técnico ou de join pode ser
exigido dela ou de qualquer outra pessoa como parte do ciclo recorrente.

## Decisão

Consumir, do resultado final e já curado do outro projeto
(`pipeline-analytics-emergencia.marts.atendimentos_pa`), apenas as colunas
`fl_conversao` e `fl_evasao` — os desfechos de negócio já reconciliados pela
curadoria. `fl_suspeito_conversao` fica de fora por ser um artefato de
processo interno daquele pipeline (sinaliza um caso ainda não resolvido, sem
valor para quem consome o desfecho final).

A integração é automatizada dentro do script local de anonimização
(`src/anonymization/`), executada **antes** da etapa de hash SHA-256:

1. A competência (mês) de referência é derivada automaticamente da própria
   base de atendimentos sendo processada — nunca informada manualmente.
2. Uma consulta autenticada via Application Default Credentials busca as
   flags curadas para a(s) competência(s) identificada(s).
3. O merge acontece com `CD_ATENDIMENTO` ainda em claro (pré-hash), usando
   `CD_ATENDIMENTO` (HSR) ↔ `atend_PA` (BigQuery) como chave.
4. Atendimentos sem correspondência ficam com `fl_conversao`/`fl_evasao`
   nulos — nulo representa "sem curadoria disponível para este caso", nunca
   "não converteu".

A lógica própria de vínculo emergência↔internação usada na
`gold_patient_journey` (ADR-0011) permanece independente da lógica de
linking do outro projeto — os dois pipelines têm escopos populacionais
distintos (o projeto de conversão cobre apenas o funil emergência→internação;
a jornada completa cobre também outras portas de entrada do hospital).

## Alternativas consideradas

**Lakehouse Federation (Databricks → BigQuery)** — descartada nesta fase.
Introduziria dependência cross-cloud em tempo de consulta e cross-billing
entre AWS e GCP, sem confirmação de que esse recurso está disponível na
Databricks Free Edition. Fica como evolução natural quando o projeto migrar
de ingestão manual mensal para ingestão automatizada.

**Export agendado (BigQuery → arquivo → Volume Databricks)** — descartada.
Mantém uma etapa manual ou semi-manual de transporte de arquivo entre nuvens,
sem resolver o requisito central de automação completa do ciclo mensal.

**Importar a lógica de linking completa do outro projeto** (não só as
flags) — descartada. O projeto de conversão foi desenhado para uma
população mais estreita (só o funil de emergência) e otimizado para essa
pergunta específica; herdar sua lógica de vínculo faria a `gold_patient_journey`
regredir para um escopo populacional menor do que o pretendido para o
Mapa Digital do Fluxo do Paciente.

## Consequências

- Nova dependência operacional: uma credencial de service account do GCP
  (Application Default Credentials) precisa existir localmente em qualquer
  máquina que rode o script de anonimização — risco de esquecimento ao
  configurar um ambiente novo.
- Acoplamento a um projeto externo: mudanças na estrutura de
  `atendimentos_pa` (nome de coluna, particionamento) quebram o
  enriquecimento sem erro explícito, silenciosamente, até serem percebidas.
- `fl_conversao`/`fl_evasao` nulos são esperados para atendimentos de fora
  do escopo de curadoria (unidades fora do recorte do outro projeto,
  competências ainda não fechadas) — não devem ser tratados como "0" em
  nenhuma análise posterior.
- Três novas dependências travadas em `requirements.txt`
  (`google-cloud-bigquery`, `pandas-gbq`, `db-dtypes`), com versão fixa
  para reprodutibilidade de ambiente.
- Zero trabalho manual adicional para a curadora ou para qualquer pessoa
  não técnica — a integração roda de forma transparente dentro do ciclo já
  existente de anonimização mensal.