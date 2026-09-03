# app.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time
import base64
import os
import random
import matplotlib.pyplot as plt
from mplsoccer import Pitch, VerticalPitch
import sqlite3

# ======================================================================
# IMPORTAÇÕES DO UTILS
# ======================================================================
from utils import (
    carregar_elenco_profissional,
    carregar_elenco_sub15,
    carregar_elenco_sub17,
    carregar_comissao,
    carregar_comissao_sub15,
    carregar_comissao_sub17,
    carregar_cartoes_json,
    salvar_cartoes_json,
    adicionar_coluna_lesionado,
    carregar_dados_bioimpedancia,
    aplicar_dados_bioimpedancia,
    carregar_estatisticas_partidas,
    precomputar_scores_posicionais,
    interpretar_formacao,
    obter_jogadores_para_posicao,
    jogador_suspenso,
    mapear_nome_para_canonico,
    obter_caminho_foto,
    obter_historico_clubes,
    obter_lesao_atual,
    obter_historico_lesoes_texto,
    autenticar_usuario,
    listar_usuarios,
    adicionar_usuario,
    remover_usuario,
    gerar_relatorio_completo_texto,
    exportar_para_excel,
    exportar_para_powerbi,
    verificar_jogo_ao_vivo,
    obter_detalhes_jogo,
    obter_estatisticas_jogo,
    obter_eventos_jogo,
    obter_lineups_completos,
    obter_players_stats,
    gerar_relatorio_excel,
    obter_atributos_chave,
    inicializar_cartoes_por_csvs,
    ATRIBUTOS_FM26,
    NOME_TIME,
    TEMPORADA,
    DATA_DIR,
    ARQUIVO_CSV_PROFISSIONAL,
    ARQUIVO_CSV_SUB15,
    ARQUIVO_CSV_SUB17,
    ARQUIVO_CSV_COMISSAO_PROFISSIONAL,
    ARQUIVO_CSV_COMISSAO_SUB15,
    ARQUIVO_CSV_COMISSAO_SUB17,
    obter_proximo_jogo,
    exibir_foto,
    formatar_cartoes,
    inicializar_banco,
    carregar_cronograma,
)

# ======================================================================
# DICIONÁRIO DE TRADUÇÃO DOS ATRIBUTOS DA COMISSÃO
# ======================================================================
TRADUCAO_ATRIBUTOS = {
    # Gerais
    'CA': 'CA (Habilidade Atual)',
    'PA': 'PA (Potencial)',
    'reputacao_mundial': 'Reputação Mundial',
    'reputacao_atual': 'Reputação Atual',
    'reputacao_local': 'Reputação Local',
    'qualificacoes_treinador': 'Qualificações de Treinador',
    'tipo_documento': 'Tipo de Documento',
    'jogos_selecao': 'Jogos pela Seleção',
    'gols_selecao': 'Gols pela Seleção',
    'jogos_sub21': 'Jogos Sub-21',
    'gols_sub21': 'Gols Sub-21',
    
    # Chairman
    'chairmanattributes_business': 'Presidente - Negócios',
    'chairmanattributes_interference': 'Presidente - Interferência',
    'chairmanattributes_patience': 'Presidente - Paciência',
    'chairmanattributes_resources': 'Presidente - Recursos',
    
    # Coaching
    'coachingattributes_attacking': 'Treinamento - Ataque',
    'coachingattributes_defending': 'Treinamento - Defesa',
    'coachingattributes_fitness': 'Treinamento - Condicionamento',
    'coachingattributes_goalkeeping': 'Treinamento - Goleiros',
    'coachingattributes_possession': 'Treinamento - Posse',
    'coachingattributes_player': 'Treinamento - Jogadores',
    'coachingattributes_tactical': 'Treinamento - Tática',
    'coachingattributes_technical': 'Treinamento - Técnico',
    'coachingattributes_peoplemanagement': 'Treinamento - Gestão de Pessoas',
    'coachingattributes_workingwithyoungsters': 'Treinamento - Trabalho com Jovens',
    'coachingattributes_dirtinessallowance': 'Treinamento - Tolerância a Rudes',
    'coachingattributes_versatility': 'Treinamento - Versatilidade',
    'coachingattributes_setpieces': 'Treinamento - Bolas Paradas',
    
    # Staff Mental
    'staffmentalattributes_adaptability': 'Adaptabilidade (Staff)',
    'staffmentalattributes_determination': 'Determinação (Staff)',
    'staffmentalattributes_judgingplayerability': 'Avaliação Habilidade Jogador',
    'staffmentalattributes_judgingplayerpotential': 'Avaliação Potencial Jogador',
    'staffmentalattributes_judgingstaffability': 'Avaliação Habilidade Staff',
    'staffmentalattributes_negotiating': 'Negociação',
    'staffmentalattributes_authority': 'Autoridade',
    'staffmentalattributes_motivating': 'Motivação',
    'staffmentalattributes_physiotherapy': 'Fisioterapia',
    'staffmentalattributes_tacticalknowledge': 'Conhecimento Tático',
    
    # Non Tactical
    'nontacticalattributes_buyingplayers': 'Compra de Jogadores',
    'nontacticalattributes_hardnessoftraining': 'Intensidade do Treino',
    'nontacticalattributes_mindgames': 'Jogos Mentais',
    'nontacticalattributes_squadrotation': 'Rotação do Elenco',
    
    # Roles
    'rolesattributes_assistantmanager': 'Auxiliar Técnico',
    'rolesattributes_coach': 'Treinador',
    'rolesattributes_fitnesscoach': 'Preparador Físico',
    'rolesattributes_goalkeepingcoach': 'Preparador de Goleiros',
    'rolesattributes_manager': 'Treinador Principal',
    'rolesattributes_physio': 'Fisioterapeuta',
    'rolesattributes_scout': 'Olheiro',
    'rolesattributes_chairman': 'Presidente',
    'rolesattributes_directoroffootball': 'Diretor de Futebol',
    'rolesattributes_headofyouthdevelopment': 'Chefe da Base',
    'rolesattributes_dataanalyst': 'Analista de Dados',
    'rolesattributes_sportsscientist': 'Cientista do Esporte',
    'rolesattributes_loanmanager': 'Gerente de Empréstimos',
    'rolesattributes_technicaldirector': 'Diretor Técnico',
    'rolesattributes_setpiececoach': 'Treinador de Bolas Paradas',
    
    # Tactical
    'tacticalattributes_attacking': 'Tática - Ataque',
    'tacticalattributes_depth': 'Profundidade',
    'tacticalattributes_directness': 'Direção',
    'tacticalattributes_flamboyancy': 'Espetacularidade',
    'tacticalattributes_flexibility': 'Flexibilidade',
    'tacticalattributes_freeroles': 'Funções Livres',
    'tacticalattributes_marking': 'Marcação',
    'tacticalattributes_offside': 'Impedimento',
    'tacticalattributes_pressing': 'Pressão',
    'tacticalattributes_sittingback': 'Recuar',
    'tacticalattributes_tempo': 'Ritmo',
    'tacticalattributes_useofplaymaker': 'Uso do Armador',
    'tacticalattributes_useofsubstitutions': 'Uso de Substituições',
    'tacticalattributes_width': 'Largura',
    
    # Scouting
    'scoutingattributes_judgingplayerdata': 'Avaliação Dados Jogador',
    'scoutingattributes_judgingteamdata': 'Avaliação Dados Time',
    'scoutingattributes_presentingdata': 'Apresentação de Dados',
    
    # Medical
    'medicalattributes_sportsscience': 'Ciência do Esporte',
    
    # Personality
    'personalityattributes_adaptability': 'Adaptabilidade (Personalidade)',
    'personalityattributes_ambition': 'Ambição',
    'personalityattributes_loyalty': 'Lealdade',
    'personalityattributes_pressure': 'Pressão (Personalidade)',
    'personalityattributes_professional': 'Profissionalismo',
    'personalityattributes_sportsmanship': 'Espírito Esportivo',
    'personalityattributes_temperament': 'Temperamento',
    'personalityattributes_controversy': 'Controvérsia',
    
    # Nation
    'pais': 'País',
    'sigla_pais': 'Sigla País',
    'conhecimento_valor': 'Conhecimento - Valor',
}

# ======================================================================
# CONFIGURAÇÃO INICIAL & CSS PERSONALIZADO
# ======================================================================
st.set_page_config(layout="wide", page_title=f"{NOME_TIME} - Temporada {TEMPORADA}", page_icon="⚽")

st.markdown("""
<style>
    div[data-testid="stAlert"] { color: black !important; }
    div[data-testid="stAlert"] .stAlert { color: black !important; }
    .stAlert { color: black !important; }

    .stApp {
        background-color: #000000 !important;
        border-radius: 10px;
        margin: 10px;
        padding: 10px;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #cc0000 !important;
    }
    .stMarkdown, .stText, .stSubheader, .stCaption {
        color: #cc0000 !important;
    }
    div.stText, div.stMarkdown, .stText, .stMarkdown {
        color: #cc0000 !important;
    }
    .stSelectbox label, .stTextInput label, .stNumberInput label,
    .stDateInput label, .stTextArea label {
        color: #cc0000 !important;
        font-weight: 500 !important;
    }
    [data-testid="stMetric"] .stMetricValue {
        color: #cc0000 !important;
    }
    [data-testid="stMetric"] label {
        color: #cc0000 !important;
    }
    .streamlit-expanderHeader {
        color: #cc0000 !important;
        background-color: #1a1a1a !important;
        border: 1px solid #333 !important;
        border-radius: 5px !important;
    }
    .streamlit-expanderContent {
        color: #cc0000 !important;
        background-color: #111111 !important;
        border: 1px solid #333 !important;
        border-top: none !important;
        border-radius: 0 0 5px 5px !important;
        padding: 10px !important;
    }
    .stButton button {
        color: #cc0000 !important;
        background-color: #222222 !important;
        border: 1px solid #444 !important;
        border-radius: 4px !important;
        transition: all 0.2s ease !important;
    }
    .stButton button:hover {
        background-color: #333333 !important;
        border-color: #666 !important;
    }
    .stButton button:active {
        background-color: #111111 !important;
    }
    .stRadio label, .stCheckbox label {
        color: #cc0000 !important;
    }
    .stRadio div[role="radiogroup"] > label {
        background-color: #1a1a1a !important;
        border: 1px solid #333 !important;
        border-radius: 4px !important;
        padding: 5px 10px !important;
        margin: 2px !important;
        color: #cc0000 !important;
    }
    .stRadio div[role="radiogroup"] > label:hover {
        background-color: #2a2a2a !important;
    }
    .stSelectbox div[data-baseweb="select"] > div,
    .stTextInput input, .stNumberInput input,
    .stDateInput input, .stTextArea textarea {
        background-color: #222222 !important;
        color: #cc0000 !important;
        border: 1px solid #444 !important;
        border-radius: 4px !important;
    }
    .stSelectbox div[data-baseweb="select"] > div:hover,
    .stTextInput input:hover, .stNumberInput input:hover,
    .stDateInput input:hover, .stDateInput input:hover,
    .stTextArea textarea:hover {
        border-color: #666 !important;
    }
    .stSelectbox div[data-baseweb="select"] > div:focus-within,
    .stTextInput input:focus, .stNumberInput input:focus,
    .stDateInput input:focus, .stTextArea textarea:focus {
        border-color: #1e88e5 !important;
        box-shadow: 0 0 0 2px rgba(30,136,229,0.3) !important;
    }
    [data-testid="stMetric"] {
        background-color: #1a1a1a !important;
        border: 1px solid #333 !important;
        border-radius: 5px !important;
        padding: 10px !important;
    }
    .stDataFrame {
        background-color: #111111 !important;
        border: 1px solid #333 !important;
        border-radius: 5px !important;
    }
    .stDataFrame table {
        color: #cc0000 !important;
    }
    .stDataFrame thead tr th {
        background-color: #1a1a1a !important;
        color: #cc0000 !important;
        border-bottom: 2px solid #444 !important;
    }
    .stDataFrame tbody tr {
        border-bottom: 1px solid #2a2a2a !important;
    }
    .stDataFrame tbody tr:hover {
        background-color: #2a2a2a !important;
    }
    .dataframe {
        background-color: #111111 !important;
        color: #cc0000 !important;
    }
    .dataframe thead th {
        background-color: #1a1a1a !important;
        color: #cc0000 !important;
    }
    .dataframe tbody td {
        border-color: #2a2a2a !important;
    }
    hr {
        border-color: #444 !important;
    }
    .stFileUploader > div {
        background-color: #1a1a1a !important;
        border: 2px dashed #444 !important;
        border-radius: 5px !important;
        color: #aaa !important;
    }
    .stFileUploader > div:hover {
        border-color: #666 !important;
    }
    .css-1d391kg, .css-1kyxreq {
        background-color: rgba(0,0,0,0.9) !important;
    }
    .sidebar .stSelectbox label, .sidebar .stTextInput label {
        color: #cc0000 !important;
    }
</style>
""", unsafe_allow_html=True)

def set_background(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode()
        ext = os.path.splitext(image_path)[1].lower()
        mime = "image/png" if ext == ".png" else "image/jpeg"
        bg_css = f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:{mime};base64,{img_base64}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        [data-testid="stHeader"] {{ background: rgba(0,0,0,0); }}
        .stApp {{ background-color: #000000; border-radius: 10px; margin: 10px; padding: 10px; }}
        [data-testid="stSidebar"] {{ background-color: rgba(0,0,0,0.9); }}
        </style>
        """
        st.markdown(bg_css, unsafe_allow_html=True)
    else:
        bg_css = """
        <style>
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #1a2a3a 0%, #0d1b2a 100%);
            background-attachment: fixed;
        }
        [data-testid="stHeader"] { background: rgba(0,0,0,0); }
        .stApp { background-color: #000000; border-radius: 10px; margin: 10px; padding: 10px; }
        [data-testid="stSidebar"] { background-color: rgba(0,0,0,0.9); }
        </style>
        """
        st.markdown(bg_css, unsafe_allow_html=True)

bg_image = os.path.join(DATA_DIR, "background.png")
set_background(bg_image)

st.title(f"⚽ {NOME_TIME} - Temporada {TEMPORADA}")

# ======================================================================
# INICIALIZAÇÃO DE ESTADO
# ======================================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""
if "titulares" not in st.session_state:
    st.session_state.titulares = []
if "reservas" not in st.session_state:
    st.session_state.reservas = []
if "substituicoes" not in st.session_state:
    st.session_state.substituicoes = []
if "gols" not in st.session_state:
    st.session_state.gols = []
if "total_substituicoes" not in st.session_state:
    st.session_state.total_substituicoes = 0
if "data_jogo" not in st.session_state:
    st.session_state.data_jogo = ""
if "adversario" not in st.session_state:
    st.session_state.adversario = ""
if "vila_e_casa" not in st.session_state:
    st.session_state.vila_e_casa = True
if "fixture_id" not in st.session_state:
    st.session_state.fixture_id = None
if "monitorando" not in st.session_state:
    st.session_state.monitorando = False
if "time_base" not in st.session_state:
    st.session_state.time_base = None
if "escalacoes_geradas" not in st.session_state:
    st.session_state.escalacoes_geradas = {}
if "instrucoes_coletivas" not in st.session_state:
    st.session_state.instrucoes_coletivas = {}

# ======================================================================
# FUNÇÕES AUXILIARES PARA OBTER DADOS POR CATEGORIA
# ======================================================================
def get_elenco(categoria):
    if categoria == "Profissional":
        return carregar_elenco_profissional()
    elif categoria == "Sub-15":
        return carregar_elenco_sub15()
    elif categoria == "Sub-17":
        return carregar_elenco_sub17()
    return None

def get_comissao(categoria):
    if categoria == "Comissão Profissional":
        return carregar_comissao()
    elif categoria == "Comissão Sub-15":
        return carregar_comissao_sub15()
    elif categoria == "Comissão Sub-17":
        return carregar_comissao_sub17()
    return None

def get_cartoes(categoria):
    mapeamento = {
        "Profissional": "profissional",
        "Sub-15": "sub15",
        "Sub-17": "sub17",
        "Comissão Profissional": "comissao_profissional",
        "Comissão Sub-15": "comissao_sub15",
        "Comissão Sub-17": "comissao_sub17",
    }
    chave = mapeamento.get(categoria)
    if chave:
        cart, _ = carregar_cartoes_json(chave)
        return cart
    return {}

def get_estatisticas_partidas(categoria):
    from utils import carregar_estatisticas_partidas
    return carregar_estatisticas_partidas(categoria)

# ======================================================================
# FUNÇÃO DETALHES COMISSÃO (CORRIGIDA PARA 'foto')
# ======================================================================
def exibir_detalhes_comissao(row, categoria, cartoes):
    with st.expander(f"📋 DETALHES - {row.get('nome', row.get('apelido', 'Membro'))}", expanded=True):
        col1, col2 = st.columns([1, 2])
        with col1:
            # Busca a foto pelo apelido (ou nome)
            caminho_foto = obter_caminho_foto(row, categoria)
            if caminho_foto and os.path.exists(caminho_foto):
                try:
                    st.image(caminho_foto, width=150)
                except Exception as e:
                    st.write("📷 Sem foto (erro ao carregar)")
                    st.error(f"Erro: {e}")
            else:
                st.write("📷 Sem foto")
        with col2:
            st.write(f"**Nome:** {row.get('nome_completo', row.get('nome', 'N/I'))}")
            st.write(f"**Apelido:** {row.get('apelido', 'N/I')}")
            st.write(f"**Cargo:** {row.get('cargo', 'N/I')}")
            st.write(f"**Data Nasc.:** {row.get('data_nascimento', 'N/I')}")
            st.write(f"**Idade:** {row.get('idade', 'N/I')}")
            st.write(f"**Cidade/UF:** {row.get('cidade_nascimento', 'N/I')} / {row.get('uf_nascimento', 'N/I')}")
            st.write(f"**País:** {row.get('pais_nascimento', row.get('pais', 'N/I'))}")
            nome_canonico = mapear_nome_para_canonico(row.get('nome', row.get('apelido')))
            suspenso = "Sim" if jogador_suspenso(nome_canonico, cartoes) else "Não"
            st.write(f"**Suspenso:** {suspenso}")
        st.divider()
        
        st.subheader("📜 Histórico")
        col_hist1, col_hist2 = st.columns(2)
        with col_hist1:
            st.write("**Histórico Profissional:**")
            st.write(row.get('historico_comissao', 'Não informado'))
        with col_hist2:
            st.write("**Histórico como Jogador:**")
            st.write(row.get('historico_jogador', 'Não informado'))
        st.divider()
        
        st.subheader("🟨 Histórico de Cartões")
        if nome_canonico in cartoes:
            historico = cartoes[nome_canonico].get('historico', [])
            if historico:
                df_hist = pd.DataFrame(historico)
                st.dataframe(df_hist[['data','adversario','cor','terceiro_amarelo','suspenso_causada','suspenso_cumprida']], width='stretch')
            else:
                st.info("Nenhum cartão registrado.")
        else:
            st.info("Nenhum cartão registrado.")
        st.divider()
        
        st.subheader("📊 Atributos Detalhados")
        colunas_excluir = ['nome', 'nome_completo', 'apelido', 'cargo', 'data_nascimento', 
                           'cidade_nascimento', 'uf_nascimento', 'pais_nascimento', 'pais',
                           'idade', 'historico_jogador', 'historico_comissao', 
                           'id_ogol_comissao', 'data_nascimento.1', 'apelido_norm']
        colunas_atributos = [col for col in row.index if col not in colunas_excluir and not pd.isna(row[col])]
        if colunas_atributos:
            col1, col2 = st.columns(2)
            for i, attr in enumerate(colunas_atributos):
                valor = row[attr]
                if pd.isna(valor):
                    valor = "N/I"
                nome_attr = TRADUCAO_ATRIBUTOS.get(attr, attr)
                with col1 if i % 2 == 0 else col2:
                    st.write(f"• **{nome_attr}:** {valor}")
        else:
            st.info("Nenhum atributo detalhado disponível para este membro.")

# ======================================================================
# FUNÇÃO DETALHES JOGADOR (CORRIGIDA PARA 'foto')
# ======================================================================
def exibir_detalhes_jogador(row, categoria, cartoes):
    with st.expander(f"📋 DETALHES COMPLETOS - {row.get('nome_completo', 'Jogador')}", expanded=True):
        col1, col2 = st.columns([1, 2])
        with col1:
            # Busca a foto pelo apelido (ou nome completo)
            caminho_foto = obter_caminho_foto(row, categoria)
            if caminho_foto and os.path.exists(caminho_foto):
                try:
                    st.image(caminho_foto, width=150)
                except Exception as e:
                    st.write("📷 Sem foto (erro ao carregar)")
                    st.error(f"Erro: {e}")
            else:
                st.write("📷 Sem foto")
        with col2:
            st.write(f"**Nome:** {row.get('nome_completo', 'N/I')}")
            st.write(f"**Apelido:** {row.get('apelido', 'N/I')}")
            data_nasc = row.get('data_nascimento', '')
            idade = row.get('Idade', 'N/I')
            st.write(f"**Data Nasc.:** {data_nasc}  **Idade:** {idade}")
            cidade = row.get('cidade_nascimento', '')
            uf = row.get('uf_nascimento', '')
            pais = row.get('pais_nascimento', '')
            st.write(f"**Cidade/UF:** {cidade if pd.notna(cidade) else 'N/I'} / {uf if pd.notna(uf) else 'N/I'}")
            st.write(f"**País:** {pais if pd.notna(pais) else 'N/I'}")
            st.write(f"**Pos. Principal:** {row.get('Posicao_Principal', 'N/I')}")
            pos_sec = row.get('Posicoes_Secundarias', [])
            if isinstance(pos_sec, list):
                pos_sec_str = ", ".join(pos_sec) if pos_sec else "Nenhuma"
            else:
                pos_sec_str = str(pos_sec) if pd.notna(pos_sec) else "Nenhuma"
            st.write(f"**Pos. Secundárias:** {pos_sec_str}")
            pe = row.get('pe_pref', '')
            pe_map = {np.nan: 'N/I', 'D': 'Destro', 'C': 'Canhoto', 'A': 'Ambidestro'}
            pe_str = pe_map.get(pe, str(pe)) if pd.notna(pe) else 'N/I'
            st.write(f"**Pé Preferencial:** {pe_str}")
            rating = row.get('Rating_Geral_FM26', 0)
            st.write(f"**Rating FM26:** {rating:.1f}" if pd.notna(rating) else "N/I")
            st.write(f"**Estado Físico:** {row.get('Estado_Fisico', 'N/I')}")
            st.write(f"**Lesionado:** {'Sim' if row.get('lesionado') else 'Não'}")
            lesao = obter_lesao_atual(row, categoria)
            st.write(f"**Lesão Atual:** {lesao if lesao else 'Nenhuma'}")
            imc = row.get('IMC')
            if pd.notna(imc):
                st.write(f"**IMC:** {imc:.1f} ({row.get('Classificacao_IMC', '')})")
            gordura = row.get('Gordura_Corporal_%')
            if pd.notna(gordura):
                st.write(f"**Gordura Corporal:** {gordura:.1f}% ({row.get('Classificacao_Gordura', '')})")
            massa_magra = row.get('Massa_Magra_kg')
            if pd.notna(massa_magra):
                st.write(f"**Massa Magra:** {massa_magra:.1f} kg")
            massa_muscular = row.get('Massa_Muscular_Estimada_kg')
            if pd.notna(massa_muscular):
                st.write(f"**Massa Muscular Estimada:** {massa_muscular:.1f} kg")
        st.divider()
        st.subheader("📜 Histórico de Clubes")
        st.text(obter_historico_clubes(row))
        st.subheader("🩺 Histórico de Lesões")
        texto_lesoes = obter_historico_lesoes_texto(row, categoria)
        st.text(texto_lesoes)
        st.subheader("📊 Estatísticas da Temporada (oGol)")
        estatisticas_ogol = {
            'jogos_temporada': 'Jogos na temporada',
            'minutos_totais': 'Minutos totais',
            'media_minutos_por_jogo': 'Média minutos/jogo',
            'gols_totais': 'Gols',
            'assistencias_totais': 'Assistências',
            'cartoes_amarelos_totais': 'Cartões amarelos',
            'cartoes_vermelhos_totais': 'Cartões vermelhos'
        }
        for col_name, label in estatisticas_ogol.items():
            valor = row.get(col_name, '0')
            if pd.isna(valor) or str(valor).strip() == '':
                valor_str = '0'
            else:
                valor_str = str(valor).strip()
                if valor_str.endswith('.0'):
                    valor_str = valor_str[:-2]
            st.write(f"**{label}:** {valor_str}")
        st.subheader("🎮 Atributos FM26 (todos os 60)")
        cols_atributos = st.columns(2)
        for i, attr in enumerate(ATRIBUTOS_FM26):
            nome_attr = attr.replace('_', ' ').title()
            valor = row.get(attr, np.nan)
            valor_str = f"{float(valor):.1f}" if pd.notna(valor) else "N/I"
            with cols_atributos[i % 2]:
                st.write(f"**{nome_attr}:** {valor_str}")
        st.subheader("🟨 Histórico de Cartões")
        nome_canonico = mapear_nome_para_canonico(row.get('nome_completo', ''))
        if nome_canonico and nome_canonico in cartoes:
            historico = cartoes[nome_canonico].get('historico', [])
            if historico:
                df_hist = pd.DataFrame(historico)
                st.dataframe(df_hist[['data','adversario','cor','terceiro_amarelo','suspenso_causada','suspenso_cumprida']], width='stretch')
            else:
                st.info("Nenhum cartão registrado.")
        else:
            st.info("Nenhum cartão registrado.")

# ======================================================================
# AUTENTICAÇÃO
# ======================================================================
def login():
    with st.form("login"):
        st.subheader("🔐 Acesso ao Sistema")
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Entrar")
        with col2:
            gerenciar = st.form_submit_button("👥 Gerenciar Usuários")
        if submitted:
            if autenticar_usuario(usuario, senha):
                st.session_state.authenticated = True
                st.session_state.usuario = usuario
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos")
        if gerenciar:
            if usuario == "Guibfpinto" and autenticar_usuario(usuario, senha):
                abrir_gerenciador_usuarios()
            else:
                st.error("Apenas o administrador pode gerenciar usuários.")

def abrir_gerenciador_usuarios():
    with st.expander("Gerenciar Usuários", expanded=True):
        st.write("**Usuários cadastrados:**")
        for u in listar_usuarios():
            st.write(f"- {u}")
        st.divider()
        with st.form("novo_usuario"):
            novo_user = st.text_input("Novo usuário")
            nova_senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Adicionar"):
                if adicionar_usuario(novo_user, nova_senha):
                    st.success(f"Usuário {novo_user} adicionado.")
                    st.rerun()
                else:
                    st.error("Usuário já existe.")
        with st.form("remover_usuario"):
            remove_user = st.selectbox("Selecionar usuário para remover", [u for u in listar_usuarios() if u != "Guibfpinto"])
            if st.form_submit_button("Remover"):
                if remover_usuario(remove_user):
                    st.success(f"Usuário {remove_user} removido.")
                    st.rerun()
                else:
                    st.error("Não foi possível remover.")

if not st.session_state.authenticated:
    login()
    st.stop()

st.sidebar.success(f"👤 Logado como: {st.session_state.usuario}")
if st.sidebar.button("Sair"):
    st.session_state.authenticated = False
    st.rerun()

# ======================================================================
# CARREGAMENTO DE DADOS (CACHE) – TODAS AS CATEGORIAS
# ======================================================================
@st.cache_data
def carregar_dfs():
    resultado = {
        "Profissional": None,
        "Sub-15": None,
        "Sub-17": None,
        "Comissão Profissional": None,
        "Comissão Sub-15": None,
        "Comissão Sub-17": None,
        "cartoes_prof": {},
        "cartoes_sub15": {},
        "cartoes_sub17": {},
        "cartoes_com_prof": {},
        "cartoes_com_sub15": {},
        "cartoes_com_sub17": {},
    }
    try:
        # Carrega elencos
        df_prof = carregar_elenco_profissional()
        df_sub15 = carregar_elenco_sub15()
        df_sub17 = carregar_elenco_sub17()

        # Aplica lesões e bioimpedância
        if df_prof is not None and not df_prof.empty:
            df_prof = adicionar_coluna_lesionado(df_prof, 'profissional')
            bio_prof = carregar_dados_bioimpedancia('profissional')
            df_prof = aplicar_dados_bioimpedancia(df_prof, bio_prof)
        if df_sub15 is not None and not df_sub15.empty:
            df_sub15 = adicionar_coluna_lesionado(df_sub15, 'sub15')
            bio_sub15 = carregar_dados_bioimpedancia('sub15')
            df_sub15 = aplicar_dados_bioimpedancia(df_sub15, bio_sub15)
        if df_sub17 is not None and not df_sub17.empty:
            df_sub17 = adicionar_coluna_lesionado(df_sub17, 'sub17')
            bio_sub17 = carregar_dados_bioimpedancia('sub17')
            df_sub17 = aplicar_dados_bioimpedancia(df_sub17, bio_sub17)

        resultado["Profissional"] = df_prof
        resultado["Sub-15"] = df_sub15
        resultado["Sub-17"] = df_sub17

        # Comissão
        resultado["Comissão Profissional"] = carregar_comissao()
        resultado["Comissão Sub-15"] = carregar_comissao_sub15()
        resultado["Comissão Sub-17"] = carregar_comissao_sub17()

        # Estatísticas de partidas (para cada categoria)
        from utils import carregar_estatisticas_partidas
        df_stats_prof = carregar_estatisticas_partidas("Profissional")
        df_stats_sub15 = carregar_estatisticas_partidas("Sub-15")
        df_stats_sub17 = carregar_estatisticas_partidas("Sub-17")

        if not df_stats_prof.empty and df_prof is not None:
            resultado["Profissional"] = precomputar_scores_posicionais(df_prof, df_stats_prof)
        if not df_stats_sub15.empty and df_sub15 is not None:
            resultado["Sub-15"] = precomputar_scores_posicionais(df_sub15, df_stats_sub15)
        if not df_stats_sub17.empty and df_sub17 is not None:
            resultado["Sub-17"] = precomputar_scores_posicionais(df_sub17, df_stats_sub17)

        # Cartões
        for cat, key in [
            ('profissional', 'cartoes_prof'),
            ('sub15', 'cartoes_sub15'),
            ('sub17', 'cartoes_sub17'),
            ('comissao_profissional', 'cartoes_com_prof'),
            ('comissao_sub15', 'cartoes_com_sub15'),
            ('comissao_sub17', 'cartoes_com_sub17')
        ]:
            cart, _ = carregar_cartoes_json(cat)
            resultado[key] = cart
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
    return resultado

dados = carregar_dfs()

def get_df_cartoes(categoria):
    m = {
        "Profissional": ("Profissional", "cartoes_prof"),
        "Sub-15": ("Sub-15", "cartoes_sub15"),
        "Sub-17": ("Sub-17", "cartoes_sub17"),
        "Comissão Profissional": ("Comissão Profissional", "cartoes_com_prof"),
        "Comissão Sub-15": ("Comissão Sub-15", "cartoes_com_sub15"),
        "Comissão Sub-17": ("Comissão Sub-17", "cartoes_com_sub17"),
    }
    df_key, cart_key = m.get(categoria, (None, None))
    return dados.get(df_key), dados.get(cart_key, {})

# ======================================================================
# ABAS PRINCIPAIS
# ======================================================================
tabs = st.tabs([
    "📊 Análise de Elenco",
    "👥 Comissão Técnica",
    "⚽ Monitoramento ao Vivo",
    "🟨 Cartões",
    "📅 Próximo Jogo",
    "📐 Escalação Tática",
    "⚙️ Gestão",
    "📄 Relatórios",
    "📤 Exportar",
    "🎥 Visualização Tática"
])

# ======================================================================
# ABA 1: ANÁLISE DE ELENCO (com seletor de categoria)
# ======================================================================
with tabs[0]:
    st.header("Análise de Jogadores")
    cat_analise = st.selectbox("Categoria", ["Profissional", "Sub-15", "Sub-17"])
    df_analise, cartoes_analise = get_df_cartoes(cat_analise)
    if df_analise is not None and not df_analise.empty:
        st.write("Colunas disponíveis:", df_analise.columns.tolist())
        st.write("Primeiras linhas:", df_analise.head())
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total", len(df_analise))
            if 'Idade' in df_analise.columns:
                st.metric("Idade média", f"{df_analise['Idade'].mean():.1f}")
        with col2:
            if 'Rating_Geral_FM26' in df_analise.columns:
                st.metric("Rating médio", f"{df_analise['Rating_Geral_FM26'].mean():.1f}")
        with col3:
            if 'Estado_Fisico' in df_analise.columns:
                st.metric("Críticos", sum(df_analise['Estado_Fisico'] == 'Crítico'))

        opcao_analise = st.radio("Opções", [
            "Lista resumida",
            "Detalhes do jogador",
            "Relatório completo",
            "Distribuição por posição",
            "Condição física detalhada",
            "Origem (UF/País)",
            "Recomendações",
            "Comparar categorias",
            "Filtrar por posição",
            "Filtrar por idade",
            "Filtrar por rating",
            "Listar lesionados"
        ])

        if opcao_analise == "Lista resumida":
            cols = ['nome_completo','apelido','Posicao_Principal','Idade','Rating_Geral_FM26','Estado_Fisico']
            st.dataframe(df_analise[[c for c in cols if c in df_analise.columns]])

        elif opcao_analise == "Detalhes do jogador":
            # Detecção automática da coluna de nomes
            col_nome = None
            for possivel in ['nome_completo', 'Nome', 'nome', 'jogador', 'Jogador', 'apelido']:
                if possivel in df_analise.columns:
                    col_nome = possivel
                    break
            if col_nome is None:
                st.error("Não foi possível identificar a coluna de nomes no elenco. Colunas disponíveis: " + ", ".join(df_analise.columns))
            else:
                jogador_sel = st.selectbox("Selecione", df_analise[col_nome].tolist())
                row = df_analise[df_analise[col_nome] == jogador_sel].iloc[0]
                exibir_detalhes_jogador(row, cat_analise, cartoes_analise)

        elif opcao_analise == "Relatório completo":
            texto = gerar_relatorio_completo_texto(df_analise, cat_analise)
            st.text_area("Relatório", texto, height=400)

        elif opcao_analise == "Distribuição por posição":
            cont = df_analise['Posicao_Principal'].value_counts()
            st.bar_chart(cont)
            st.dataframe(cont)

        elif opcao_analise == "Condição física detalhada":
            for estado in sorted(df_analise['Estado_Fisico'].unique()):
                grupo = df_analise[df_analise['Estado_Fisico'] == estado]
                st.write(f"**{estado}** ({len(grupo)} jogadores)")
                st.dataframe(grupo[['nome_completo','apelido','IMC','Gordura_Corporal_%']])

        elif opcao_analise == "Origem (UF/País)":
            st.subheader("Distribuição por UF")
            if 'uf_nascimento' in df_analise.columns:
                st.dataframe(df_analise['uf_nascimento'].value_counts())
            st.subheader("Por País")
            if 'pais_nascimento' in df_analise.columns:
                st.dataframe(df_analise['pais_nascimento'].value_counts())

        elif opcao_analise == "Recomendações":
            st.subheader("🔍 Recomendações")
            contagem = df_analise['Posicao_Principal'].value_counts()
            carencias = contagem[contagem < 3]
            if not carencias.empty:
                st.warning("Posições carentes (menos de 3 jogadores):")
                st.write(carencias)
            else:
                st.success("Todas as posições têm pelo menos 3 jogadores.")
            criticos = df_analise[df_analise['Estado_Fisico'] == 'Crítico']
            if not criticos.empty:
                st.error("Jogadores com condição crítica:")
                st.dataframe(criticos[['nome_completo','Estado_Fisico','IMC','Gordura_Corporal_%']])
            jovens = df_analise[(df_analise['Idade'] < 20) & (df_analise['Rating_Geral_FM26'] >= 70)]
            if not jovens.empty:
                st.success("🌟 Jovens promessas:")
                st.dataframe(jovens[['nome_completo','Idade','Rating_Geral_FM26']])

        elif opcao_analise == "Comparar categorias":
            comp_texto = "Comparação entre categorias:\n\n"
            for cat in ["Profissional", "Sub-15", "Sub-17"]:
                df_cat, _ = get_df_cartoes(cat)
                if df_cat is not None and not df_cat.empty:
                    comp_texto += f"**{cat}**: {len(df_cat)} jogadores, "
                    comp_texto += f"idade média {df_cat['Idade'].mean():.1f}, "
                    comp_texto += f"rating médio {df_cat['Rating_Geral_FM26'].mean():.1f}\n"
            st.text(comp_texto)

        elif opcao_analise == "Filtrar por posição":
            pos = st.selectbox("Posição", df_analise['Posicao_Principal'].unique())
            st.dataframe(df_analise[df_analise['Posicao_Principal'] == pos][['nome_completo','apelido','Idade','Rating_Geral_FM26']])

        elif opcao_analise == "Filtrar por idade":
            faixa = st.selectbox("Faixa", ["<20", "21-29", "≥30"])
            if faixa == "<20":
                filtro = df_analise[df_analise['Idade'] < 20]
            elif faixa == "21-29":
                filtro = df_analise[(df_analise['Idade'] >= 21) & (df_analise['Idade'] <= 29)]
            else:
                filtro = df_analise[df_analise['Idade'] >= 30]
            st.dataframe(filtro[['nome_completo','Idade','Posicao_Principal']])

        elif opcao_analise == "Filtrar por rating":
            min_rating = st.slider("Rating mínimo", 0, 100, 70)
            st.dataframe(df_analise[df_analise['Rating_Geral_FM26'] >= min_rating][['nome_completo','Rating_Geral_FM26','Posicao_Principal']])

        elif opcao_analise == "Listar lesionados":
            lesionados = df_analise[df_analise['lesionado'] == True]
            if not lesionados.empty:
                for _, row in lesionados.iterrows():
                    st.write(f"• {row['nome_completo']} ({row['apelido']}) - {obter_lesao_atual(row, cat_analise)}")
            else:
                st.info("Nenhum lesionado.")
    else:
        st.error(f"Dados não disponíveis para {cat_analise}")

# ======================================================================
# ABA 2: COMISSÃO TÉCNICA (com seletor de categoria)
# ======================================================================
with tabs[1]:
    st.header("Comissão Técnica")
    cat_com = st.selectbox("Categoria", ["Comissão Profissional", "Comissão Sub-15", "Comissão Sub-17"])
    df_com, cartoes_com = get_df_cartoes(cat_com)
    
    if df_com is not None and not df_com.empty:
        busca = st.text_input("Buscar membro")
        if busca:
            cols_busca = ['apelido', 'nome', 'nome_completo', 'cargo']
            mask = pd.Series([False]*len(df_com))
            for col in cols_busca:
                if col in df_com.columns:
                    mask |= df_com[col].str.contains(busca, case=False, na=False)
            df_com_filtrado = df_com[mask]
        else:
            df_com_filtrado = df_com
        
        cols_exibicao = [c for c in ['apelido', 'cargo', 'idade', 'cidade_nascimento', 'uf_nascimento', 'pais_nascimento'] if c in df_com_filtrado.columns]
        st.dataframe(df_com_filtrado[cols_exibicao] if cols_exibicao else df_com_filtrado, width='stretch')
        
        if not df_com_filtrado.empty:
            if 'apelido' in df_com_filtrado.columns:
                membro_opcoes = df_com_filtrado['apelido'].dropna().unique().tolist()
            elif 'nome' in df_com_filtrado.columns:
                membro_opcoes = df_com_filtrado['nome'].dropna().unique().tolist()
            else:
                membro_opcoes = df_com_filtrado.index.tolist()
            
            if membro_opcoes:
                membro_selecionado = st.selectbox("Selecione um membro", membro_opcoes)
                if membro_selecionado:
                    if 'apelido' in df_com_filtrado.columns:
                        row = df_com_filtrado[df_com_filtrado['apelido'] == membro_selecionado].iloc[0]
                    elif 'nome' in df_com_filtrado.columns:
                        row = df_com_filtrado[df_com_filtrado['nome'] == membro_selecionado].iloc[0]
                    else:
                        row = df_com_filtrado.iloc[0]
                    
                    exibir_detalhes_comissao(row, cat_com, cartoes_com)
                    
                    if st.button(f"🟨 Registrar cartão para {membro_selecionado}"):
                        with st.expander("Registrar cartão", expanded=True):
                            tipo = st.radio("Tipo", ["Amarelo", "Vermelho"], key="tipo_cartao_com")
                            if st.button("Confirmar cartão", key="conf_cartao_com"):
                                nome_canonico = mapear_nome_para_canonico(membro_selecionado)
                                if nome_canonico not in cartoes_com:
                                    cartoes_com[nome_canonico] = {'amarelos':0, 'vermelho':False, 'suspenso_proxima':False, 'historico':[]}
                                if tipo == "Amarelo":
                                    cartoes_com[nome_canonico]['amarelos'] += 1
                                    if cartoes_com[nome_canonico]['amarelos'] >= 3:
                                        cartoes_com[nome_canonico]['suspenso_proxima'] = True
                                    cartoes_com[nome_canonico]['historico'].append({
                                        'data': datetime.now().strftime("%d/%m/%Y"),
                                        'adversario': "N/I",
                                        'cor': 'amarelo',
                                        'terceiro_amarelo': cartoes_com[nome_canonico]['amarelos']>=3,
                                        'suspenso_causada': cartoes_com[nome_canonico]['amarelos']>=3,
                                        'suspenso_cumprida': False
                                    })
                                else:
                                    cartoes_com[nome_canonico]['vermelho'] = True
                                    cartoes_com[nome_canonico]['suspenso_proxima'] = True
                                    cartoes_com[nome_canonico]['historico'].append({
                                        'data': datetime.now().strftime("%d/%m/%Y"),
                                        'adversario': "N/I",
                                        'cor': 'vermelho',
                                        'terceiro_amarelo': False,
                                        'suspenso_causada': True,
                                        'suspenso_cumprida': False
                                    })
                                salvar_cartoes_json(cartoes_com, cat_com.replace("Comissão ", "").lower())
                                st.success("Cartão registrado!")
                                st.rerun()
    else:
        st.info("Nenhum dado de comissão disponível.")

# ======================================================================
# ABA 3: MONITORAMENTO AO VIVO (com seletor de categoria)
# ======================================================================
with tabs[2]:
    cat_monitor = st.selectbox("Categoria para Monitoramento", ["Profissional", "Sub-15", "Sub-17"], key="monitor_categoria")
    try:
        import pages.monitoramento as monitoramento
        st.session_state.categoria_monitoramento = cat_monitor
        monitoramento.show()
    except ImportError as e:
        st.error(f"Erro ao carregar página de monitoramento: {e}")
    except Exception as e:
        st.error(f"Erro ao executar monitoramento: {e}")

# ======================================================================
# ABA 4: CARTÕES (já adaptado em pages/cartoes.py)
# ======================================================================
with tabs[3]:
    try:
        import pages.cartoes as cartoes
        cartoes.show()
    except ImportError as e:
        st.error(f"Erro ao carregar página de cartões: {e}")

# ======================================================================
# ABA 5: PRÓXIMO JOGO (USANDO A NOVA PÁGINA COM JSON)
# ======================================================================
with tabs[4]:
    try:
        import pages.proximo_jogo as proximo_jogo
        proximo_jogo.show()
    except ImportError as e:
        st.error(f"Erro ao carregar página de próximo jogo: {e}")
    except Exception as e:
        st.error(f"Erro ao executar próximo jogo: {e}")

# ======================================================================
# ABA 6: ESCALAÇÃO TÁTICA (com seletor de categoria)
# ======================================================================
with tabs[5]:
    st.header("📐 Escalação Tática")
    cat_tatica = st.selectbox("Categoria", ["Profissional", "Sub-15", "Sub-17"], key="tatica_categoria")
    
    df_elenco, cartoes_tatica = get_df_cartoes(cat_tatica)
    if df_elenco is None or df_elenco.empty:
        st.warning(f"Elenco não disponível para {cat_tatica}.")
    else:
        try:
            import pages.tatica_page as tatica_page
            st.session_state.categoria_tatica = cat_tatica
            tatica_page.show()
        except ImportError:
            st.info("Página de tática não disponível. Usando versão simplificada.")
            
            formacao = st.text_input("Formação (ex: 4-4-2)", value="4-4-2")
            if st.button("Gerar Escalação"):
                defensores, meias, atacantes, posicoes = interpretar_formacao(formacao)
                if posicoes is None:
                    st.error("Formação inválida.")
                else:
                    titulares = []
                    reservas = []
                    jogadores_usados = []
                    for pos_exibida, pos_tipo in posicoes:
                        candidatos = obter_jogadores_para_posicao(df_elenco, pos_tipo, jogadores_usados, cartoes_tatica)
                        if not candidatos.empty:
                            melhor = candidatos.sort_values('Rating_Geral_FM26', ascending=False).iloc[0]
                            titulares.append({
                                'posicao_exibida': pos_exibida,
                                'posicao_tipo': pos_tipo,
                                'nome': melhor['nome_completo'],
                                'apelido': melhor['apelido'],
                                'row': melhor
                            })
                            jogadores_usados.append(melhor['nome_completo'])
                        else:
                            titulares.append({
                                'posicao_exibida': pos_exibida,
                                'posicao_tipo': pos_tipo,
                                'nome': 'N/D',
                                'apelido': 'N/D',
                                'row': None
                            })
                    reservas_df = df_elenco[~df_elenco['nome_completo'].isin(jogadores_usados)]
                    reservas_df = reservas_df.sort_values('Rating_Geral_FM26', ascending=False)
                    for _, row in reservas_df.head(12).iterrows():
                        reservas.append({
                            'nome': row['nome_completo'],
                            'apelido': row['apelido'],
                            'row': row
                        })
                    
                    st.subheader("Time Titular")
                    for j in titulares:
                        st.write(f"**{j['posicao_exibida']}:** {j['nome']} ({j['apelido']})")
                    st.subheader("Reservas")
                    for j in reservas:
                        st.write(f"• {j['nome']} ({j['apelido']})")

# ======================================================================
# ABA 7: GESTÃO (com seletor de categoria)
# ======================================================================
with tabs[6]:
    st.header("⚙️ Gestão")
    cat_gestao = st.selectbox("Categoria", ["Profissional", "Sub-15", "Sub-17"], key="gestao_categoria")
    try:
        import pages.gestao as gestao
        st.session_state.categoria_gestao = cat_gestao
        gestao.show()
    except ImportError as e:
        st.error(f"Erro ao carregar página de gestão: {e}")
    except Exception as e:
        st.error(f"Erro ao executar gestão: {e}")

# ======================================================================
# ABA 8: RELATÓRIOS (com seletor de categoria)
# ======================================================================
with tabs[7]:
    st.header("📄 Relatórios")
    cat_rel = st.selectbox("Categoria", ["Profissional", "Sub-15", "Sub-17"], key="rel_categoria")
    df_rel, _ = get_df_cartoes(cat_rel)
    if df_rel is not None and not df_rel.empty:
        texto = gerar_relatorio_completo_texto(df_rel, cat_rel)
        st.text_area("Relatório", texto, height=300)
        
        if st.button("Exportar Relatório (TXT)"):
            st.download_button(
                label="Baixar TXT",
                data=texto,
                file_name=f"relatorio_{cat_rel}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
    else:
        st.warning(f"Nenhum dado disponível para {cat_rel}.")

# ======================================================================
# ABA 9: EXPORTAR (já com seletor de categoria)
# ======================================================================
with tabs[8]:
    st.header("📤 Exportar Dados")
    cat_export = st.selectbox(
        "Categoria",
        ["Profissional", "Sub-15", "Sub-17", "Comissão Profissional", "Comissão Sub-15", "Comissão Sub-17"],
        key="export_categoria"
    )
    df_export, _ = get_df_cartoes(cat_export)
    if df_export is not None and not df_export.empty:
        if st.button("📥 Exportar para Excel"):
            caminho = f"export_{cat_export.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            if exportar_para_excel(df_export, cat_export, caminho):
                with open(caminho, "rb") as f:
                    st.download_button("Baixar Excel", data=f, file_name=caminho, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                st.success("Exportado!")
            else:
                st.error("Erro na exportação")
        if st.button("📊 Exportar para Power BI"):
            caminho = f"powerbi_{cat_export.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            if exportar_para_powerbi(df_export, cat_export, "", "", caminho):
                with open(caminho, "rb") as f:
                    st.download_button("Baixar Power BI", data=f, file_name=caminho)
                st.success("Exportado!")
            else:
                st.error("Erro")
    else:
        st.warning("Nenhum dado disponível")

# ======================================================================
# ABA 10: VISUALIZAÇÃO TÁTICA (com seletor de categoria)
# ======================================================================
with tabs[9]:
    st.header("🎥 Visualização Tática")
    cat_viz = st.selectbox("Categoria", ["Profissional", "Sub-15", "Sub-17"], key="viz_categoria")
    df_viz, _ = get_df_cartoes(cat_viz)
    if df_viz is not None and not df_viz.empty:
        try:
            import pages.visualizacao as visualizacao
            st.session_state.categoria_visualizacao = cat_viz
            visualizacao.show()
        except ImportError:
            st.info("Página de visualização não disponível. Usando visualização simples.")
            st.write(f"Visualização tática para {cat_viz} - {len(df_viz)} jogadores")
            st.info("Para visualização avançada, instale mplsoccer e configure a página.")
    else:
        st.warning(f"Nenhum dado disponível para {cat_viz}.")