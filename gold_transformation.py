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
    df = df.withColumn("especialidade", F.lit(None).cast("string"))
    df = df.withColumn("source", F.lit("silver_movimentacoes"))

    # seleciona apenas as colunas do schema canônico na ordem correta
    return df.select(
        "case_id", "activity", "timestamp", "lifecycle",
        "event_type", "case_type", "outcome", "resource",
        "especialidade", "location", "source"
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
    df = df.withColumn("resource", F.col("PRESTADOR"))
    df = df.withColumn("especialidade", F.col("ESPECIALID_ATEND"))
    df = df.withColumn("source", F.lit("silver_internacoes"))

    # cria a tabela com data e hora da internação
    df_internacao = df.withColumn("activity", F.lit("Internacao")) \
                      .withColumnRenamed("DT_HR_ATENDIMENTO", "timestamp") \
                      .withColumnRenamed("CD_INTERNACAO", "case_id") \
                      .select(
                          "case_id", "activity", "timestamp", "lifecycle",
                              "event_type", "case_type", "outcome", "resource",
                              "especialidade", "location", "source"
                      )
    
    # cria a tabela com data e hora da alta
    df_alta = df.withColumn("activity", F.lit("Alta da Internacao")) \
                .withColumnRenamed("DT_HR_ALTA", "timestamp") \
                .withColumnRenamed("CD_INTERNACAO", "case_id") \
                .select(
                    "case_id", "activity", "timestamp", "lifecycle",
                        "event_type", "case_type", "outcome", "resource",
                        "especialidade", "location", "source"
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
    df = df.withColumn("especialidade", F.col("DS_ESPECIALID"))
    df = df.withColumn("source", F.lit("silver_altas"))

    # cria o DataFrame de prescrição da alta
    df_prescricao_alta = df.withColumn("activity", F.lit("Prescricao de alta")) \
                           .withColumnRenamed("DT_HR_PRE_MED", "timestamp") \
                           .withColumnRenamed("ATENDIMENTO", "case_id") \
                           .withColumn("resource", F.col("PREST_ALTA")) \
                           .select(
                               "case_id", "activity", "timestamp", "lifecycle",
                               "event_type", "case_type", "outcome", "resource",
                               "especialidade", "location", "source"
                           )
    
    # cria o DataFrame de alta médica
    df_alta_medica = df.withColumn("activity", F.lit("Alta médica")) \
                       .withColumnRenamed("DT_HR_ALTA_MEDICA", "timestamp") \
                       .withColumnRenamed("ATENDIMENTO", "case_id") \
                       .select(
                           "case_id", "activity", "timestamp", "lifecycle",
                            "event_type", "case_type", "outcome", "resource",
                            "especialidade", "location", "source"
                       )
    
    # cria o DataFrame de alta hospitalar
    df_alta_hospitalar = df.withColumn("activity", F.lit("Alta Hospitalar")) \
                           .withColumnRenamed("DT_HR_ALTA_FINAL", "timestamp") \
                           .withColumnRenamed("ATENDIMENTO", "case_id") \
                           .select(
                               "case_id", "activity", "timestamp", "lifecycle",
                                "event_type", "case_type", "outcome", "resource",
                                "especialidade", "location", "source"
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
        ("DT_AVISO_CIRURGIA",        "Aviso de Cirurgia",               None),
        ("DT_AGENDA_CIR",            "Agendamento de Cirurgia",         None),
        ("INICIO_PROGRAMADO_CIRURGIA", "Inicio Programado da Cirurgia", None),
        ("FINAL_PROGRAMADO_CIRURGIA",  "Fim Programado da Cirurgia",    None),
        ("DT_HR_ENTRADA_SALA_CIRURG",  "Entrada na Sala Cirurgica",     None),
        ("INICIO_ANESTESIA",           "Inicio da Anestesia",           "ANESTESISTA_01"),
        ("DT_INICIO_CIRURGIA",         "Inicio da Cirurgia",            "CIRURGIAO_01"),
        ("DT_FIM_CIRURGIA",            "Fim da Cirurgia",               "CIRURGIAO_01"),
        ("FIM_ANESTESIA",              "Fim da Anestesia",              "ANESTESISTA_01"),
        ("DT_HR_SAIDA_SALA_CIRURG",    "Saida da Sala Cirurgica",       None),
        ("INICIO_LIMPEZA",             "Inicio da Limpeza da Sala",     None),
        ("FIM_LIMPEZA",                "Fim da Limpeza da Sala",        None),
    ]

    # adiciona colunas fixas do schema canônico
    df = df.withColumn("lifecycle", F.lit("complete"))
    df = df.withColumn("event_type", F.lit("cirurgia"))
    df = df.withColumn("case_type", F.lit("cirurgico"))
    df = df.withColumn("outcome", F.lit(None).cast("string"))
    df = df.withColumn("resource", F.lit(None).cast("string"))
    df = df.withColumn("especialidade", F.col("ESPECIALIDADE"))
    df = df.withColumn("source", F.lit("silver_cirurgias"))

    # itera a lista de eventos para criar os DataFrames
    
    df_resultado = None

    for coluna_timestamp, nome_atividade, coluna_resource in eventos:
        # verifica evento por evento de onde vem resource
        if coluna_resource is None:
            df_evento = df.withColumn("resource", F.lit(None).cast("string"))
        else:
            df_evento = df.withColumn("resource", F.col(coluna_resource))
        
        df_evento = df_evento.withColumn("activity", F.lit(nome_atividade)) \
                      .withColumnRenamed(coluna_timestamp, "timestamp") \
                      .withColumnRenamed("ATENDIMENTO", "case_id") \
                      .select(
                          "case_id", "activity", "timestamp", "lifecycle",
                          "event_type", "case_type", "outcome", "resource",
                          "especialidade", "location", "source"
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
    df = df.withColumn("resource", F.col("PRESTADOR"))
    df = df.withColumn("especialidade", F.col("ESPECIALIDADE"))
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
                          "especialidade", "location", "source"
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
        ("DATA_HORA_PRESCRICAO",       "Prescrição do Exame de Imagem",  "MEDICO_SOLICITANTE"),
        ("STATUS_ADMITIDO",            "Admissão no RIS",                None),
        ("STATUS_LIBERADO",            "Liberação para Início do Exame", None),
        ("STATUS_INICIO_PREPARO",      "Início do Preparo",              None),
        ("STATUS_FIM_PREPARO",         "Fim do Preparo",                 None),
        ("STATUS_INICIO_EXAME",        "Início do Exame",                None),
        ("STATUS_TERMINO_EXAME",       "Término do Exame de Imagem",     None),
        ("DATA_DITADO",                "Ditado do Laudo",                None),
        ("DATA_LAUDO",                 "Laudo Registrado no Sistema",    None),
        ("STATUS_APROVADO",            "Laudo Aprovado",                 None),
    ]

    # adiciona colunas fixas do schema canônico
    df = df.withColumn("lifecycle", F.lit("complete"))
    df = df.withColumn("event_type", F.lit("exames de imagem"))
    df = df.withColumn("case_type", F.col("TIPO_ATENDIMENTO"))
    df = df.withColumn("outcome", F.lit(None).cast("string"))
    df = df.withColumn("resource", F.lit(None).cast("string"))
    df = df.withColumn("especialidade", F.col("ESPECIALIDADE_MEDICO"))
    df = df.withColumn("location", F.lit(None).cast("string"))
    df = df.withColumn("source", F.lit("silver_exames_imagem"))

    # itera sobre a lista de eventos para construir os DataFrames
    df_resultado = None

    for coluna_timestamp, nome_atividade, coluna_resource in eventos:

        if coluna_resource is None:
            df_eventos = df.withColumn("resource", F.lit(None).cast("string"))
        else:
            df_eventos = df.withColumn("resource", F.col(coluna_resource))

        df_eventos = df_eventos.withColumn("activity", F.lit(nome_atividade)) \
                       .withColumnRenamed(coluna_timestamp, "timestamp") \
                       .withColumnRenamed("CD_ATENDIMENTO", "case_id") \
                       .select(
                           "case_id", "activity", "timestamp", "lifecycle",
                          "event_type", "case_type", "outcome", "resource",
                          "especialidade", "location", "source"
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
    df = df.withColumn("especialidade", F.lit(None).cast("string"))
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
                          "especialidade", "location", "source"
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

@dlt.table(
    name="gold_data_quality",
    comment="Tabela sobre a qualidade dos dados com medição da cobertura dos timestamps"
)
def gold_data_quality():

    # leitura do gold_event_log
    df = dlt.read("gold_event_log")
    
    # cálculo da cobertura de timestamp por paciente
    df_atividade = df.groupby("source", "activity") \
                     .agg(F.count("*").alias("total"),
                          F.count("timestamp").alias("registros_com_timestamp"),
                          F.round((F.count("timestamp") / F.count("*") * 100), 2).alias("cobertura_perc")) \
                     .withColumn("registros_sem_timestamp", F.col("total") - F.col("registros_com_timestamp")) \
                     .withColumn("data_referencia", F.current_date()) \
                     .withColumn("nivel", F.lit("atividade")) \
                     .withColumnRenamed("source", "fonte") \
                     .withColumnRenamed("activity", "atividade")
    
    # agrupamento de casos nulos
    df_caso = df.groupby("case_id") \
                .agg(F.min(F.col("timestamp").isNull().cast("int")).alias("tem_timestamp_nulo"))
    
    # agrupamento dos resultados globais
    df_global = df_caso.agg(
        F.sum((F.col("tem_timestamp_nulo") == 0).cast("int")).alias("registros_com_timestamp"),
        F.sum((F.col("tem_timestamp_nulo") == 1).cast("int")).alias("registros_sem_timestamp"),
        F.count("*").alias("total")
    ) \
    .withColumn("cobertura_perc", F.round(F.col("registros_com_timestamp") / F.col("total") * 100, 2)) \
    .withColumn("data_referencia", F.current_date()) \
    .withColumn("nivel", F.lit("caso")) \
    .withColumn("fonte", F.lit(None).cast("string")) \
    .withColumn("atividade", F.lit(None).cast("string"))
    
    df = df_atividade.unionByName(df_global)
    return df

@dlt.table(
    name="gold_patient_journey",
    comment="Jornada completa do paciente cross-source com timestamps de transição entre etapas"
)
def gold_patient_journey():
    
    # leitura das tabelas silvers
    df_emerg = spark.read.table("hospital_santa_rosa.silver_fluxo.silver_atendimento_emergencia")
    df_intern = spark.read.table("hospital_santa_rosa.silver_fluxo.silver_internacoes")
    df_cirug = spark.read.table("hospital_santa_rosa.silver_fluxo.silver_cirurgias")
    df_movim = spark.read.table("hospital_santa_rosa.silver_fluxo.silver_movimentacoes")
    df_altas = spark.read.table("hospital_santa_rosa.silver_fluxo.silver_altas")

    # seleção das colunas necessárias na tabela da emergência
    df_emerg = df_emerg.select(
        F.col("CD_ATENDIMENTO"),
        F.col("CD_PACIENTE"),
        F.col("DT_ATENDIMENTO"),
        F.col("DT_HR_TOTEM_RECEP").alias("ts_chegada"),
        F.col("DT_HR_ALTA").alias("ts_alta_emergencia")
    )

    # seleção das colunas necessárias na tabela de internações
    df_intern = df_intern.select(
        F.col("CD_INTERNACAO"),
        F.col("COD_PACIENTE").alias("CD_PACIENTE"),
        F.col("DT_HR_ATENDIMENTO").alias("ts_entrada_internacao"),
        F.col("DT_HR_ALTA").alias("ts_alta_internacao"),
        F.col("ORIGEM_ATEND")
    )

    # seleção das colunas necessárias na tabela de cirurgias
    df_cirug = df_cirug.select(
        F.col("ATENDIMENTO").alias("CD_INTERNACAO"),
        F.col("CD_PACIENTE"),
        F.col("DT_ATENDIMENTO").alias("DT_CIRURGIA"),
        F.col("DT_HR_ENTRADA_SALA_CIRURG").alias("ts_entrada_cirurgia"),
        F.col("DT_HR_SAIDA_SALA_CIRURG").alias("ts_saida_cirurgia")
    )

    # cirurgias de internação (CD_INTERNACAO existe em silver_internacoes)
    df_cirug_internacao = df_cirug.join(
        df_intern.select("CD_INTERNACAO"),
        on="CD_INTERNACAO",
        how="inner"
    ).drop("CD_PACIENTE", "DT_CIRURGIA")

    # cirurgias ambulatoriais (CD_INTERNACAO não existe em silver_internacoes)
    df_cirug_ambulatorial = df_cirug.join(
        df_intern.select("CD_INTERNACAO"),
        on="CD_INTERNACAO",
        how="left_anti"
    )

    # join de cirurgias ambulatoriais com emergência via CD_PACIENTE + janela temporal
    df_cirug_ambulatorial = df_cirug_ambulatorial.join(
        df_emerg.select("CD_ATENDIMENTO", "CD_PACIENTE", "DT_ATENDIMENTO"),
        on=(
            (df_cirug_ambulatorial["CD_PACIENTE"] == df_emerg["CD_PACIENTE"]) &
            (df_cirug_ambulatorial["DT_CIRURGIA"] >= df_emerg["DT_ATENDIMENTO"]) &
            (df_cirug_ambulatorial["DT_CIRURGIA"] <= F.date_add(df_emerg["DT_ATENDIMENTO"], 1))
        ),
        how="inner"
    ).drop(df_emerg["CD_PACIENTE"], "DT_ATENDIMENTO", "DT_CIRURGIA") \
     .withColumnRenamed("CD_ATENDIMENTO", "CD_ATENDIMENTO_AMBULATORIAL")

    # seleção das colunas necessárias na tabela de movimentações
    df_movim = df_movim.select(
        F.col("CD_INTERNACAO"),
        F.col("TIPO").alias("tipo_movimentacao"),
        F.col("ORIGEM").alias("origem_movimentacao"),
        F.col("DESTINO").alias("destino_movimentacao"),
        F.col("UNIDADE").alias("unidade_movimentacao"),
        F.col("DT_HR_MOVIMENTACAO")
    )

    # seleção das colunas necessárias na tabela de altas
    df_altas = df_altas.select(
        F.col("ATENDIMENTO").alias("CD_INTERNACAO"),
        F.col("DT_HR_ALTA_MEDICA").alias("ts_alta_medica"),
        F.col("DT_HR_ALTA_FINAL").alias("ts_alta_final")
    )

    # join entre as tabelas da emergência e internação
    df_emerg_intern = df_emerg.join(
        df_intern,
        on=(
            (df_emerg["CD_PACIENTE"] == df_intern["CD_PACIENTE"]) &
            (df_intern["ts_entrada_internacao"] >= df_emerg["DT_ATENDIMENTO"]) &
            (df_intern["ts_entrada_internacao"] <= F.date_add(df_emerg["DT_ATENDIMENTO"], 1))
        ),
        how="left"
    ).drop(df_intern["CD_PACIENTE"])

    # prefixos de leito UTI
    uti_prefixos = ["UTIA1", "UTIA2", "UTIB", "UCO", "UNP"]

    # entrada na UTI (destino é leito de UTI)
    condicao_entrada_uti = None
    for prefixo in uti_prefixos:
        cond = F.col("destino_movimentacao").startswith(prefixo)
        if condicao_entrada_uti is None:
            condicao_entrada_uti = cond
        else:
            condicao_entrada_uti = condicao_entrada_uti | cond

    # saída real da UTI (origem é leito de UTI e destino não)
    condicao_saida_uti = None
    for prefixo in uti_prefixos:
        cond = F.col("origem_movimentacao").startswith(prefixo)
        if condicao_saida_uti is None:
            condicao_saida_uti = cond
        else:
            condicao_saida_uti = condicao_saida_uti | cond
    condicao_saida_uti = condicao_saida_uti & ~condicao_entrada_uti

    # DataFrame para a primeira entrada na UTI
    df_primeira_entrada_uti = df_movim.filter(condicao_entrada_uti) \
        .groupBy("CD_INTERNACAO") \
        .agg(F.min("DT_HR_MOVIMENTACAO").alias("ts_primeira_entrada_uti"))
    
    # DataFrame para a saída da UTI
    df_ultima_saida_uti = df_movim.filter(condicao_saida_uti) \
        .groupBy("CD_INTERNACAO") \
        .agg(F.max("DT_HR_MOVIMENTACAO").alias("ts_ultima_saida_uti"))

    # DataFrame para contagem de passagens na UTI
    df_qtd_passagens_uti = df_movim.filter(condicao_entrada_uti) \
        .groupBy("CD_INTERNACAO") \
        .agg(F.count("DT_HR_MOVIMENTACAO").alias("qtd_passagens_uti"))

    # DataFrame de entradas
    df_entradas = df_movim.filter(condicao_entrada_uti) \
        .select("CD_INTERNACAO", F.col("DT_HR_MOVIMENTACAO").alias("ts_entrada"))
    
    # DataFrame de saídas
    df_saidas = df_movim.filter(condicao_saida_uti) \
        .select("CD_INTERNACAO", F.col("DT_HR_MOVIMENTACAO").alias("ts_saida"))
    
    # DataFrame do tempo de duração em UTI (minutos)
    df_duracao_uti = df_entradas.join(df_saidas, on="CD_INTERNACAO", how="left") \
        .filter(F.col("ts_saida") > F.col("ts_entrada")) \
        .groupBy("CD_INTERNACAO", "ts_entrada") \
        .agg(F.min("ts_saida").alias("ts_saida_correspondente")) \
        .withColumn("duracao_min", (F.unix_timestamp("ts_saida_correspondente") - F.unix_timestamp("ts_entrada")) / 60) \
        .groupBy("CD_INTERNACAO") \
        .agg(F.round(F.sum("duracao_min"), 0).cast("int").alias("duracao_total_uti_min"))
    
    # DataFrame sobre a jornada com internação em passagens pela UTI
    df_journey = df_emerg_intern \
        .join(df_primeira_entrada_uti, on="CD_INTERNACAO", how="left") \
        .join(df_ultima_saida_uti, on="CD_INTERNACAO", how="left") \
        .join(df_qtd_passagens_uti, on="CD_INTERNACAO", how="left") \
        .join(df_duracao_uti, on="CD_INTERNACAO", how="left")
    
    # unidades extras para exclusão do primeiro movimento de leito
    unidades_extras = ["BERCARIO - ALOJAMENTO CONJUNTO", "HEMODINAMICA", "OBSERVACAO PA", "EXTRA INTERNACAO"]

    # DataFrame com o timestamp do primeiro leito físico real
    df_primeiro_leito = df_movim.filter(
        ~F.col("unidade_movimentacao").isin(unidades_extras)
    ).groupBy("CD_INTERNACAO") \
     .agg(F.min("DT_HR_MOVIMENTACAO").alias("ts_primeiro_leito"))

    # DataFrame da jornada com junção das tabelas de cirurgias, movimentações e altas
    df_journey = df_journey \
        .join(df_cirug_internacao, on="CD_INTERNACAO", how="left") \
        .join(
            df_cirug_ambulatorial
                .drop("CD_INTERNACAO", "CD_PACIENTE")
                .withColumnRenamed("ts_entrada_cirurgia", "ts_entrada_cirurgia_amb")
                .withColumnRenamed("ts_saida_cirurgia", "ts_saida_cirurgia_amb"),
            on=F.col("CD_ATENDIMENTO") == F.col("CD_ATENDIMENTO_AMBULATORIAL"),
            how="left"
        ) \
        .withColumn("ts_entrada_cirurgia",
            F.coalesce(F.col("ts_entrada_cirurgia"), F.col("ts_entrada_cirurgia_amb"))) \
        .withColumn("ts_saida_cirurgia",
            F.coalesce(F.col("ts_saida_cirurgia"), F.col("ts_saida_cirurgia_amb"))) \
        .drop("ts_entrada_cirurgia_amb", "ts_saida_cirurgia_amb", "CD_ATENDIMENTO_AMBULATORIAL") \
        .join(df_altas, on="CD_INTERNACAO", how="left") \
        .join(df_primeiro_leito, on="CD_INTERNACAO", how="left")
    
    # adiciona colunas ao DataFrame da jornada
    df_journey = df_journey \
        .withColumn("has_uti", F.col("qtd_passagens_uti").isNotNull() & (F.col("qtd_passagens_uti") > 0)) \
        .withColumn("has_internacao", F.col("CD_INTERNACAO").isNotNull()) \
        .withColumn("has_cirurgia", F.col("ts_entrada_cirurgia").isNotNull()) \
        .withColumn("ano_mes", F.date_format(F.coalesce(F.col("ts_chegada"), F.col("ts_entrada_internacao")), "yyyy-MM")) \
        .withColumn("duracao_emergencia_internacao_min", (F.unix_timestamp("ts_entrada_internacao") - F.unix_timestamp("ts_chegada")) / 60) \
        .withColumn("duracao_internacao_cirurgia_min", (F.unix_timestamp("ts_entrada_cirurgia") - F.unix_timestamp("ts_entrada_internacao")) / 60) \
        .withColumn("duracao_cirurgia_leito_min", (F.unix_timestamp("ts_primeiro_leito") - F.unix_timestamp("ts_saida_cirurgia")) / 60) \
        .withColumn("duracao_total_min", (F.unix_timestamp("ts_alta_final") - F.unix_timestamp(F.coalesce(F.col("ts_chegada"), F.col("ts_entrada_internacao")))) / 60)

    # classificação das jornadas
    df_journey = df_journey.withColumn(
        "journey_type",
        F.when(
            F.col("CD_ATENDIMENTO").isNotNull() & F.col("CD_INTERNACAO").isNull() & F.col("ts_entrada_cirurgia").isNull(),
            F.lit("emergencia_pura")
        ).when(
            F.col("CD_ATENDIMENTO").isNotNull() & F.col("CD_INTERNACAO").isNull() & F.col("ts_entrada_cirurgia").isNotNull(),
            F.lit("emergencia_cirurgia_ambulatorial")
        ).when(
            F.col("CD_ATENDIMENTO").isNotNull() & F.col("CD_INTERNACAO").isNotNull() & F.col("ts_entrada_cirurgia").isNull(),
            F.lit("emergencia_internacao_clinica")
        ).when(
            F.col("CD_ATENDIMENTO").isNotNull() & F.col("CD_INTERNACAO").isNotNull() & F.col("ts_entrada_cirurgia").isNotNull(),
            F.lit("emergencia_internacao_cirurgica")
        ).when(
            F.col("CD_ATENDIMENTO").isNull() & F.col("CD_INTERNACAO").isNotNull() & F.col("ts_entrada_cirurgia").isNull(),
            F.lit("internacao_direta_clinica")
        ).otherwise(F.lit("internacao_direta_cirurgica"))
    )

    return df_journey.select(
        F.col("CD_ATENDIMENTO").alias("cd_atendimento"),
        F.col("CD_INTERNACAO").alias("cd_internacao"),
        F.col("CD_PACIENTE").alias("cd_paciente"),
        "journey_type",
        "ano_mes",
        "has_internacao",
        "has_cirurgia",
        "has_uti",
        "qtd_passagens_uti",
        "duracao_total_uti_min",
        "ts_chegada",
        "ts_entrada_internacao",
        "ts_entrada_cirurgia",
        "ts_saida_cirurgia",
        "ts_primeiro_leito",
        "ts_primeira_entrada_uti",
        "ts_ultima_saida_uti",
        "ts_alta_medica",
        "ts_alta_final",
        F.col("ORIGEM_ATEND").alias("origem_atendimento"),
        "duracao_emergencia_internacao_min",
        "duracao_internacao_cirurgia_min",
        "duracao_cirurgia_leito_min",
        "duracao_total_min"
    )
