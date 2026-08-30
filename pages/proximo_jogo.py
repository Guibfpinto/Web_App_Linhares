# pages/proximo_jogo.py
import streamlit as st
import pandas as pd
from datetime import datetime
import json
from pathlib import Path

# ============================================================
# CONFIGURAÇÃO DE CAMINHOS
# ============================================================
# Supondo que este arquivo está em pages/ e a pasta dados/ está na raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent
DADOS_DIR = BASE_DIR / "dados"

# ============================================================
# FUNÇÕES DE CARREGAMENTO E FILTRO
# ============================================================
@st.cache_data(ttl=60)
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
    caminho_abs = caminho.resolve()

    if not caminho.exists():
        return None, f"Arquivo não encontrado: {caminho_abs}", caminho_abs

    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            data = json.load(f)
            jogos = data.get('jogos', [])
            if not jogos:
                return None, "Arquivo JSON carregado, mas a lista 'jogos' está vazia.", caminho_abs
            return jogos, f"Carregado com sucesso ({len(jogos)} jogos)", caminho_abs
    except json.JSONDecodeError as e:
        return None, f"Erro de sintaxe JSON: {e}", caminho_abs
    except Exception as e:
        return None, f"Erro inesperado: {e}", caminho_abs

def calcular_proximo_jogo(jogos):
    """
    Retorna o próximo jogo (dicionário) a partir da lista.
    Critérios:
      - Data >= hoje
      - Status AGENDADO ou AGUARDANDO (prioridade)
      - Se nenhum com esses status, retorna o mais próximo no futuro (independente do status)
    """
    hoje = datetime.now().date()
    futuros = []

    for jogo in jogos:
        data_str = jogo.get('data_jogo') or jogo.get('data')
        if not data_str:
            continue

        # Remove espaços extras
        data_str = data_str.strip()

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

        futuros.append((data_obj, jogo))

    if not futuros:
        return None

    # Ordena por data
    futuros.sort(key=lambda x: x[0])

    # Prioriza jogos com status AGENDADO ou AGUARDANDO
    for _, jogo in futuros:
        status = jogo.get('status', '').upper()
        if status in ['AGENDADO', 'AGUARDANDO']:
            return jogo

    # Se nenhum com status desejado, retorna o mais próximo
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
    jogos, mensagem, caminho_abs = carregar_jogos_do_json(categoria)

    # ===== EXIBIR STATUS DE CARREGAMENTO =====
    if jogos is None:
        st.error(f"❌ **Erro ao carregar dados:** {mensagem}")
        st.info(f"**Caminho procurado:** `{caminho_abs}`")
        st.info("Verifique se a pasta 'dados' está na raiz do projeto e contém o arquivo correto.")
        return

    st.success(f"✅ {mensagem}")

    # ===== PAINEL DE DIAGNÓSTICO (opcional, mas útil) =====
    with st.expander("🔍 Diagnóstico - Dados carregados"):
        st.write(f"**Data do sistema:** `{datetime.now().date()}`")
        st.write(f"**Total de jogos carregados:** {len(jogos)}")
        df_all = pd.DataFrame(jogos)
        st.dataframe(df_all)

    # ===== CALCULAR PRÓXIMO JOGO =====
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
        st.info("Caso existam jogos com status diferente, eles aparecerão na lista abaixo, mas não serão marcados como 'próximo'.")

    # ===== LISTA DE TODOS OS JOGOS FUTUROS =====
    st.markdown("---")
    st.subheader("📋 Todos os jogos futuros")

    df = pd.DataFrame(jogos)

    # Identifica a coluna de data
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
    else:
        # Seleciona colunas amigáveis para exibição
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

    # ===== INFORMAÇÕES ADICIONAIS =====
    with st.expander("📁 Detalhes do arquivo carregado"):
        st.write(f"**Caminho absoluto:** `{caminho_abs}`")
        st.write(f"**Total de jogos no JSON:** {len(jogos)}")
        st.write(f"**Categoria selecionada:** {categoria}")