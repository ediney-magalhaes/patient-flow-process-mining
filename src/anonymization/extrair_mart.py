"""Extrai a mart curada de atendimentos do PA (projeto GCP) para data/raw.

Uso (PowerShell, com a .venv ativa):
    python -m src.anonymization.extrair_mart 2026-03
    python -m src.anonymization.extrair_mart 2026-03 2026-04 2026-05   # varias competencias

Gera data/raw/atendimento_emergencia_AAAA_MM.xlsx, que segue pelo run.py
(anonimizacao) exatamente como o export bruto seguia. Decisao: ADR-0024.
"""
import os
import re
import sys
from datetime import date

import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery

# carrega o .env (PROJECT_ID) para a variavel de ambiente, como faz o enrichment.py
load_dotenv()
PROJECT_ID = os.getenv("PROJECT_ID")

# pasta onde o run.py procura os arquivos de entrada
RAW_DIR = "data/raw"

# tabela de origem: a mart inteira, sem escolher colunas (ADR-0024)
QUERY = """
    SELECT *
    FROM `pipeline-analytics-emergencia.marts.atendimentos_pa`
    WHERE competencia = @competencia
"""


def consultar_competencia(competencia: str) -> pd.DataFrame:
    """Le da mart todos os atendimentos de uma competencia ('AAAA-MM')."""
    # separa ano e mes do texto recebido
    ano, mes = competencia.split("-")

    # no BigQuery, competencia e uma coluna DATE sempre no dia 1 (ex.: 2026-03-01)
    primeiro_dia = date(int(ano), int(mes), 1)

    client = bigquery.Client(project=PROJECT_ID)

    # parametro nomeado e tipado: o BigQuery valida o tipo e nao ha texto concatenado no SQL
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("competencia", "DATE", primeiro_dia)]
    )

    # executa a consulta e traz o resultado como DataFrame do pandas
    return client.query(QUERY, job_config=job_config).to_dataframe()


def validar(df: pd.DataFrame, competencia: str) -> None:
    """Interrompe a extracao se a competencia vier vazia ou com atendimento repetido."""
    # competencia sem linhas: nome errado ou mes ainda nao carregado no projeto GCP
    if df.empty:
        raise ValueError(f"Competencia {competencia}: a mart nao retornou nenhuma linha")

    # a mart tem um atendimento por linha; repeticao indica problema na origem
    duplicados = int(df["atend_PA"].duplicated().sum())
    if duplicados > 0:
        raise ValueError(f"Competencia {competencia}: {duplicados} atend_PA repetidos na mart")


def normalizar_tipos(df: pd.DataFrame) -> pd.DataFrame:
    """Converte colunas DATE do BigQuery (dtype 'dbdate') para datetime comum do pandas."""
    # 'dbdate' e um tipo de extensao que o to_excel nao grava; datetime64 e aceito
    for coluna in df.columns:
        if str(df[coluna].dtype) == "dbdate":
            df[coluna] = pd.to_datetime(df[coluna])
    return df


def extrair(competencia: str) -> str:
    """Extrai uma competencia e grava o arquivo em data/raw. Retorna o caminho."""
    # aceita apenas o formato AAAA-MM
    if re.fullmatch(r"\d{4}-\d{2}", competencia) is None:
        raise ValueError(f"Competencia fora do formato AAAA-MM: {competencia}")

    df = consultar_competencia(competencia)
    validar(df, competencia)
    df = normalizar_tipos(df)

    # nome no padrao nome-base_AAAA_MM, que o run.py usa para achar a config
    os.makedirs(RAW_DIR, exist_ok=True)
    caminho = os.path.join(RAW_DIR, f"atendimento_emergencia_{competencia.replace('-', '_')}.xlsx")
    df.to_excel(caminho, index=False)

    # resumo para conferir contra o BigQuery
    sem_chegada = int(df["DT_HR_TOTEM_RECEP"].isna().sum())
    print(f"{competencia}: {len(df)} atendimentos, {sem_chegada} sem chegada -> {caminho}")
    return caminho


def main() -> None:
    competencias = sys.argv[1:]
    if not competencias:
        print("Informe ao menos uma competencia (AAAA-MM). Ex.: python -m src.anonymization.extrair_mart 2026-03")
        sys.exit(1)
    for competencia in competencias:
        extrair(competencia)


if __name__ == "__main__":
    main()