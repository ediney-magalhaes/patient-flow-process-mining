import pm4py
import pandas as pd

# lê o CSV exportado do Databricks
df = pd.read_csv("temp/event_log_export.csv")

# converte o timestamp para datetime com timezone UTC
df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

# prepara o DataFrame para o PM4Py
df_formatado = pm4py.format_dataframe(
    df,
    case_id="case_id",
    activity_key="activity",
    timestamp_key="timestamp"
)

# converte para EventLog
event_log = pm4py.convert_to_event_log(df_formatado)

# aplica o Inductive Miner
process_tree = pm4py.discover_process_tree_inductive(event_log)

# gera a visualização e salva como PNG
pm4py.save_vis_process_tree(process_tree, "temp/process_tree.png")
print("Process tree salvo em temp/process_tree.png")