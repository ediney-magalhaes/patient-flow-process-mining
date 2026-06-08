import dlt
from pyspark.sql.functions import col, to_date, to_timestamp, concat_ws, trim, regexp_replace, when, lit, row_number
from pyspark.sql.window import Window
#---------------------------------------------------------------------------------------------------------------------
# materialização da tabela de ALTAS
#---------------------------------------------------------------------------------------------------------------------
@dlt.table(
  name="silver_altas",
  comment="Tabela silver de altas hospitalares — tipada, deduplicada e limpa"
)
# regra de qualidade de dados
@dlt.expect_or_drop("atendimento_valido", "ATENDIMENTO IS NOT NULL")
def silver_altas():
    
    # leitura da tabela bronze_altas_raw
    df = spark.read.table("hospital_santa_rosa.bronze_fluxo.bronze_altas_raw")
    
    # correção do encoding: 1? Andar -> 1º Andar
    df = df.withColumn("UNID_INT", regexp_replace(col("UNID_INT"), r"\?", "o"))
    
    # combina data + hora em timestamp unico
    df = (
        df
        .withColumn("DT_HR_ATENDIMENTO", to_timestamp(concat_ws(" ", col("DT_ATENDIMENTO"), col("HR_ATENDIMENTO"))))
        .withColumn("DT_HR_ALTA_MEDICA", to_timestamp(concat_ws(" ", col("DT_ALTA_MEDICA"), col("HR_ALTA_MEDICA"))))
        .withColumn("DT_HR_ALTA_FINAL", to_timestamp(concat_ws(" ", col("DT_ALTA_FINAL"), col("HR_ALTA_FINAL"))))
        .withColumn("DT_HR_PRE_MED", to_timestamp(col("HR_PRE_MED")))
    )
    
    # converte colunas numericas de string para inteiro
    df = (
        df
        .withColumn("COD_CONVENIO", col("COD_CONVENIO").cast("int"))
        .withColumn("QTD_DIARIAS_UTI", col("QTD_DIARIAS_UTI").cast("int"))
        .withColumn("QTD_DIARIAS_UNID_ABERTA", col("QTD_DIARIAS_UNID_ABERTA").cast("int"))
    )

    # deduplica: mantém apenas o registro mais recente por atendimento
    window = Window.partitionBy("ATENDIMENTO").orderBy(col("DT_HR_PRE_MED").desc_nulls_last())
    df = df.withColumn("_row_num", row_number().over(window))
    df = df.filter(col("_row_num") == 1).drop("_row_num")
    
    # remove colunas desnecessárias originais de data/hora separadas e metadados de ingestao
    df = df.drop(
        "DT_ATENDIMENTO", "HR_ATENDIMENTO",
        "DT_ALTA_MEDICA", "HR_ALTA_MEDICA",
        "DT_ALTA_FINAL", "HR_ALTA_FINAL",
        "HR_PRE_MED", "FREQUENCIA",
        "_rescued_data", "_source_file", "_ingestion_timestamp"
    )
    return df

#---------------------------------------------------------------------------------------------------------------------
# materialização da tabela de ATENDIMENTOS EMERGÊNCIA
#---------------------------------------------------------------------------------------------------------------------
@dlt.table(
    name="silver_atendimento_emergencia",
    comment="Tabela Silver de atendimentos de emergencia - tipada, deduplicada e limpa"
)
# monitoramento de qualidade dos tempos para cada etapa do fluxo
@dlt.expect("flag_totem_classif", "DT_HR_TOTEM_RECEP <= INICIO_CLASSIFICACAO OR DT_HR_TOTEM_RECEP IS NULL OR INICIO_CLASSIFICACAO IS NULL")
@dlt.expect("flag_classif_recep", "DT_HR_CLASSIF_RISCO <= DH_CADASTRO_RECEPCAO OR DT_HR_CLASSIF_RISCO IS NULL OR DH_CADASTRO_RECEPCAO IS NULL")
@dlt.expect("flag_recep_atend", "FIM_CAD_RECEP <= INI_ATD_MEDICO OR FIM_CAD_RECEP IS NULL OR INI_ATD_MEDICO IS NULL")
@dlt.expect("flag_atend_alta", "FIM_ATD_MEDICO <= DT_HR_ALTA OR FIM_ATD_MEDICO IS NULL OR DT_HR_ALTA IS NULL")
def silver_atendimento_emergencia():
    df = spark.read.table("hospital_santa_rosa.bronze_fluxo.bronze_atendimento_emergencia_raw")

    # filtra apenas atendimentos do Hospital Santa Rosa
    df = df.filter(col("EMPRESA") == "HSR")

    # converte colunas de timestamp de string para timestamp
    timestamp_cols = [
        "DT_HR_TOTEM_RECEP", "CHAMADA_CLASSIFICACAO", "INICIO_CLASSIFICACAO",
        "DT_HR_CLASSIF_RISCO", "CHAMADA_CAD_RECEP", "DH_CADASTRO_RECEPCAO",
        "FIM_CAD_RECEP", "DH_ATEND_MEDICO", "INI_ATD_MEDICO", "FIM_ATD_MEDICO",
        "DT_HR_TRANF_LEITO", "DT_HR_SAIDA_LEITO", "DT_HR_ALTA"
    ]
    for c in timestamp_cols:
        df = df.withColumn(c, to_timestamp(col(c)))
    
    # converte data de atendimento para date
    df = df.withColumn("DT_ATENDIMENTO", to_date(col("DT_ATENDIMENTO")))

    # converte colunas numericas de string para inteiro
    df = (
        df
        .withColumn("IDADE", col("IDADE").cast("int"))
        .withColumn("COD_TRIAGEM", col("COD_TRIAGEM").cast("int"))
        .withColumn("REGISTRO_ANS", col("REGISTRO_ANS").cast("int"))
        .withColumn("IDADE_CALCULADA", col("IDADE_CALCULADA").cast("int"))
    )

    # padroniza classificacao de risco: AMARELO1 -> AMARELO
    df = df.withColumn("COR_CLASSIF", regexp_replace(col("COR_CLASSIF"), "AMARELO1", "AMARELO"))

    # flags de inconsistência temporal
    df = (
        df
        .withColumn("flag_totem_classif",
                    when(
                        (col("DT_HR_TOTEM_RECEP").isNotNull()) & (col("INICIO_CLASSIFICACAO").isNotNull()) & 
                        (col("DT_HR_TOTEM_RECEP") > col("INICIO_CLASSIFICACAO")),
                        lit(True)
                    ).otherwise(lit(False))
        )
        .withColumn("flag_classif_recep",
                    when(
                        (col("DT_HR_CLASSIF_RISCO").isNotNull()) & (col("DH_CADASTRO_RECEPCAO").isNotNull()) & 
                        (col("DT_HR_CLASSIF_RISCO") > col("DH_CADASTRO_RECEPCAO")),
                        lit(True)
                    ).otherwise(lit(False))
        )
        .withColumn("flag_recep_atend",
                    when(
                        (col("FIM_CAD_RECEP").isNotNull()) & (col("INI_ATD_MEDICO").isNotNull()) &
                        (col("FIM_CAD_RECEP") > col("INI_ATD_MEDICO")),
                        lit(True)
                    ).otherwise(lit(False))
        )
        .withColumn("flag_atend_alta",
                    when(
                        (col("FIM_ATD_MEDICO").isNotNull()) & (col("DT_HR_ALTA").isNotNull()) &
                        (col("FIM_ATD_MEDICO") > col("DT_HR_ALTA")),
                        lit(True)
                    ).otherwise(lit(False))
        )
    )
    # remove colunas financeiras e metadados
    df = df.drop(
        "CONTA", "TOTAL_CONTA", "CONTA_FECHADA",
        "CD_LEITO", "ENCAMINHADO_LEITO", "DT_HR_TRANF_LEITO", "DT_HR_SAIDA_LEITO",
        "DT_ATENDIMENTO_FILTRO", "IDADE", "EMPRESA",
        "_rescued_data", "_source_file", "_ingestion_timestamp"
    )

    # deduplicação da coluna CD_ATENDIMENTO, mantém a coluna mais antiga
    window = Window.partitionBy("CD_ATENDIMENTO").orderBy(col("DT_HR_CLASSIF_RISCO").asc_nulls_last())
    df = df.withColumn("_row_num", row_number().over(window))
    df = df.filter(col("_row_num") == 1).drop("_row_num")
    return df

#---------------------------------------------------------------------------------------------------------------------
# materialização da tabela de CIRURGIAS REALIZADAS
#---------------------------------------------------------------------------------------------------------------------
@dlt.table(
    name="silver_cirurgias",
    comment="Tabela Silver de cirurgias realizadas - tipada e limpa, granularidade por procedimento"
)
@dlt.expect("flag_entrada_anestesia", "DT_HR_ENTRADA_SALA_CIRURG <= INICIO_ANESTESIA OR DT_HR_ENTRADA_SALA_CIRURG IS NULL OR INICIO_ANESTESIA IS NULL")
@dlt.expect("flag_anestesia_cirurgia", "INICIO_ANESTESIA <= DT_INICIO_CIRURGIA OR INICIO_ANESTESIA IS NULL OR DT_INICIO_CIRURGIA IS NULL")
@dlt.expect("flag_cirurgia_fim", "DT_INICIO_CIRURGIA <= DT_FIM_CIRURGIA OR DT_INICIO_CIRURGIA IS NULL OR DT_FIM_CIRURGIA IS NULL")
@dlt.expect("flag_fim_anestesia", "DT_FIM_CIRURGIA <= FIM_ANESTESIA OR DT_FIM_CIRURGIA IS NULL OR FIM_ANESTESIA IS NULL")
@dlt.expect("flag_anestesia_saida", "FIM_ANESTESIA <= DT_HR_SAIDA_SALA_CIRURG OR FIM_ANESTESIA IS NULL OR DT_HR_SAIDA_SALA_CIRURG IS NULL")
def silver_cirurgias():
    df = spark.read.table("hospital_santa_rosa.bronze_fluxo.bronze_cirurgias_raw")
    
    # correcao de encoding
    df = df.withColumn("SEXO", regexp_replace(col("SEXO"), "MASCULIN0", "MASCULINO"))
    df = df.withColumn("TIPO_ATENDIMENTO", regexp_replace(col("TIPO_ATENDIMENTO"), r"INTERNAC\?O", "INTERNACAO"))

    # converte colunas de timestamp de string para timestamp
    timestamp_cols = [
        "DT_AVISO_CIRURGIA", "DT_AGENDA_CIR", "INICIO_PROGRAMADO_CIRURGIA",
        "FINAL_PROGRAMADO_CIRURGIA", "DATA_INICIO_CIRURGIA",
        "DT_HR_ENTRADA_SALA_CIRURG", "DT_HR_SAIDA_SALA_CIRURG",
        "INICIO_ANESTESIA", "FIM_ANESTESIA", "INICIO_LIMPEZA", "FIM_LIMPEZA",
        "DT_INICIO_CIRURGIA", "DT_FIM_CIRURGIA"
    ]
    for c in timestamp_cols:
        df = df.withColumn(c, to_timestamp(col(c)))
    
    # converte colunas numericas de string para inteiro
    df = (
        df
        .withColumn("IDADE", col("IDADE").cast("int"))
        .withColumn("CD_AVISO_CIRURGIA", col("CD_AVISO_CIRURGIA").cast("int"))
        .withColumn("CD_CIRURGIA_AVISO", col("CD_CIRURGIA_AVISO").cast("int"))
        .withColumn("CODIGO_CIRURGIA", col("CODIGO_CIRURGIA").cast("int"))
        .withColumn("COD_FATURAMENTO", col("COD_FATURAMENTO").cast("int"))
    )

    # flags de inconsistencia temporal
    df = (
        df
        .withColumn("flag_entrada_anestesia",
            when(
                (col("DT_HR_ENTRADA_SALA_CIRURG").isNotNull()) & (col("INICIO_ANESTESIA").isNotNull()) &
                (col("DT_HR_ENTRADA_SALA_CIRURG") > col("INICIO_ANESTESIA")),
                lit(True)
            ).otherwise(lit(False))
        )
        .withColumn("flag_anestesia_cirurgia",
            when(
                (col("INICIO_ANESTESIA").isNotNull()) & (col("DT_INICIO_CIRURGIA").isNotNull()) &
                (col("INICIO_ANESTESIA") > col("DT_INICIO_CIRURGIA")),
                lit(True)
            ).otherwise(lit(False))
        )
        .withColumn("flag_cirurgia_fim",
            when(
                (col("DT_INICIO_CIRURGIA").isNotNull()) & (col("DT_FIM_CIRURGIA").isNotNull()) &
                (col("DT_INICIO_CIRURGIA") > col("DT_FIM_CIRURGIA")),
                lit(True)
            ).otherwise(lit(False))
        )
        .withColumn("flag_fim_anestesia",
            when(
                (col("DT_FIM_CIRURGIA").isNotNull()) & (col("FIM_ANESTESIA").isNotNull()) &
                (col("DT_FIM_CIRURGIA") > col("FIM_ANESTESIA")),
                lit(True)
            ).otherwise(lit(False))
        )
        .withColumn("flag_anestesia_saida",
            when(
                (col("FIM_ANESTESIA").isNotNull()) & (col("DT_HR_SAIDA_SALA_CIRURG").isNotNull()) &
                (col("FIM_ANESTESIA") > col("DT_HR_SAIDA_SALA_CIRURG")),
                lit(True)
            ).otherwise(lit(False))
        )
    )

    # remove colunas desnecessarias
    df = df.drop(
        "data", "hora", "Dia",
        "tempo", "tempo_acesso", "Tempo_permanencia",
        "ATRASO_CIRURGIA", "GIRO_SALA",
        "HORÁRIO_ADM_ATB", "TEMPO ATB", "ATB < 60min?",
        "DT_HR_ENTRADA_RPA", "DT_HR_SAIDA_RPA", "LOCAL_TRANSF_POS_CIRURGIA",
        "UNID_INT_POS_CIR", "LEITO_POS_CIR", "DT_CHEGADA_RPA",
        "DT_ALTA_ANESTESIA", "ANESTESISTA", "DT_SAIDA_RPA",
        "Tempo_permanencia", "USU_CONF_REGISTRO",
        "_rescued_data", "_source_file", "_ingestion_timestamp"
    )
    return df

#---------------------------------------------------------------------------------------------------------------------
# materialização da tabela EPIDEMIO (enrequecimento dos dados)
#---------------------------------------------------------------------------------------------------------------------
@dlt.table(
    name="silver_epidemio",
    comment="Tabela Silver epidemiologica - tipada e limpa, base de enriquecimento"
)
# regra de qualidade de dados
@dlt.expect_or_drop("atendimento_valido", "atendimento IS NOT NULL")
def silver_epidemio():
    df = spark.read.table("hospital_santa_rosa.bronze_fluxo.bronze_epidemio_raw")
    
    # converte timestamps formato brasileiro (dd/MM/yyyy HH:mm)
    df = df.withColumn("dt_atendimento", to_timestamp(col("dt_atendimento"), "dd/MM/yyyy HH:mm"))
    df = df.withColumn("hr_pre_med", to_timestamp(col("hr_pre_med"), "dd/MM/yyyy HH:mm:ss"))

    # converte timestamps formato ISO
    df = df.withColumn("previsao_alta", to_timestamp(col("previsao_alta")))
    df = df.withColumn("dtsumario", to_timestamp(col("dtsumario")))

    # combina dt_alta + hr_alta em timestamp unico
    df = df.withColumn("dt_hr_alta", to_timestamp(concat_ws(" ", col("dt_alta"), col("hr_alta")), "dd/MM/yyyy HH:mm:ss"))

    # Converte dates formato brasileiro (dd/MM/yyyy)
    df = df.withColumn("entrada_uti", to_date(col("entrada_uti"), "dd/MM/yyyy"))
    df = df.withColumn("dt_saida", to_date(col("dt_saida"), "dd/MM/yyyy"))

    # converte dates formato brasileiro com ano 2 digitos (dd/MM/yy)
    df = df.withColumn("dt_proc_1", to_date(col("dt_proc_1"), "dd/MM/yy"))
    df = df.withColumn("dt_proc_2", to_date(col("dt_proc_2"), "dd/MM/yy"))

    # converte colunas numericas inteiras
    int_cols = [
        "idade", "registro_ans", "nr_dias",
        "cod_proc_1", "cod_proc_2", "cd_cirurgia_1", "cd_cirurgia_2",
        "qtd_diarias_uti", "qtd_uco", "qtd_uco_retag",
        "qtd_uti_geral", "qtd_uti_cirurgica_2", "qtd_uti_geral_3",
        "qtd_uti_neo", "qtd_uti_ped", "qtd_uti_alerta", "qtd_passagens_uti"
    ]
    for c in int_cols:
        df = df.withColumn(c, col(c).cast("int"))

    # remove colunas desnecessarias
    df = df.drop(
        "dt_alta", "hr_alta",
        "vl_conta", "vl_honorario",
        "saps3_admissao", "saps3_obito", "peso_nascer",
        "sn_fechada",
        "CAPÍTULO BREVE", "GRUPO",
        "_rescued_data", "_source_file", "_ingestion_timestamp"
    )
    return df

#---------------------------------------------------------------------------------------------------------------------
# materialização da tabela de exames de imagem
#---------------------------------------------------------------------------------------------------------------------
@dlt.expect("flag_prescricao_admissao", "flag_prescricao_admissao IS NULL OR flag_prescricao_admissao = true")
@dlt.expect("flag_admissao_inicio", "flag_admissao_inicio IS NULL OR flag_admissao_inicio = true")
@dlt.expect("flag_inicio_termino", "flag_inicio_termino IS NULL OR flag_inicio_termino = true")
@dlt.expect("flag_termino_liberado", "flag_termino_liberado IS NULL OR flag_termino_liberado = true")
@dlt.table(
    name="silver_exames_imagem",
    comment="Tabela silver de exames de imagem — tipada, limpa e com flags de consistência temporal"
)
def siver_exames_imagem():
    # leitura da tabela bronze_exames_imagem_raw
    df = spark.read.table("hospital_santa_rosa.bronze_fluxo.bronze_exames_imagem_raw")
    
    # mantém apenas registros do HSR
    df = df.filter(col("Unidade") == "HSR")

    # substitui "//" por null
    colunas_com_barra = [
        "DATA_DITADO", "DATA_HORA_PRESCRICAO", "DATA_LAUDO",
        "STATUS_A_REVISAR", "STATUS_A_TRANSCREVER", "STATUS_ADMITIDO",
        "STATUS_APROVADO", "STATUS_CANCELADO_RIS", "STATUS_EDITAR_LAUDO",
        "STATUS_FIM_PREPARO", "STATUS_INICIO_EXAME", "STATUS_INICIO_PREPARO",
        "STATUS_LIBERADO", "STATUS_PACIENTE_RECONVOCADO", "STATUS_PAUSA_EXAME",
        "STATUS_PENDENCIA", "STATUS_PENDENCIA_ANDAMENTO", "STATUS_PRELIMINAR",
        "STATUS_PRONTO_RETIRAR", "STATUS_RETIRADO", "STATUS_TERMINO_EXAME",
        "STATUS_WETREAD"
    ]

    for coluna in colunas_com_barra:
        df = df.withColumn(coluna, when(col(coluna) == "//", None).otherwise(col(coluna)))
    
    # converte timestamps em formato (dd/MM/yyyy HH:mm)
    colunas_timestamps_br = [
    "DATA_DITADO", "DATA_LAUDO",
    "STATUS_A_REVISAR", "STATUS_A_TRANSCREVER", "STATUS_ADMITIDO",
    "STATUS_APROVADO", "STATUS_CANCELADO_RIS", "STATUS_EDITAR_LAUDO",
    "STATUS_FIM_PREPARO", "STATUS_INICIO_EXAME", "STATUS_INICIO_PREPARO",
    "STATUS_LIBERADO", "STATUS_PACIENTE_RECONVOCADO", "STATUS_PAUSA_EXAME",
    "STATUS_PENDENCIA", "STATUS_PENDENCIA_ANDAMENTO", "STATUS_PRELIMINAR",
    "STATUS_PRONTO_RETIRAR", "STATUS_RETIRADO", "STATUS_TERMINO_EXAME",
    "STATUS_WETREAD"
    ]

    for coluna in colunas_timestamps_br:
        df = df.withColumn(coluna, to_timestamp(col(coluna), "dd/MM/yyyy HH:mm"))
    
    # converte DATA_HORA_PRESCRICAO — insere espaco faltante antes de converter
    df = df.withColumn(
        "DATA_HORA_PRESCRICAO",
        to_timestamp(
            regexp_replace(col("DATA_HORA_PRESCRICAO"), r"(\d{2}/\d{2}/\d{4})(\d{2}:\d{2})", "$1 $2"),
            "dd/MM/yyyy HH:mm"
        )
    )

    # converte timestamps em ISO (yyyy-MM-dd HH:mm:ss) para timestamp
    df = df.withColumn("DH_MAX", to_timestamp(col("DH_MAX"), "yyyy-MM-dd HH:mm:ss"))
    df = df.withColumn("DH_MIN", to_timestamp(col("DH_MIN"), "yyyy-MM-dd HH:mm:ss"))

    # converte coluna numérica de string para inteiro
    df = df.withColumn("CODIGO_PROCEDIMENTO", col("CODIGO_PROCEDIMENTO").cast("int"))

    # flags de consistência temporal
    # TRUE = sequência correta, FALSE = inconsistência encontrada
    df = (
        df
        .withColumn("flag_prescricao_admissao",
            when(
                col("DATA_HORA_PRESCRICAO").isNull() | col("STATUS_ADMITIDO").isNull(), None
            ).otherwise(col("DATA_HORA_PRESCRICAO") <= col("STATUS_ADMITIDO"))
        )
        .withColumn("flag_admissao_inicio",
            when(
                col("STATUS_ADMITIDO").isNull() | col("STATUS_INICIO_EXAME").isNull(), None
            ).otherwise(col("STATUS_ADMITIDO") <= col("STATUS_INICIO_EXAME"))
        )
        .withColumn("flag_inicio_termino",
            when(
                col("STATUS_INICIO_EXAME").isNull() | col("STATUS_TERMINO_EXAME").isNull(), None
            ).otherwise(col("STATUS_INICIO_EXAME") <= col("STATUS_TERMINO_EXAME"))
        )
        .withColumn("flag_termino_liberado",
            when(
                col("STATUS_TERMINO_EXAME").isNull() | col("STATUS_LIBERADO").isNull(), None
            ).otherwise(col("STATUS_TERMINO_EXAME") <= col("STATUS_LIBERADO"))
        )
    )

    # deduplicação por atendimento - procedimento
    numero_linha = Window.partitionBy("CD_ATENDIMENTO", "CODIGO_PROCEDIMENTO").orderBy(col("DH_MIN").asc_nulls_last())
    df = df.withColumn("linha", row_number().over(numero_linha))
    df = df.filter(col("linha") == 1)
    df = df.drop("linha")

    # remove colunas desnecessárias
    df = df.drop(
        "DIA", "MES", "MES_ANO",
        "NUMERO_ATENDIMENTO",
        "Contagem Linhas",
        "_rescued_data", "_source_file", "_ingestion_timestamp"
    )

    return df

#---------------------------------------------------------------------------------------------------------------------
# materialização da tabela de exames laboratoriais
#---------------------------------------------------------------------------------------------------------------------
@dlt.expect("flag_pedido_coleta", "flag_pedido_coleta IS NULL OR flag_pedido_coleta = true")
@dlt.expect("flag_coleta_laudo", "flag_coleta_laudo IS NULL OR flag_coleta_laudo = true")
@dlt.table(
    name="silver_exames_laboratoriais",
    comment="Tabela silver de exames laboratoriais — tipada, limpa e com flags de consistência temporal"
)
def silver_exames_laboratoriais():
    # leitura da tabela bronze_exames_laboratoriais_raw
    df = spark.read.table("hospital_santa_rosa.bronze_fluxo.bronze_exames_laboratoriais_raw")

    # renomeia ATEND para CD_ATENDIMENTO
    df = df.withColumnRenamed("ATEND", "CD_ATENDIMENTO")

    # converte colunas timestamps formato ISO (yyyy-MM-dd HH:mm:ss) para timestamp
    colunas_timestamp = ["HR_PED_LAB", "DT_COLETA", "HR_LAUDO_LAB", "HR_CHAM_MED"]

    for coluna in colunas_timestamp:
        df = df.withColumn(coluna, to_timestamp(col(coluna), "yyyy-MM-dd HH:mm:ss"))
    
    # flags de consistência temporal (True = sequência correta, False = inconsistência encontrada)
    df = (
        df
        .withColumn("flag_pedido_coleta",
            when(
                col("HR_PED_LAB").isNull() | col("DT_COLETA").isNull(), None
            ).otherwise(col("HR_PED_LAB") <= col("DT_COLETA"))
        )
        .withColumn("flag_coleta_laudo",
            when(
                col("DT_COLETA").isNull() | col("HR_LAUDO_LAB").isNull(), None
            ).otherwise(col("DT_COLETA") <= col("HR_LAUDO_LAB"))
        )
    )

    # deduplicação por atendimento + exame
    numero_linha = Window.partitionBy("CD_ATENDIMENTO", "CD_EXAME").orderBy(col("HR_PED_LAB").asc_nulls_last())
    df = df.withColumn("linha", row_number().over(numero_linha))
    df = df.filter(col("linha") == 1)
    df = df.drop("linha")

    # remove colunas desnecessárias
    df = df.drop(
        "_rescued_data", "_source_file", "_ingestion_timestamp"
    )

    return df

#---------------------------------------------------------------------------------------------------------------------
# materialização da tabela de internações
#---------------------------------------------------------------------------------------------------------------------
@dlt.expect("flag_atendimento_alta", "flag_atendimento_alta IS NULL OR flag_atendimento_alta = true")
@dlt.table(
    name="silver_internacoes",
    comment="Tabela silver de internações — tipada, deduplicada e com flag de consistência temporal"
)
def silver_internacoes():
    # leitura da tabela bronze_internacoes_raw
    df = spark.read.table("hospital_santa_rosa.bronze_fluxo.bronze_internacoes_raw")

    # renomeia ATENDIMENTO para CD_INTERNACAO
    df = df.withColumnRenamed("ATENDIMENTO", "CD_INTERNACAO")

    # converter colunas timestamp
    df = df.withColumn("DT_HR_ATENDIMENTO", to_timestamp(col("DT_HR_ATENDIMENTO"), "yyyy-MM-dd HH:mm:ss"))
    df = df.withColumn("DT_HR_ALTA", to_timestamp(col("DT_HR_ALTA"), "yyyy-MM-dd HH:mm:ss"))

    # converte colunas numéricas de string para inteiro
    for coluna in ["IDADE", "CD_ORIGEM"]:
        df = df.withColumn(coluna, col(coluna).cast("int"))
    
    # flag de consistência temporal (True = sequência correta, False = inconsistência encontrada)
    df = df.withColumn("flag_atendimento_alta",
        when(
            col("DT_HR_ATENDIMENTO").isNull() | col("DT_HR_ALTA").isNull(), None
            ).otherwise(col("DT_HR_ATENDIMENTO") <= col("DT_HR_ALTA"))
    )

    # deduplicacao por CD_ATENDIMENTO
    numero_linha = Window.partitionBy("CD_INTERNACAO").orderBy(col("DT_HR_ATENDIMENTO").asc_nulls_last())
    df = df.withColumn("linha", row_number().over(numero_linha))
    df = df.filter(col("linha") == 1)
    df = df.drop("linha")

    # remove colunas desnecessárias
    df = df.drop(
        "CD_LEITO",
        "_rescued_data", "_source_file", "_ingestion_timestamp"
    )

    return df

#---------------------------------------------------------------------------------------------------------------------
# materialização da tabela de movimentações
#---------------------------------------------------------------------------------------------------------------------
@dlt.table(
    name="silver_movimentacoes",
    comment="Tabela silver de movimentações de leito — tipada, limpa e deduplicada"
)
def silver_movimentacoes():
    # leitura da bronze_movimentacoes_raw
    df = spark.read.table("hospital_santa_rosa.bronze_fluxo.bronze_movimentacoes_raw")

    # renomeia ATEND para CD_INTERNACAO
    df = df.withColumnRenamed("ATEND", "CD_INTERNACAO")

    # corrige enconding quebrado na coluna UNIDADE
    df = df.withColumn("UNIDADE", regexp_replace(col("UNIDADE"), "Âº", "º"))

    # combina DATA + HORA em timestamp único DT_HR_MOVIMENTACAO
    df = df.withColumn(
        "DT_HR_MOVIMENTACAO",
        to_timestamp(concat_ws(" ", col("DATA"), col("HORA")), "yyyy-MM-dd HH:mm:ss")
    )

    # deduplicação por internação + timestamp + tipo de movimentação
    numero_linha = Window.partitionBy("CD_INTERNACAO", "DT_HR_MOVIMENTACAO", "TIPO").orderBy(col("DT_HR_MOVIMENTACAO").asc_nulls_last())
    df = df.withColumn("linha", row_number().over(numero_linha))
    df = df.filter(col("linha") == 1)
    df = df.drop("linha")

    # remove colunas desnecessárias
    df = df.drop(
        "DATA", "HORA",
        "_rescued_data", "_source_file", "_ingestion_timestamp"
    )

    return df