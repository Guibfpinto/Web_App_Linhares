# pages/proximo_jogo.py
import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
from utils import carregar_cronograma, obter_proximo_jogo

# ============================================================
# FUNÇÕES PARA CARREGAR DADOS
# ============================================================
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

def obter_proximo_jogo_do_script(categoria):
    """Tenta usar a função obter_proximo_jogo do script específico."""
    try:
        if categoria == "Profissional":
            from linhares_profissional_crono_2026 import obter_proximo_jogo
        elif categoria == "Sub-15":
            from linhares_sub15_crono_2026 import obter_proximo_jogo
        elif categoria == "Sub-17":
            from linhares_sub17_crono_2026 import obter_proximo_jogo
        else:
            return None
        return obter_proximo_jogo()
    except ImportError:
        return None

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

def calcular_proximo_jogo(jogos):
    """
    Recebe uma lista de dicionários de jogos e retorna o próximo jogo
    (data >= hoje, com status AGENDADO/AGUARDANDO, ou o mais próximo se nenhum).
    """
    if not jogos:
        return None

    hoje = datetime.now().date()
    jogos_com_data = []

    for jogo in jogos:
        data_str = jogo.get('data_jogo') or jogo.get('data')
        if not data_str:
            continue

        # Tenta parsear a data com diferentes formatos
        data_obj = None
        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                data_obj = datetime.strptime(data_str, fmt).date()
                break
            except ValueError:
                continue
        if data_obj is None:
            continue

        # Filtra apenas jogos a partir de hoje
        if data_obj < hoje:
            continue

        jogos_com_data.append((data_obj, jogo))

    if not jogos_com_data:
        return None

    # Ordena por data
    jogos_com_data.sort(key=lambda x: x[0])

    # Prioriza jogos com status AGENDADO ou AGUARDANDO
    for data, jogo in jogos_com_data:
        status = jogo.get('status', '').upper()
        if status in ['AGENDADO', 'AGUARDANDO']:
            return jogo

    # Se nenhum agendado, retorna o primeiro (mais próximo)
    return jogos_com_data[0][1]

# ============================================================
# PÁGINA PRINCIPAL
# ============================================================
def show():
    categoria = st.session_state.get("categoria_proximo_jogo", "Profissional")
    st.title(f"📅 Próximo Jogo - {categoria}")
    st.markdown("---")

    # Botão para recarregar (útil para testes)
    if st.button("🔄 Recarregar dados"):
        st.cache_data.clear()
        st.rerun()

    jogos = None
    origem = None
    prox = None

    # ===== 1. TENTA DO SCRIPT =====
    jogos_script = carregar_jogos_do_script(categoria)
    if jogos_script is not None:
        jogos = jogos_script
        origem = "script (Python)"
        prox = obter_proximo_jogo_do_script(categoria)
        st.info(f"✅ Carregados {len(jogos)} jogos do script.")
    else:
        # ===== 2. TENTA DO JSON =====
        jogos_json = carregar_jogos_do_json(categoria)
        if jogos_json is not None:
            jogos = jogos_json
            origem = "JSON"
            prox = calcular_proximo_jogo(jogos)
            st.info(f"✅ Carregados {len(jogos)} jogos do JSON.")
        else:
            # ===== 3. FALLBACK: CSV =====
            st.info(f"⚠️ Script e JSON não encontrados. Carregando do CSV para {categoria}.")
            df_crono = carregar_cronograma(categoria)
            if df_crono.empty:
                st.warning(f"Nenhum dado de cronograma disponível para {categoria}.")
                return
            jogos = df_crono.to_dict('records')
            origem = "CSV"
            prox = obter_proximo_jogo(categoria)
            st.info(f"✅ Carregados {len(jogos)} jogos do CSV.")

    if not jogos:
        st.warning(f"Nenhum jogo encontrado para {categoria}.")
        return

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

    # ===== EXIBE TODOS OS JOGOS FUTUROS =====
    st.markdown("---")
    st.subheader("📋 Todos os jogos futuros")

    # Converte a lista para DataFrame
    df = pd.DataFrame(jogos)

    # Identifica a coluna de data
    coluna_data = None
    for col in ['data_jogo', 'data', 'Data']:
        if col in df.columns:
            coluna_data = col
            break

    if coluna_data:
        # Converte para datetime
        df[coluna_data] = pd.to_datetime(df[coluna_data], dayfirst=True, errors='coerce')
        # Filtra datas futuras (a partir de hoje)
        hoje = datetime.now().date()
        df_futuros = df[df[coluna_data].dt.date >= hoje]
        # Ordena por data
        df_futuros = df_futuros.sort_values(coluna_data)
    else:
        df_futuros = df

    if df_futuros.empty:
        st.info("📭 Nenhum jogo futuro encontrado.")
        # Mostra os primeiros jogos (mesmo que passados) para depuração
        if not df.empty:
            with st.expander("🔍 Ver todos os jogos carregados (incluindo passados)"):
                st.dataframe(df.head(10), use_container_width=True)
    else:
        # Seleciona colunas para exibir
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