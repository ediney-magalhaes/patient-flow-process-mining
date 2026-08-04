-- View: gold_bi_jornada
-- Schema: hospital_santa_rosa.gold_fluxo
-- Propósito: camada de abstração para BI — resolve o join entre
--   gold_patient_journey e gold_events_emergencia, encapsulando a
--   complexidade das famílias de identificador (cd_atendimento = case_id)
--   e expondo colunas com vocabulário de negócio para Dashboard e Genie Space.
--
-- Histórico:
--   2026-07-xx — criação original, com has_internacao
--   2026-08-04 — has_internacao substituída por fl_conversao (ADR-0013);
--                 fl_evasao adicionada

CREATE OR REPLACE VIEW hospital_santa_rosa.gold_fluxo.gold_bi_jornada (
  cd_atendimento,
  cd_internacao,
  cd_paciente,
  journey_type,
  ano_mes,
  fl_conversao,
  fl_evasao,
  has_cirurgia,
  has_uti,
  duracao_total_min,
  duracao_emergencia_internacao_min,
  activity,
  ts_evento,
  event_type,
  especialidade,
  resource)
AS SELECT
  j.cd_atendimento,
  j.cd_internacao,
  j.cd_paciente,
  j.journey_type,
  j.ano_mes,
  j.fl_conversao,
  j.fl_evasao,
  j.has_cirurgia,
  j.has_uti,
  j.duracao_total_min,
  j.duracao_emergencia_internacao_min,
  e.activity,
  e.timestamp AS ts_evento,
  e.event_type,
  e.especialidade,
  e.resource
FROM hospital_santa_rosa.gold_fluxo.gold_patient_journey j
LEFT JOIN hospital_santa_rosa.gold_fluxo.gold_events_emergencia e
  ON j.cd_atendimento = e.case_id