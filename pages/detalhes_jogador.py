# pages/detalhes_jogador.py
import streamlit as st
import pandas as pd
from utils import carregar_elenco_profissional, exibir_foto, inicializar_banco

def show():
    inicializar_banco()
    st.title("👤 Detalhes do Jogador")

    jogador_id = st.session_state.get("jogador_id")
    if jogador_id is None:
        st.warning("Nenhum jogador selecionado.")
        if st.button("Voltar para análise"):
            st.switch_page("pages/analise.py")
        return

    # Carrega o DataFrame completo
    df = carregar_elenco_profissional()
    if df.empty:
        st.error("Dados do elenco não carregados.")
        return

    # Tenta encontrar o jogador pelo ID (se existir) ou pelo índice
    # Verifica se 'id' é uma coluna no DataFrame
    if 'id' in df.columns:
        jogador = df[df['id'] == jogador_id]
    else:
        # Se não houver coluna 'id', usa o índice (que passamos como jogador_id)
        try:
            jogador = df.iloc[int(jogador_id)]
            # converte para DataFrame para manter consistência
            jogador = pd.DataFrame([jogador])
        except:
            st.error("Jogador não encontrado.")
            return

    if jogador.empty:
        st.error("Jogador não encontrado.")
        return

    row = jogador.iloc[0]  # primeira linha

    # Exibe os dados
    col1, col2 = st.columns([1, 3])
    with col1:
        exibir_foto(row, categoria="Profissional", width=150)
    with col2:
        nome = row.get('nome_completo', 'N/I')
        apelido = row.get('apelido', 'N/I')
        st.subheader(f"⚽ {nome} ({apelido})")
        st.write(f"**Posição:** {row.get('Posicao_Principal', 'N/I')}")
        st.write(f"**Idade:** {row.get('Idade', 'N/I')} anos")
        if 'numero' in row:
            st.write(f"**Número:** {row.get('numero', 'N/I')}")

    # Dados pessoais
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

    # Condição física
    if 'IMC' in row and pd.notna(row['IMC']):
        st.subheader("📊 Condição Física")
        st.write(f"**IMC:** {row['IMC']:.1f}" if pd.notna(row['IMC']) else "N/I")
        st.write(f"**% Gordura:** {row.get('Gordura_Corporal_%', 'N/I')}")
        st.write(f"**Estado Físico:** {row.get('Estado_Fisico', 'N/I')}")

    # Atributos FM26 (se existirem)
    atributos_fm26 = ['finalizacao', 'passe', 'drible', 'desarme', 'velocidade_maxima', 'resistencia', 'forca_fisica', 'reflexos', 'jogo_aereo_goleiro', 'defesas_goleiro']
    attrs = {attr: row.get(attr) for attr in atributos_fm26 if attr in row and pd.notna(row[attr])}
    if attrs:
        st.subheader("🎮 Atributos FM26")
        st.dataframe(pd.DataFrame([attrs]), width='stretch')

    # Histórico de clubes
    if row.get('historico'):
        st.subheader("📜 Histórico de Clubes")
        st.write(row['historico'])

    # Cartões (buscar do banco SQLite ou JSON)
    st.subheader("🟨 Cartões e Suspensões")
    # Aqui podemos integrar com a função de cartões, mas para simplificar, mostraremos uma mensagem.
    st.info("Os cartões podem ser visualizados na página de Cartões.")

    # Botão voltar
    if st.button("← Voltar para lista"):
        st.switch_page("pages/analise.py")