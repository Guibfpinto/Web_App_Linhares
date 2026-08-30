# pages/proximo_jogo.py
import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
from utils import carregar_cronograma, obter_proximo_jogo

# ============================================================
# FUNÇÕES DE CARREGAMENTO
# ============================================================
def carregar_jogos_do_json(categoria):
    """Carrega a lista de jogos do arquivo JSON específico da categoria."""
    nome_arquivo = {
        "Profissional": "jogos_profissional.json",
        "Sub-15": "jogos_sub15.json",
        "Sub-17": "jogos_sub17.json"
    }.get(categoria)
    if not nome_arquivo:
        return None
    if not os.path.exists(nome_arquivo):
        return None
    try:
        with open(nome_arquivo, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('jogos', [])
    except Exception as e:
        st.error(f"Erro ao carregar JSON: {e}")
        return None

def carregar_jogos_do_script(categoria):
    """Tenta importar JOGOS_TEMPORADA_2026 do script específico."""
    try:
        if categoria == "Profissional":
            from linhares_profissional_crono_2026 import JOGOS_TEMPORADA_2026
        elif categoria == "Sub-15":
            from linhares_sub15_crono_2026 import JOGOS_TEMPORADA_2026
        elif categoria == "Sub-17":
            from linhares_sub17_crono_2026 import JOGOS_TEMPORADA_2026
        else:
            return None
        return JOGOS_TEMPORADA_2026
    except ImportError:
        return None

def calcular_proximo_jogo(jogos):
    """Retorna o próximo jogo a partir de uma lista de dicionários."""
    if not jogos:
        return None
    hoje = datetime.now().date()
    jogos_com_data = []
    for jogo in jogos:
        data_str = jogo.get('data_jogo') or jogo.get('data')
        if not data_str:
            continue
        try:
            data_obj = datetime.strptime(data_str, "%d/%m/%Y").date()
        except:
            try:
                data_obj = datetime.strptime(data_str, "%Y-%m-%d").date()
            except:
                continue
        if data_obj < hoje:
            continue
        jogos_com_data.append((data_obj, jogo))
    if not jogos_com_data:
        return None
    jogos_com_data.sort(key=lambda x: x[0])
    for _, jogo in jogos_com_data:
        if jogo.get('status', '').upper() in ['AGENDADO', 'AGUARDANDO']:
            return jogo
    return jogos_com_data[0][1]

# ============================================================
# PÁGINA PRINCIPAL
# ============================================================
def show():
    # ===== MENSAGEM DE DEPURAÇÃO =====
    st.write("🔍 DEBUG: O código novo está rodando!")

    st.title("📅 Próximo Jogo")
    st.markdown("---")

    # ===== SELETOR DE CATEGORIA =====
    categoria = st.selectbox(
        "Selecione a categoria",
        ["Profissional", "Sub-15", "Sub-17"],
        key="proximo_jogo_categoria"
    )

    # ===== BOTÃO DE RECARREGAR =====
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🔄 Recarregar Dados", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col2:
        st.caption("Clique para recarregar os dados do arquivo JSON")

    # ===== CARREGAMENTO DOS DADOS =====
    jogos = None
    origem = None
    prox = None

    # 1. Tenta carregar do JSON
    jogos_json = carregar_jogos_do_json(categoria)
    if jogos_json is not None:
        jogos = jogos_json
        origem = "JSON"
        prox = calcular_proximo_jogo(jogos)
        st.success(f"✅ {len(jogos)} jogos carregados do JSON.")

    # 2. Fallback: script (se JSON não existir)
    if jogos is None:
        jogos_script = carregar_jogos_do_script(categoria)
        if jogos_script is not None:
            jogos = jogos_script
            origem = "script (Python)"
            # Tenta usar a função do script (se disponível)
            try:
                if categoria == "Profissional":
                    from linhares_profissional_crono_2026 import obter_proximo_jogo
                elif categoria == "Sub-15":
                    from linhares_sub15_crono_2026 import obter_proximo_jogo
                elif categoria == "Sub-17":
                    from linhares_sub17_crono_2026 import obter_proximo_jogo
                else:
                    prox = None
                prox = obter_proximo_jogo()
            except:
                prox = calcular_proximo_jogo(jogos)
            st.success(f"✅ {len(jogos)} jogos carregados do script.")

    # 3. Fallback final: CSV
    if jogos is None:
        st.info("⚠️ JSON e script não encontrados. Usando CSV.")
        df_crono = carregar_cronograma(categoria)
        if df_crono.empty:
            st.warning(f"Nenhum dado de cronograma para {categoria}.")
            return
        jogos = df_crono.to_dict('records')
        origem = "CSV"
        prox = obter_proximo_jogo(categoria)
        st.success(f"✅ {len(jogos)} jogos carregados do CSV.")

    if not jogos:
        st.warning(f"Nenhum jogo encontrado para {categoria}.")
        return

    st.caption(f"Fonte: {origem}")

    # ===== EXIBE O PRÓXIMO JOGO =====
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
        st.info("⚠️ Nenhum jogo futuro encontrado. Verifique se há jogos com data a partir de hoje e status AGENDADO ou AGUARDANDO.")

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
        st.info("📭 Nenhum jogo futuro.")
        # Expansor de depuração para ver todos os dados
        with st.expander("🔍 Ver dados carregados (depuração)"):
            st.write(f"Total de jogos: {len(df)}")
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