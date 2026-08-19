# pages/detalhes_comissao.py
import streamlit as st
import pandas as pd
from utils import carregar_comissao, exibir_foto, inicializar_banco

def show():
    inicializar_banco()
    st.title("👤 Detalhes do Membro da Comissão")

    # Tenta obter o índice via query params
    params = st.query_params
    idx = params.get("idx", None)
    if idx is not None:
        try:
            idx = int(idx)
        except:
            idx = None

    # Fallback para session_state
    if idx is None:
        idx = st.session_state.get("membro_comissao_idx")
    nome_membro = st.session_state.get("membro_comissao_nome", "desconhecido")

    if idx is None:
        st.warning("Nenhum membro selecionado.")
        if st.button("← Voltar para lista"):
            st.switch_page("pages/comissao.py")
        return

    df = carregar_comissao()
    if df.empty:
        st.error("Dados da comissão não carregados. Verifique o CSV.")
        return

    try:
        if idx < len(df):
            membro = df.iloc[idx]
        else:
            st.error("Membro não encontrado.")
            return
    except:
        st.error("Erro ao acessar os dados.")
        return

    # ===== CABEÇALHO COM FOTO =====
    col1, col2 = st.columns([1, 3])
    with col1:
        exibir_foto(membro, categoria="Comissão Profissional", width=120)
    with col2:
        nome = membro.get('nome', membro.get('nome_completo', 'N/I'))
        st.subheader(f"👤 {nome}")
        st.write(f"**Cargo:** {membro.get('cargo', 'N/I')}")
        st.write(f"**Idade:** {membro.get('idade', 'N/I')} anos")

    # ===== DADOS PESSOAIS =====
    st.subheader("📋 Dados Pessoais")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Data Nascimento:** {membro.get('data_nascimento', 'N/I')}")
        st.write(f"**Cidade:** {membro.get('cidade_nascimento', 'N/I')}")
    with col2:
        st.write(f"**UF:** {membro.get('uf_nascimento', 'N/I')}")
        st.write(f"**País:** {membro.get('pais_nascimento', 'N/I')}")

    # ===== HISTÓRICO PROFISSIONAL =====
    if membro.get('historico_profissional'):
        st.subheader("📋 Histórico Profissional")
        st.write(membro['historico_profissional'])

    # ===== HISTÓRICO COMO JOGADOR =====
    if membro.get('historico_jogador'):
        st.subheader("⚽ Histórico como Jogador")
        st.write(membro['historico_jogador'])

    # ===== ATRIBUTOS DE STAFF =====
    atributos_staff = [col for col in membro.index if col.startswith('staff_')]
    if atributos_staff:
        st.subheader("📊 Atributos de Staff")
        for attr in atributos_staff:
            val = membro[attr]
            if pd.notna(val):
                nome_attr = attr.replace('staff_', '').replace('_', ' ').title()
                st.write(f"- **{nome_attr}:** {val}")

    # ===== CARTÕES =====
    st.subheader("🟨 Cartões e Suspensões")
    try:
        import sqlite3
        conn = sqlite3.connect('meu_futebol.db', timeout=10)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM tecnicos WHERE nome = ?", (nome,))
        tec_id = cursor.fetchone()
        if tec_id:
            cartoes = pd.read_sql_query(f"""
                SELECT 
                    SUM(CASE WHEN detalhes LIKE '%amarelo%' OR tipo = 'Yellow Card' THEN 1 ELSE 0 END) AS amarelos,
                    SUM(CASE WHEN detalhes LIKE '%vermelho%' OR tipo = 'Red Card' THEN 1 ELSE 0 END) AS vermelhos,
                    COUNT(*) AS total
                FROM eventos
                WHERE jogador_id = {tec_id[0]} 
                  AND (tipo = 'Card' OR detalhes LIKE '%cartão%' OR detalhes LIKE '%amarelo%' OR detalhes LIKE '%vermelho%')
            """, conn)
            if not cartoes.empty and cartoes.iloc[0]['total'] > 0:
                amarelos = cartoes.iloc[0]['amarelos'] or 0
                vermelhos = cartoes.iloc[0]['vermelhos'] or 0
                st.write(f"🟨 Amarelos: {amarelos}")
                st.write(f"🟥 Vermelhos: {vermelhos}")
                if amarelos >= 3:
                    st.warning("⚠️ Membro está suspenso por acúmulo de amarelos.")
                if vermelhos > 0:
                    st.warning("⚠️ Membro possui cartões vermelhos.")
            else:
                st.write("Nenhum cartão registrado.")
        else:
            st.write("Nenhum cartão registrado.")
        conn.close()
    except Exception as e:
        st.info(f"Erro ao buscar cartões: {e}")

    # ===== BOTÃO VOLTAR =====
    if st.button("← Voltar para lista"):
        st.switch_page("pages/comissao.py")