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
                      .withColumnRenamed("CD_INTERNACAO", "case_id") \
                      .select(
                          "case_id", "activity", "timestamp", "lifecycle",
                              "event_type", "case_type", "outcome", "resource",
                              "location", "source"
                      )
    
    # cria a tabela com data e hora da alta
    df_alta = df.withColumn("activity", F.lit("Alta da Internacao")) \
                .withColumnRenamed("DT_HR_ALTA", "timestamp") \
                .withColumnRenamed("CD_INTERNACAO", "case_id") \
                .select(
                    "case_id", "activity", "timestamp", "lifecycle",
                        "event_type", "case_type", "outcome", "resource",
                        "location", "source"
                )
    # seleciona apenas as colunas do schema canônico na ordem correta
    return df_internacao.unionByName(df_alta)

@dlt.table(
    name="gold_events_altas",
    comment="Eventos de altas no schema canônico do event log"
)
def gold_events_altas():

    # leitura da tabela silver_altas
    df = spark.read.table("hospital_santa_rosa.silver_fluxo.silver_altas")

    # renomeia a coluna de unidade
    df = df.withColumnRenamed("UNID_INT", "location")

    # adiciona colunas fixas do schema canônico
    df = df.withColumn("lifecycle", F.lit("complete"))
    df = df.withColumn("event_type", F.lit("alta"))
    df = df.withColumn("case_type", F.lit("alta"))
    df = df.withColumn("outcome", F.lit(None).cast("string"))
    df = df.withColumn("resource", F.lit(None).cast("string"))
    df = df.withColumn("source", F.lit("silver_altas"))

    # cria o DataFrame de prescrição da alta
    df_prescricao_alta = df.withColumn("activity", F.lit("Prescricao de alta")) \
                           .withColumnRenamed("DT_HR_PRE_MED", "timestamp") \
                           .withColumnRenamed("ATENDIMENTO", "case_id") \
                           .select(
                               "case_id", "activity", "timestamp", "lifecycle",
                               "event_type", "case_type", "outcome", "resource",
                               "location", "source"
                           )
    
    # cria o DataFrame de alta médica
    df_alta_medica = df.withColumn("activity", F.lit("Alta médica")) \
                       .withColumnRenamed("DT_HR_ALTA_MEDICA", "timestamp") \
                       .withColumnRenamed("ATENDIMENTO", "case_id") \
                       .select(
                           "case_id", "activity", "timestamp", "lifecycle",
                            "event_type", "case_type", "outcome", "resource",
                            "location", "source"
                       )
    
    # cria o DataFrame de alta hospitalar
    df_alta_hospitalar = df.withColumn("activity", F.lit("Alta Hospitalar")) \
                           .withColumnRenamed("DT_HR_ALTA_FINAL", "timestamp") \
                           .withColumnRenamed("ATENDIMENTO", "case_id") \
                           .select(
                               "case_id", "activity", "timestamp", "lifecycle",
                                "event_type", "case_type", "outcome", "resource",
                                "location", "source"
                           )
    
    # seleciona apenas as colunas do schema canônico na ordem correta
    return df_prescricao_alta.unionByName(df_alta_medica).unionByName(df_alta_hospitalar)

@dlt.table(
    name="gold_events_cirurgias",
    comment="Eventos de cirurgias no schema canônico do event log"
)
def gold_events_cirurgias():

    # leitura da tabela silver_cirurgias
    df = spark.read.table("hospital_santa_rosa.silver_fluxo.silver_cirurgias")

    # renomeia a coluna de sala cirúrgica
    df = df.withColumnRenamed("SALA_CIRURGIA", "location")

    # lista de eventos
    eventos = [
        ("DT_AVISO_CIRURGIA",        "Aviso de Cirurgia"),
        ("DT_AGENDA_CIR",            "Agendamento de Cirurgia"),
        ("INICIO_PROGRAMADO_CIRURGIA", "Inicio Programado da Cirurgia"),
        ("FINAL_PROGRAMADO_CIRURGIA",  "Fim Programado da Cirurgia"),
        ("DT_HR_ENTRADA_SALA_CIRURG",  "Entrada na Sala Cirurgica"),
        ("INICIO_ANESTESIA",           "Inicio da Anestesia"),
        ("DT_INICIO_CIRURGIA",         "Inicio da Cirurgia"),
        ("DT_FIM_CIRURGIA",            "Fim da Cirurgia"),
        ("FIM_ANESTESIA",              "Fim da Anestesia"),
        ("DT_HR_SAIDA_SALA_CIRURG",    "Saida da Sala Cirurgica"),
        ("INICIO_LIMPEZA",             "Inicio da Limpeza da Sala"),
        ("FIM_LIMPEZA",                "Fim da Limpeza da Sala"),
    ]

    # adiciona colunas fixas do schema canônico
    df = df.withColumn("lifecycle", F.lit("complete"))
    df = df.withColumn("event_type", F.lit("cirurgia"))
    df = df.withColumn("case_type", F.lit("cirurgico"))
    df = df.withColumn("outcome", F.lit(None).cast("string"))
    df = df.withColumn("resource", F.lit(None).cast("string"))
    df = df.withColumn("source", F.lit("silver_cirurgias"))

    # itera a lista de eventos para criar os DataFrames
    
    df_resultado = None

    for coluna_timestamp, nome_atividade in eventos:
        df_evento = df.withColumn("activity", F.lit(nome_atividade)) \
                      .withColumnRenamed(coluna_timestamp, "timestamp") \
                      .withColumnRenamed("ATENDIMENTO", "case_id") \
                      .select(
                          "case_id", "activity", "timestamp", "lifecycle",
                          "event_type", "case_type", "outcome", "resource",
                          "location", "source"
                        ) 
        if df_resultado is None:
            df_resultado = df_evento
        else:
            df_resultado = df_resultado.unionByName(df_evento)
    
    return df_resultado

@dlt.table(
    name="gold_events_emergencia",
    comment="Eventos da emergência no schema canônico do event log"
)
def gold_events_emergencia():

    # leitura da tabela silver_emergencia
    df = spark.read.table("hospital_santa_rosa.silver_fluxo.silver_atendimento_emergencia")

    # renomeia a coluna local de procedencia
    df = df.withColumnRenamed("LOCAL_PROCED", "location")

    # lista de eventos
    eventos = [
        ("DT_HR_TOTEM_RECEP",          "Chegada ao Pronto-Socorro"),
        ("INICIO_CLASSIFICACAO",       "Início da Triagem"),
        ("DT_HR_CLASSIF_RISCO",        "Classificação de Risco"),
        ("DH_CADASTRO_RECEPCAO",       "Início do Cadastro"),
        ("FIM_CAD_RECEP",              "Fim do Cadastro"),
        ("INI_ATD_MEDICO",             "Início da Consulta Médica"),
        ("FIM_ATD_MEDICO",             "Fim da Consulta Médica"),
        ("DT_HR_ALTA",                 "Alta da Emergência"),
    ]

    # adiciona colunas fixas do schema canônico
    df = df.withColumn("lifecycle", F.lit("complete"))
    df = df.withColumn("event_type", F.lit("emergencia"))
    df = df.withColumn("case_type", F.lit("emergencia"))
    df = df.withColumn("outcome", F.lit(None).cast("string"))
    df = df.withColumn("resource", F.lit(None).cast("string"))
    df = df.withColumn("source", F.lit("silver_atendimento_emergencia"))

    # itera sobre os eventos e constrói os DataFrames
    df_resultado = None
    for coluna_timestamp, nome_atividade in eventos:
        df_evento = df.withColumn("activity", F.lit(nome_atividade)) \
                      .withColumnRenamed(coluna_timestamp, "timestamp") \
                      .withColumnRenamed("CD_ATENDIMENTO", "case_id") \
                      .select(
                          "case_id", "activity", "timestamp", "lifecycle",
                          "event_type", "case_type", "outcome", "resource",
                          "location", "source"
                        )
        if df_resultado is None:
            df_resultado = df_evento
        else:
            df_resultado = df_resultado.unionByName(df_evento)
    
    return df_resultado

@dlt.table(
    name="gold_events_exames_imagem",
    comment="Eventos da radiologia no schema canônico do event log"
)
def gold_events_exames_imagem():

    # leitura da tabela silver_exames_imagem
    df = spark.read.table("hospital_santa_rosa.silver_fluxo.silver_exames_imagem")

    # lista de eventos
    eventos = [
        ("DATA_HORA_PRESCRICAO",       "Prescrição do Exame de Imagem"),
        ("STATUS_ADMITIDO",            "Admissão no RIS"),
        ("STATUS_LIBERADO",            "Liberação para Início do Exame"),
        ("STATUS_INICIO_PREPARO",      "Início do Preparo"),
        ("STATUS_FIM_PREPARO",         "Fim do Preparo"),
        ("STATUS_INICIO_EXAME",        "Início do Exame"),
        ("STATUS_TERMINO_EXAME",       "Término do Exame de Imagem"),
        ("DATA_DITADO",                "Ditado do Laudo"),
        ("DATA_LAUDO",                 "Laudo Registrado no Sistema"),
        ("STATUS_APROVADO",            "Laudo Aprovado"),
    ]

    # adiciona colunas fixas do schema canônico
    df = df.withColumn("lifecycle", F.lit("complete"))
    df = df.withColumn("event_type", F.lit("exames de imagem"))
    df = df.withColumn("case_type", F.col("TIPO_ATENDIMENTO"))
    df = df.withColumn("outcome", F.lit(None).cast("string"))
    df = df.withColumn("resource", F.lit(None).cast("string"))
    df = df.withColumn("location", F.lit(None).cast("string"))
    df = df.withColumn("source", F.lit("silver_exames_imagem"))

    # itera sobre a lista de eventos para construir os DataFrames
    df_resultado = None

    for coluna_timestamp, nome_atividade in eventos:
        df_eventos = df.withColumn("activity", F.lit(nome_atividade)) \
                       .withColumnRenamed(coluna_timestamp, "timestamp") \
                       .withColumnRenamed("CD_ATENDIMENTO", "case_id") \
                       .select(
                           "case_id", "activity", "timestamp", "lifecycle",
                          "event_type", "case_type", "outcome", "resource",
                          "location", "source"
                       )
        
        if df_resultado is None:
            df_resultado = df_eventos
        else:
            df_resultado = df_resultado.unionByName(df_eventos)
    
    return df_resultado

@dlt.table(
    name="gold_events_exames_laboratoriais",
    comment="Eventos do laboratório no schema canônico do event log"
)
def gold_events_exames_laboratoriais():

    # leitura da tabela silver_exames_laboratoriais
    df = spark.read.table("hospital_santa_rosa.silver_fluxo.silver_exames_laboratoriais")

    # lista de eventos
    eventos = [
        ("HR_PED_LAB",      "Pedido de Exame Laboratorial"),
        ("DT_COLETA",       "Coleta do Exame Laboratorial"),
        ("HR_LAUDO_LAB",    "Laudo do Exame Laboratorial"),
    ]

    # adiciona colunas fixas do schema canônico
    df = df.withColumn("lifecycle", F.lit("complete"))
    df = df.withColumn("event_type", F.lit("exames laboratoriais"))
    df = df.withColumn("case_type", F.lit("emergencia"))
    df = df.withColumn("outcome", F.lit(None).cast("string"))
    df = df.withColumn("resource", F.lit(None).cast("string"))
    df = df.withColumn("location", F.lit(None).cast("string"))
    df = df.withColumn("source", F.lit("silver_exames_laboratoriais"))

    # itera sobre a lista de eventos e cria os DataFrames
    df_resultado = None
    for coluna_timestamp, nome_atividade in eventos:
        df_evento = df.withColumn("activity", F.lit(nome_atividade)) \
                      .withColumnRenamed(coluna_timestamp, "timestamp") \
                      .withColumnRenamed("CD_ATENDIMENTO", "case_id") \
                      .select(
                          "case_id", "activity", "timestamp", "lifecycle",
                          "event_type", "case_type", "outcome", "resource",
                          "location", "source"
                      )
        
        if df_resultado is None:
            df_resultado = df_evento
        else:
            df_resultado = df_resultado.unionByName(df_evento)
    
    return df_resultado
                      
@dlt.table(
    name="gold_event_log",
    comment="Evento com a união de todas as tabelas gold_events"
)
def gold_event_log():

    # leitura das sete tabelas gold_events
    df_altas = dlt.read("gold_events_altas")
    df_cirurgias = dlt.read("gold_events_cirurgias")
    df_emergencia = dlt.read("gold_events_emergencia")
    df_imagem = dlt.read("gold_events_exames_imagem")
    df_laborarorio = dlt.read("gold_events_exames_laboratoriais")
    df_internacoes = dlt.read("gold_events_internacoes")
    df_movimentacoes = dlt.read("gold_events_movimentacoes")

    # UNION ALL com unionByName
    df = df_altas.unionByName(df_cirurgias) \
                 .unionByName(df_emergencia) \
                 .unionByName(df_imagem) \
                 .unionByName(df_laborarorio)\
                 .unionByName(df_internacoes) \
                 .unionByName(df_movimentacoes)
    
    # cálculo da duração de tempo entre cada evento
    janela_caso = Window.partitionBy("case_id")

    df = df.withColumn("duration_minutes", ((F.unix_timestamp(F.max("timestamp").over(janela_caso)) - 
                                           F.unix_timestamp(F.min("timestamp").over(janela_caso)))
                                           / 60).cast("int")
    )
    return df

@dlt.table(
    name="gold_case_attributes",
    comment="Evento com atributos de enriquecimento de análise para o event_log canônico (gold_event_log)"
)
def gold_case_attributes():

    # leitura das fontes
    df_epidemio = spark.read.table("hospital_santa_rosa.silver_fluxo.silver_epidemio")
    df_emergencia = spark.read.table("hospital_santa_rosa.silver_fluxo.silver_atendimento_emergencia")

    # DataFrame da internação
    df_internacao = df_epidemio.select(
        F.col("atendimento").alias("case_id"),
        F.col("tp_atendimento").alias("case_type"),
        F.col("idade"),
        F.col("sexo"),
        F.col("convenio"),
        F.col("especialidade"),
        F.col("cid_1_principal").alias("cid_principal"),
        F.col("motivo_alta"),
        F.lit(None).cast("string").alias("classificacao_risco"),
        F.col("tipo_internacao"),
        F.col("nr_dias"),
        F.col("qtd_passagens_uti"),
        F.col("PREVISAO_COMPLEXIDADE").alias("complexidade"),
        F.col("PREVISAO_GRUPO").alias("grupo_diagnostico"),
        F.col("cirurgia").alias("teve_cirurgia")
    )

    # Dataframe da emergência
    df_emergencia = df_emergencia.select(
        F.col("CD_ATENDIMENTO").alias("case_id"),
        F.lit("emergencia").alias("case_type"),
        F.col("IDADE_CALCULADA").alias("idade"),
        F.col("SEXO").alias("sexo"),
        F.col("CONVENIO").alias("convenio"),
        F.col("ESPECIALIDADE").alias("especialidade"),
        F.col("CID").alias("cid_principal"),
        F.col("MOTIVO_ALTA").alias("motivo_alta"),
        F.col("COR_CLASSIF").alias("classificacao_risco"),
        F.lit(None).cast("string").alias("tipo_internacao"),
        F.lit(None).cast("string").alias("complexidade"),
        F.lit(None).cast("string").alias("grupo_diagnostico"),
        F.lit(None).cast("string").alias("teve_cirurgia"),
        F.lit(None).cast("int").alias("nr_dias"),
        F.lit(None).cast("int").alias("qtd_passagens_uti")
    )

    # UNION ALL com unionByName
    df = df_internacao.unionByName(df_emergencia)

    return df