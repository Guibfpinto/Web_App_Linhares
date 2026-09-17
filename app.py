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
    carregar_elenco_profissional, carregar_elenco_sub15, carregar_elenco_sub17,
    carregar_comissao, carregar_comissao_sub15, carregar_comissao_sub17,
    carregar_diretoria,
    carregar_cartoes_json, salvar_cartoes_json,
    adicionar_coluna_lesionado, carregar_dados_bioimpedancia, aplicar_dados_bioimpedancia,
    carregar_estatisticas_partidas, precomputar_scores_posicionais,
    interpretar_formacao, obter_jogadores_para_posicao, jogador_suspenso,
    mapear_nome_para_canonico, obter_caminho_foto, obter_caminho_foto_arbitro,
    obter_caminho_foto_diretoria,
    obter_historico_clubes, obter_lesao_atual, obter_historico_lesoes_texto,
    autenticar_usuario, listar_usuarios, adicionar_usuario, remover_usuario,
    promover_admin, rebaixar_admin, usuario_eh_admin, carregar_usuarios,
    ADMIN_FIXOS, SENHAS_FIXAS,
    gerar_relatorio_completo_texto,
    exportar_para_excel, exportar_para_powerbi,
    verificar_jogo_ao_vivo, obter_detalhes_jogo, obter_estatisticas_jogo,
    obter_eventos_jogo, obter_lineups_completos, obter_players_stats,
    gerar_relatorio_excel, obter_atributos_chave, inicializar_cartoes_por_csvs,
    ATRIBUTOS_FM26, NOME_TIME, TEMPORADA, DATA_DIR,
    ARQUIVO_CSV_PROFISSIONAL, ARQUIVO_CSV_SUB15, ARQUIVO_CSV_SUB17,
    ARQUIVO_CSV_COMISSAO_PROFISSIONAL, ARQUIVO_CSV_COMISSAO_SUB15, ARQUIVO_CSV_COMISSAO_SUB17,
    ARQUIVO_CSV_DIRETORIA,
    obter_proximo_jogo, exibir_foto, formatar_cartoes,
    inicializar_banco, carregar_cronograma, normalizar_texto, sanitizar_dataframe,
    FIELDS, CLASSIFICADORES,
    classificar_valor, formatar_atributo, encontrar_tipo_atributo,
    rotulo_atributo,
)

# ======================================================================
# IMPORTAÇÕES DAS PÁGINAS
# ======================================================================
import pages.monitoramento as monitoramento
import pages.cartoes as cartoes
import pages.proximo_jogo as proximo_jogo
import pages.tatica_page as tatica_page
import pages.gestao as gestao
import pages.visualizacao as visualizacao
import pages.relatorios as relatorios
import pages.minutagem as minutagem

# ======================================================================
# TRADUÇÃO DE ATRIBUTOS
# ======================================================================
TRADUCAO_ATRIBUTOS = {
    'CA': 'CA (Habilidade Atual)', 'PA': 'PA (Potencial)',
    'ca': 'CA (Habilidade Atual)', 'pa': 'PA (Potencial)',
    'reputacao_mundial': 'Reputação Mundial', 'reputacao_atual': 'Reputação Atual',
    'reputacao_local': 'Reputação Local', 'qualificacoes_treinador': 'Qualificações de Treinador',
    'tipo_documento': 'Tipo de Documento', 'jogos_selecao': 'Jogos pela Seleção',
    'gols_selecao': 'Gols pela Seleção', 'jogos_sub21': 'Jogos Sub-21',
    'gols_sub21': 'Gols Sub-21', 'pais': 'País', 'sigla_pais': 'Sigla País',
    'conhecimento_valor': 'Conhecimento - Valor', 'nome_canonico': 'Nome Canonizado',
    'cidade_uf': 'Cidade/UF', 'nation.id': 'ID País',
    'knowledge_0_nationalteam.id': 'ID Seleção Conhecida',
    'knowledge_0_value': 'Valor Conhecimento', 'id_ogol_comissao': 'ID oGol',
    'chairmanattributes_business': 'Presidente - Negócios',
    'chairmanattributes_interference': 'Presidente - Interferência',
    'chairmanattributes_patience': 'Presidente - Paciência',
    'chairmanattributes_resources': 'Presidente - Recursos',
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
    'nontacticalattributes_buyingplayers': 'Compra de Jogadores',
    'nontacticalattributes_hardnessoftraining': 'Intensidade do Treino',
    'nontacticalattributes_mindgames': 'Jogos Mentais',
    'nontacticalattributes_squadrotation': 'Rotação do Elenco',
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
    'scoutingattributes_judgingplayerdata': 'Avaliação Dados Jogador',
    'scoutingattributes_judgingteamdata': 'Avaliação Dados Time',
    'scoutingattributes_presentingdata': 'Apresentação de Dados',
    'medicalattributes_sportsscience': 'Ciência do Esporte',
    'personalityattributes_adaptability': 'Adaptabilidade (Personalidade)',
    'personalityattributes_ambition': 'Ambição',
    'personalityattributes_loyalty': 'Lealdade',
    'personalityattributes_pressure': 'Pressão (Personalidade)',
    'personalityattributes_professional': 'Profissionalismo',
    'personalityattributes_sportsmanship': 'Espírito Esportivo',
    'personalityattributes_temperament': 'Temperamento',
    'personalityattributes_controversy': 'Controvérsia',
    'jogos_temporada': 'Jogos na temporada',
    'cartoes_amarelos_totais': 'Cartões amarelos (total)',
    'cartoes_vermelhos_totais': 'Cartões vermelhos (total)',
    'media_cartoes_amarelos': 'Média de amarelos',
    'media_cartoes_vermelhos': 'Média de vermelhos',
}

# ======================================================================
# AGRUPAMENTO DOS ATRIBUTOS DA DIRETORIA
# ======================================================================
ATRIBUTOS_DIRETORIA_GRUPOS = {
    "🏆 Reputação": [
        ('reputacao_mundial', 'Reputação Mundial'),
        ('reputacao_atual', 'Reputação Atual'),
        ('reputacao_local', 'Reputação Local'),
        ('dir_rep_mundial', 'Reputação Mundial'),
        ('dir_rep_atual', 'Reputação Atual'),
        ('dir_rep_local', 'Reputação Local'),
    ],
    "🎯 Habilidade (FM26)": [
        ('CA', 'CA (Habilidade Atual)'),
        ('ca', 'CA (Habilidade Atual)'),
        ('PA', 'PA (Potencial)'),
        ('pa', 'PA (Potencial)'),
        ('habilidade_atual', 'Habilidade Atual'),
        ('habilidade_potencial', 'Habilidade Potencial'),
    ],
    "🏛️ Atributos de Presidente": [
        ('chairmanattributes_business', 'Negócios'),
        ('chairmanattributes_interference', 'Interferência'),
        ('chairmanattributes_patience', 'Paciência'),
        ('chairmanattributes_resources', 'Recursos'),
        ('dir_negocios', 'Negócios'),
        ('dir_interferencia', 'Interferência'),
        ('dir_paciencia', 'Paciência'),
        ('dir_recursos', 'Recursos'),
    ],
    "📋 Funções / Cargos": [
        ('rolesattributes_chairman', 'Presidente'),
        ('rolesattributes_directoroffootball', 'Diretor de Futebol'),
        ('rolesattributes_technicaldirector', 'Diretor Técnico'),
        ('rolesattributes_manager', 'Treinador Principal'),
        ('rolesattributes_assistantmanager', 'Auxiliar Técnico'),
        ('rolesattributes_coach', 'Treinador'),
        ('rolesattributes_headofyouthdevelopment', 'Chefe da Base'),
        ('rolesattributes_dataanalyst', 'Analista de Dados'),
        ('rolesattributes_sportsscientist', 'Cientista do Esporte'),
        ('rolesattributes_loanmanager', 'Gerente de Empréstimos'),
        ('rolesattributes_scout', 'Olheiro'),
        ('rolesattributes_setpiececoach', 'Treinador de Bolas Paradas'),
        ('rolesattributes_physio', 'Fisioterapeuta'),
        ('rolesattributes_fitnesscoach', 'Preparador Físico'),
        ('rolesattributes_goalkeepingcoach', 'Preparador de Goleiros'),
    ],
    "🧠 Personalidade": [
        ('personalityattributes_adaptability', 'Adaptabilidade'),
        ('personalityattributes_ambition', 'Ambição'),
        ('personalityattributes_loyalty', 'Lealdade'),
        ('personalityattributes_pressure', 'Pressão'),
        ('personalityattributes_professional', 'Profissionalismo'),
        ('personalityattributes_sportsmanship', 'Espírito Esportivo'),
        ('personalityattributes_temperament', 'Temperamento'),
        ('personalityattributes_controversy', 'Controvérsia'),
        ('per_adaptabilidade', 'Adaptabilidade'),
        ('per_ambicao', 'Ambição'),
        ('per_lealdade', 'Lealdade'),
        ('per_pressao', 'Pressão'),
        ('per_profissionalismo', 'Profissionalismo'),
        ('per_espirito_esportivo', 'Espírito Esportivo'),
        ('per_temperamento', 'Temperamento'),
        ('per_controversia', 'Controvérsia'),
    ],
    "💼 Não-Táticas": [
        ('nontacticalattributes_buyingplayers', 'Compra de Jogadores'),
        ('nontacticalattributes_hardnessoftraining', 'Intensidade do Treino'),
        ('nontacticalattributes_mindgames', 'Jogos Mentais'),
        ('nontacticalattributes_squadrotation', 'Rotação do Elenco'),
        ('nta_compra_jogadores', 'Compra de Jogadores'),
        ('nta_intensidade_treino', 'Intensidade do Treino'),
        ('nta_jogos_mentais', 'Jogos Mentais'),
        ('nta_rotacao_elenco', 'Rotação do Elenco'),
    ],
    "⚽ Táticas": [
        ('tacticalattributes_attacking', 'Ataque'),
        ('tacticalattributes_depth', 'Profundidade'),
        ('tacticalattributes_directness', 'Direção'),
        ('tacticalattributes_flamboyancy', 'Espetacularidade'),
        ('tacticalattributes_flexibility', 'Flexibilidade'),
        ('tacticalattributes_freeroles', 'Funções Livres'),
        ('tacticalattributes_marking', 'Marcação'),
        ('tacticalattributes_offside', 'Impedimento'),
        ('tacticalattributes_pressing', 'Pressão'),
        ('tacticalattributes_sittingback', 'Recuar'),
        ('tacticalattributes_tempo', 'Ritmo'),
        ('tacticalattributes_useofplaymaker', 'Uso do Armador'),
        ('tacticalattributes_useofsubstitutions', 'Uso de Substituições'),
        ('tacticalattributes_width', 'Largura'),
        ('tac_ataque', 'Ataque'),
        ('tac_profundidade', 'Profundidade'),
        ('tac_direcao', 'Direção'),
        ('tac_espetaculo', 'Espetacularidade'),
        ('tac_flexibilidade', 'Flexibilidade'),
        ('tac_funcoes_livres', 'Funções Livres'),
        ('tac_marcacao', 'Marcação'),
        ('tac_impedimento', 'Impedimento'),
        ('tac_pressao', 'Pressão'),
        ('tac_recuar', 'Recuar'),
        ('tac_ritmo', 'Ritmo'),
        ('tac_armador', 'Uso do Armador'),
        ('tac_substituicoes', 'Uso de Substituições'),
        ('tac_largura', 'Largura'),
    ],
    "🔍 Scouting": [
        ('scoutingattributes_judgingplayerdata', 'Avaliação Dados Jogador'),
        ('scoutingattributes_judgingteamdata', 'Avaliação Dados Time'),
        ('scoutingattributes_presentingdata', 'Apresentação de Dados'),
        ('sct_aval_dados_jogador', 'Avaliação Dados Jogador'),
        ('sct_aval_dados_time', 'Avaliação Dados Time'),
        ('sct_apresentacao', 'Apresentação de Dados'),
    ],
    "🩺 Médico / Ciência": [
        ('medicalattributes_sportsscience', 'Ciência do Esporte'),
        ('med_ciencia_esporte', 'Ciência do Esporte'),
    ],
    "🧑‍🏫 Treinamento (Coaching)": [
        ('coachingattributes_attacking', 'Ataque'),
        ('coachingattributes_defending', 'Defesa'),
        ('coachingattributes_fitness', 'Condicionamento'),
        ('coachingattributes_goalkeeping', 'Goleiros'),
        ('coachingattributes_possession', 'Posse'),
        ('coachingattributes_player', 'Jogadores'),
        ('coachingattributes_tactical', 'Tática'),
        ('coachingattributes_technical', 'Técnico'),
        ('coachingattributes_peoplemanagement', 'Gestão de Pessoas'),
        ('coachingattributes_workingwithyoungsters', 'Trabalho com Jovens'),
        ('coachingattributes_dirtinessallowance', 'Tolerância a Rudes'),
        ('coachingattributes_versatility', 'Versatilidade'),
        ('coachingattributes_setpieces', 'Bolas Paradas'),
        ('tre_ataque', 'Ataque'),
        ('tre_defesa', 'Defesa'),
        ('tre_condicionamento', 'Condicionamento'),
        ('tre_goleiros', 'Goleiros'),
        ('tre_posse', 'Posse'),
        ('tre_jogadores', 'Jogadores'),
        ('tre_tatica', 'Tática'),
        ('tre_tecnico', 'Técnico'),
        ('tre_gestao_pessoas', 'Gestão de Pessoas'),
        ('tre_jovens', 'Trabalho com Jovens'),
        ('tre_tolerancia', 'Tolerância a Rudes'),
        ('tre_versatilidade', 'Versatilidade'),
        ('tre_bolas_paradas', 'Bolas Paradas'),
    ],
    "🧠 Mental (Staff)": [
        ('staffmentalattributes_adaptability', 'Adaptabilidade'),
        ('staffmentalattributes_determination', 'Determinação'),
        ('staffmentalattributes_judgingplayerability', 'Avaliação Habilidade Jogador'),
        ('staffmentalattributes_judgingplayerpotential', 'Avaliação Potencial Jogador'),
        ('staffmentalattributes_judgingstaffability', 'Avaliação Habilidade Staff'),
        ('staffmentalattributes_negotiating', 'Negociação'),
        ('staffmentalattributes_authority', 'Autoridade'),
        ('staffmentalattributes_motivating', 'Motivação'),
        ('staffmentalattributes_physiotherapy', 'Fisioterapia'),
        ('staffmentalattributes_tacticalknowledge', 'Conhecimento Tático'),
        ('sta_adaptabilidade', 'Adaptabilidade'),
        ('sta_determinacao', 'Determinação'),
        ('sta_aval_habilidade', 'Avaliação Habilidade Jogador'),
        ('sta_aval_potencial', 'Avaliação Potencial Jogador'),
        ('sta_aval_staff', 'Avaliação Habilidade Staff'),
        ('sta_negociacao', 'Negociação'),
        ('sta_autoridade', 'Autoridade'),
        ('sta_motivacao', 'Motivação'),
        ('sta_fisioterapia', 'Fisioterapia'),
        ('sta_conhecimento_tatico', 'Conhecimento Tático'),
    ],
    "🌎 Dados Gerais / Carreira": [
        ('pais', 'País'),
        ('sigla_pais', 'Sigla País'),
        ('tipo_documento', 'Tipo de Documento'),
        ('qualificacoes_treinador', 'Qualificações de Treinador'),
        ('jogos_selecao', 'Jogos pela Seleção'),
        ('gols_selecao', 'Gols pela Seleção'),
        ('jogos_sub21', 'Jogos Sub-21'),
        ('gols_sub21', 'Gols Sub-21'),
    ],
}

# ======================================================================
# CONFIGURAÇÃO INICIAL
# ======================================================================
st.set_page_config(layout="wide",
                   page_title=f"{NOME_TIME} - Temporada {TEMPORADA}",
                   page_icon="⚽")

# ======================================================================
# CSS COM FUNDO
# ======================================================================
def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

bg_path = "data/background.png"

if os.path.exists(bg_path):
    b64_bg = get_base64_image(bg_path)
    st.markdown(f"""
    <style>
        .stApp {{ position: relative; background-color: #1a1a1a !important; }}
        .stApp::before {{
            content: ""; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background-image: url("data:image/png;base64,{b64_bg}");
            background-size: cover; background-position: center;
            background-repeat: no-repeat; background-attachment: fixed;
            opacity: 0.60; z-index: 0; pointer-events: none;
        }}
        .stApp > * {{ position: relative; z-index: 1; }}
        .main > div {{
            background-color: rgba(0, 0, 0, 0.60) !important;
            padding: 2rem; border-radius: 12px; color: white !important;
        }}
        header, #MainMenu, footer, [data-testid="stSidebar"] {{ display: none !important; }}
        .main .block-container {{ padding-top: 0 !important; padding-bottom: 0 !important; max-width: 100% !important; }}
        .main, .main * {{ color: white !important; }}
        .stButton button {{
            background-color: rgba(255, 255, 255, 0.15) !important;
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
            border-radius: 6px; transition: all 0.2s ease;
        }}
        .stButton button:hover {{
            background-color: rgba(255, 255, 255, 0.25) !important;
            border-color: rgba(255, 255, 255, 0.5) !important;
        }}
        .stTextInput input, .stSelectbox select, .stNumberInput input,
        .stDateInput input, .stTextArea textarea {{
            background-color: rgba(255, 255, 255, 0.12) !important;
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 4px;
        }}
        .stTextInput input::placeholder, .stTextArea textarea::placeholder {{ color: #cccccc !important; }}
        .stTextInput input:focus, .stSelectbox select:focus,
        .stNumberInput input:focus, .stDateInput input:focus,
        .stTextArea textarea:focus {{
            border-color: rgba(255, 255, 255, 0.6) !important;
            background-color: rgba(255, 255, 255, 0.18) !important;
            box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.2) !important;
        }}
        .stSelectbox div[data-baseweb="select"] {{
            background-color: rgba(0, 0, 0, 0.8) !important; color: white !important;
        }}
        .dataframe, .stDataFrame {{
            background-color: rgba(0, 0, 0, 0.5) !important; color: white !important;
        }}
        .dataframe thead th, .stDataFrame thead th {{
            background-color: rgba(255, 255, 255, 0.15) !important;
            color: white !important;
            border-color: rgba(255, 255, 255, 0.2) !important;
        }}
        .dataframe tbody td, .stDataFrame tbody td {{
            color: white !important;
            border-color: rgba(255, 255, 255, 0.1) !important;
        }}
        .stAlert {{
            background-color: rgba(0, 0, 0, 0.65) !important;
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 6px !important;
        }}
        .stAlert .stAlertContent, .stAlert .stAlertIcon {{ color: white !important; }}
        .streamlit-expanderHeader {{
            background-color: rgba(255, 255, 255, 0.08) !important;
            color: white !important;
            border-radius: 6px !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
        }}
        .streamlit-expanderHeader:hover {{ background-color: rgba(255, 255, 255, 0.15) !important; }}
        .streamlit-expanderContent {{
            background-color: rgba(0, 0, 0, 0.85) !important;
            color: white !important;
            border-radius: 0 0 6px 6px !important;
            border-left: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
            padding: 1rem !important;
        }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
        .stTabs [data-baseweb="tab"] {{
            background-color: rgba(255, 255, 255, 0.05) !important;
            color: white !important;
            border-radius: 4px 4px 0 0 !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-bottom: none !important;
            padding: 8px 16px !important;
        }}
        .stTabs [data-baseweb="tab"][aria-selected="true"] {{
            background-color: rgba(255, 255, 255, 0.15) !important;
            border-color: rgba(255, 255, 255, 0.3) !important;
        }}
        .stTabs [data-baseweb="tab-panel"] {{
            background-color: rgba(0, 0, 0, 0.5) !important;
            color: white !important;
            padding: 16px !important;
            border-radius: 0 0 6px 6px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-top: none !important;
        }}
        ::-webkit-scrollbar {{ width: 8px; }}
        ::-webkit-scrollbar-track {{ background: rgba(0, 0, 0, 0.3); border-radius: 4px; }}
        ::-webkit-scrollbar-thumb {{ background: rgba(255, 255, 255, 0.2); border-radius: 4px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: rgba(255, 255, 255, 0.3); }}
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background-color: #1a1a1a; }
        .main > div { background-color: rgba(0,0,0,0.8); padding: 2rem; border-radius: 12px; color: white; }
        header, #MainMenu, footer, [data-testid="stSidebar"] { display: none !important; }
        .main .block-container { padding-top: 0; padding-bottom: 0; max-width: 100%; }
        .main, .main * { color: white !important; }
        .streamlit-expanderContent { background-color: rgba(0,0,0,0.85) !important; }
    </style>
    """, unsafe_allow_html=True)

# ======================================================================
# FUNÇÕES AUXILIARES
# ======================================================================
def buscar_foto_unificada(row, categoria=None, tipo='jogador'):
    if tipo == 'jogador':
        return obter_caminho_foto(row, categoria)
    if tipo == 'diretoria':
        return obter_caminho_foto_diretoria(row)
    foto = row.get('foto', '')
    if not foto:
        nome_base = row.get('apelido') or row.get('nome')
        if not nome_base:
            return None
    else:
        nome_base = os.path.basename(foto)
    if not nome_base:
        return None
    base, _ = os.path.splitext(nome_base)
    nome_clean = normalizar_texto(base).replace(' ', '_')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = script_dir
    pastas_raiz = [
        "assets/fotos_comissao", "assets/fotos_tecnicos", "fotos",
        "assets/fotos_jogadores", "Fotos_Tecnicos", "fotos_comissao",
        "fotos_sistema_Analise_Elenco/Comissao_Tecnica/Profissional",
        "fotos_sistema_Analise_Elenco/Comissao_Tecnica/Sub15",
        "fotos_sistema_Analise_Elenco/Comissao_Tecnica/Sub17",
    ]
    pastas = [os.path.join(parent_dir, p) for p in pastas_raiz]
    extensoes = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
    for pasta in pastas:
        if not os.path.isdir(pasta):
            continue
        for ext in extensoes:
            caminho = os.path.join(pasta, f"{base}{ext}")
            if os.path.exists(caminho):
                return os.path.abspath(caminho)
            caminho = os.path.join(pasta, f"{nome_clean}{ext}")
            if os.path.exists(caminho):
                return os.path.abspath(caminho)
        import glob
        matches = glob.glob(os.path.join(pasta, f"{base}.*"))
        if matches:
            return os.path.abspath(matches[0])
        matches = glob.glob(os.path.join(pasta, f"{nome_clean}.*"))
        if matches:
            return os.path.abspath(matches[0])
    return None


def exibir_atributo_com_label(coluna, valor, label_override=None):
    """Mostra APENAS o rótulo da classificação (2ª Divisão Capixaba)."""
    tipo = encontrar_tipo_atributo(coluna)
    valor_fmt = rotulo_atributo(valor, tipo) if tipo else (
        str(valor) if not pd.isna(valor) else "N/I"
    )
    nome_attr = label_override or TRADUCAO_ATRIBUTOS.get(
        coluna, coluna.replace('_', ' ').title()
    )
    st.write(f"• **{nome_attr}:** {valor_fmt}")


def exibir_legenda_classificacoes():
    """Exibe a legenda das classificações adaptadas à 2ª Divisão Capixaba."""
    with st.expander("ℹ️ Legenda das classificações (2ª Divisão Capixaba)"):
        st.markdown("""
        **CA / PA (escala 1-200):**
        - `0–20` → Muito Baixo (Amador)
        - `21–40` → Baixo (Semi-amador)
        - `41–65` → Médio (Regional)
        - `66–90` → Alto (Destaque Estadual)
        - `91+`  → Muito Alto (Fora do Padrão)

        **Atributos FM26 (escala 1-20):**
        - `1–5`   → Muito Ruim
        - `6–8`   → Ruim
        - `9–12`  → Médio
        - `13–15` → Bom
        - `16–20` → Muito Bom

        **Perna (escala 1-20):**
        - `1–4`   → Muito Fraco
        - `5–9`   → Fraco
        - `10–13` → Razoável
        - `14–17` → Forte
        - `18–20` → Muito Forte
        """)


def limpar_cache():
    st.cache_data.clear()
    st.cache_resource.clear()
    st.success("✅ Cache limpo com sucesso!")
    st.rerun()


def campo_senha_com_visibilidade(label, key, placeholder=""):
    visivel_key = f"{key}_visivel"
    if visivel_key not in st.session_state:
        st.session_state[visivel_key] = False
    mostrar = st.checkbox("Mostrar senha", key=f"{key}_mostrar", value=st.session_state[visivel_key])
    if mostrar != st.session_state[visivel_key]:
        st.session_state[visivel_key] = mostrar
        st.rerun()
    if st.session_state[visivel_key]:
        return st.text_input(label, type="default", key=key, placeholder=placeholder)
    return st.text_input(label, type="password", key=key, placeholder=placeholder)


# ======================================================================
# INICIALIZAÇÃO DE ESTADO
# ======================================================================
for k, v in {
    "authenticated": False, "usuario": "", "is_admin": False,
    "gerenciar_usuarios": False, "carregando": False,
    "titulares": [], "reservas": [], "substituicoes": [], "gols": [],
    "total_substituicoes": 0, "data_jogo": "", "adversario": "",
    "vila_e_casa": True, "fixture_id": None, "monitorando": False,
    "time_base": None, "escalacoes_geradas": {}, "instrucoes_coletivas": {}
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ======================================================================
# FUNÇÕES AUXILIARES DE DADOS
# ======================================================================
def get_elenco(categoria):
    if categoria == "Profissional":
        return carregar_elenco_profissional()
    if categoria == "Sub-15":
        return carregar_elenco_sub15()
    if categoria == "Sub-17":
        return carregar_elenco_sub17()
    return None


def get_comissao(categoria):
    if categoria == "Comissão Profissional":
        return carregar_comissao()
    if categoria == "Comissão Sub-15":
        return carregar_comissao_sub15()
    if categoria == "Comissão Sub-17":
        return carregar_comissao_sub17()
    return None


def get_cartoes(categoria):
    mapeamento = {
        "Profissional": "profissional", "Sub-15": "sub15", "Sub-17": "sub17",
        "Comissão Profissional": "comissao_profissional",
        "Comissão Sub-15": "comissao_sub15",
        "Comissão Sub-17": "comissao_sub17",
    }
    chave = mapeamento.get(categoria)
    if chave:
        cart, _ = carregar_cartoes_json(chave)
        return cart
    return {}


# ======================================================================
# DETALHES COMISSÃO
# ======================================================================
def exibir_detalhes_comissao(row, categoria, cartoes):
    with st.expander(f"📋 DETALHES - {row.get('nome', row.get('apelido', 'Membro'))}", expanded=True):
        col1, col2 = st.columns([1, 2])
        with col1:
            caminho_foto = buscar_foto_unificada(row, categoria, tipo='comissao')
            if caminho_foto and os.path.exists(caminho_foto):
                try:
                    st.image(caminho_foto, width=150)
                except:
                    st.write("📷 Sem foto")
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
                df_hist = sanitizar_dataframe(pd.DataFrame(historico))
                cols = [c for c in ['data', 'adversario', 'cor',
                                    'terceiro_amarelo', 'suspenso_causada',
                                    'suspenso_cumprida'] if c in df_hist.columns]
                st.dataframe(df_hist[cols], width='stretch')
            else:
                st.info("Nenhum cartão registrado.")
        else:
            st.info("Nenhum cartão registrado.")
        st.divider()

        colunas_estatisticas = ['jogos_temporada', 'cartoes_amarelos_totais',
                                'cartoes_vermelhos_totais',
                                'media_cartoes_amarelos', 'media_cartoes_vermelhos']
        tem_estatistica = any(col in row.index and pd.notna(row[col]) for col in colunas_estatisticas)
        if tem_estatistica:
            st.subheader("📊 Estatísticas da Temporada")
            for col in colunas_estatisticas:
                if col in row.index and pd.notna(row[col]):
                    nome_attr = TRADUCAO_ATRIBUTOS.get(col, col)
                    st.write(f"• **{nome_attr}:** {row[col]}")
            st.divider()

        st.subheader("📊 Atributos Detalhados")
        st.caption("Rótulos adaptados à realidade da 2ª Divisão Capixaba")
        colunas_excluir = [
            'nome', 'nome_completo', 'apelido', 'cargo', 'data_nascimento',
            'cidade_nascimento', 'uf_nascimento', 'pais_nascimento', 'pais',
            'idade', 'historico_jogador', 'historico_comissao',
            'id_ogol_comissao', 'data_nascimento.1', 'apelido_norm',
        ] + colunas_estatisticas
        colunas_atributos = [c for c in row.index
                             if c not in colunas_excluir and not pd.isna(row[c])]
        if colunas_atributos:
            col1, col2 = st.columns(2)
            for i, attr in enumerate(colunas_atributos):
                with col1 if i % 2 == 0 else col2:
                    exibir_atributo_com_label(attr, row[attr])
        else:
            st.info("Nenhum atributo detalhado disponível para este membro.")
        exibir_legenda_classificacoes()


# ======================================================================
# DETALHES JOGADOR
# ======================================================================
def exibir_detalhes_jogador(row, categoria, cartoes):
    nome_exibicao = row.get('nome_completo') or row.get('apelido') or 'Jogador'
    with st.expander(f"📋 DETALHES COMPLETOS - {nome_exibicao}", expanded=True):
        col1, col2 = st.columns([1, 2])
        with col1:
            caminho_foto = buscar_foto_unificada(row, categoria, tipo='jogador')
            if caminho_foto and os.path.exists(caminho_foto):
                try:
                    st.image(caminho_foto, width=150)
                except:
                    st.write("📷 Sem foto")
            else:
                st.write("📷 Sem foto")
        with col2:
            st.write(f"**Nome:** {row.get('nome_completo', row.get('apelido', 'N/I'))}")
            st.write(f"**Apelido:** {row.get('apelido', 'N/I')}")
            st.write(f"**Data Nasc.:** {row.get('data_nascimento', '')}  **Idade:** {row.get('Idade', 'N/I')}")
            cidade = row.get('cidade_nascimento', '')
            uf = row.get('uf_nascimento', '')
            pais = row.get('pais_nascimento', '')
            st.write(f"**Cidade/UF:** {cidade if pd.notna(cidade) else 'N/I'} / {uf if pd.notna(uf) else 'N/I'}")
            st.write(f"**País:** {pais if pd.notna(pais) else 'N/I'}")

            altura = row.get('altura_cm')
            st.write(f"**Altura:** {altura:.1f} cm" if pd.notna(altura) else "**Altura:** N/I")
            peso = row.get('peso_kg')
            st.write(f"**Peso:** {peso:.1f} kg" if pd.notna(peso) else "**Peso:** N/I")

            st.write(f"**Pos. Principal:** {row.get('Posicao_Principal', 'N/I')}")
            pos_sec = row.get('Posicoes_Secundarias', [])
            pos_sec_str = ", ".join(pos_sec) if isinstance(pos_sec, list) and pos_sec else (
                str(pos_sec) if pd.notna(pos_sec) else "Nenhuma")
            st.write(f"**Pos. Secundárias:** {pos_sec_str}")
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

        st.divider()
        st.subheader("📜 Histórico de Clubes")
        st.text(obter_historico_clubes(row))
        st.subheader("🩺 Histórico de Lesões")
        st.text(obter_historico_lesoes_texto(row, categoria))

        st.subheader("📊 Estatísticas da Temporada (oGol)")
        for col, label in {
            'jogos_temporada': 'Jogos na temporada',
            'minutos_totais': 'Minutos totais',
            'media_minutos_por_jogo': 'Média minutos/jogo',
            'gols_totais': 'Gols', 'assistencias_totais': 'Assistências',
            'cartoes_amarelos_totais': 'Cartões amarelos',
            'cartoes_vermelhos_totais': 'Cartões vermelhos'
        }.items():
            valor = row.get(col, '0')
            valor_str = '0' if pd.isna(valor) or str(valor).strip() == '' else str(valor).strip()
            if valor_str.endswith('.0'):
                valor_str = valor_str[:-2]
            st.write(f"**{label}:** {valor_str}")

        st.subheader("🎮 Atributos FM26")
        st.caption("Rótulos adaptados à realidade da 2ª Divisão Capixaba")
        cols_atributos = st.columns(2)
        for i, attr in enumerate(ATRIBUTOS_FM26):
            valor = row.get(attr, np.nan)
            with cols_atributos[i % 2]:
                nome_attr = attr.replace('_', ' ').title()
                tipo = encontrar_tipo_atributo(attr) or "habilidade"
                rotulo = rotulo_atributo(valor, tipo)
                st.write(f"**{nome_attr}:** {rotulo}")
        exibir_legenda_classificacoes()

        st.subheader("🟨 Histórico de Cartões")
        nome_canonico = mapear_nome_para_canonico(row.get('nome_completo', ''))
        if nome_canonico and nome_canonico in cartoes:
            historico = cartoes[nome_canonico].get('historico', [])
            if historico:
                df_hist = sanitizar_dataframe(pd.DataFrame(historico))
                cols = [c for c in ['data', 'adversario', 'cor',
                                    'terceiro_amarelo', 'suspenso_causada',
                                    'suspenso_cumprida'] if c in df_hist.columns]
                st.dataframe(df_hist[cols], width='stretch')
            else:
                st.info("Nenhum cartão registrado.")
        else:
            st.info("Nenhum cartão registrado.")


# ======================================================================
# EXIBIR ATRIBUTOS DA DIRETORIA (agrupados)
# ======================================================================
def exibir_atributos_diretoria(row):
    """Exibe os atributos da diretoria agrupados por categoria,
    mostrando APENAS o rótulo adaptado à 2ª Divisão Capixaba."""
    st.subheader("📊 Atributos da Diretoria")
    st.caption("Rótulos adaptados à realidade da 2ª Divisão Capixaba")

    colunas_usadas = set()
    grupos_mostrados = 0

    for titulo_grupo, atributos in ATRIBUTOS_DIRETORIA_GRUPOS.items():
        encontrados = []
        for key, label in atributos:
            if key in row.index and pd.notna(row[key]) and str(row[key]).strip() != '':
                if key in colunas_usadas:
                    continue
                encontrados.append((key, label, row[key]))
                colunas_usadas.add(key)

        if encontrados:
            grupos_mostrados += 1
            with st.expander(f"{titulo_grupo} ({len(encontrados)})", expanded=True):
                col_a, col_b = st.columns(2)
                for i, (key, label, valor) in enumerate(encontrados):
                    with col_a if i % 2 == 0 else col_b:
                        tipo = encontrar_tipo_atributo(key) or "habilidade"
                        st.write(f"• **{label}:** {rotulo_atributo(valor, tipo)}")

    # ----- Atributos não catalogados (fallback) -----
    colunas_excluir = {
        'nome', 'nome_completo', 'apelido', 'cargo', 'data_nascimento',
        'cidade_nascimento', 'uf_nascimento', 'pais_nascimento', 'pais',
        'idade', 'cidade', 'uf', 'cidade_uf',
        'historico', 'historico_profissional', 'historico_diretoria',
        'historico_jogador', 'nome_canonico', 'foto',
    }
    restantes = [
        c for c in row.index
        if c not in colunas_excluir
        and c not in colunas_usadas
        and not pd.isna(row[c])
        and str(row[c]).strip() != ''
    ]

    if restantes:
        with st.expander(f"📌 Outros Atributos ({len(restantes)})", expanded=False):
            col_a, col_b = st.columns(2)
            for i, attr in enumerate(restantes):
                with col_a if i % 2 == 0 else col_b:
                    exibir_atributo_com_label(attr, row[attr])

    if grupos_mostrados == 0 and not restantes:
        st.info("Nenhum atributo disponível para este membro da diretoria.")
    else:
        exibir_legenda_classificacoes()


# ======================================================================
# DETALHES DIRETORIA
# ======================================================================
def exibir_detalhes_diretoria(row):
    nome_exibicao = (
        row.get('nome_completo')
        or row.get('nome')
        or row.get('apelido')
        or 'Membro da Diretoria'
    )
    with st.expander(f"📋 DETALHES - {nome_exibicao}", expanded=True):
        col1, col2 = st.columns([1, 2])
        with col1:
            caminho_foto = buscar_foto_unificada(row, "Diretoria", tipo='diretoria')
            if caminho_foto and (str(caminho_foto).startswith('http') or os.path.exists(caminho_foto)):
                try:
                    st.image(caminho_foto, width=150)
                except Exception:
                    st.write("📷 Sem foto")
            else:
                st.write("📷 Sem foto")

        with col2:
            st.write(f"**Nome:** {row.get('nome_completo', row.get('nome', 'N/I'))}")
            st.write(f"**Apelido:** {row.get('apelido', 'N/I')}")
            st.write(f"**Cargo:** {row.get('cargo', 'N/I')}")
            st.write(f"**Data Nasc.:** {row.get('data_nascimento', 'N/I')}")
            st.write(f"**Idade:** {row.get('idade', 'N/I')}")
            st.write(
                f"**Cidade/UF:** {row.get('cidade_nascimento', 'N/I')} / "
                f"{row.get('uf_nascimento', 'N/I')}"
            )
            st.write(f"**País:** {row.get('pais_nascimento', row.get('pais', 'N/I'))}")

        st.divider()

        st.subheader("📜 Histórico Profissional")
        st.write(row.get('historico_profissional',
                         row.get('historico_diretoria',
                                 row.get('historico', 'Não informado'))))

        st.subheader("⚽ Histórico como Jogador")
        hist_jog = row.get('historico_jogador', 'Não informado')
        if pd.isna(hist_jog) or str(hist_jog).strip() == '':
            hist_jog = 'Não informado'
        st.write(hist_jog)

        st.divider()

        exibir_atributos_diretoria(row)


# ======================================================================
# AUTENTICAÇÃO E GERENCIAMENTO DE USUÁRIOS
# ======================================================================
def login():
    if st.session_state.get("gerenciar_usuarios", False):
        abrir_gerenciador_usuarios()
        if st.button("🔙 Voltar ao Login"):
            st.session_state.gerenciar_usuarios = False
            st.rerun()
        return

    with st.form("login_form"):
        st.subheader("🔐 Acesso ao Sistema")
        usuario = st.text_input("Usuário")
        senha = campo_senha_com_visibilidade("Senha", "login_senha")
        submitted = st.form_submit_button("Entrar")
        if submitted:
            autenticado, is_admin = autenticar_usuario(usuario, senha)
            if autenticado:
                st.session_state.authenticated = True
                st.session_state.usuario = usuario
                st.session_state.is_admin = is_admin
                st.session_state.carregando = True
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos")

    if st.button("👥 Gerenciar Usuários"):
        st.session_state.gerenciar_usuarios = True
        st.rerun()


def abrir_gerenciador_usuarios():
    st.subheader("👥 Gerenciamento de Usuários")
    usuarios = carregar_usuarios()
    st.write("**Usuários cadastrados:**")
    for u, dados in usuarios.items():
        is_admin = dados.get("is_admin", False) or (u in ADMIN_FIXOS)
        st.write(f"- {u} {'⭐ Admin' if is_admin else ''}")
    st.divider()

    with st.form("novo_usuario"):
        st.write("**Adicionar novo usuário**")
        novo_user = st.text_input("Novo usuário")
        nova_senha = campo_senha_com_visibilidade("Senha", "novo_senha")
        tornar_admin = st.checkbox("Tornar administrador")
        if st.form_submit_button("Adicionar"):
            if adicionar_usuario(novo_user, nova_senha, is_admin=tornar_admin):
                st.success(f"Usuário {novo_user} adicionado.")
                st.rerun()
            else:
                st.error("Usuário já existe.")

    with st.form("remover_usuario"):
        st.write("**Remover usuário**")
        usuarios_para_remover = [u for u in listar_usuarios() if u not in ADMIN_FIXOS]
        if usuarios_para_remover:
            remove_user = st.selectbox("Selecionar usuário para remover", usuarios_para_remover)
            if st.form_submit_button("Remover"):
                if remover_usuario(remove_user):
                    st.success(f"Usuário {remove_user} removido.")
                    st.rerun()
                else:
                    st.error("Não foi possível remover.")
        else:
            st.info("Nenhum outro usuário para remover.")


# ======================================================================
# TELA DE LOADING (SPINNER AZUL)
# ======================================================================
if st.session_state.get("carregando", False):
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("""
        <style>
            .loading-container {
                display: flex; flex-direction: column; align-items: center;
                justify-content: center; height: 80vh; gap: 20px;
            }
            .spinner {
                width: 80px; height: 80px;
                border: 6px solid rgba(30, 144, 255, 0.2);
                border-top: 6px solid #1E90FF;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                box-shadow: 0 0 20px rgba(30, 144, 255, 0.5);
            }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            .loading-text {
                color: #1E90FF; font-size: 22px; font-weight: bold;
                animation: pulse 1.5s ease-in-out infinite;
            }
            @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
            .loading-sub { color: #cccccc; font-size: 14px; font-style: italic; }
        </style>
        <div class="loading-container">
            <div class="spinner"></div>
            <div class="loading-text">⚽ Carregando dados...</div>
            <div class="loading-sub">Preparando o sistema, aguarde um instante</div>
        </div>
        """, unsafe_allow_html=True)
    time.sleep(1.5)
    st.session_state.carregando = False
    placeholder.empty()
    st.rerun()

# ======================================================================
# VERIFICAÇÃO DE AUTENTICAÇÃO
# ======================================================================
if not st.session_state.authenticated:
    login()
    st.stop()

# ======================================================================
# CARREGAMENTO DE DADOS (CACHE)
# ======================================================================
@st.cache_data
def carregar_dfs():
    resultado = {
        "Profissional": None, "Sub-15": None, "Sub-17": None,
        "Comissão Profissional": None, "Comissão Sub-15": None, "Comissão Sub-17": None,
        "Diretoria": None,
        "cartoes_prof": {}, "cartoes_sub15": {}, "cartoes_sub17": {},
        "cartoes_com_prof": {}, "cartoes_com_sub15": {}, "cartoes_com_sub17": {},
    }
    try:
        df_prof = carregar_elenco_profissional()
        df_sub15 = carregar_elenco_sub15()
        df_sub17 = carregar_elenco_sub17()

        if df_prof is not None and not df_prof.empty:
            df_prof = adicionar_coluna_lesionado(df_prof, 'profissional')
            df_prof = aplicar_dados_bioimpedancia(df_prof, carregar_dados_bioimpedancia('profissional'))
        if df_sub15 is not None and not df_sub15.empty:
            df_sub15 = adicionar_coluna_lesionado(df_sub15, 'sub15')
            df_sub15 = aplicar_dados_bioimpedancia(df_sub15, carregar_dados_bioimpedancia('sub15'))
        if df_sub17 is not None and not df_sub17.empty:
            df_sub17 = adicionar_coluna_lesionado(df_sub17, 'sub17')
            df_sub17 = aplicar_dados_bioimpedancia(df_sub17, carregar_dados_bioimpedancia('sub17'))

        resultado["Profissional"] = df_prof
        resultado["Sub-15"] = df_sub15
        resultado["Sub-17"] = df_sub17
        resultado["Comissão Profissional"] = carregar_comissao()
        resultado["Comissão Sub-15"] = carregar_comissao_sub15()
        resultado["Comissão Sub-17"] = carregar_comissao_sub17()
        resultado["Diretoria"] = carregar_diretoria()

        stats_prof = carregar_estatisticas_partidas("Profissional")
        stats_sub15 = carregar_estatisticas_partidas("Sub-15")
        stats_sub17 = carregar_estatisticas_partidas("Sub-17")
        if not stats_prof.empty and df_prof is not None:
            resultado["Profissional"] = precomputar_scores_posicionais(df_prof, stats_prof)
        if not stats_sub15.empty and df_sub15 is not None:
            resultado["Sub-15"] = precomputar_scores_posicionais(df_sub15, stats_sub15)
        if not stats_sub17.empty and df_sub17 is not None:
            resultado["Sub-17"] = precomputar_scores_posicionais(df_sub17, stats_sub17)

        for cat, key in [('profissional', 'cartoes_prof'), ('sub15', 'cartoes_sub15'),
                         ('sub17', 'cartoes_sub17'),
                         ('comissao_profissional', 'cartoes_com_prof'),
                         ('comissao_sub15', 'cartoes_com_sub15'),
                         ('comissao_sub17', 'cartoes_com_sub17')]:
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
        "Diretoria": ("Diretoria", None),
    }
    df_key, cart_key = m.get(categoria, (None, None))
    df = dados.get(df_key) if df_key else None
    cart = dados.get(cart_key, {}) if cart_key else {}
    return df, cart

# ======================================================================
# MENU SUPERIOR
# ======================================================================
st.title(f"⚽ {NOME_TIME} - Temporada {TEMPORADA}")
st.caption(f"👤 Logado como: {st.session_state.usuario}")

col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    if st.button("Sair"):
        st.session_state.authenticated = False
        st.rerun()
with col2:
    if st.button("🧹 Limpar Cache"):
        limpar_cache()
if st.session_state.get("is_admin", False):
    with col3:
        if st.button("👥 Gerenciar Usuários (Admin)"):
            st.session_state.gerenciar_usuarios = True
            st.rerun()

# ======================================================================
# ABAS PRINCIPAIS
# ======================================================================
tabs = st.tabs([
    "📊 Análise de Elenco", "👥 Comissão Técnica", "🏛️ Diretoria",
    "⚽ Monitoramento ao Vivo", "🟨 Cartões", "📅 Próximo Jogo",
    "📐 Escalação Tática", "⚙️ Gestão", "📄 Relatórios",
    "📊 Minutagem", "📤 Exportar", "🎥 Visualização Tática"
])

# ======================================================================
# ABA 0: ANÁLISE DE ELENCO
# ======================================================================
with tabs[0]:
    st.header("Análise de Jogadores")
    cat_analise = st.selectbox("Categoria", ["Profissional", "Sub-15", "Sub-17"])
    df_analise, cartoes_analise = get_df_cartoes(cat_analise)
    if df_analise is not None and not df_analise.empty:
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
            "Lista resumida", "Detalhes do jogador", "Relatório completo",
            "Distribuição por posição", "Condição física detalhada",
            "Origem (UF/País)", "Recomendações", "Comparar categorias",
            "Filtrar por posição", "Filtrar por idade", "Filtrar por rating",
            "Listar lesionados"
        ])

        if opcao_analise == "Lista resumida":
            cols = ['nome_completo', 'apelido', 'Posicao_Principal', 'Idade',
                    'Rating_Geral_FM26', 'Estado_Fisico', 'altura_cm', 'peso_kg']
            df_exib = sanitizar_dataframe(df_analise[[c for c in cols if c in df_analise.columns]])
            st.dataframe(df_exib, width='stretch')

        elif opcao_analise == "Detalhes do jogador":
            col_nome = next((c for c in ['nome_completo', 'Nome', 'nome', 'jogador', 'Jogador', 'apelido']
                             if c in df_analise.columns), None)
            if col_nome is None:
                st.error("Não foi possível identificar a coluna de nomes.")
            else:
                jogador_sel = st.selectbox("Selecione", df_analise[col_nome].tolist())
                row = df_analise[df_analise[col_nome] == jogador_sel].iloc[0]
                exibir_detalhes_jogador(row, cat_analise, cartoes_analise)

        elif opcao_analise == "Relatório completo":
            st.subheader(f"📋 Relatório Completo - {cat_analise}")
            total = len(df_analise)
            idade_media = df_analise['Idade'].mean() if 'Idade' in df_analise.columns else 0
            altura_media = df_analise['altura_cm'].mean() if 'altura_cm' in df_analise.columns else 0
            peso_media = df_analise['peso_kg'].mean() if 'peso_kg' in df_analise.columns else 0
            imc_media = df_analise['IMC'].mean() if 'IMC' in df_analise.columns else 0

            st.markdown("### 📊 Estatísticas Gerais")
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                st.metric("👥 Total", total)
            with c2:
                st.metric("🎂 Idade Média", f"{idade_media:.1f} anos")
            with c3:
                st.metric("📏 Altura Média", f"{altura_media:.1f} cm")
            with c4:
                st.metric("⚖️ Peso Médio", f"{peso_media:.1f} kg")
            with c5:
                st.metric("📐 IMC Médio", f"{imc_media:.1f}")

            st.divider()
            st.markdown("### 💧 Percentuais de Gordura")
            gordura_media = df_analise['Gordura_Corporal_%'].mean() if 'Gordura_Corporal_%' in df_analise.columns else 0
            massa_magra_media = df_analise['Massa_Magra_kg'].mean() if 'Massa_Magra_kg' in df_analise.columns else 0
            massa_gorda_media = peso_media - massa_magra_media if peso_media and massa_magra_media else 0
            massa_muscular_media = df_analise['Massa_Muscular_Estimada_kg'].mean() if 'Massa_Muscular_Estimada_kg' in df_analise.columns else 0
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("📘 Média Geral", f"{gordura_media:.1f}%")
            with c2:
                st.metric("💪 Massa Magra", f"{massa_magra_media:.1f} kg")
            with c3:
                st.metric("🔥 Massa Gorda", f"{massa_gorda_media:.1f} kg")
            with c4:
                st.metric("🏋️ Massa Muscular", f"{massa_muscular_media:.1f} kg")

            st.divider()
            st.markdown("### 🎮 Dados FM26")
            ca_media = df_analise['habilidade_atual'].mean() if 'habilidade_atual' in df_analise.columns else 0
            pa_media = df_analise['habilidade_potencial'].mean() if 'habilidade_potencial' in df_analise.columns else 0
            rating_medio = df_analise['Rating_Geral_FM26'].mean() if 'Rating_Geral_FM26' in df_analise.columns else 0
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("🎯 CA Médio", f"{ca_media:.1f} ({classificar_valor('ca_pa', ca_media) or 'N/A'})")
            with c2:
                st.metric("🚀 PA Médio", f"{pa_media:.1f} ({classificar_valor('ca_pa', pa_media) or 'N/A'})")
            with c3:
                st.metric("⭐ Rating Médio", f"{rating_medio:.1f}")

            st.divider()
            st.markdown("### ⚽ Distribuição por Posição Principal")
            if 'Posicao_Principal' in df_analise.columns:
                dist = df_analise['Posicao_Principal'].value_counts().reset_index()
                dist.columns = ['Posição', 'Quantidade']
                dist['Percentual'] = (dist['Quantidade'] / total * 100).round(1)
                col_tab, col_graf = st.columns([1, 1])
                with col_tab:
                    st.dataframe(dist, use_container_width=True, hide_index=True)
                with col_graf:
                    st.bar_chart(dist.set_index('Posição')['Quantidade'])

            st.divider()
            if 'Estado_Fisico' in df_analise.columns:
                st.markdown("### 🏃 Distribuição por Estado Físico")
                estado_dist = df_analise['Estado_Fisico'].value_counts().reset_index()
                estado_dist.columns = ['Estado', 'Quantidade']
                st.bar_chart(estado_dist.set_index('Estado')['Quantidade'])
                st.divider()

            exibir_legenda_classificacoes()

            with st.expander("📄 Ver relatório em texto (igual ao desktop)", expanded=False):
                texto = gerar_relatorio_completo_texto(df_analise, cat_analise)
                st.text_area("Relatório", texto, height=400, key="rel_completo_texto")
                st.download_button(
                    label="📥 Baixar relatório (TXT)",
                    data=texto,
                    file_name=f"relatorio_completo_{cat_analise.lower()}.txt",
                    mime="text/plain"
                )

        elif opcao_analise == "Distribuição por posição":
            cont = df_analise['Posicao_Principal'].value_counts()
            st.bar_chart(cont)
            st.dataframe(cont)

        elif opcao_analise == "Condição física detalhada":
            for estado in sorted(df_analise['Estado_Fisico'].unique()):
                grupo = df_analise[df_analise['Estado_Fisico'] == estado]
                st.write(f"**{estado}** ({len(grupo)} jogadores)")
                df_g = sanitizar_dataframe(grupo[['nome_completo', 'apelido', 'IMC', 'Gordura_Corporal_%']])
                st.dataframe(df_g, width='stretch')

        elif opcao_analise == "Origem (UF/País)":
            st.subheader("Distribuição por UF")
            if 'uf_nascimento' in df_analise.columns:
                st.dataframe(sanitizar_dataframe(df_analise['uf_nascimento'].value_counts().reset_index()), width='stretch')
            st.subheader("Por País")
            if 'pais_nascimento' in df_analise.columns:
                st.dataframe(sanitizar_dataframe(df_analise['pais_nascimento'].value_counts().reset_index()), width='stretch')

        elif opcao_analise == "Recomendações":
            st.subheader("🔍 Recomendações")
            contagem = df_analise['Posicao_Principal'].value_counts()
            carencias = contagem[contagem < 3]
            if not carencias.empty:
                st.warning("Posições carentes:")
                st.write(carencias)
            else:
                st.success("Todas as posições têm pelo menos 3 jogadores.")
            criticos = df_analise[df_analise['Estado_Fisico'] == 'Crítico']
            if not criticos.empty:
                st.error("Jogadores com condição crítica:")
                st.dataframe(sanitizar_dataframe(criticos[['nome_completo', 'Estado_Fisico', 'IMC', 'Gordura_Corporal_%']]), width='stretch')
            jovens = df_analise[(df_analise['Idade'] < 20) & (df_analise['Rating_Geral_FM26'] >= 70)]
            if not jovens.empty:
                st.success("🌟 Jovens promessas:")
                st.dataframe(sanitizar_dataframe(jovens[['nome_completo', 'Idade', 'Rating_Geral_FM26']]), width='stretch')

        elif opcao_analise == "Comparar categorias":
            comp = "Comparação entre categorias:\n\n"
            for cat in ["Profissional", "Sub-15", "Sub-17"]:
                df_cat, _ = get_df_cartoes(cat)
                if df_cat is not None and not df_cat.empty:
                    comp += f"**{cat}**: {len(df_cat)} jogadores, idade média {df_cat['Idade'].mean():.1f}, rating médio {df_cat['Rating_Geral_FM26'].mean():.1f}\n"
            st.text(comp)

        elif opcao_analise == "Filtrar por posição":
            pos = st.selectbox("Posição", df_analise['Posicao_Principal'].unique())
            st.dataframe(sanitizar_dataframe(df_analise[df_analise['Posicao_Principal'] == pos][
                ['nome_completo', 'apelido', 'Idade', 'Rating_Geral_FM26']]), width='stretch')

        elif opcao_analise == "Filtrar por idade":
            faixa = st.selectbox("Faixa", ["<20", "21-29", "≥30"])
            if faixa == "<20":
                filtro = df_analise[df_analise['Idade'] < 20]
            elif faixa == "21-29":
                filtro = df_analise[(df_analise['Idade'] >= 21) & (df_analise['Idade'] <= 29)]
            else:
                filtro = df_analise[df_analise['Idade'] >= 30]
            st.dataframe(sanitizar_dataframe(filtro[['nome_completo', 'Idade', 'Posicao_Principal']]), width='stretch')

        elif opcao_analise == "Filtrar por rating":
            min_rating = st.slider("Rating mínimo", 0, 100, 70)
            st.dataframe(sanitizar_dataframe(df_analise[df_analise['Rating_Geral_FM26'] >= min_rating][
                ['nome_completo', 'Rating_Geral_FM26', 'Posicao_Principal']]), width='stretch')

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
# ABA 1: COMISSÃO TÉCNICA
# ======================================================================
with tabs[1]:
    st.header("Comissão Técnica")
    cat_com = st.selectbox("Categoria", ["Comissão Profissional", "Comissão Sub-15", "Comissão Sub-17"])
    df_com, cartoes_com = get_df_cartoes(cat_com)
    if df_com is not None and not df_com.empty:
        busca = st.text_input("Buscar membro")
        if busca:
            cols_busca = ['apelido', 'nome', 'nome_completo', 'cargo']
            mask = pd.Series([False] * len(df_com))
            for col in cols_busca:
                if col in df_com.columns:
                    mask |= df_com[col].astype(str).str.contains(busca, case=False, na=False)
            df_com_filtrado = df_com[mask]
        else:
            df_com_filtrado = df_com

        cols_exibicao = [c for c in ['apelido', 'cargo', 'idade', 'cidade_nascimento', 'uf_nascimento', 'pais_nascimento']
                         if c in df_com_filtrado.columns]
        df_exib = sanitizar_dataframe(df_com_filtrado[cols_exibicao]) if cols_exibicao else df_com_filtrado
        st.dataframe(df_exib, width='stretch')

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
                                    cartoes_com[nome_canonico] = {'amarelos': 0, 'vermelho': False,
                                                                   'suspenso_proxima': False, 'historico': []}
                                if tipo == "Amarelo":
                                    cartoes_com[nome_canonico]['amarelos'] += 1
                                    if cartoes_com[nome_canonico]['amarelos'] >= 3:
                                        cartoes_com[nome_canonico]['suspenso_proxima'] = True
                                    cartoes_com[nome_canonico]['historico'].append({
                                        'data': datetime.now().strftime("%d/%m/%Y"),
                                        'adversario': "N/I", 'cor': 'amarelo',
                                        'terceiro_amarelo': cartoes_com[nome_canonico]['amarelos'] >= 3,
                                        'suspenso_causada': cartoes_com[nome_canonico]['amarelos'] >= 3,
                                        'suspenso_cumprida': False
                                    })
                                else:
                                    cartoes_com[nome_canonico]['vermelho'] = True
                                    cartoes_com[nome_canonico]['suspenso_proxima'] = True
                                    cartoes_com[nome_canonico]['historico'].append({
                                        'data': datetime.now().strftime("%d/%m/%Y"),
                                        'adversario': "N/I", 'cor': 'vermelho',
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
# ABA 2: DIRETORIA
# ======================================================================
with tabs[2]:
    st.header("🏛️ Diretoria")
    df_dir = dados.get("Diretoria")

    if df_dir is None or df_dir.empty:
        st.warning("Nenhum dado de diretoria disponível. "
                   "Verifique se o arquivo `perfil_completo_diretoria_2026.csv` está na pasta `data/`.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Membros", len(df_dir))
        with col2:
            if 'idade' in df_dir.columns:
                try:
                    st.metric("Idade Média", f"{df_dir['idade'].astype(float).mean():.1f}")
                except Exception:
                    st.metric("Idade Média", "N/I")
        with col3:
            if 'cargo' in df_dir.columns:
                st.metric("Cargos Distintos", df_dir['cargo'].nunique())

        busca_dir = st.text_input("🔍 Buscar membro da diretoria", key="busca_diretoria")
        if busca_dir:
            cols_busca = ['nome_completo', 'nome', 'apelido', 'cargo']
            mask = pd.Series([False] * len(df_dir))
            for col in cols_busca:
                if col in df_dir.columns:
                    mask |= df_dir[col].astype(str).str.contains(
                        busca_dir, case=False, na=False)
            df_dir_filtrado = df_dir[mask]
        else:
            df_dir_filtrado = df_dir

        cols_exib = [c for c in ['nome_completo', 'apelido', 'cargo', 'idade',
                                 'cidade_nascimento', 'uf_nascimento', 'pais_nascimento']
                     if c in df_dir_filtrado.columns]
        if cols_exib:
            st.dataframe(sanitizar_dataframe(df_dir_filtrado[cols_exib]),
                         width='stretch')
        else:
            st.dataframe(sanitizar_dataframe(df_dir_filtrado), width='stretch')

        st.divider()

        if not df_dir_filtrado.empty:
            if 'apelido' in df_dir_filtrado.columns:
                opcoes = df_dir_filtrado['apelido'].dropna().unique().tolist()
            elif 'nome' in df_dir_filtrado.columns:
                opcoes = df_dir_filtrado['nome'].dropna().unique().tolist()
            else:
                opcoes = df_dir_filtrado.index.tolist()

            if opcoes:
                selecionado = st.selectbox("Selecione um membro da diretoria",
                                            opcoes, key="sel_diretoria")
                if selecionado:
                    if 'apelido' in df_dir_filtrado.columns:
                        row = df_dir_filtrado[df_dir_filtrado['apelido'] == selecionado].iloc[0]
                    elif 'nome' in df_dir_filtrado.columns:
                        row = df_dir_filtrado[df_dir_filtrado['nome'] == selecionado].iloc[0]
                    else:
                        row = df_dir_filtrado.iloc[0]
                    exibir_detalhes_diretoria(row)

        st.divider()

        if 'cargo' in df_dir.columns:
            st.subheader("📊 Distribuição por Cargo")
            dist = df_dir['cargo'].value_counts().reset_index()
            dist.columns = ['Cargo', 'Quantidade']
            c1, c2 = st.columns([1, 1])
            with c1:
                st.dataframe(dist, use_container_width=True, hide_index=True)
            with c2:
                st.bar_chart(dist.set_index('Cargo')['Quantidade'])

# ======================================================================
# ABA 3: MONITORAMENTO
# ======================================================================
with tabs[3]:
    cat_monitor = st.selectbox("Categoria para Monitoramento", ["Profissional", "Sub-15", "Sub-17"], key="monitor_categoria")
    try:
        st.session_state.categoria_monitoramento = cat_monitor
        monitoramento.show()
    except Exception as e:
        st.error(f"Erro ao executar monitoramento: {e}")

# ======================================================================
# ABA 4: CARTÕES
# ======================================================================
with tabs[4]:
    try:
        cartoes.show()
    except Exception as e:
        st.error(f"Erro ao carregar página de cartões: {e}")

# ======================================================================
# ABA 5: PRÓXIMO JOGO
# ======================================================================
with tabs[5]:
    try:
        proximo_jogo.show()
    except Exception as e:
        st.error(f"Erro ao executar próximo jogo: {e}")

# ======================================================================
# ABA 6: ESCALAÇÃO TÁTICA
# ======================================================================
with tabs[6]:
    st.header("📐 Escalação Tática")
    cat_tatica = st.selectbox("Categoria", ["Profissional", "Sub-15", "Sub-17"], key="tatica_categoria")
    df_elenco, cartoes_tatica = get_df_cartoes(cat_tatica)
    if df_elenco is None or df_elenco.empty:
        st.warning(f"Elenco não disponível para {cat_tatica}.")
    else:
        try:
            st.session_state.categoria_tatica = cat_tatica
            tatica_page.show()
        except Exception as e:
            st.error(f"Erro ao carregar tática: {e}")

# ======================================================================
# ABA 7: GESTÃO
# ======================================================================
with tabs[7]:
    cat_gestao = st.selectbox("Categoria", ["Profissional", "Sub-15", "Sub-17"], key="gestao_categoria")
    try:
        st.session_state.categoria_gestao = cat_gestao
        gestao.show()
    except Exception as e:
        st.error(f"Erro ao executar gestão: {e}")

# ======================================================================
# ABA 8: RELATÓRIOS
# ======================================================================
with tabs[8]:
    try:
        relatorios.show()
    except Exception as e:
        st.error(f"Erro ao executar relatórios: {e}")

# ======================================================================
# ABA 9: MINUTAGEM
# ======================================================================
with tabs[9]:
    minutagem.show()

# ======================================================================
# ABA 10: EXPORTAR
# ======================================================================
with tabs[10]:
    st.header("📤 Exportar Dados")
    cat_export = st.selectbox(
        "Categoria",
        ["Profissional", "Sub-15", "Sub-17",
         "Comissão Profissional", "Comissão Sub-15", "Comissão Sub-17",
         "Diretoria"],
        key="export_categoria"
    )
    df_export, _ = get_df_cartoes(cat_export)
    if df_export is not None and not df_export.empty:
        if st.button("📥 Exportar para Excel"):
            caminho = f"export_{cat_export.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            if exportar_para_excel(df_export, cat_export, caminho):
                with open(caminho, "rb") as f:
                    st.download_button("Baixar Excel", data=f, file_name=caminho,
                                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                st.success("Exportado!")
            else:
                st.error("Erro na exportação")
    else:
        st.warning("Nenhum dado disponível")

# ======================================================================
# ABA 11: VISUALIZAÇÃO TÁTICA
# ======================================================================
with tabs[11]:
    st.header("🎥 Visualização Tática")
    cat_viz = st.selectbox("Categoria", ["Profissional", "Sub-15", "Sub-17"], key="viz_categoria")
    df_viz, _ = get_df_cartoes(cat_viz)
    if df_viz is not None and not df_viz.empty:
        try:
            st.session_state.categoria_visualizacao = cat_viz
            visualizacao.show()
        except Exception as e:
            st.error(f"Erro ao carregar visualização: {e}")
    else:
        st.warning(f"Nenhum dado disponível para {cat_viz}.")