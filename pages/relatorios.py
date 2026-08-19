# pages/relatorios.py
import streamlit as st
import pandas as pd
from io import BytesIO
from utils import carregar_elenco_profissional, carregar_comissao, gerar_relatorio_diretoria, gerar_relatorio_jogador, gerar_relatorio_comissao

def show():
    st.title("📄 Relatórios")
    tipo = st.selectbox("Tipo", ["Diretoria", "Jogador", "Comissão"])

    if tipo == "Diretoria":
        if st.button("Gerar", use_container_width=True):
            df_jog = carregar_elenco_profissional()
            df_com = carregar_comissao()
            if df_jog.empty or df_com.empty:
                st.warning("Dados incompletos.")
                return
            output = BytesIO()
            gerar_relatorio_diretoria(df_jog, df_com, output)
            st.download_button("Baixar Excel", output.getvalue(), "relatorio_diretoria.xlsx")

    elif tipo == "Jogador":
        df = carregar_elenco_profissional()
        if df.empty:
            st.warning("Elenco não carregado.")
            return
        jogador = st.selectbox("Jogador", df['nome_completo'].tolist())
        if st.button("Gerar", use_container_width=True):
            row = df[df['nome_completo'] == jogador].iloc[0]
            output = BytesIO()
            gerar_relatorio_jogador(row, output)
            st.download_button("Baixar Excel", output.getvalue(), f"relatorio_{jogador}.xlsx")

    elif tipo == "Comissão":
        df = carregar_comissao()
        if df.empty:
            st.warning("Comissão não carregada.")
            return
        membro = st.selectbox("Membro", df['nome'].tolist())
        if st.button("Gerar", use_container_width=True):
            row = df[df['nome'] == membro].iloc[0]
            output = BytesIO()
            gerar_relatorio_comissao(row, output)
            st.download_button("Baixar Excel", output.getvalue(), f"relatorio_{membro}.xlsx")