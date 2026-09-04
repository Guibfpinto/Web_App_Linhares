# ver_estrutura_banco.py
import sqlite3
import pandas as pd

def ver_estrutura_banco(arquivo_db="meu_futebol.db"):
    """
    Conecta ao banco SQLite e imprime a estrutura de todas as tabelas.
    """
    try:
        conn = sqlite3.connect(arquivo_db)
        print(f"✅ Conectado ao banco: {arquivo_db}\n")
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        return

    # Lista todas as tabelas (ignorando tabelas internas do SQLite)
    tabelas = pd.read_sql_query(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';",
        conn
    )

    if tabelas.empty:
        print("⚠️ Nenhuma tabela encontrada.")
        conn.close()
        return

    for table_name in tabelas['name']:
        print(f"📋 Tabela: {table_name}")
        # Obtém informações das colunas
        df_cols = pd.read_sql_query(f"PRAGMA table_info({table_name});", conn)
        # Exibe apenas as colunas relevantes
        df_cols = df_cols[['name', 'type', 'notnull', 'pk']]
        # Renomeia para exibição mais clara
        df_cols.rename(columns={
            'name': 'Coluna',
            'type': 'Tipo',
            'notnull': 'Obrigatório?',
            'pk': 'Chave Primária?'
        }, inplace=True)
        print(df_cols.to_string(index=False))
        print("-" * 60)

    conn.close()

if __name__ == "__main__":
    # Altere o nome do arquivo se seu banco tiver outro nome
    ver_estrutura_banco("meu_futebol.db")