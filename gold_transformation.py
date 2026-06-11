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

#------------------------------------------------------------------------------
# gold_events_movimentacoes
# Normaliza eventos de movimentação de leito para o schema canônico
#-----------------------------------------------------------------------------

@dlt.table(
    name="gold_events_movimentacoes",
    comment="Eventos de movimentação de leito no schema canônico do event log"
)
def gold_events_movimentacoes():

    # leitura da tabela silver movimentacoes
    df = spark.read.table("hospital_santa_rosa.silver_fluxo.silver_movimentacoes")

    # renomeira colunas existentes para o schema canônico
    df = df.withColumnRenamed("CD_INTERNACAO", "case_id")
    df = df.withColumnRenamed("TIPO", "activity")
    df = df.withColumnRenamed("DT_HR_MOVIMENTACAO", "timestamp")
    df = df.withColumnRenamed("UNIDADE", "location")

    # adiciona colunas fixas do schema canônico
    df = df.withColumn("lifecycle", F.lit("complete"))
    df = df.withColumn("event_type", F.lit("movimentacao"))
    df = df.withColumn("case_type", F.lit("internacao"))
    df = df.withColumn("outcome", F.lit(None).cast("string"))
    df = df.withColumn("resource", F.lit(None).cast("string"))
    df = df.withColumn("source", F.lit("silver_movimentacoes"))

    # seleciona apenas as colunas do schema canônico na ordem correta
    return df.select(
        "case_id", "activity", "timestamp", "lifecycle",
        "event_type", "case_type", "outcome", "resource",
        "location", "source"
    )

@dlt.table(
    name="gold_events_internacoes",
    comment="Eventos de internação no schema canônico do event log"
)
def gold_events_internacoes():

    # leitura da tabela silver internacoes
    df = spark.read.table("hospital_santa_rosa.silver_fluxo.silver_internacoes")

    df = df.withColumnRenamed("UNIDADE", "location")

    # adiciona colunas fixas do schema canônico
    df = df.withColumn("lifecycle", F.lit("complete"))
    df = df.withColumn("event_type", F.lit("internacao"))
    df = df.withColumn("case_type", F.lit("internacao"))
    df = df.withColumn("outcome", F.lit(None).cast("string"))
    df = df.withColumn("resource", F.lit(None).cast("string"))
    df = df.withColumn("source", F.lit("silver_internacoes"))

    # cria a tabela com data e hora da internação
    df_internacao = df.withColumn("activity", F.lit("Internacao")) \
                      .withColumnRenamed("DT_HR_ATENDIMENTO", "timestamp") \
                      .withColumnRenamed("CD_INTERNACAO", "case_id")
    
    # cria a tabela com data e hora da alta
    df_alta = df.withColumn("activity", F.lit("Alta da Internacao")) \
                .withColumnRenamed("DT_HR_ALTA", "timestamp") \
                .withColumnRenamed("CD_INTERNACAO", "case_id")

    # faz união dos DataFrames
    df_resultado = df_internacao.unionByName(df_alta)

    # seleciona apenas as colunas do schema canônico na ordem correta
    return df_resultado.select(
        "case_id", "activity", "timestamp", "lifecycle",
        "event_type", "case_type", "outcome", "resource",
        "location", "source"
    )
    
