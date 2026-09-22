import os
import sys

from databricks import sql
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("DATABRICKS_SERVER_HOSTNAME")
HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH")
TOKEN = os.getenv("DATABRICKS_TOKEN")


def rodar_consulta(query: str) -> None:
    """Conecta ao SQL Warehouse e imprime o resultado de uma query"""
    with sql.connect(
        server_hostname=HOST,
        http_path=HTTP_PATH,
        access_token=TOKEN,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            colunas = [c[0] for c in cursor.description]
            print(" | ".join(colunas))
            for linha in cursor.fetchall():
                print(" | ".join(str(v) for v in linha))


if __name__ == "__main__":
    # a query vem como argumento de linha de comando, entre aspas
    if len(sys.argv) < 2:
        print("Uso: python consultar_databricks.py \"SELECT ...\"")
        sys.exit(1)
    rodar_consulta(sys.argv[1])