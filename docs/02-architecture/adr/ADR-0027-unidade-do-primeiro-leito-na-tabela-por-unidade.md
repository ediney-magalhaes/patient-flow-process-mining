# ADR-0027: Unidade do 1º leito definitivo na tabela por unidade da Internação

- **Status:** aceito
- **Data:** 2026-11-13
- **Decisores:** Ediney Magalhães
- **Relacionado a:** ADR-0011, ADR-0023, ADR-0026

---

## Contexto

A seção Internação da Página 1 precisava mostrar onde as internações acontecem e quanto esperam pelo leito. A tabela por unidade responde a isso, e ela precisa de uma unidade para cada internação.

A `gold_patient_journey` só tinha `ts_primeiro_leito`, o primeiro leito físico real, sem unidade. Nem toda internação chega a ter esse leito: em mar/2026, 732 das 867 internações têm leito definitivo, e as outras 135 ficariam sem unidade.

A base de internações traz o `LEITO`/`UNIDADE` do leito inicial, alocado só para poder registrar a internação. Às vezes é o leito definitivo, mas na maioria das vezes não é. Toda internação tem esse campo, mesmo sem movimentação.

## Decisão

### 1. Duas colunas na `gold_patient_journey`

- `unidade_primeiro_leito`: unidade do primeiro leito definitivo, lida das movimentações. É a unidade do mesmo registro que define `ts_primeiro_leito`, então fica nula quando `ts_primeiro_leito` é nulo.
- `unidade_leito_inicial`: `UNIDADE` da base de internações, o leito de registro. Está preenchida em todas as internações.

### 2. A tabela usa as duas, nesta ordem

A unidade de cada internação é `COALESCE(unidade_primeiro_leito, unidade_leito_inicial)`. O leito inicial só entra como último recurso, para quem não tem leito definitivo. No dashboard, a coluna se chama "Unidade do 1º leito definitivo".

### 3. Todas as unidades aparecem

A tabela mostra todas as unidades, mesmo com um caso só, sem número mínimo de casos. O leito extra (`EXTRA INTERNACAO`) e a `OBSERVACAO PA` aparecem como linhas, e é onde a tabela mostra o que fica fora do cálculo de espera.

### 4. O que a tabela mostra

Para cada unidade: número de internações, casos com espera, mediana da espera pelo leito (regra do ADR-0026), mediana e P90 da jornada (ADR-0023). A mediana da espera tem destaque condicional a partir de 3 h, critério de "demora" definido por Ediney. Durações de jornada acima de 24 h aparecem em dias e horas ("1 d 8 h"), e abaixo disso em horas.

## Alternativas consideradas

**Usar só `unidade_primeiro_leito`.** Rejeitada: as internações sem leito definitivo ficariam sem unidade, e o total da tabela não fecharia com o total de internações.

**Manter uma linha "Sem movimentação registrada".** Rejeitada: como toda internação tem leito inicial na base, esse grupo deixa de existir. Em março eram 25 internações em `EXTRA INTERNACAO` e 2 em `OBSERVACAO PA`, que passaram a aparecer nas próprias unidades.

**Ocultar unidades com poucos casos.** Rejeitada: esconderia justamente os casos que a tabela existe para mostrar.

**Dividir a internação entre as unidades por onde passou (permanência por unidade).** Não adotada: a tabela atribui a internação inteira à unidade do primeiro leito. É uma limitação aceita, e a tabela não mede permanência por unidade.

**Gráfico no lugar da tabela, com os dados no tooltip.** Plano B, caso a tabela não ficasse legível. A tabela ficou boa e foi mantida.

## Consequências

- Em mar/2026, a tabela tem 13 unidades e fecha com as 867 internações.
- Duas colunas novas na `gold_patient_journey` exigem Full Refresh do pipeline `gold_transformations`, e o dicionário de dados foi atualizado.
- Atribuir a internação à unidade do primeiro leito tem viés conhecido: a unidade de um paciente que se transfere depois não aparece na tabela.
- Com mais meses carregados, os nomes de unidade precisam ser reconferidos. A unificação de `GINECOLOGIA/OBSTETRICIA` em `TERREO` existe no event log (ADR-0021), mas não nas unidades da `gold_patient_journey`.
- A tabela é um dataset do dashboard (`internacao_por_unidade`) e está documentada em `dashboard-kpis-jornada.md`.