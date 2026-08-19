# pages/gestao.py
import streamlit as st
import sqlite3
import pandas as pd
from utils import carregar_elenco_profissional

def show():
    st.title("⚙️ Gestão")
    tabs = st.tabs(["Atletas", "Treinos", "Well-being", "Lesões", "Jogos", "GPS"])
    conn = sqlite3.connect('meu_futebol.db')
    df_atletas = carregar_elenco_profissional()

    with tabs[0]:
        st.subheader("Atletas")
        st.dataframe(df_atletas[['nome_completo', 'apelido', 'Posicao_Principal', 'Idade', 'Estado_Fisico']], use_container_width=True)

    with tabs[1]:
        st.subheader("Treinos")
        df = pd.read_sql_query("SELECT * FROM treinos", conn)
        st.dataframe(df, use_container_width=True)

    with tabs[2]:
        st.subheader("Well-being")
        df = pd.read_sql_query("SELECT * FROM wellbeing", conn)
        st.dataframe(df, use_container_width=True)

    with tabs[3]:
        st.subheader("Lesões")
        df = pd.read_sql_query("SELECT * FROM lesoes", conn)
        st.dataframe(df, use_container_width=True)

    with tabs[4]:
        st.subheader("Jogos")
        df = pd.read_sql_query("SELECT * FROM jogos", conn)
        st.dataframe(df, use_container_width=True)

    with tabs[5]:
        st.subheader("GPS")
        df = pd.read_sql_query("SELECT * FROM gps", conn)
        st.dataframe(df, use_container_width=True)

    conn.close()