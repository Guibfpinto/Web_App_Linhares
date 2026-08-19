# pages/detalhes_comissao.py
import streamlit as st
import pandas as pd
from utils import carregar_comissao, exibir_foto, inicializar_banco

def show():
    inicializar_banco()
    st.title("👤 Detalhes do Membro")

    idx = st.session_state.get("membro_comissao_idx")
    if idx is None:
        st.warning("Nenhum membro selecionado.")
        if st.button("Voltar para lista"):
            st.switch_page("pages/comissao.py")
        return

    df = carregar_comissao()
    if df.empty or idx >= len(df):
        st.error("Membro não encontrado.")
        return

    membro = df.iloc[idx]

    col1, col2 = st.columns([1, 3])
    with col1:
        exibir_foto(membro, categoria="Comissão Profissional", width=120)
    with col2:
        nome = membro.get('nome', membro.get('nome_completo', 'N/I'))
        st.subheader(f"👤 {nome}")
        st.write(f"**Cargo:** {membro.get('cargo', 'N/I')}")
        st.write(f"**Idade:** {membro.get('idade', 'N/I')} anos")

    st.subheader("📋 Dados Pessoais")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Data Nascimento:** {membro.get('data_nascimento', 'N/I')}")
        st.write(f"**Cidade/UF:** {membro.get('cidade_nascimento', 'N/I')} / {membro.get('uf_nascimento', 'N/I')}")
    with col2:
        st.write(f"**País:** {membro.get('pais_nascimento', 'N/I')}")

    if membro.get('historico_profissional'):
        st.subheader("📋 Histórico Profissional")
        st.write(membro['historico_profissional'])

    if membro.get('historico_jogador'):
        st.subheader("⚽ Histórico como Jogador")
        st.write(membro['historico_jogador'])

    # Atributos de staff
    staff_cols = [col for col in membro.index if col.startswith('staff_')]
    if staff_cols:
        st.subheader("📊 Atributos de Staff")
        for col in staff_cols:
            val = membro[col]
            if pd.notna(val):
                st.write(f"- **{col.replace('staff_', '').replace('_', ' ').title()}:** {val}")

    if st.button("← Voltar para lista"):
        st.switch_page("pages/comissao.py")