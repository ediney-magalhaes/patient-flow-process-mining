import pandas as pd
import os
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()
PROJECT_ID = os.getenv("PROJECT_ID")

# função para descobrir a competência presentes no DataFrame
def get_competencias(df: pd.DataFrame, date_column: str) -> list[str]:
    """Extrai as competências (yyy-MM-01) distintas presentes no DataFrame"""
    competencias = df[date_column].dt.to_period("M").dt.to_timestamp().dt.strftime("%Y-%m-%d")
    return competencias.unique().tolist()

# função para consulta no BigQuery
def buscar_conversao_curada(competencias: list[str]) -> pd.DataFrame:
    """Busca fl_conversao e fl_evasao curados no BigQuery para as competências informadas"""
    client = bigquery.Client(project=PROJECT_ID)

    query = """
        SELECT DISTINCT
            atend_PA,
            atend_internacao,
            fl_conversao,
            fl_evasao
        FROM `pipeline-analytics-emergencia.marts.atendimentos_pa`
        WHERE competencia IN UNNEST(@competencias)
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("competencias", "DATE", competencias),
        ]
    )

    return client.query(query, job_config=job_config).to_dataframe()