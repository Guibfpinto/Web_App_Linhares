import streamlit as st
import pandas as pd
from datetime import datetime
import json
from pathlib import Path

# ============================================================
# CAMINHO PARA A PASTA DADOS (raiz do projeto)
# ============================================================
# Se este arquivo está em pages/, a raiz é um nível acima
BASE_DIR = Path(__file__).resolve().parent.parent
DADOS_DIR = BASE_DIR / "dados"

# ============================================================
# FUNÇÃO PARA CARREGAR JSON (com cache)
# ============================================================
@st.cache_data(ttl=60)  # cache de 60 segundos
def carregar_jogos_do_json(categoria):
    """
    Carrega a lista de jogos do arquivo JSON específico da categoria.
    Retorna (lista_de_jogos, mensagem_status, caminho_absoluto)
    """
    nome_arquivo = {
        "Profissional": "jogos_profissional.json",
        "Sub-15": "jogos_sub15.json",
        "Sub-17": "jogos_sub17.json"
    }.get(categoria)
    if not nome_arquivo:
        return None, "Categoria inválida", None

    caminho = DADOS_DIR / nome_arquivo
    caminho_absoluto = caminho.resolve()

    if not caminho.exists():
        return None, f"Arquivo não encontrado: {caminho_absoluto}", caminho_absoluto

    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            data = json.load(f)
            jogos = data.get('jogos', [])
            if not jogos:
                return None, "Arquivo JSON está vazio ou não contém a chave 'jogos'", caminho_absoluto
            return jogos, f"Carregado com sucesso ({len(jogos)} jogos)", caminho_absoluto
    except json.JSONDecodeError as e:
        return None, f"Erro de sintaxe JSON: {e}", caminho_absoluto
    except Exception as e:
        return None, f"Erro inesperado: {e}", caminho_absoluto

# ============================================================
# FUNÇÃO PARA CALCULAR O PRÓXIMO JOGO
# ============================================================
def calcular_proximo_jogo(jogos):
    if not jogos:
        return None

    hoje = datetime.now().date()
    jogos_futuros = []

    for jogo in jogos:
        data_str = jogo.get('data_jogo') or jogo.get('data')
        if not data_str:
            continue

        # Tenta dd/mm/aaaa
        try:
            data_obj = datetime.strptime(data_str, "%d/%m/%Y").date()
        except ValueError:
            # Tenta aaaa-mm-dd
            try:
                data_obj = datetime.strptime(data_str, "%Y-%m-%d").date()
            except ValueError:
                continue

        if data_obj < hoje:
            continue
        jogos_futuros.append((data_obj, jogo))

    if not jogos_futuros:
        return None

    jogos_futuros.sort(key=lambda x: x[0])

    # Prioriza status AGENDADO ou AGUARDANDO
    for _, jogo in jogos_futuros:
        status = jogo.get('status', '').upper()
        if status in ['AGENDADO', 'AGUARDANDO']:
            return jogo

    # Caso contrário, retorna o mais próximo
    return jogos_futuros[0][1]

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
    jogos, mensagem, caminho_abs = carregar_jogos_do_json(categoria)

    # ===== EXIBIR STATUS =====
    if jogos is None:
        st.error(f"❌ {mensagem}")
        st.info(f"**Caminho esperado:** `{caminho_abs}`")
        st.info("Verifique se a pasta 'dados' está na raiz do projeto e o arquivo existe.")
        return

    st.success(f"✅ {mensagem}")

    # ===== PRÓXIMO JOGO =====
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
        st.info("Verifique se há jogos com data a partir de hoje e status 'AGENDADO' ou 'AGUARDANDO'.")

    # ===== LISTA DE TODOS OS JOGOS FUTUROS =====
    st.markdown("---")
    st.subheader("📋 Todos os jogos futuros")

    df = pd.DataFrame(jogos)

    col_data = None
    for col in ['data_jogo', 'data', 'Data']:
        if col in df.columns:
            col_data = col
            break

    if col_data:
        df[col_data] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce')
        hoje = datetime.now().date()
        df_futuros = df[df[col_data].dt.date >= hoje].sort_values(col_data)
    else:
        df_futuros = df

    if df_futuros.empty:
        st.info("📭 Nenhum jogo futuro para exibir.")
        with st.expander("🔍 Ver todos os dados carregados (depuração)"):
            st.dataframe(df, use_container_width=True)
    else:
        colunas_exibir = ['data_jogo', 'adversario', 'local_jogo', 'competicao', 'fase', 'status', 'estadio', 'horario']
        colunas_existentes = [c for c in colunas_exibir if c in df_futuros.columns]
        if not colunas_existentes:
            st.dataframe(df_futuros, use_container_width=True)
        else:
            renomear = {
                'data_jogo': 'Data',
                'adversario': 'Adversário',
                'local_jogo': 'Local',
                'competicao': 'Competição',
                'fase': 'Fase',
                'status': 'Status',
                'estadio': 'Estádio',
                'horario': 'Horário'
            }
            df_exibicao = df_futuros[colunas_existentes].rename(columns=renomear)
            st.dataframe(df_exibicao, use_container_width=True)

    # ===== INFORMAÇÃO DO CAMINHO (opcional) =====
    with st.expander("📁 Informações do arquivo carregado"):
        st.write(f"**Arquivo:** {caminho_abs}")
        st.write(f"**Total de jogos:** {len(jogos)}")
        st.write(f"**Categoria:** {categoria}")