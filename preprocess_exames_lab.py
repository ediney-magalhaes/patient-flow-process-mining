import pandas as pd
from datetime import datetime

# leitura do arquivo sem interpretar o cabeçalho
df = pd.read_excel('data/raw/exames_laboratoriais.xlsx', header=None, sheet_name=0)

# filtra as linhas com números de atendimentos e descarta o restante
df = df[pd.to_numeric(df[0], errors='coerce').notna()]

# exclui colunas vazias
df = df.drop(columns=[1,2,3,7,8,9,14,15,17])

# renomear as colunas existentes
df.columns = [
    'ATEND', 'NM_PACIENTE',
    'CD_EXAME', 'NM_EXAME',
    'HR_PED_LAB', 'DT_COLETA',
    'HR_LAUDO_LAB', 'HR_CHAM_MED',
    'PED_X_LAUDO', 'CLASSI_RISCO'
]

# normalizar timestamp
time_stamps = ['HR_PED_LAB', 'DT_COLETA', 'HR_LAUDO_LAB', 'HR_CHAM_MED']

# identifica quais dados estão como datetime
for col in time_stamps:
    mask_dt = df[col].apply(lambda x: isinstance(x, datetime))

    # troca dia com mês para datetime invertido
    df.loc[mask_dt, col] = df.loc[mask_dt, col].apply(
        lambda x: x.replace(month=x.day, day=x.month) if pd.notna(x) else x
    )

    # para os datetime que estão com string (AM e PM) converte
    df.loc[~mask_dt, col] = pd.to_datetime(df.loc[~mask_dt, col], format='mixed', dayfirst=False)

# reseta o índice após o filtro 
df = df.reset_index(drop=True)

# salva como csv
df.to_csv('data/raw/exames_laboratoriais_limpo.csv', index=False, encoding='utf-8', sep=';')
print(f'Linhas processadas: {len(df)}')