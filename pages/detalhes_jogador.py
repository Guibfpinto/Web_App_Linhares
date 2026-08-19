# pages/detalhes_jogador.py
import streamlit as st
import pandas as pd
import sqlite3
from utils import exibir_foto, carregar_elenco_profissional, inicializar_banco

def show():
    inicializar_banco()
    st.title("👤 Detalhes do Jogador")

    # Obtém o ID do jogador vindo da página anterior (analise.py)
    jogador_id = st.session_state.get("jogador_id")

    if jogador_id is None:
        st.warning("Nenhum jogador selecionado. Volte e clique em 'Ver detalhes'.")
        if st.button("← Voltar para análise", width='stretch'):
            st.switch_page("pages/analise.py")
        return

    # Carrega o DataFrame completo do elenco
    df = carregar_elenco_profissional()
    if df.empty:
        st.error("Dados do elenco não carregados. Verifique o CSV.")
        return

    # Busca o jogador pelo ID (assumindo que a coluna 'id' existe)
    # Se não existir, tenta usar o índice
    if 'id' in df.columns:
        jogador = df[df['id'] == jogador_id]
    else:
        # Fallback: usa o índice (se o ID for o índice)
        try:
            jogador = df.iloc[int(jogador_id)]
            jogador = pd.DataFrame([jogador])
        except:
            jogador = pd.DataFrame()

    if jogador.empty:
        st.error(f"Jogador com ID {jogador_id} não encontrado.")
        if st.button("← Voltar para análise", width='stretch'):
            st.switch_page("pages/analise.py")
        return

    row = jogador.iloc[0]

    # ===== CABEÇALHO COM FOTO =====
    col1, col2 = st.columns([1, 3])
    with col1:
        exibir_foto(row, categoria="Profissional", width=120)
    with col2:
        nome = row.get('nome_completo', 'N/I')
        apelido = row.get('apelido', 'N/I')
        st.subheader(f"⚽ {nome} ({apelido})")
        st.write(f"**Posição:** {row.get('Posicao_Principal', row.get('posicao', 'N/I'))}")
        st.write(f"**Idade:** {row.get('Idade', 'N/I')} anos")
        st.write(f"**Número:** {row.get('numero', 'N/I')}")

    # ===== DADOS PESSOAIS =====
    st.subheader("📋 Dados Pessoais")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Data Nascimento:** {row.get('data_nascimento', 'N/I')}")
        st.write(f"**Altura:** {row.get('altura_cm', 'N/I')} cm")
        st.write(f"**Peso:** {row.get('peso_kg', 'N/I')} kg")
    with col2:
        st.write(f"**Cidade:** {row.get('cidade_nascimento', 'N/I')}")
        st.write(f"**UF:** {row.get('uf_nascimento', 'N/I')}")
        st.write(f"**País:** {row.get('pais_nascimento', 'N/I')}")

    # ===== CONDIÇÃO FÍSICA =====
    st.subheader("📊 Condição Física")
    imc = row.get('IMC')
    gordura = row.get('Gordura_Corporal_%')
    estado = row.get('Estado_Fisico')
    st.write(f"**IMC:** {imc:.1f}" if pd.notna(imc) else "**IMC:** N/I")
    st.write(f"**% Gordura:** {gordura:.1f}%" if pd.notna(gordura) else "**% Gordura:** N/I")
    st.write(f"**Estado Físico:** {estado if pd.notna(estado) else 'N/I'}")

    # ===== ATRIBUTOS FM26 =====
    atributos_fm26 = [
        'finalizacao', 'passe', 'drible', 'desarme', 'velocidade_maxima',
        'resistencia', 'forca_fisica', 'reflexos', 'jogo_aereo_goleiro',
        'defesas_goleiro', 'cabecada', 'marcacao', 'antecipacao', 'posicionamento'
    ]
    # Filtra apenas os atributos que existem no DataFrame
    attrs_existentes = [a for a in atributos_fm26 if a in row.index and pd.notna(row.get(a))]
    if attrs_existentes:
        st.subheader("🎮 Atributos FM26")
        data = {attr.replace('_', ' ').title(): row[attr] for attr in attrs_existentes}
        st.dataframe(pd.DataFrame([data]), width='stretch')

    # ===== HISTÓRICO DE CLUBES =====
    if row.get('historico'):
        st.subheader("📜 Histórico de Clubes")
        st.write(row['historico'])

    # ===== CARTÕES (buscar do SQLite) =====
    st.subheader("🟨 Cartões e Suspensões")
    try:
        conn = sqlite3.connect('meu_futebol.db', timeout=10)
        cursor = conn.cursor()
        # Busca o ID do jogador na tabela elenco (se existir)
        cursor.execute("SELECT id FROM elenco WHERE nome = ? OR apelido = ?", (nome, apelido))
        elenco_id = cursor.fetchone()
        if elenco_id:
            cartoes = pd.read_sql_query(f"""
                SELECT 
                    SUM(CASE WHEN detalhes LIKE '%amarelo%' OR tipo = 'Yellow Card' THEN 1 ELSE 0 END) AS amarelos,
                    SUM(CASE WHEN detalhes LIKE '%vermelho%' OR tipo = 'Red Card' THEN 1 ELSE 0 END) AS vermelhos,
                    COUNT(*) AS total
                FROM eventos
                WHERE jogador_id = {elenco_id[0]} 
                  AND (tipo = 'Card' OR detalhes LIKE '%cartão%' OR detalhes LIKE '%amarelo%' OR detalhes LIKE '%vermelho%')
            """, conn)
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
        else:
            st.write("Nenhum cartão registrado.")
        conn.close()
    except Exception as e:
        st.info(f"Erro ao buscar cartões: {e}")

    # ===== LESÕES =====
    st.subheader("🩹 Lesões")
    try:
        conn = sqlite3.connect('meu_futebol.db', timeout=10)
        lesoes = pd.read_sql_query(f"""
            SELECT tipo_lesao, data_inicio, data_fim, ativo
            FROM lesoes
            WHERE jogador = '{nome}'
            ORDER BY data_inicio DESC
        """, conn)
        conn.close()
        if not lesoes.empty:
            for _, lesao in lesoes.iterrows():
                status = "Ativa" if lesao['ativo'] == 1 else "Encerrada"
                st.write(f"- **{lesao['tipo_lesao']}** ({status})")
                st.write(f"  Início: {lesao['data_inicio']} | Fim: {lesao['data_fim'] or 'Em andamento'}")
        else:
            st.write("Nenhuma lesão registrada.")
    except Exception as e:
        st.info(f"Erro ao buscar lesões: {e}")

    # ===== BOTÃO VOLTAR =====
    if st.button("← Voltar para análise", width='stretch'):
        st.switch_page("pages/analise.py")