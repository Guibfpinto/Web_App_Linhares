# pages/proximo_jogo.py
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from utils import carregar_cronograma, obter_proximo_jogo, inicializar_banco

def show():
    # Inicializa o banco (cria tabelas se não existirem)
    inicializar_banco()

    st.title("📅 Próximo Jogo")

    categoria = st.selectbox("Categoria", ["Profissional", "Sub-20"])

    if st.button("Atualizar", width='stretch'):
        # Tenta buscar do CSV de cronograma
        jogo = obter_proximo_jogo(categoria)
        if jogo:
            st.success("Jogo encontrado no cronograma!")
            st.write(f"**Adversário:** {jogo.get('adversario', 'N/I')}")
            st.write(f"**Data:** {jogo.get('data', 'N/I')}")
            st.write(f"**Local:** {'Casa' if str(jogo.get('local', '')).lower() == 'casa' else 'Fora'}")
            st.write(f"**Competição:** {jogo.get('competicao', 'N/I')}")
            st.write(f"**Status:** {jogo.get('status', 'N/I')}")
        else:
            # Fallback: buscar do SQLite (tabela jogos)
            st.info("Nenhum jogo no cronograma. Buscando do banco de dados...")
            try:
                conn = sqlite3.connect('meu_futebol.db', timeout=10)
                hoje = datetime.now().strftime("%Y-%m-%d")
                # Busca o próximo jogo com data >= hoje
                df = pd.read_sql_query(f"SELECT * FROM jogos WHERE data_hora >= '{hoje}' ORDER BY data_hora LIMIT 1", conn)
                conn.close()
                if not df.empty:
                    row = df.iloc[0]
                    st.success("Jogo encontrado no banco de dados!")
                    st.write(f"**Adversário:** {row.get('adversario', 'N/I')}")
                    st.write(f"**Data:** {row['data_hora']}")
                    st.write(f"**Status:** {row['status']}")
                else:
                    st.warning("Nenhum jogo encontrado no banco de dados.")
            except Exception as e:
                st.error(f"Erro ao buscar do banco: {e}")

    # Mostra todos os jogos do cronograma (se existir)
    st.subheader("📋 Todos os jogos do cronograma")
    df_crono = carregar_cronograma(categoria)
    if not df_crono.empty:
        st.dataframe(df_crono, use_container_width=True)
    else:
        st.info("Nenhum jogo cadastrado no cronograma.")

    # Mostra também os jogos do SQLite (opcional)
    st.subheader("📋 Jogos do banco de dados")
    try:
        conn = sqlite3.connect('meu_futebol.db', timeout=10)
        df_jogos = pd.read_sql_query("SELECT * FROM jogos ORDER BY data_hora", conn)
        conn.close()
        if not df_jogos.empty:
            st.dataframe(df_jogos[['id', 'data_hora', 'status']], use_container_width=True)
        else:
            st.info("Nenhum jogo no banco de dados.")
    except Exception as e:
        st.error(f"Erro ao carregar jogos: {e}")

if __name__ == "__main__":
    show()