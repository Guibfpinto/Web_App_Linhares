import streamlit as st
import pandas as pd
from datetime import datetime
import json
from pathlib import Path

# ============================================================
# CONFIGURAÇÃO DE CAMINHOS
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DADOS_DIR = BASE_DIR / "dados"

# ============================================================
# FUNÇÃO PARA CARREGAR JSON (COM CACHE)
# ============================================================
@st.cache_data(ttl=60)
def carregar_jogos_do_json(categoria):
    nome_arquivo = {
        "Profissional": "jogos_profissional.json",
        "Sub-15": "jogos_sub15.json",
        "Sub-17": "jogos_sub17.json"
    }.get(categoria)
    if not nome_arquivo:
        return None, "Categoria inválida", None

    caminho = DADOS_DIR / nome_arquivo
    caminho_abs = caminho.resolve()

    if not caminho.exists():
        return None, f"Arquivo não encontrado: {caminho_abs}", caminho_abs

    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            data = json.load(f)
            jogos = data.get('jogos', [])
            if not jogos:
                return None, "JSON carregado, mas lista 'jogos' vazia.", caminho_abs
            return jogos, f"Carregado ({len(jogos)} jogos)", caminho_abs
    except Exception as e:
        return None, f"Erro ao ler JSON: {e}", caminho_abs

# ============================================================
# FUNÇÃO PARA CALCULAR PRÓXIMO JOGO
# ============================================================
def calcular_proximo_jogo(jogos):
    hoje = datetime.now().date()
    futuros = []

    for jogo in jogos:
        data_str = jogo.get('data_jogo') or jogo.get('data')
        if not data_str:
            continue
        data_str = data_str.strip()
        try:
            data_obj = datetime.strptime(data_str, "%d/%m/%Y").date()
        except ValueError:
            try:
                data_obj = datetime.strptime(data_str, "%Y-%m-%d").date()
            except ValueError:
                continue

        if data_obj < hoje:
            continue
        futuros.append((data_obj, jogo))

    if not futuros:
        return None

    futuros.sort(key=lambda x: x[0])

    # Prioriza status AGENDADO ou AGUARDANDO
    for _, jogo in futuros:
        status = jogo.get('status', '').upper()
        if status in ['AGENDADO', 'AGUARDANDO']:
            return jogo

    # Se nenhum, retorna o mais próximo
    return futuros[0][1]

# ============================================================
# PÁGINA PRINCIPAL
# ============================================================
def show():
    st.title("📅 Próximo Jogo")
    st.markdown("---")

    # ===== SELETOR DE CATEGORIA =====
    categoria = st.selectbox(
        "Selecione a categoria",
        ["Profissional", "Sub-15", "Sub-17"],
        key="proximo_jogo_categoria"
    )

    # ===== BOTÃO RECARREGAR =====
    if st.button("🔄 Recarregar Dados"):
        st.cache_data.clear()
        st.rerun()

    # ===== CARREGAR DADOS =====
    jogos, mensagem, caminho = carregar_jogos_do_json(categoria)

    if jogos is None:
        st.error(f"❌ {mensagem}")
        st.info(f"Caminho procurado: `{caminho}`")
        return

    # ============================================================
    # PRÓXIMO JOGO (DESTAQUE)
    # ============================================================
    prox = calcular_proximo_jogo(jogos)

    if prox:
        st.subheader("🔜 Próximo Jogo")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Adversário:** {prox.get('adversario', 'N/I')}")
            st.write(f"**Data:** {prox.get('data_jogo', prox.get('data', 'N/I'))}")
            st.write(f"**Horário:** {prox.get('horario', 'N/I')}")
            st.write(f"**Local:** {prox.get('local_jogo', prox.get('local', 'N/I'))}")
        with col2:
            st.write(f"**Competição:** {prox.get('competicao', 'N/I')}")
            st.write(f"**Fase:** {prox.get('fase', 'N/I')}")
            st.write(f"**Status:** {prox.get('status', 'N/I')}")
            if prox.get('estadio'):
                st.write(f"**Estádio:** {prox['estadio']}")
            if prox.get('cidade'):
                st.write(f"**Cidade:** {prox['cidade']}")
        if prox.get('url_completa'):
            st.markdown(f"[🔗 Link do jogo]({prox['url_completa']})")
    else:
        st.warning("⚠️ Nenhum jogo futuro encontrado.")
        st.info("Verifique se há jogos com data >= hoje no JSON.")

    # ============================================================
    # DIAGNÓSTICO (recolhido por padrão)
    # ============================================================
    with st.expander("🔍 Diagnóstico (dados carregados)"):
        st.write(f"**Data do sistema:** `{datetime.now().date()}`")
        st.write(f"**Categoria:** {categoria}")
        st.write(f"**Total de jogos no JSON:** {len(jogos)}")
        if st.checkbox("Mostrar tabela completa"):
            df = pd.DataFrame(jogos)
            st.dataframe(df, use_container_width=True)

    # ============================================================
    # INFORMAÇÕES ADICIONAIS
    # ============================================================
    st.caption(f"Arquivo carregado: `{caminho}`")