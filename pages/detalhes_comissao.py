# pages/detalhes_comissao.py
import streamlit as st
import pandas as pd
from utils import carregar_comissao, exibir_foto, inicializar_banco, mapear_nome_para_canonico, carregar_cartoes_json

def show():
    inicializar_banco()
    st.title("👤 Detalhes do Membro da Comissão")

    # Obtém o índice do membro armazenado na sessão
    membro_idx = st.session_state.get("membro_comissao_idx")
    if membro_idx is None:
        st.warning("Nenhum membro selecionado.")
        if st.button("← Voltar para lista"):
            st.switch_page("pages/comissao.py")
        return

    # Carrega a comissão
    df = carregar_comissao()
    if df.empty or membro_idx >= len(df):
        st.error("Membro não encontrado.")
        return

    membro = df.iloc[membro_idx]

    # Cabeçalho com foto
    col1, col2 = st.columns([1, 3])
    with col1:
        exibir_foto(membro, categoria="Comissão Profissional", width=120)
    with col2:
        nome = membro.get('nome', membro.get('nome_completo', 'N/I'))
        st.subheader(f"👤 {nome}")
        st.write(f"**Cargo:** {membro.get('cargo', 'N/I')}")
        st.write(f"**Idade:** {membro.get('idade', 'N/I')} anos")

    # Dados pessoais
    st.subheader("📋 Dados Pessoais")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Data Nascimento:** {membro.get('data_nascimento', 'N/I')}")
        st.write(f"**Cidade:** {membro.get('cidade_nascimento', 'N/I')}")
    with col2:
        st.write(f"**UF:** {membro.get('uf_nascimento', 'N/I')}")
        st.write(f"**País:** {membro.get('pais_nascimento', 'N/I')}")

    # Histórico profissional
    if membro.get('historico_profissional'):
        st.subheader("📋 Histórico Profissional")
        st.write(membro['historico_profissional'])

    # Histórico como jogador
    if membro.get('historico_jogador'):
        st.subheader("⚽ Histórico como Jogador")
        st.write(membro['historico_jogador'])

    # Atributos de staff
    atributos_staff = [col for col in membro.index if col.startswith('staff_')]
    if atributos_staff:
        st.subheader("📊 Atributos de Staff")
        for attr in atributos_staff:
            val = membro[attr]
            if pd.notna(val):
                nome_attr = attr.replace('staff_', '').replace('_', ' ').title()
                st.write(f"- **{nome_attr}:** {val}")

    # Cartões (buscar do JSON da comissão)
    st.subheader("🟨 Cartões e Suspensões")
    cartoes, _ = carregar_cartoes_json('comissao_profissional')
    nome_canonico = mapear_nome_para_canonico(membro.get('nome'))
    if nome_canonico and nome_canonico in cartoes:
        dados = cartoes[nome_canonico]
        amarelos = dados.get('amarelos', 0)
        vermelho = dados.get('vermelho', False)
        suspenso = dados.get('suspenso_proxima', False)
        st.write(f"🟨 Amarelos: {amarelos}")
        st.write(f"🟥 Vermelhos: {'Sim' if vermelho else 'Não'}")
        st.write(f"⚠️ Suspenso: {'Sim' if suspenso else 'Não'}")
        if amarelos >= 3:
            st.warning("⚠️ Membro está suspenso por acúmulo de amarelos.")
        if vermelho:
            st.warning("⚠️ Membro possui cartão vermelho.")
        historico_cartoes = dados.get('historico', [])
        if historico_cartoes:
            st.write("**Histórico de cartões:**")
            df_hist = pd.DataFrame(historico_cartoes)
            st.dataframe(df_hist, use_container_width=True)
    else:
        st.write("Nenhum cartão registrado para este membro.")

    # Botão voltar
    if st.button("← Voltar para lista"):
        st.switch_page("pages/comissao.py")