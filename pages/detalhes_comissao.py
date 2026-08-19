# pages/detalhes_comissao.py
import streamlit as st
import pandas as pd
from utils import carregar_comissao, exibir_foto, inicializar_banco

def show():
    inicializar_banco()
    st.title("👤 Detalhes do Membro da Comissão")

    idx = st.session_state.get("membro_comissao_idx")
    if idx is None:
        st.warning("Nenhum membro selecionado.")
        if st.button("Voltar para lista"):
            st.switch_page("pages/comissao.py")
        return

    df = carregar_comissao()
    if df.empty:
        st.error("Dados da comissão não carregados.")
        return

    try:
        row = df.iloc[int(idx)]
    except:
        st.error("Membro não encontrado.")
        return

    # Exibe os dados
    col1, col2 = st.columns([1, 3])
    with col1:
        exibir_foto(row, categoria="Comissão Profissional", width=150)
    with col2:
        nome = row.get('nome', row.get('nome_completo', 'N/I'))
        st.subheader(f"👤 {nome}")
        st.write(f"**Cargo:** {row.get('cargo', 'N/I')}")
        st.write(f"**Idade:** {row.get('idade', 'N/I')} anos")

    st.subheader("📋 Dados Pessoais")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Data Nascimento:** {row.get('data_nascimento', 'N/I')}")
        st.write(f"**Cidade/UF:** {row.get('cidade_nascimento', 'N/I')} / {row.get('uf_nascimento', 'N/I')}")
    with col2:
        st.write(f"**País:** {row.get('pais_nascimento', 'N/I')}")

    # Histórico profissional
    if row.get('historico_profissional'):
        st.subheader("📋 Histórico Profissional")
        st.write(row['historico_profissional'])

    if row.get('historico_jogador'):
        st.subheader("⚽ Histórico como Jogador")
        st.write(row['historico_jogador'])

    # Atributos de staff
    atributos_staff = [col for col in row.index if col.startswith('staff_')]
    if atributos_staff:
        st.subheader("📊 Atributos de Staff")
        for attr in atributos_staff:
            val = row[attr]
            if pd.notna(val):
                st.write(f"- **{attr.replace('staff_', '').replace('_', ' ').title()}:** {val}")

    if st.button("← Voltar para lista"):
        st.switch_page("pages/comissao.py")