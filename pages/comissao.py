# pages/comissao.py
import streamlit as st
import pandas as pd
from utils import carregar_comissao, exibir_foto, inicializar_banco

def show():
    inicializar_banco()
    st.title("👔 Comissão Técnica")

    df = carregar_comissao()

    if df.empty:
        st.warning("Nenhum membro da comissão encontrado no CSV.")
        st.info("Certifique-se de que o arquivo 'perfil_completo_comissao_2026.csv' está na pasta do projeto.")
        return

    if 'cargo' in df.columns:
        cargos = ['Todos'] + sorted(df['cargo'].dropna().unique().tolist())
        filtro = st.selectbox("Filtrar por cargo", cargos)
        if filtro != 'Todos':
            df = df[df['cargo'] == filtro]

    st.subheader(f"{len(df)} membros encontrados")

    for idx, row in df.iterrows():
        col1, col2 = st.columns([1, 4])
        with col1:
            exibir_foto(row, categoria="Comissão Profissional", width=80)
        with col2:
            nome = row.get('nome', row.get('nome_completo', 'N/I'))
            cargo = row.get('cargo', 'N/I')
            idade = row.get('idade', 'N/I')
            st.write(f"**{nome}**")
            st.write(f"Cargo: {cargo} | Idade: {idade if pd.notna(idade) else 'N/I'} anos")
            if st.button("Ver detalhes", key=f"btn_{idx}"):
                st.session_state.membro_comissao_idx = idx
                st.session_state.membro_comissao_nome = nome
                st.switch_page("pages/detalhes_comissao.py")
        st.divider()