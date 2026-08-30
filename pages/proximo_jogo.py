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
    except Exception:
        return None

# ============================================================
# PÁGINA PRINCIPAL
# ============================================================
def show():
    categoria = st.session_state.get("categoria_proximo_jogo", "Profissional")
    st.title(f"📅 Próximo Jogo - {categoria}")
    st.markdown("---")

    jogos = None
    origem = None

    # ===== 1. TENTA DO SCRIPT =====
    jogos_script = carregar_jogos_do_script(categoria)
    if jogos_script is not None:
        jogos = jogos_script
        origem = "script (Python)"
        # Tenta obter o próximo jogo pela função do script
        prox = obter_proximo_jogo_do_script(categoria)
    else:
        # ===== 2. TENTA DO JSON =====
        jogos_json = carregar_jogos_do_json(categoria)
        if jogos_json is not None:
            jogos = jogos_json
            origem = "JSON"
            # Calcula o próximo jogo manualmente a partir da lista JSON
            prox = calcular_proximo_jogo(jogos)
        else:
            # ===== 3. FALLBACK: CSV =====
            st.info(f"Script e JSON não encontrados. Carregando do CSV para {categoria}.")
            df_crono = carregar_cronograma(categoria)
            if df_crono.empty:
                st.warning(f"Nenhum dado de cronograma disponível para {categoria}.")
                return
            # Converte DataFrame para lista de dicionários (mesmo formato)
            jogos = df_crono.to_dict('records')
            origem = "CSV"
            # Usa a função do utils para obter o próximo jogo
            prox = obter_proximo_jogo(categoria)

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
        st.info("Nenhum jogo futuro encontrado.")

    # ===== EXIBE TODOS OS JOGOS FUTUROS =====
    st.markdown("---")
    st.subheader("📋 Todos os jogos futuros")

    # Converte a lista para DataFrame
    df = pd.DataFrame(jogos)

    # Filtra apenas jogos com data futura (ou a partir de hoje)
    hoje = datetime.now().date()
    coluna_data = None
    for col in ['data_jogo', 'data', 'Data']:
        if col in df.columns:
            coluna_data = col
            break
    if coluna_data:
        try:
            df[coluna_data] = pd.to_datetime(df[coluna_data], dayfirst=True, errors='coerce')
            df_futuros = df[df[coluna_data].dt.date >= hoje].sort_values(coluna_data)
        except:
            df_futuros = df
    else:
        df_futuros = df

    if df_futuros.empty:
        st.info("Nenhum jogo futuro.")
    else:
        # Seleciona colunas para exibir
        colunas_exibir = ['data_jogo', 'adversario', 'local_jogo', 'competicao', 'fase', 'status', 'estadio', 'horario']
        colunas_existentes = [c for c in colunas_exibir if c in df_futuros.columns]
        if not colunas_existentes:
            # Fallback: exibe todas as colunas
            st.dataframe(df_futuros, use_container_width=True)
        else:
            # Renomeia para exibição amigável
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

# ============================================================
# FUNÇÃO AUXILIAR PARA CALCULAR PRÓXIMO JOGO A PARTIR DA LISTA
# ============================================================
def calcular_proximo_jogo(jogos):
    """
    Recebe uma lista de dicionários de jogos e retorna o próximo jogo
    (data >= hoje, com status AGENDADO/AGUARDANDO, ou o mais próximo se nenhum).
    """
    if not jogos:
        return None

    hoje = datetime.now().date()

    # Converte data para datetime
    jogos_com_data = []
    for jogo in jogos:
        data_str = jogo.get('data_jogo') or jogo.get('data')
        if not data_str:
            continue
        try:
            # Tenta parsear no formato DD/MM/YYYY
            data_obj = datetime.strptime(data_str, "%d/%m/%Y").date()
        except:
            try:
                # Tenta outros formatos comuns
                data_obj = pd.to_datetime(data_str, errors='coerce').date()
                if pd.isna(data_obj):
                    continue
            except:
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