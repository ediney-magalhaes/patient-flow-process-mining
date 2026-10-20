# ADR-0022: Coluna `internou_em_uti` separada do `has_uti` na `gold_patient_journey`

- **Status:** aceito
- **Data:** 2026-10-20
- **Decisores:** Ediney Magalhães
- **Relacionado a:** ADR-0014, RQ-017

---

## Contexto

O cartão "Conversão UTI" da Página 1 media `has_uti`, que marca a passagem pela UTI em qualquer momento da internação. A validação do dashboard (`validacao-dashboard.md`) mostrou que isso não corresponde à definição de conversão em UTI, que é o atendimento do PA que virou internação em UTI. Em mar/2026 os números diferem: 186 atendimentos (2,98%) pela passagem, 170 (2,73%) pela internação em UTI.

Os dados mostraram quatro fatos que moldam a regra:

1. A primeira movimentação da internação é sempre uma unidade virtual. Em mar/2026, 443 dos 445 convertidos com movimentação começam em `OBSERVACAO PA` ou `EXTRA INTERNACAO`, e nenhum começa na UTI. Olhar só a primeira movimentação daria zero.
2. Depois da unidade virtual, 169 atendimentos têm a UTI como primeiro leito real, em uma transferência.
3. Um atendimento tem a internação registrada direto em leito de UTI (`silver_internacoes.LEITO`) e só a `ALTA` como movimentação.
4. Nos pares `TRANSFER. DE` e `TRANSFER. PARA`, a `UNIDADE` é diferente entre as duas linhas (973 de 973 pares em mar/2026). A deduplicação do código mantém uma delas ao acaso.

O `has_uti` é usado em outros lugares com o sentido de passagem: o cartão "Internações com UTI" da Página 1, o desenho da Página 4 (UTI antes e depois da cirurgia, UTI sem cirurgia) e a view `gold_bi_jornada`.

## Decisão

### 1. Coluna nova, `has_uti` mantido

A `gold_patient_journey` ganha `internou_em_uti` (boolean, sem nulos). O `has_uti` não muda.

### 2. Regra

O atendimento internou em UTI quando:

- o **primeiro leito real** da internação é de UTI, ou
- a **própria internação foi registrada em leito de UTI**.

Unidade virtual (`OBSERVACAO PA`, `EXTRA INTERNACAO`, `HEMODINAMICA`, `BERCARIO - ALOJAMENTO CONJUNTO`, a lista `unidades_extras` já usada em `ts_primeiro_leito`) não conta como primeiro leito. Passar por ela e ser transferido para a UTI conta.

### 3. Como o código calcula

- **Primeiro leito real:** primeira movimentação, por horário, com `UNIDADE` fora das unidades virtuais, lida de `silver_movimentacoes` **antes da deduplicação** (`df_movim_bruta`). Vale `True` quando o leito de destino começa por um prefixo da lista `uti_prefixos`, a mesma do `has_uti`.
- **Internação direta:** `LEITO` de `silver_internacoes` com o mesmo critério de prefixo.
- **Resultado:** o "ou" dos dois, com nulo tratado como `False`, calculado por jornada.

### 4. Dashboard

O cartão "Conversão UTI" usa o campo `Internou Em Uti Numerico` (`CASE WHEN source.internou_em_uti THEN 1 ELSE 0 END`), com `AVG`.

## Alternativas consideradas

**Redefinir o `has_uti`.** Rejeitada: mudaria sem aviso o cartão "Internações com UTI", a Página 4 e a view para o Genie, que medem passagem pela UTI.

**Olhar só a primeira movimentação da internação.** Rejeitada: é sempre unidade virtual, e o resultado seria zero.

**Ler o primeiro leito das movimentações já deduplicadas.** Rejeitada: a linha que sobra na deduplicação é arbitrária, e a unidade lida pode ser a virtual de origem.

**Calcular a regra no SQL do dashboard.** Rejeitada: a regra ficaria fora da camada Gold e não chegaria à view `gold_bi_jornada` nem ao Genie.

**Identificar a UTI pelo nome da `UNIDADE`.** Rejeitada: manteria dois critérios de "leito de UTI". O prefixo do leito, já usado no `has_uti`, fica como critério único.

## Consequências

- A `gold_patient_journey` ganha uma coluna, e o pipeline `gold_transformations` exige Full Refresh.
- Duas medidas de UTI convivem: passagem (`has_uti`) e internação (`internou_em_uti`). Os documentos de cada página dizem qual usam.
- Em mar/2026, o cartão da Página 1 passou de 2,98% para 2,73% (170 de 6.236). Na tabela inteira, 229 linhas têm a coluna verdadeira, contando as internações que não vieram do PA.
- A regra vive em uma coluna só. Se a definição mudar, o ajuste é naquele ponto do código.
- A lista `uti_prefixos` é fixa no código. Em mar/2026 ela reconhece as cinco unidades de UTI do hospital (`UTI - CORONARIANA`, `UTI A1`, `UTI A2`, `UTI B - CIRURGICA` e `UTI INFANTIL`). Com o histórico, a cobertura precisa ser reconferida (checklist de ingestão).
- Convertidos sem leito real não contam: em mar/2026, 33 passaram só por unidade virtual e 7 não têm internação em `silver_internacoes`.