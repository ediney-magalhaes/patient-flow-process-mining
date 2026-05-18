import os

import pandas as pd
from dotenv import load_dotenv

from src.anonymization.config import ColumnConfig
from src.anonymization.operations import drop_columns, generalize_birth_date, hash_value

#carrega variável de ambiente
load_dotenv()
SALT = os.getenv("SALT_ANONIMIZACAO")


def anonymize_file(filepath: str, config: ColumnConfig, output_dir: str) -> str:
    """Lê um arquivo, aplica anonimização e salva o resultado"""
    
    #verifica se o salt foi carregado do .env
    if SALT is None:
        raise ValueError("SALT_ANONIMIZACAO não encontrado. Verifique o arquivo .env")
    
    #verificação do tipo de arquivo para leitura correta
    if filepath.endswith(".csv"):
        df = pd.read_csv(filepath, encoding="latin-1", sep=";")
    else:
        df = pd.read_excel(filepath)

    #exclui as colunas "descartáveis"
    df = drop_columns(df, config.drop_columns)

    #percorre as colunas que necessitam de hash
    for col in config.hash_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).apply(lambda x: hash_value(x, SALT))
    
    #percorre o dicionário para aplicação da generalização
    for col, method in config.generalize_columns.items():
        if method == "age_only":
            df = generalize_birth_date(df, col)
    
    #nome do arquivo de saída
    filename = f'{config.name}_anonimizado.csv'
    #junta pasta de saída com nome do arquivo
    output_path = os.path.join(output_dir, filename)
    #salva arquivo como csv
    df.to_csv(output_path, index=False, encoding="utf-8-sig", sep=";")
    #retorna o caminho do arquivo gerado
    return output_path
    