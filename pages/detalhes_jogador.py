# pages/detalhes_jogador.py
import streamlit as st
import pandas as pd
from utils import (
    carregar_elenco_profissional,
    exibir_foto,
    inicializar_banco,
    mapear_nome_para_canonico,
    carregar_cartoes_json
)

def show():
    inicializar_banco()
    st.title("👤 Detalhes do Jogador")

    # Obtém o índice ou ID do jogador armazenado na sessão
    jogador_idx = st.session_state.get("jogador_idx")
    if jogador_idx is None:
        st.warning("Nenhum jogador selecionado.")
        if st.button("← Voltar para análise"):
            st.switch_page("pages/analise.py")
        return

    # Carrega o elenco
    df = carregar_elenco_profissional()
    if df.empty or jogador_idx >= len(df):
        st.error("Jogador não encontrado.")
        return

    jogador = df.iloc[jogador_idx]

    # Cabeçalho com foto
    col1, col2 = st.columns([1, 3])
    with col1:
        exibir_foto(jogador, categoria="Profissional", width=120)
    with col2:
        nome = jogador.get('nome_completo', 'N/I')
        apelido = jogador.get('apelido', 'N/I')
        st.subheader(f"⚽ {nome} ({apelido})")
        st.write(f"**Posição:** {jogador.get('Posicao_Principal', 'N/I')}")
        st.write(f"**Idade:** {jogador.get('Idade', 'N/I')} anos")
        st.write(f"**Estado Físico:** {jogador.get('Estado_Fisico', 'N/I')}")

    # Dados pessoais
    st.subheader("📋 Dados Pessoais")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Data Nascimento:** {jogador.get('data_nascimento', 'N/I')}")
        st.write(f"**Altura:** {jogador.get('altura_cm', 'N/I')} cm")
        st.write(f"**Peso:** {jogador.get('peso_kg', 'N/I')} kg")
        st.write(f"**IMC:** {jogador.get('IMC', 'N/I')}")
    with col2:
        st.write(f"**Cidade:** {jogador.get('cidade_nascimento', 'N/I')}")
        st.write(f"**UF:** {jogador.get('uf_nascimento', 'N/I')}")
        st.write(f"**País:** {jogador.get('pais_nascimento', 'N/I')}")
        st.write(f"**Pé Preferido:** {jogador.get('pe_pref', 'N/I')}")

    # Atributos FM26 (se houver)
    atributos_fm26 = [
        'finalizacao', 'passe', 'drible', 'desarme', 'velocidade_maxima',
        'resistencia', 'forca_fisica', 'reflexos', 'jogo_aereo_goleiro',
        'defesas_goleiro', 'marcacao', 'cabecada', 'antecipacao', 'posicionamento'
    ]
    atributos_exib = {attr: jogador.get(attr) for attr in atributos_fm26 if pd.notna(jogador.get(attr))}
    if atributos_exib:
        st.subheader("🎮 Atributos FM26")
        df_atributos = pd.DataFrame([atributos_exib])
        st.dataframe(df_atributos, use_container_width=True)

    # Histórico de clubes
    if jogador.get('historico'):
        st.subheader("📜 Histórico de Clubes")
        st.write(jogador['historico'])

    # Cartões (buscar do JSON)
    st.subheader("🟨 Cartões e Suspensões")
    cartoes, _ = carregar_cartoes_json('profissional')
    nome_canonico = mapear_nome_para_canonico(jogador.get('nome_completo'))
    if nome_canonico and nome_canonico in cartoes:
        dados = cartoes[nome_canonico]
        amarelos = dados.get('amarelos', 0)
        vermelho = dados.get('vermelho', False)
        suspenso = dados.get('suspenso_proxima', False)
        st.write(f"🟨 Amarelos: {amarelos}")
        st.write(f"🟥 Vermelhos: {'Sim' if vermelho else 'Não'}")
        st.write(f"⚠️ Suspenso: {'Sim' if suspenso else 'Não'}")
        if amarelos >= 3:
            st.warning("⚠️ Jogador está suspenso por acúmulo de amarelos.")
        if vermelho:
            st.warning("⚠️ Jogador possui cartão vermelho.")
        # Histórico
        historico_cartoes = dados.get('historico', [])
        if historico_cartoes:
            st.write("**Histórico de cartões:**")
            df_hist = pd.DataFrame(historico_cartoes)
            st.dataframe(df_hist, use_container_width=True)
    else:
        st.write("Nenhum cartão registrado para este jogador.")

    # Botão voltar
    if st.button("← Voltar para lista"):
        st.switch_page("pages/analise.py")