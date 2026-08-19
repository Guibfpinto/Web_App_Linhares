# pages/proximo_jogo.py
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from utils import carregar_cronograma, obter_proximo_jogo, inicializar_banco

TEAM_ID = 12928

def show():
    inicializar_banco()

    st.title("📅 Próximo Jogo")

    categoria = st.selectbox("Categoria", ["Profissional", "Sub-20"])

    if st.button("Atualizar", width='stretch'):
        # 1) Tenta buscar do cronograma (se existir)
        jogo = obter_proximo_jogo(categoria)
        if jogo:
            # Verifica se o jogo é do Linhares (pelo local, ou por coluna específica)
            # Como o cronograma não tem time_id, assumimos que todos são do Linhares.
            st.success("Jogo encontrado no cronograma!")
            st.write(f"**Adversário:** {jogo.get('adversario', 'N/I')}")
            st.write(f"**Data:** {jogo.get('data', 'N/I')}")
            st.write(f"**Local:** {'Casa' if str(jogo.get('local', '')).lower() == 'casa' else 'Fora'}")
            st.write(f"**Competição:** {jogo.get('competicao', 'N/I')}")
            st.write(f"**Status:** {jogo.get('status', 'N/I')}")
        else:
            # 2) Fallback: buscar do SQLite filtrando apenas jogos do Linhares
            st.info("Nenhum jogo no cronograma. Buscando do banco de dados (apenas jogos do Linhares)...")
            try:
                conn = sqlite3.connect('meu_futebol.db', timeout=10)
                hoje = datetime.now().strftime("%Y-%m-%d")
                query = f"""
                    SELECT * FROM jogos 
                    WHERE (time_casa_id = {TEAM_ID} OR time_fora_id = {TEAM_ID})
                      AND data_hora >= '{hoje}'
                    ORDER BY data_hora 
                    LIMIT 1
                """
                df = pd.read_sql_query(query, conn)
                conn.close()
                if not df.empty:
                    row = df.iloc[0]
                    # Busca o nome do adversário
                    if row['time_casa_id'] == TEAM_ID:
                        adversario_id = row['time_fora_id']
                        local = "Casa"
                    else:
                        adversario_id = row['time_casa_id']
                        local = "Fora"
                    conn2 = sqlite3.connect('meu_futebol.db')
                    adv_nome = pd.read_sql_query(f"SELECT nome FROM times WHERE id = {adversario_id}", conn2).iloc[0]['nome']
                    conn2.close()
                    st.success("Jogo encontrado no banco de dados!")
                    st.write(f"**Adversário:** {adv_nome}")
                    st.write(f"**Data:** {row['data_hora']}")
                    st.write(f"**Local:** {local}")
                    st.write(f"**Status:** {row['status']}")
                else:
                    st.warning("Nenhum jogo futuro do Linhares encontrado no banco de dados.")
            except Exception as e:
                st.error(f"Erro ao buscar do banco: {e}")

    # Mostra todos os jogos do cronograma (se existir)
    st.subheader("📋 Todos os jogos do cronograma")
    df_crono = carregar_cronograma(categoria)
    if not df_crono.empty:
        st.dataframe(df_crono, use_container_width=True)
    else:
        st.info("Nenhum jogo cadastrado no cronograma.")

    # Mostra todos os jogos futuros do Linhares no SQLite
    st.subheader("📋 Jogos futuros do Linhares FC")
    try:
        conn = sqlite3.connect('meu_futebol.db', timeout=10)
        hoje = datetime.now().strftime("%Y-%m-%d")
        query = f"""
            SELECT j.id, j.data_hora, j.status, 
                   t1.nome AS time_casa, t2.nome AS time_fora
            FROM jogos j
            LEFT JOIN times t1 ON j.time_casa_id = t1.id
            LEFT JOIN times t2 ON j.time_fora_id = t2.id
            WHERE (j.time_casa_id = {TEAM_ID} OR j.time_fora_id = {TEAM_ID})
              AND j.data_hora >= '{hoje}'
            ORDER BY j.data_hora
        """
        df_jogos = pd.read_sql_query(query, conn)
        conn.close()
        if not df_jogos.empty:
            st.dataframe(df_jogos, use_container_width=True)
        else:
            st.info("Nenhum jogo futuro do Linhares no banco de dados.")
    except Exception as e:
        st.error(f"Erro ao carregar jogos futuros: {e}")

if __name__ == "__main__":
    show()