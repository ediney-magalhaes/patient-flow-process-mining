# =============================================================================
# gold_transformation.py
# Pipeline Gold — Event Log Canônico para Process Mining
#
# Consome as tabelas Silver e produz:
#   - gold_events_*        : eventos normalizados por fonte
#   - gold_event_log       : event log unificado (UNION ALL)
#   - gold_case_attributes : atributos do caso para enriquecimento analítico
#
# Pipeline: gold_transformations
# Schema:   hospital_santa_rosa.gold_fluxo
# =============================================================================

import dlt
from pyspark.sql import functions as F
from pyspark.sql.window import Window