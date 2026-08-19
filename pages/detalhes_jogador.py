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

    conn = sqlite3.connect('meu_futebol.db', timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM elenco WHERE id = ?", (jogador_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        st.error("Jogador não encontrado.")
        return

    colunas = [desc[0] for desc in cursor.description]
    jogador = dict(zip(colunas, row))

    # Cabeçalho com foto
    col1, col2 = st.columns([1, 3])
    with col1:
        exibir_foto(jogador, categoria="Profissional", width=120)
    with col2:
        st.subheader(f"⚽ {jogador['nome']} ({jogador['apelido']})")
        st.write(f"**Posição:** {jogador.get('posicao', 'N/I')}")
        st.write(f"**Idade:** {jogador.get('idade', 'N/I')} anos")
        st.write(f"**Número:** {jogador.get('numero', 'N/I')}")

    # Dados pessoais
    st.subheader("📋 Dados Pessoais")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Data Nascimento:** {jogador.get('data_nascimento', 'N/I')}")
        st.write(f"**Altura:** {jogador.get('altura', 'N/I')} cm")
        st.write(f"**Peso:** {jogador.get('peso', 'N/I')} kg")
    with col2:
        st.write(f"**Cidade:** {jogador.get('cidade_nascimento', 'N/I')}")
        st.write(f"**UF:** {jogador.get('uf_nascimento', 'N/I')}")
        st.write(f"**País:** {jogador.get('pais_nascimento', 'N/I')}")

    # Estatísticas físicas (se houver)
    if 'imc' in jogador:
        st.subheader("📊 Condição Física")
        st.write(f"**IMC:** {jogador['imc']:.1f}" if jogador['imc'] else "N/I")
        st.write(f"**% Gordura:** {jogador.get('gordura', 'N/I')}%")
        st.write(f"**Estado Físico:** {jogador.get('estado_fisico', 'N/I')}")

    # Atributos FM26 (se houver)
    atributos_fm26 = [col for col in jogador.keys() if col in ['finalizacao', 'passe', 'drible', 'desarme', 'velocidade_maxima', 'resistencia', 'forca_fisica', 'reflexos', 'jogo_aereo_goleiro', 'defesas_goleiro']]
    if atributos_fm26:
        st.subheader("🎮 Atributos FM26")
        data = {attr: jogador[attr] for attr in atributos_fm26 if jogador[attr] is not None}
        if data:
            st.dataframe(pd.DataFrame([data]), use_container_width=True)

    # Histórico de clubes
    if jogador.get('historico'):
        st.subheader("📜 Histórico de Clubes")
        st.write(jogador['historico'])

    # Cartões acumulados (buscar da tabela eventos)
    st.subheader("🟨 Cartões e Suspensões")
    conn = sqlite3.connect('meu_futebol.db', timeout=10)
    cartoes = pd.read_sql_query(f"""
        SELECT 
            SUM(CASE WHEN detalhes LIKE '%amarelo%' OR tipo = 'Yellow Card' THEN 1 ELSE 0 END) AS amarelos,
            SUM(CASE WHEN detalhes LIKE '%vermelho%' OR tipo = 'Red Card' THEN 1 ELSE 0 END) AS vermelhos,
            COUNT(*) AS total
        FROM eventos
        WHERE jogador_id = {jogador_id} 
          AND (tipo = 'Card' OR detalhes LIKE '%cartão%' OR detalhes LIKE '%amarelo%' OR detalhes LIKE '%vermelho%')
    """, conn)
    conn.close()
    if not cartoes.empty and cartoes.iloc[0]['total'] > 0:
        amarelos = cartoes.iloc[0]['amarelos'] or 0
        vermelhos = cartoes.iloc[0]['vermelhos'] or 0
        st.write(f"🟨 Amarelos: {amarelos}")
        st.write(f"🟥 Vermelhos: {vermelhos}")
        if amarelos >= 3:
            st.warning("⚠️ Jogador está suspenso por acúmulo de amarelos.")
        if vermelhos > 0:
            st.warning("⚠️ Jogador possui cartões vermelhos.")
    else:
        st.write("Nenhum cartão registrado.")

    # Lesões (se existir tabela lesoes)
    conn = sqlite3.connect('meu_futebol.db', timeout=10)
    lesoes = pd.read_sql_query(f"""
        SELECT tipo_lesao, data_inicio, data_fim, ativo
        FROM lesoes
        WHERE jogador = '{jogador['nome']}'
        ORDER BY data_inicio DESC
    """, conn)
    conn.close()
    if not lesoes.empty:
        st.subheader("🩹 Lesões")
        for _, lesao in lesoes.iterrows():
            status = "Ativa" if lesao['ativo'] == 1 else "Encerrada"
            st.write(f"- **{lesao['tipo_lesao']}** ({status})")
            st.write(f"  Início: {lesao['data_inicio']} | Fim: {lesao['data_fim'] or 'Em andamento'}")

    # Botão voltar
    if st.button("← Voltar para lista"):
        st.switch_page("pages/analise.py")