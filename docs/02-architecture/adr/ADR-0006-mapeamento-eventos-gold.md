# ADR-0006: Mapeamento de Timestamps para Eventos no Event Log Gold

- **Status:** aceito
- **Data:** 2026-06-12
- **Decisores:** Ediney Magalhães

---

## Contexto

As tabelas Silver contêm timestamps em colunas separadas — cada coluna representa
um marco temporal do processo hospitalar. Para construir o event log canônico no
padrão XES, cada timestamp relevante precisa virar uma linha com `activity` e
`timestamp` definidos. A decisão de quais timestamps viram eventos e com qual nome
de atividade é uma decisão de domínio clínico, não técnica.

## Decisão

Para cada tabela Silver de eventos, foram mapeados os timestamps que representam
marcos clínicos relevantes para Process Mining. Timestamps operacionais do sistema
(chamadas internas, artefatos de Excel, durações calculadas) foram descartados.
O mapeamento completo por fonte é:

| Fonte | Timestamp | Atividade |
|---|---|---|
| `silver_atendimento_emergencia` | `DT_HR_TOTEM_RECEP` | Chegada ao Pronto-Socorro |
| `silver_atendimento_emergencia` | `INICIO_CLASSIFICACAO` | Início da Triagem |
| `silver_atendimento_emergencia` | `DT_HR_CLASSIF_RISCO` | Classificação de Risco |
| `silver_atendimento_emergencia` | `DH_CADASTRO_RECEPCAO` | Início do Cadastro |
| `silver_atendimento_emergencia` | `FIM_CAD_RECEP` | Fim do Cadastro |
| `silver_atendimento_emergencia` | `INI_ATD_MEDICO` | Início da Consulta Médica |
| `silver_atendimento_emergencia` | `FIM_ATD_MEDICO` | Fim da Consulta Médica |
| `silver_atendimento_emergencia` | `DT_HR_ALTA` | Alta da Emergência |
| `silver_internacoes` | `DT_HR_ATENDIMENTO` | Internacao |
| `silver_internacoes` | `DT_HR_ALTA` | Alta da Internacao |
| `silver_altas` | `DT_HR_PRE_MED` | Prescricao de Alta |
| `silver_altas` | `DT_HR_ALTA_MEDICA` | Alta Medica |
| `silver_altas` | `DT_HR_ALTA_FINAL` | Alta Hospitalar |
| `silver_cirurgias` | `DT_AVISO_CIRURGIA` | Aviso de Cirurgia |
| `silver_cirurgias` | `DT_AGENDA_CIR` | Agendamento de Cirurgia |
| `silver_cirurgias` | `INICIO_PROGRAMADO_CIRURGIA` | Inicio Programado da Cirurgia |
| `silver_cirurgias` | `FINAL_PROGRAMADO_CIRURGIA` | Fim Programado da Cirurgia |
| `silver_cirurgias` | `DT_HR_ENTRADA_SALA_CIRURG` | Entrada na Sala Cirurgica |
| `silver_cirurgias` | `INICIO_ANESTESIA` | Inicio da Anestesia |
| `silver_cirurgias` | `DT_INICIO_CIRURGIA` | Inicio da Cirurgia |
| `silver_cirurgias` | `DT_FIM_CIRURGIA` | Fim da Cirurgia |
| `silver_cirurgias` | `FIM_ANESTESIA` | Fim da Anestesia |
| `silver_cirurgias` | `DT_HR_SAIDA_SALA_CIRURG` | Saida da Sala Cirurgica |
| `silver_cirurgias` | `INICIO_LIMPEZA` | Inicio da Limpeza da Sala |
| `silver_cirurgias` | `FIM_LIMPEZA` | Fim da Limpeza da Sala |
| `silver_exames_imagem` | `DATA_HORA_PRESCRICAO` | Prescrição do Exame de Imagem |
| `silver_exames_imagem` | `STATUS_ADMITIDO` | Admissão no RIS |
| `silver_exames_imagem` | `STATUS_LIBERADO` | Liberação para Início do Exame |
| `silver_exames_imagem` | `STATUS_INICIO_PREPARO` | Início do Preparo |
| `silver_exames_imagem` | `STATUS_FIM_PREPARO` | Fim do Preparo |
| `silver_exames_imagem` | `STATUS_INICIO_EXAME` | Início do Exame |
| `silver_exames_imagem` | `STATUS_TERMINO_EXAME` | Término do Exame de Imagem |
| `silver_exames_imagem` | `DATA_DITADO` | Ditado do Laudo |
| `silver_exames_imagem` | `DATA_LAUDO` | Laudo Registrado no Sistema |
| `silver_exames_imagem` | `STATUS_APROVADO` | Laudo Aprovado |
| `silver_exames_laboratoriais` | `HR_PED_LAB` | Pedido de Exame Laboratorial |
| `silver_exames_laboratoriais` | `DT_COLETA` | Coleta do Exame Laboratorial |
| `silver_exames_laboratoriais` | `HR_LAUDO_LAB` | Laudo do Exame Laboratorial |
| `silver_movimentacoes` | `DT_HR_MOVIMENTACAO` | valor de `TIPO` |

## Alternativas consideradas

**Usar todos os timestamps disponíveis** — descartado. Timestamps operacionais
como `CHAMADA_CLASSIFICACAO` e `DH_ATEND_MEDICO` representam chamadas internas
do sistema, não marcos da jornada do paciente. Incluí-los geraria ruído no
process map.

**Criar camada intermediária física** — descartado. A normalização inline na
Gold via loop de eventos é suficiente para o volume atual e evita tabelas
intermediárias sem valor analítico direto. Ver ADR-0007 para essa decisão.

## Consequências

- O vocabulário do process map está fixado neste documento — qualquer novo
  evento ou renomeação deve atualizar este ADR
- O CID registrado em `silver_atendimento_emergencia` representa hipótese
  diagnóstica de entrada, não diagnóstico confirmado — documentado no
  dicionário de dados
- `STATUS_LIBERADO` em exames de imagem representa liberação para início
  do exame, não liberação do laudo — comportamento confirmado após análise
  do achado de 100% de violações na flag `flag_termino_liberado`
- Timestamps descartados por serem redundantes: `HR_CHAM_MED` de
  `silver_exames_laboratoriais` (mesmo valor de `DT_HR_TOTEM_RECEP` da emergência)
  e `DATA_INICIO_CIRURGIA` de `silver_cirurgias` (redundante com `DT_INICIO_CIRURGIA`)