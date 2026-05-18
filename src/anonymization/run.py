import os
import sys

from src.anonymization.config import ANONYMIZATION_CONFIGS
from src.anonymization.processor import anonymize_file


def find_config(name: str):
    """Busca a configuração de anonimização pelo nome da base"""
    for config in ANONYMIZATION_CONFIGS:
        if config.name == name:
            return config
    return None


def main():
    """Executa a anonimização dos arquivos"""
    input_dir = "data/raw"
    output_dir = "data/anonymized"
    os.makedirs(output_dir, exist_ok=True)
    #lista arquivos excel e csv existentes na pasta data/raw
    files = [f for f in os.listdir(input_dir) if f.endswith((".csv", ".xlsx", ".xls"))]
    #verifica se a pasta esta vazia e caso esteja retorna aviso e encerra
    if not files:
        print("Nenhum arquivo encontrado em data/raw")
        sys.exit(1)

    #extrai a nome do arquivo sem a extensão convertendo para minúscula
    for file in files:
        name = file.rsplit(".", 1)[0].lower()
        #o nome do arquivo na pasta precisa ser igual ao definido nas configurações
        config = find_config(name)
        #caso não encontre o arquivo com o nome correto segue para o próximo
        if config is None:
            print(f"Configuração não encontrada para: {file}. Pulando...")
            continue
        #quando arquivo é encontrado chama anonimização e imprime resultado
        filepath = os.path.join(input_dir, file)
        output = anonymize_file(filepath, config, output_dir)
        print(f"Anonimizado: {file} -> {output}")

#execução no terminal deve rodar o main
if __name__ == "__main__":
    main()