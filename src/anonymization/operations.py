import hashlib
import pandas as pd

def hash_value(value: str, salt: str) -> str:
    """Aplica SHA-256 com salt para pseudonimização consistente"""
    if pd.isna(value):
        return value
    return hashlib.sha256(f'{salt}.{value}'.encode()).hexdigest()

def drop_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Remove colunas de PII que não tem valor analítico"""
    existing = [col for col in columns if col in df.columns]
    return df.drop(columns=existing)

def generalize_birth_date(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Substitui data de nascimento pela idade em anos"""
    if column not in df.columns:
        return df
    df[column] = pd.to_datetime(df[column], errors="coerce")
    today = pd.Timestamp.now()
    age_in_days = (today - df[column]).dt.days
    df["IDADE_CALCULADA"] = pd.to_numeric(age_in_days / 365.25, errors="coerce").round(0).astype("Int64")
    df = df.drop(columns=[column])
    return df