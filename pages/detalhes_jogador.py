# pages/detalhes_jogador.py
import streamlit as st
import sqlite3
import pandas as pd
from utils import exibir_foto, inicializar_banco, mapear_nome_para_canonico

def show():
    inicializar_banco()
    st.title("👤 Detalhes do Jogador")

    jogador_id = st.session_state.get("jogador_id")
    if not jogador_id:
        st.warning("Nenhum jogador selecionado.")
        if st.button("Voltar para análise"):
            st.switch_page("pages/analise.py")
        return

    # Carrega dados do jogador do SQLite (ou do CSV)
    conn = sqlite3.connect('meu_futebol.db', timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM elenco WHERE id = ?", (jogador_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        # Fallback: tenta buscar do CSV
        from utils import carregar_elenco_profissional
        df = carregar_elenco_profissional()
        if jogador_id < len(df):
            row = df.iloc[jogador_id].to_dict()
        else:
            st.error("Jogador não encontrado.")
            return

    # Se row for um dicionário (do CSV), usa diretamente, senão converte
    if isinstance(row, tuple):
        colunas = [desc[0] for desc in cursor.description] if 'cursor' in locals() else ['id', 'nome', 'apelido', 'posicao', 'idade']
        jogador = dict(zip(colunas, row))
    else:
        jogador = row

    # Exibe dados
    col1, col2 = st.columns([1, 3])
    with col1:
        exibir_foto(jogador, categoria="Profissional", width=120)
    with col2:
        st.subheader(f"⚽ {jogador.get('nome', jogador.get('nome_completo', 'N/I'))} ({jogador.get('apelido', 'N/I')})")
        st.write(f"**Posição:** {jogador.get('posicao', 'N/I')}")
        st.write(f"**Idade:** {jogador.get('idade', jogador.get('Idade', 'N/I'))} anos")
        st.write(f"**Número:** {jogador.get('numero', 'N/I')}")

    # Mais detalhes (físicos, atributos, etc.)
    st.subheader("📋 Dados Pessoais")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Altura:** {jogador.get('altura_cm', 'N/I')} cm")
        st.write(f"**Peso:** {jogador.get('peso_kg', 'N/I')} kg")
        st.write(f"**IMC:** {jogador.get('IMC', 'N/I')}")
    with col2:
        st.write(f"**Cidade:** {jogador.get('cidade_nascimento', 'N/I')}")
        st.write(f"**UF:** {jogador.get('uf_nascimento', 'N/I')}")
        st.write(f"**País:** {jogador.get('pais_nascimento', 'N/I')}")

    if st.button("← Voltar para lista"):
        st.switch_page("pages/analise.py")