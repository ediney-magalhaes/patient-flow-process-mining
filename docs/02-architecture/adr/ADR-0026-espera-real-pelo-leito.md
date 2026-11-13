# ADR-0026: Espera real pelo leito — marco inicial por tipo de jornada e exclusão de quem já tinha leito antes da cirurgia

- **Status:** aceito
- **Data:** 2026-11-13
- **Decisores:** Ediney Magalhães
- **Relacionado a:** ADR-0011, ADR-0014, ADR-0023

---

## Contexto

O dashboard mostra o tempo até o leito em três lugares: o card da Emergência, a tabela por unidade da Internação e o gráfico das etapas. A primeira versão media o intervalo entre a abertura da internação (`ts_entrada_internacao`) e o primeiro leito (`ts_primeiro_leito`) para todos os tipos de jornada.

Nas internações cirúrgicas, esse intervalo inclui a ida ao centro cirúrgico e a própria cirurgia. O número não mede espera por leito, e o card da Emergência ficava inflado. Ao passar a contar a partir da saída da sala (`ts_saida_cirurgia`), apareceram esperas negativas.

A causa não é erro de dado. `ts_primeiro_leito` é a primeira movimentação para leito físico real da internação (ADR-0011), e não necessariamente o leito do pós-operatório. O paciente que já ocupava um leito antes da cirurgia tem o primeiro leito anterior à saída da sala. Ele não esperou leito depois da cirurgia, porque já tinha um.

## Decisão

### 1. Definição

Espera real pelo leito é o tempo que o paciente aguarda um leito físico, contado a partir do momento em que passa a precisar dele.

### 2. Marco inicial por tipo de jornada

| Tipo de jornada | Início da espera | Fim da espera |
|---|---|---|
| `internacao_clinica`, `internacao_clinica_direta` | abertura da internação (`ts_entrada_internacao`) | `ts_primeiro_leito` |
| `internacao_cirurgica_emergencia`, `internacao_cirurgica_eletiva` | saída da sala cirúrgica (`ts_saida_cirurgia`) | `ts_primeiro_leito` |

Os demais tipos de jornada não têm espera calculada, e o valor fica nulo.

### 3. Quem já tinha leito antes da cirurgia fica fora

Nas jornadas cirúrgicas, a espera só é calculada quando `ts_primeiro_leito >= ts_saida_cirurgia`. Nos outros casos, o valor fica nulo, e a mediana e o P90 ignoram nulos. O valor negativo não é corrigido para zero nem descartado: o paciente simplesmente não entra no cálculo, porque não houve espera.

### 4. A contagem é sempre visível

Os datasets expõem quantos casos entraram na espera: `casos_leito` no card da Emergência e `casos_com_espera_h` na tabela por unidade. Nenhum caso sai do cálculo sem que a contagem mostre o tamanho do recorte.

### 5. Onde a regra vive

A regra é uma expressão SQL em três datasets do dashboard, não uma coluna da Gold:

- `kpis_jornada_emergencia_cards`: `leito_min`
- `internacao_por_unidade`: `h_espera_leito`
- `internacao_etapas_leito`: `h_sala_ate_leito` (etapa 3)

## Alternativas consideradas

**Manter a abertura da internação como início para todos.** Rejeitada: nas cirúrgicas, o intervalo inclui o tempo até a sala e a cirurgia, que não é espera por leito.

**Substituir o valor negativo por zero.** Rejeitada: cria um valor que não aconteceu e puxa a mediana para baixo.

**Descartar os negativos sem mostrar.** Rejeitada: o recorte some do número sem aviso. A regra do projeto é não excluir caso em silêncio, e quando um valor sai ruim, a regra que o produz é que se corrige.

**Identificar o leito do pós-operatório nas movimentações** (a primeira movimentação para leito físico depois da saída da sala) **e medir a espera até ele.** Adiada: exige uma coluna nova na `gold_patient_journey`. Fica como evolução possível.

## Consequências

- O card "Mediana do tempo até o leito" da Emergência passou de 3,95 h (412 casos) para 3,1 h, com P90 de 13,1 h e 297 casos em mar/2026.
- A etapa 3 do gráfico das etapas, na internação cirúrgica eletiva, tem 252 casos e mediana de 2,7 h em mar/2026.
- A mediana das cirúrgicas mede só quem aguardou leito depois da cirurgia. Quem já tinha leito fica de fora, e a contagem de casos mostra isso.
- A mesma lógica está repetida em três datasets. Uma mudança de regra exige três edições, e subir a regra para uma coluna da Gold removeria esse risco.
- `duracao_cirurgia_leito_min`, na `gold_patient_journey`, não aplica esta regra. Quem a usar precisa aplicar o mesmo filtro.
- Os casos com leito anterior à cirurgia devem entrar em `data-quality-rules.md`, com a contagem.