# utils.py
import streamlit as st
import pandas as pd
import numpy as np
import os
import re
import unicodedata
import json
import sqlite3
import bcrypt
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, Optional, List, Tuple
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from io import BytesIO
import requests
import time
from pathlib import Path

# =============================================
# CONSTANTES DE CAMINHOS (CSVs)
# =============================================
DATA_DIR = "data"
RELATORIOS_DIR = "relatorios"
NOME_TIME = "Linhares FC"
TEMPORADA = str(datetime.now().year)

ARQUIVO_CSV_PROFISSIONAL = "perfil_completo_jogadores_profissional_2026.csv"
ARQUIVO_CSV_SUB15 = "perfil_completo_jogadores_Sub15_2026.csv"
ARQUIVO_CSV_SUB17 = "perfil_completo_jogadores_Sub17_2026.csv"
ARQUIVO_CSV_COMISSAO_PROFISSIONAL = "perfil_completo_comissao_2026.csv"
ARQUIVO_CSV_COMISSAO_SUB15 = "perfil_completo_comissao_Sub15_2026.csv"
ARQUIVO_CSV_COMISSAO_SUB17 = "perfil_completo_comissao_Sub17_2026.csv"
ARQUIVO_CSV_DIRETORIA = "perfil_completo_diretoria_2026.csv"
ARQUIVO_LESOES_PROFISSIONAL = "jogadores_linhares_profissional_lesoes.csv"
ARQUIVO_LESOES_SUB15 = "jogadores_linhares_Sub15_lesoes.csv"
ARQUIVO_LESOES_SUB17 = "jogadores_linhares_Sub17_lesoes.csv"
ARQUIVO_BIO_PROFISSIONAL = "jogadores_linhares_profissional_Bioimpedancia.csv"
ARQUIVO_BIO_SUB15 = "jogadores_linhares_Sub15_Bioimpedancia.csv"
ARQUIVO_BIO_SUB17 = "jogadores_linhares_Sub17_Bioimpedancia.csv"
ARQUIVO_CRONO_PROF = "cronograma_profissional_2026.csv"
ARQUIVO_CRONO_SUB15 = "cronograma_sub15_2026.csv"
ARQUIVO_CRONO_SUB17 = "cronograma_sub17_2026.csv"

# =============================================
# CONSTANTES DE PASTAS DE ESTATÍSTICAS
# =============================================
PASTA_ESTATISTICAS_PROFISSIONAL = "data/estatisticas_jogadores/"
PASTA_ESTATISTICAS_SUB15 = "data/estatisticas_sub15/"
PASTA_ESTATISTICAS_SUB17 = "data/estatisticas_sub17/"
PASTA_ESTATISTICAS_COMISSAO_PROFISSIONAL = "data/estatisticas_comissao_tecnica_profissional/"
PASTA_ESTATISTICAS_COMISSAO_SUB15 = "data/estatisticas_comissao_tecnica_sub15/"
PASTA_ESTATISTICAS_COMISSAO_SUB17 = "data/estatisticas_comissao_tecnica_sub17/"

# =============================================
# CONSTANTES DOS ARQUIVOS DE CARTÕES (JSON)
# =============================================
CAMINHO_CARTOES_PROFISSIONAL = "cartoes_acumulados_profissional.json"
CAMINHO_CARTOES_SUB15 = "cartoes_acumulados_sub15.json"
CAMINHO_CARTOES_SUB17 = "cartoes_acumulados_sub17.json"
CAMINHO_CARTOES_COMISSAO_PROFISSIONAL = "cartoes_acumulados_comissao_profissional.json"
CAMINHO_CARTOES_COMISSAO_SUB15 = "cartoes_acumulados_comissao_sub15.json"
CAMINHO_CARTOES_COMISSAO_SUB17 = "cartoes_acumulados_comissao_sub17.json"

# =============================================
# CONFIGURAÇÕES POR CATEGORIA
# =============================================
CATEGORIA_CONFIG = {
    "Profissional": {"team_id": 12928, "competicao_id": 2,
                     "elenco_func": "carregar_elenco_profissional", "cartoes_key": "profissional"},
    "Sub-15": {"team_id": 27831, "competicao_id": 11,
               "elenco_func": "carregar_elenco_sub15", "cartoes_key": "sub15"},
    "Sub-17": {"team_id": 27832, "competicao_id": 10,
               "elenco_func": "carregar_elenco_sub17", "cartoes_key": "sub17"}
}

# =============================================
# MAPEAMENTO DE NOMES (JOGADORES E COMISSÃO)
# =============================================
MAPEAMENTO_NOMES_PROFISSIONAL = {
    'Wenderson Silva Neves': 'Wendy', 'Wendy': 'Wendy',
    'Marcus Paulo Sousa Oliveira': 'Marcus Paulo', 'Marcus Paulo': 'Marcus Paulo',
    'Francisco Wesley da Silva Sousa': 'Wesley', 'Wesley': 'Wesley',
    'Francisco de Assis Rapozo Neto': 'Francisco Neto', 'Francisco Neto': 'Francisco Neto',
    'Stuart Asafe Ferreira Alves': 'Stuart', 'Stuart': 'Stuart',
    'Yuri Ribeiro Giovanelli': 'Yuri Ribeiro', 'Yuri Ribeiro': 'Yuri Ribeiro',
    'João Pedro Firmino Oliveira': 'João Firmino', 'João Firmino': 'João Firmino',
    'Joao Firmino': 'João Firmino',
    'Lucas Titol Lopes': 'Lucas Titol', 'Lucas Titol': 'Lucas Titol',
    'Rayner Silva Gomes': 'Rayner', 'Rayner': 'Rayner',
    'Kayque Santos da Cunha': 'Kayque Santos', 'Kayque Santos': 'Kayque Santos',
    'Cayque': 'Kayque Santos',
    'Ruan Amaral Rios': 'Ruan Rios', 'Ruan Rios': 'Ruan Rios',
    'Genilson dos Santos Júnior': 'Júnior Espeto', 'Júnior Espeto': 'Junior Espeto',
    'Clavis Severo Leão': 'Clavis Neto', 'Clavis Neto': 'Clavis Neto',
    'Jeferson David Palacios Cantillo': 'Jeferson Palacios', 'Jeferson Palacios': 'Jeferson Palacios',
    'J. D. Palacios Cantillo': 'Jeferson Palacios',
    'Gabriel Amorim de Aguiar': 'Gabriel Amorim', 'Gabriel Amorim': 'Gabriel Amorim',
    'Virgílio Santos Borges': 'Borjão', 'Borjão': 'Borjão', 'Borjao': 'Borjão',
    'Matheus Toribes Ferreira Souza': 'Matheus Toribes', 'Matheus Toribes': 'Matheus Toribes',
    'João Marcos Santos Ferraz Luz': 'João Marcos', 'João Marcos': 'João Marcos',
    'Davi Fornaciari Lima': 'Davi Fornaciari', 'Davi Fornaciari': 'Davi Fornaciari',
    'Karlos Henrique dos Reis Calavort': 'Kaká', 'Kaká': 'Kaká', 'Kaka': 'Kaká',
    'Daniel Olmo Morais Gonçalves': 'Daniel Olmo', 'Daniel Olmo': 'Daniel Olmo',
    'Arthur Luiz Darros': 'Arthur Darros', 'Arthur Darros': 'Arthur Darros',
    'Júlio César Fontana Leite': 'Julio César', 'Julio César': 'Julio César',
    'Matheus Sarmento Mesquita': 'Matheus Nossa', 'Matheus Nossa': 'Matheus Nossa',
    'Gabriel de Jesus Rodrigues': 'Gabriel Jesus', 'Gabriel Jesus': 'Gabriel Jesus',
    'Luander da Silva Denerval': 'Luander',
    'Thayson Lourenço dos Santos': 'Thayson',
}
MAPEAMENTO_NOMES_SUB15 = {}
MAPEAMENTO_NOMES_SUB17 = {}
MAPEAMENTO_NOMES_COMISSAO_PROFISSIONAL = {
    'Jonair da Silva Ferreira': 'Yupi Silva', 'Yupi Silva': 'Yupi Silva',
    'Ricardo da Silva Santos': 'Ricardo', 'Ricardo': 'Ricardo',
    'Karen da Silva Loureiro': 'Karen', 'Karen': 'Karen',
    'Marcos Vinicius Vieira Lima Furguilin': 'Asamoah', 'Asamoah': 'Asamoah',
    'Marya Eduarda Cabral de Carvalho Mello': 'Marya Eduarda', 'Marya Eduarda': 'Marya Eduarda',
    'Guilherme Battistella Frigini Pinto': 'Guilherme Pinto', 'Guilherme Pinto': 'Gui Pinto'
}
MAPEAMENTO_NOMES_COMISSAO_SUB15 = {}
MAPEAMENTO_NOMES_COMISSAO_SUB17 = {}

# =============================================
# ATRIBUTOS FM26 (GLOBAL)
# =============================================
ATRIBUTOS_FM26 = [
    'escanteios', 'cruzamentos', 'drible', 'finalizacao', 'primeiro_controle',
    'cobranca_faltas', 'cabecada', 'chutes_longe', 'arremessos_laterais',
    'marcacao', 'passe', 'cobranca_penaltis', 'desarme', 'tecnica',
    'agressividade', 'antecipacao', 'coragem', 'composicao', 'concentracao',
    'decisao', 'determinacao', 'criatividade', 'lideranca', 'movimentacao_sem_bola',
    'posicionamento', 'trabalho_equipe', 'visao_jogo', 'intensidade_trabalho',
    'aceleracao', 'agilidade', 'equilibrio', 'altura_salto', 'condicao_fisica_natural',
    'velocidade_maxima', 'resistencia', 'forca_fisica', 'reflexos', 'jogo_aereo_goleiro',
    'defesas_goleiro', 'comando_area', 'comunicacao_goleiro', 'chutes_goleiro',
    'um_contra_um_goleiro', 'saida_gol', 'tendencia_socar', 'arremessos_goleiro',
    'excentricidade', 'consistencia', 'jogo_sujo', 'jogos_importantes',
    'propensao_lesao', 'versatilidade', 'adaptabilidade', 'ambicao', 'lealdade',
    'pressao', 'profissionalismo', 'esportividade', 'temperamento', 'controversia'
]

# =============================================
# MAPEAMENTO JSON → PT-BR + CLASSIFICADORES
# Adaptado para a SEGUNDA DIVISÃO DO CAPIXABA
# =============================================
FIELDS = {
    ("CA",): ("habilidade_atual",     "ca_pa"),
    ("PA",): ("habilidade_potencial", "ca_pa"),

    ("GoalKeeperAttributes", "AerialAbility"):   ("gol_jogo_aereo",     "habilidade"),
    ("GoalKeeperAttributes", "CommandOfArea"):   ("gol_comando_area",   "habilidade"),
    ("GoalKeeperAttributes", "Communication"):   ("gol_comunicacao",    "habilidade"),
    ("GoalKeeperAttributes", "Eccentricity"):    ("gol_excentricidade", "habilidade"),
    ("GoalKeeperAttributes", "Handling"):        ("gol_encaixe",        "habilidade"),
    ("GoalKeeperAttributes", "Kicking"):         ("gol_chute",          "habilidade"),
    ("GoalKeeperAttributes", "OneOnOnes"):       ("gol_um_a_um",        "habilidade"),
    ("GoalKeeperAttributes", "Reflexes"):        ("gol_reflexos",       "habilidade"),
    ("GoalKeeperAttributes", "RushingOut"):      ("gol_saida",          "habilidade"),
    ("GoalKeeperAttributes", "TendencyToPunch"): ("gol_socar",          "habilidade"),
    ("GoalKeeperAttributes", "Throwing"):        ("gol_arremesso",      "habilidade"),

    ("MentalAttributes", "Aggression"):    ("men_agressividade",   "habilidade"),
    ("MentalAttributes", "Anticipation"):  ("men_antecipacao",     "habilidade"),
    ("MentalAttributes", "Bravery"):       ("men_coragem",         "habilidade"),
    ("MentalAttributes", "Composure"):     ("men_sangue_frio",     "habilidade"),
    ("MentalAttributes", "Concentration"): ("men_concentracao",    "habilidade"),
    ("MentalAttributes", "Vision"):        ("men_visao",           "habilidade"),
    ("MentalAttributes", "Decisions"):     ("men_decisoes",        "habilidade"),
    ("MentalAttributes", "Determination"): ("men_determinacao",    "habilidade"),
    ("MentalAttributes", "Flair"):         ("men_criatividade",    "habilidade"),
    ("MentalAttributes", "Leadership"):    ("men_lideranca",       "habilidade"),
    ("MentalAttributes", "OffTheBall"):    ("men_sem_bola",        "habilidade"),
    ("MentalAttributes", "Positioning"):   ("men_posicionamento",  "habilidade"),
    ("MentalAttributes", "Teamwork"):      ("men_trabalho_equipe", "habilidade"),
    ("MentalAttributes", "Workrate"):      ("men_entrega",         "habilidade"),

    ("PhysicalAttributes", "Acceleration"):   ("fis_aceleracao",       "habilidade"),
    ("PhysicalAttributes", "Agility"):        ("fis_agilidade",        "habilidade"),
    ("PhysicalAttributes", "Balance"):        ("fis_equilibrio",       "habilidade"),
    ("PhysicalAttributes", "Jumping"):        ("fis_impulsao",         "habilidade"),
    ("PhysicalAttributes", "LeftFoot"):       ("fis_pe_esquerdo",      "perna"),
    ("PhysicalAttributes", "NaturalFitness"): ("fis_condicao_natural", "habilidade"),
    ("PhysicalAttributes", "Pace"):           ("fis_velocidade",       "habilidade"),
    ("PhysicalAttributes", "RightFoot"):      ("fis_pe_direito",       "perna"),
    ("PhysicalAttributes", "Stamina"):        ("fis_resistencia",      "habilidade"),
    ("PhysicalAttributes", "Strength"):       ("fis_forca",            "habilidade"),

    ("HiddenAttributes", "Consistency"):      ("ocu_regularidade",    "habilidade"),
    ("HiddenAttributes", "Dirtiness"):        ("ocu_sujeira",         "habilidade"),
    ("HiddenAttributes", "ImportantMatches"): ("ocu_grandes_jogos",   "habilidade"),
    ("HiddenAttributes", "InjuryProness"):    ("ocu_propensao_lesao", "habilidade"),
    ("HiddenAttributes", "Versatility"):      ("ocu_versatilidade",   "habilidade"),

    ("TechnicalAttributes", "Corners"):       ("tec_cantos",          "habilidade"),
    ("TechnicalAttributes", "Crossing"):      ("tec_cruzamento",      "habilidade"),
    ("TechnicalAttributes", "Dribbling"):     ("tec_drible",          "habilidade"),
    ("TechnicalAttributes", "Finishing"):     ("tec_finalizacao",     "habilidade"),
    ("TechnicalAttributes", "FirstTouch"):    ("tec_dominio",         "habilidade"),
    ("TechnicalAttributes", "Freekicks"):     ("tec_faltas",          "habilidade"),
    ("TechnicalAttributes", "Heading"):       ("tec_cabecada",        "habilidade"),
    ("TechnicalAttributes", "LongShots"):     ("tec_chutes_longe",    "habilidade"),
    ("TechnicalAttributes", "Longthrows"):    ("tec_laterais_longos", "habilidade"),
    ("TechnicalAttributes", "Marking"):       ("tec_marcacao",        "habilidade"),
    ("TechnicalAttributes", "Passing"):       ("tec_passe",           "habilidade"),
    ("TechnicalAttributes", "PenaltyTaking"): ("tec_penalties",       "habilidade"),
    ("TechnicalAttributes", "Tackling"):      ("tec_desarme",         "habilidade"),
    ("TechnicalAttributes", "Technique"):     ("tec_tecnica",         "habilidade"),

    ("PersonalityAttributes", "Adaptability"):  ("per_adaptabilidade",     "habilidade"),
    ("PersonalityAttributes", "Ambition"):      ("per_ambicao",            "habilidade"),
    ("PersonalityAttributes", "Loyalty"):       ("per_lealdade",           "habilidade"),
    ("PersonalityAttributes", "Pressure"):      ("per_pressao",            "habilidade"),
    ("PersonalityAttributes", "Professional"):  ("per_profissionalismo",   "habilidade"),
    ("PersonalityAttributes", "Sportsmanship"): ("per_espirito_esportivo", "habilidade"),
    ("PersonalityAttributes", "Temperament"):   ("per_temperamento",       "habilidade"),
    ("PersonalityAttributes", "Controversy"):   ("per_controversia",       "habilidade"),

    ("CoachingAttributes", "Attacking"):              ("tre_ataque",         "habilidade"),
    ("CoachingAttributes", "Defending"):              ("tre_defesa",         "habilidade"),
    ("CoachingAttributes", "Fitness"):                ("tre_condicionamento", "habilidade"),
    ("CoachingAttributes", "Goalkeeping"):            ("tre_goleiros",       "habilidade"),
    ("CoachingAttributes", "Possession"):             ("tre_posse",          "habilidade"),
    ("CoachingAttributes", "Player"):                 ("tre_jogadores",      "habilidade"),
    ("CoachingAttributes", "Tactical"):               ("tre_tatica",         "habilidade"),
    ("CoachingAttributes", "Technical"):              ("tre_tecnico",        "habilidade"),
    ("CoachingAttributes", "PeopleManagement"):       ("tre_gestao_pessoas", "habilidade"),
    ("CoachingAttributes", "WorkingWithYoungsters"):  ("tre_jovens",         "habilidade"),
    ("CoachingAttributes", "DirtinessAllowance"):     ("tre_tolerancia",     "habilidade"),
    ("CoachingAttributes", "Versatility"):            ("tre_versatilidade",  "habilidade"),
    ("CoachingAttributes", "SetPieces"):              ("tre_bolas_paradas",  "habilidade"),

    ("StaffMentalAttributes", "Adaptability"):           ("sta_adaptabilidade",     "habilidade"),
    ("StaffMentalAttributes", "Determination"):          ("sta_determinacao",       "habilidade"),
    ("StaffMentalAttributes", "JudgingPlayerAbility"):   ("sta_aval_habilidade",    "habilidade"),
    ("StaffMentalAttributes", "JudgingPlayerPotential"): ("sta_aval_potencial",     "habilidade"),
    ("StaffMentalAttributes", "JudgingStaffAbility"):    ("sta_aval_staff",         "habilidade"),
    ("StaffMentalAttributes", "Negotiating"):            ("sta_negociacao",         "habilidade"),
    ("StaffMentalAttributes", "Authority"):              ("sta_autoridade",         "habilidade"),
    ("StaffMentalAttributes", "Motivating"):             ("sta_motivacao",          "habilidade"),
    ("StaffMentalAttributes", "Physiotherapy"):          ("sta_fisioterapia",       "habilidade"),
    ("StaffMentalAttributes", "TacticalKnowledge"):      ("sta_conhecimento_tatico","habilidade"),

    ("NonTacticalAttributes", "BuyingPlayers"):       ("nta_compra_jogadores", "habilidade"),
    ("NonTacticalAttributes", "HardnessOfTraining"):  ("nta_intensidade_treino","habilidade"),
    ("NonTacticalAttributes", "MindGames"):           ("nta_jogos_mentais",    "habilidade"),
    ("NonTacticalAttributes", "SquadRotation"):       ("nta_rotacao_elenco",   "habilidade"),

    ("TacticalAttributes", "Attacking"):               ("tac_ataque",         "habilidade"),
    ("TacticalAttributes", "Depth"):                   ("tac_profundidade",   "habilidade"),
    ("TacticalAttributes", "Directness"):              ("tac_direcao",        "habilidade"),
    ("TacticalAttributes", "Flamboyancy"):             ("tac_espetaculo",     "habilidade"),
    ("TacticalAttributes", "Flexibility"):             ("tac_flexibilidade",  "habilidade"),
    ("TacticalAttributes", "FreeRoles"):               ("tac_funcoes_livres", "habilidade"),
    ("TacticalAttributes", "Marking"):                 ("tac_marcacao",       "habilidade"),
    ("TacticalAttributes", "Offside"):                 ("tac_impedimento",    "habilidade"),
    ("TacticalAttributes", "Pressing"):                ("tac_pressao",        "habilidade"),
    ("TacticalAttributes", "SittingBack"):             ("tac_recuar",         "habilidade"),
    ("TacticalAttributes", "Tempo"):                   ("tac_ritmo",          "habilidade"),
    ("TacticalAttributes", "UseOfPlaymaker"):          ("tac_armador",        "habilidade"),
    ("TacticalAttributes", "UseOfSubstitutions"):      ("tac_substituicoes",  "habilidade"),
    ("TacticalAttributes", "Width"):                   ("tac_largura",        "habilidade"),

    ("ScoutingAttributes", "JudgingPlayerData"): ("sct_aval_dados_jogador", "habilidade"),
    ("ScoutingAttributes", "JudgingTeamData"):   ("sct_aval_dados_time",    "habilidade"),
    ("ScoutingAttributes", "PresentingData"):    ("sct_apresentacao",       "habilidade"),

    ("MedicalAttributes", "SportsScience"): ("med_ciencia_esporte", "habilidade"),

    ("ChairmanAttributes", "Business"):       ("dir_negocios",      "habilidade"),
    ("ChairmanAttributes", "Interference"):   ("dir_interferencia", "habilidade"),
    ("ChairmanAttributes", "Patience"):       ("dir_paciencia",     "habilidade"),
    ("ChairmanAttributes", "Resources"):      ("dir_recursos",      "habilidade"),

    ("Reputation", "Worldwide"): ("dir_rep_mundial", "habilidade"),
    ("Reputation", "Current"):   ("dir_rep_atual",   "habilidade"),
    ("Reputation", "Local"):     ("dir_rep_local",   "habilidade"),
}


# =============================================
# NORMALIZAÇÃO / NAVEGAÇÃO
# =============================================
def norm_key(s) -> str:
    """minúsculas, sem acento, só a-z0-9."""
    if s is None:
        return ""
    s = str(s).replace("_", " ")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", s.lower())


def get_value(data, path):
    """Navega dict aninhado por uma tupla de chaves."""
    cur = data
    for k in path:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return None
    return cur


# =============================================
# CLASSIFICADORES — 2ª Divisão Capixaba
# =============================================
def classificar_ca_pa(v):
    """CA/PA (1-200) — faixas realistas para o futebol capixaba."""
    try:
        v = int(float(v))
    except (TypeError, ValueError):
        return None
    if v <= 20:  return "Muito Baixo (Amador)"
    if v <= 40:  return "Baixo (Semi-amador)"
    if v <= 65:  return "Médio (Regional)"
    if v <= 90:  return "Alto (Destaque Estadual)"
    return "Muito Alto (Fora do Padrão)"


def classificar_habilidade(v):
    """Atributos FM26 (1-20) — recalibrados para a 2ª Divisão Capixaba."""
    try:
        v = int(float(v))
    except (TypeError, ValueError):
        return None
    if v <= 5:   return "Muito Ruim"
    if v <= 8:   return "Ruim"
    if v <= 12:  return "Médio"
    if v <= 15:  return "Bom"
    return "Muito Bom"


def classificar_perna(v):
    """Força de perna (1-20)."""
    try:
        v = int(float(v))
    except (TypeError, ValueError):
        return None
    if v <= 4:   return "Muito Fraco"
    if v <= 9:   return "Fraco"
    if v <= 13:  return "Razoável"
    if v <= 17:  return "Forte"
    return "Muito Forte"


CLASSIFICADORES = {
    "ca_pa":      classificar_ca_pa,
    "perna":      classificar_perna,
    "habilidade": classificar_habilidade,
}


def classificar_valor(tipo: str, valor):
    """Retorna o rótulo textual correspondente ao valor numérico."""
    func = CLASSIFICADORES.get(tipo)
    if func is None:
        return None
    return func(valor)


def formatar_atributo(valor, tipo: str) -> str:
    """Retorna 'valor (rótulo)' — ou apenas o valor se não houver classificador."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return "N/I"
    label = classificar_valor(tipo, valor)
    try:
        if isinstance(valor, float) and valor.is_integer():
            valor_fmt = str(int(valor))
        else:
            valor_fmt = str(valor)
    except Exception:
        valor_fmt = str(valor)
    return f"{valor_fmt} ({label})" if label else valor_fmt


def rotulo_atributo(valor, tipo: str) -> str:
    """Retorna APENAS o rótulo textual (ex: 'Médio', 'Bom', 'Alto (Destaque Estadual)').
    Se não houver classificador, devolve o próprio valor como string."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return "N/I"
    label = classificar_valor(tipo, valor)
    if label:
        return label
    try:
        if isinstance(valor, float) and valor.is_integer():
            return str(int(valor))
        return str(valor)
    except Exception:
        return str(valor)


def encontrar_tipo_atributo(nome_coluna: str) -> Optional[str]:
    """Descobre o tipo de classificador ('ca_pa', 'habilidade', 'perna')
    a partir do nome PT-BR ou chave interna da coluna."""
    if not nome_coluna:
        return None
    col = norm_key(nome_coluna)

    for path, (nome_pt, tipo) in FIELDS.items():
        if norm_key(nome_pt) == col:
            return tipo
    for path, (nome_pt, tipo) in FIELDS.items():
        if norm_key("".join(path)) == col:
            return tipo

    if col.startswith("fispe") or "pe_esquerdo" in col or "pe_direito" in col:
        return "perna"
    if col in ("ca", "pa", "habilidadeatual", "habilidadepotencial"):
        return "ca_pa"
    return "habilidade"


# =============================================
# SANITIZAÇÃO E ORDENAÇÃO
# =============================================
def sanitizar_dataframe(df):
    if df is None or df.empty:
        return df
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].apply(
                lambda x: ', '.join(x) if isinstance(x, list) else (str(x) if pd.notna(x) else '')
            )
        elif pd.api.types.is_categorical_dtype(df[col]):
            df[col] = df[col].astype(str)
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime('%Y-%m-%d')
    return df

def ordenar_historico_cartoes(cartoes: dict) -> dict:
    for jogador, dados in cartoes.items():
        if 'historico' in dados and dados['historico']:
            def parse_data(data_str):
                if not data_str:
                    return datetime.now()
                if '/' in data_str:
                    try:
                        dia, mes, ano = data_str.split('/')
                        return datetime(int(ano), int(mes), int(dia))
                    except:
                        return datetime.now()
                else:
                    try:
                        return datetime.strptime(data_str, "%Y-%m-%d")
                    except:
                        return datetime.now()
            dados['historico'] = sorted(
                dados['historico'],
                key=lambda x: (parse_data(x['data']).month,
                               parse_data(x['data']).day,
                               parse_data(x['data']).year)
            )
    return cartoes

# =============================================
# FUNÇÕES AUXILIARES BÁSICAS
# =============================================
def calcular_idade(data_nasc_str, data_referencia=None):
    if pd.isna(data_nasc_str) or not data_nasc_str:
        return np.nan
    try:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                data_nasc = datetime.strptime(str(data_nasc_str).strip(), fmt)
                break
            except ValueError:
                continue
        else:
            return np.nan
        hoje = data_referencia if data_referencia else datetime.now()
        if isinstance(hoje, str):
            for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
                try:
                    hoje = datetime.strptime(hoje, fmt)
                    break
                except ValueError:
                    continue
            if isinstance(hoje, str):
                return np.nan
        return hoje.year - data_nasc.year - ((hoje.month, hoje.day) < (data_nasc.month, data_nasc.day))
    except Exception:
        return np.nan

def normalizar_texto(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).strip().lower()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    texto = re.sub(r'[^a-z0-9\s]', '', texto)
    return ' '.join(texto.split())

def mapear_nome_para_canonico(nome):
    if pd.isna(nome):
        return None
    nome = str(nome).strip()
    for d in [MAPEAMENTO_NOMES_PROFISSIONAL, MAPEAMENTO_NOMES_SUB15, MAPEAMENTO_NOMES_SUB17,
              MAPEAMENTO_NOMES_COMISSAO_PROFISSIONAL, MAPEAMENTO_NOMES_COMISSAO_SUB15,
              MAPEAMENTO_NOMES_COMISSAO_SUB17]:
        if nome in d:
            return d[nome]
    nome_norm = normalizar_texto(nome)
    for d in [MAPEAMENTO_NOMES_PROFISSIONAL, MAPEAMENTO_NOMES_SUB15, MAPEAMENTO_NOMES_SUB17,
              MAPEAMENTO_NOMES_COMISSAO_PROFISSIONAL, MAPEAMENTO_NOMES_COMISSAO_SUB15,
              MAPEAMENTO_NOMES_COMISSAO_SUB17]:
        for var, can in d.items():
            if normalizar_texto(var) == nome_norm:
                return can
    return nome

def safe_str(valor, padrao="N/I"):
    if pd.isna(valor) or str(valor).strip() == '':
        return padrao
    return str(valor).strip()

def extrair_id_jogo(caminho_arquivo):
    match = re.search(r'jogo_(\d+)_', os.path.basename(caminho_arquivo))
    return int(match.group(1)) if match else None

def extrair_data_jogo(caminho_arquivo):
    match = re.search(r'(\d{4}-\d{2}-\d{2})', caminho_arquivo)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y-%m-%d")
        except:
            pass
    return None

# =============================================
# CLASSIFICAÇÕES
# =============================================
def classif_imc(imc):
    if pd.isna(imc): return "Indefinido"
    if imc < 20: return "Baixo peso"
    if imc < 24: return "Normal"
    if imc < 27: return "Sobrepeso leve"
    if imc < 30: return "Sobrepeso"
    return "Obesidade"

def classif_gordura(p, idade):
    if pd.isna(p) or pd.isna(idade): return "Indefinido"
    if idade < 30:
        if p < 12: return "Excelente"
        if p < 17: return "Bom"
        if p < 22: return "Médio"
        return "Alto"
    else:
        if p < 15: return "Excelente"
        if p < 20: return "Bom"
        if p < 25: return "Médio"
        return "Alto"

def estado_fisico(imc_class, gor_class):
    if imc_class == "Indefinido" or gor_class == "Indefinido": return "Bom"
    if imc_class == "Normal" and gor_class in ["Excelente", "Bom"]: return "Ótimo"
    if imc_class == "Normal" and gor_class == "Médio": return "Bom"
    if imc_class in ["Sobrepeso leve", "Sobrepeso"]: return "Atenção"
    if imc_class == "Obesidade" or gor_class == "Alto": return "Crítico"
    return "Regular"

# =============================================
# INICIALIZAÇÃO DO BANCO SQLITE
# =============================================
def inicializar_banco():
    conn = sqlite3.connect('meu_futebol.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS treinos (id INTEGER PRIMARY KEY AUTOINCREMENT, atleta_id TEXT, data TEXT, carga REAL, duracao_min INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS wellbeing (id INTEGER PRIMARY KEY AUTOINCREMENT, atleta_id TEXT, data TEXT, sono INTEGER, estresse INTEGER, dor INTEGER, disposicao INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS lesoes (id INTEGER PRIMARY KEY AUTOINCREMENT, jogador TEXT, tipo_lesao TEXT, data_inicio TEXT, data_fim TEXT, ativo INTEGER DEFAULT 1)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS jogos (id INTEGER PRIMARY KEY, time_casa_id INTEGER, time_fora_id INTEGER, gols_casa INTEGER, gols_fora INTEGER, status TEXT, data_hora TEXT, formacao_casa TEXT, formacao_fora TEXT, venue_id INTEGER, arbitro_id INTEGER, competicao_id INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS gps (id INTEGER PRIMARY KEY AUTOINCREMENT, atleta_id TEXT, data TEXT, distancia_total REAL, velocidade_max REAL, sprints INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS times (id INTEGER PRIMARY KEY, nome TEXT, sigla TEXT, logo_url TEXT, fundado INTEGER, pais TEXT, temporada INTEGER, venue_id INTEGER, id_principal INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS elenco (id INTEGER PRIMARY KEY, nome TEXT, apelido TEXT, posicao TEXT, numero INTEGER, idade INTEGER, foto TEXT, time_id INTEGER, data_nascimento TEXT, cidade_nascimento TEXT, uf_nascimento TEXT, pais_nascimento TEXT, competicao_id INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS eventos (id INTEGER PRIMARY KEY AUTOINCREMENT, jogo_id INTEGER, tempo INTEGER, tipo TEXT, jogador_id INTEGER, detalhes TEXT, time_id INTEGER, membro_id INTEGER, tipo_alvo TEXT, competicao_id INTEGER, fonte TEXT DEFAULT 'api')''')
    cursor.execute("PRAGMA table_info(eventos)")
    colunas = [col[1] for col in cursor.fetchall()]
    if 'fonte' not in colunas:
        cursor.execute("ALTER TABLE eventos ADD COLUMN fonte TEXT DEFAULT 'api'")
    cursor.execute('''CREATE TABLE IF NOT EXISTS tecnicos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cargo TEXT, idade INTEGER, data_nascimento TEXT, historico_profissional TEXT, historico_jogador TEXT, nacionalidade TEXT, foto TEXT, time_id INTEGER, cidade TEXT, uf TEXT, pais TEXT, competicao_id INTEGER, apelido TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS arbitros (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, foto TEXT, categoria TEXT, uf TEXT, genero TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS comissao (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, cargo TEXT NOT NULL, foto TEXT, data_nascimento TEXT, cidade TEXT, uf TEXT, pais TEXT, historico_profissional TEXT, historico_jogador TEXT, categoria TEXT, time_id INTEGER, apelido TEXT, competicao_id INTEGER, idade INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS competicoes (id INTEGER PRIMARY KEY, nome TEXT NOT NULL, categoria TEXT, nivel TEXT, genero TEXT, temporada INTEGER, ativa BOOLEAN)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS venues (id INTEGER PRIMARY KEY, nome TEXT, cidade TEXT, capacidade INTEGER, endereco TEXT, superficie TEXT, imagem TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS estatisticas_jogadores (id INTEGER PRIMARY KEY AUTOINCREMENT, jogo_id INTEGER, jogador_id INTEGER, minutos INTEGER, gols INTEGER, assistencias INTEGER, cartoes_amarelos INTEGER, cartoes_vermelhos INTEGER, chutes INTEGER, chutes_ao_gol INTEGER, desarmes INTEGER, interceptacoes INTEGER, passes_certos INTEGER, passes_chave INTEGER, defesas INTEGER, competicao_id INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS lineup (id INTEGER PRIMARY KEY AUTOINCREMENT, jogo_id INTEGER NOT NULL, competicao_id INTEGER, time TEXT NOT NULL, time_id INTEGER, formacao TEXT, status TEXT, nome TEXT NOT NULL, numero TEXT, posicao TEXT, posicao_grid TEXT, jogador_id INTEGER, data_importacao DATETIME, tecnico_id INTEGER, comissao_id INTEGER)''')
    conn.commit()
    conn.close()

# =============================================
# CARREGAR ELENCO
# =============================================
def _carregar_elenco_generico(caminho_arquivo: str) -> pd.DataFrame:
    if not os.path.exists(caminho_arquivo):
        st.warning(f"Arquivo não encontrado: {caminho_arquivo}")
        return pd.DataFrame()
    separadores = [';', ',', '\t', '|']
    df = None
    for sep in separadores:
        try:
            df_temp = pd.read_csv(caminho_arquivo, sep=sep, encoding='utf-8-sig',
                                   skipinitialspace=True, on_bad_lines='skip', dtype=str,
                                   nrows=5, index_col=False)
            if len(df_temp.columns) > 1:
                df = pd.read_csv(caminho_arquivo, sep=sep, encoding='utf-8-sig',
                                  skipinitialspace=True, on_bad_lines='skip', dtype=str,
                                  index_col=False)
                break
        except Exception:
            continue
    if df is None:
        st.error(f"❌ Não foi possível ler o arquivo {caminho_arquivo}.")
        return pd.DataFrame()

    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    df = df.loc[:, ~df.columns.str.match('^unnamed.*$', case=False)]

    colunas_numericas = ['altura_cm', 'peso_kg', 'habilidade_atual', 'habilidade_potencial',
                         'jogos_temporada', 'minutos_totais', 'media_minutos_por_jogo',
                         'gols_totais', 'assistencias_totais', 'cartoes_amarelos_totais',
                         'cartoes_vermelhos_totais', 'chutes_totais', 'chutes_ao_gol_totais',
                         'desarmes_totais', 'interceptacoes_totais', 'passes_certos_totais',
                         'passes_chave_totais', 'defesas_totais', 'participacoes_diretas']
    for col in colunas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            df[col] = np.nan
    for attr in ATRIBUTOS_FM26:
        if attr in df.columns:
            df[attr] = pd.to_numeric(df[attr], errors='coerce')
        else:
            df[attr] = np.nan

    coluna_nome = None
    for possivel in ['nome_completo', 'apelido', 'jogador', 'nome']:
        if possivel in df.columns:
            coluna_nome = possivel
            break
    if coluna_nome is None:
        return pd.DataFrame()
    if coluna_nome != 'nome_completo':
        df.rename(columns={coluna_nome: 'nome_completo'}, inplace=True)
    if 'apelido' not in df.columns:
        df['apelido'] = df['nome_completo']

    if 'ogol_id' in df.columns:
        df = df.drop_duplicates(subset=['ogol_id'], keep='first')
    else:
        df = df.drop_duplicates(subset=['nome_completo'], keep='first')

    for col in ['data_nascimento', 'posicao', 'pe_pref', 'altura_cm', 'peso_kg']:
        if col not in df.columns:
            df[col] = None
        elif col in ['altura_cm', 'peso_kg']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df['IMC'] = df.apply(
        lambda x: x['peso_kg'] / ((x['altura_cm'] / 100) ** 2)
        if pd.notna(x['altura_cm']) and pd.notna(x['peso_kg']) and x['altura_cm'] > 0 else np.nan,
        axis=1).round(1)
    df['Classificacao_IMC'] = df['IMC'].apply(classif_imc)
    df['Idade'] = df['data_nascimento'].apply(lambda x: calcular_idade(x) if pd.notna(x) else np.nan)
    df['Gordura_Corporal_%'] = df.apply(
        lambda row: round((1.20 * row['IMC']) + (0.23 * row['Idade']) - 16.2, 1)
        if pd.notna(row['IMC']) and pd.notna(row['Idade']) else np.nan, axis=1)
    df['Massa_Magra_kg'] = df.apply(
        lambda row: round(row['peso_kg'] * (1 - row['Gordura_Corporal_%'] / 100), 1)
        if pd.notna(row['peso_kg']) and pd.notna(row['Gordura_Corporal_%']) else np.nan, axis=1)
    df['Massa_Muscular_Estimada_kg'] = df.apply(
        lambda row: round(row['Massa_Magra_kg'] * 0.55, 1)
        if pd.notna(row['Massa_Magra_kg']) else np.nan, axis=1)
    df['Classificacao_Gordura'] = df.apply(
        lambda x: classif_gordura(x['Gordura_Corporal_%'], x['Idade']), axis=1)
    df['Estado_Fisico'] = df.apply(
        lambda row: estado_fisico(row['Classificacao_IMC'], row['Classificacao_Gordura']), axis=1)

    def cat_pos(pos_str):
        if pd.isna(pos_str):
            return 'Outros', []
        pos = str(pos_str).upper().strip()
        pos_list = [p.strip() for p in pos.split('/')] if '/' in pos else [pos.strip()]
        cats = []
        for p in pos_list:
            pu = p.upper()
            if 'GOLEIRO' in pu: cats.append('Goleiro')
            elif 'ZAGUEIRO' in pu: cats.append('Zagueiro')
            elif 'LATERAL DIREITO' in pu or 'LAT. DIREITO' in pu: cats.append('Lateral Direito')
            elif 'LATERAL ESQUERDO' in pu or 'LAT. ESQUERDO' in pu: cats.append('Lateral Esquerdo')
            elif 'LATERAL' in pu: cats.append('Lateral')
            elif 'VOLANTE' in pu: cats.append('Volante')
            elif 'MEIA-CENTRAL' in pu or 'MEIA CENTRAL' in pu or 'MEIO-CENTRO' in pu: cats.append('Meia-Central')
            elif 'MEIA-ATACANTE' in pu or 'MEIA ATACANTE' in pu or 'MEIA OFENSIVO' in pu: cats.append('Meia-Atacante')
            elif 'MEIA' in pu or 'MEIO' in pu: cats.append('Meia')
            elif 'PONTA DIREITA' in pu: cats.append('Ponta Direita')
            elif 'PONTA ESQUERDA' in pu: cats.append('Ponta Esquerda')
            elif 'PONTA' in pu: cats.append('Ponta')
            elif 'CENTROAVANTE' in pu: cats.append('Centroavante')
            elif 'SEGUNDO ATACANTE' in pu: cats.append('Segundo Atacante')
            elif 'ATACANTE' in pu: cats.append('Atacante')
            else: cats.append('Outros')
        cats = [c for c in cats if c != 'Outros']
        cats = list(dict.fromkeys(cats))
        return cats[0] if cats else 'Outros', cats

    res = df['posicao'].apply(cat_pos)
    df['Posicao_Principal'] = res.apply(lambda x: x[0])
    df['Posicoes_Secundarias'] = res.apply(lambda x: x[1])

    if 'habilidade_atual' in df.columns and df['habilidade_atual'].notna().any():
        df['Rating_Geral_FM26'] = df['habilidade_atual'] / 2
    else:
        df['Rating_Geral_FM26'] = df[ATRIBUTOS_FM26].mean(axis=1)
    df['Rating_Geral_FM26'] = df['Rating_Geral_FM26'].clip(0, 100).fillna(50)

    for col in colunas_numericas:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    if 'foto' in df.columns:
        df.drop(columns=['foto'], inplace=True)

    return sanitizar_dataframe(df)

@st.cache_data
def carregar_elenco_profissional() -> pd.DataFrame:
    caminho = ARQUIVO_CSV_PROFISSIONAL
    if not os.path.exists(caminho):
        caminho = os.path.join(DATA_DIR, ARQUIVO_CSV_PROFISSIONAL)
    return _carregar_elenco_generico(caminho)

@st.cache_data
def carregar_elenco_sub15() -> pd.DataFrame:
    caminho = ARQUIVO_CSV_SUB15
    if not os.path.exists(caminho):
        caminho = os.path.join(DATA_DIR, ARQUIVO_CSV_SUB15)
    return _carregar_elenco_generico(caminho)

@st.cache_data
def carregar_elenco_sub17() -> pd.DataFrame:
    caminho = ARQUIVO_CSV_SUB17
    if not os.path.exists(caminho):
        caminho = os.path.join(DATA_DIR, ARQUIVO_CSV_SUB17)
    return _carregar_elenco_generico(caminho)

# =============================================
# CARREGAMENTO DA COMISSÃO
# =============================================
def _carregar_comissao_generico(caminho_arquivo: str) -> pd.DataFrame:
    if not os.path.exists(caminho_arquivo):
        return pd.DataFrame()
    try:
        df = pd.read_csv(caminho_arquivo, sep=';', encoding='utf-8-sig', skipinitialspace=True)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        if 'nome' not in df.columns and 'apelido' in df.columns:
            df['nome'] = df['apelido']
        elif 'nome' not in df.columns and 'nome_completo' in df.columns:
            df['nome'] = df['nome_completo']
        if 'cargo' not in df.columns:
            df['cargo'] = 'Técnico'
        if 'idade' not in df.columns and 'data_nascimento' in df.columns:
            df['idade'] = df['data_nascimento'].apply(lambda x: calcular_idade(x) if pd.notna(x) else np.nan)
        if 'cidade_uf' not in df.columns and 'cidade_nascimento' in df.columns and 'uf_nascimento' in df.columns:
            df['cidade_uf'] = df['cidade_nascimento'].fillna('') + ', ' + df['uf_nascimento'].fillna('')
            df['cidade_uf'] = df['cidade_uf'].str.rstrip(', ')
        elif 'cidade_uf' not in df.columns:
            df['cidade_uf'] = 'N/I'
        if 'pais' not in df.columns and 'pais_nascimento' in df.columns:
            df['pais'] = df['pais_nascimento']
        elif 'pais' not in df.columns:
            df['pais'] = 'N/I'
        if 'nome_canonico' not in df.columns and 'apelido' in df.columns:
            df['nome_canonico'] = df['apelido'].apply(mapear_nome_para_canonico)
        elif 'nome_canonico' not in df.columns and 'nome' in df.columns:
            df['nome_canonico'] = df['nome'].apply(mapear_nome_para_canonico)
        return sanitizar_dataframe(df)
    except Exception as e:
        st.error(f"Erro ao carregar comissão de {caminho_arquivo}: {e}")
        return pd.DataFrame()

@st.cache_data
def carregar_comissao() -> pd.DataFrame:
    return _carregar_comissao_generico(ARQUIVO_CSV_COMISSAO_PROFISSIONAL)

@st.cache_data
def carregar_comissao_sub15() -> pd.DataFrame:
    return _carregar_comissao_generico(ARQUIVO_CSV_COMISSAO_SUB15)

@st.cache_data
def carregar_comissao_sub17() -> pd.DataFrame:
    return _carregar_comissao_generico(ARQUIVO_CSV_COMISSAO_SUB17)

# =============================================
# CARREGAMENTO DA DIRETORIA
# =============================================
def _carregar_diretoria_generico(caminho_arquivo: str) -> pd.DataFrame:
    if not os.path.exists(caminho_arquivo):
        caminho_arquivo = os.path.join(DATA_DIR, ARQUIVO_CSV_DIRETORIA)
    if not os.path.exists(caminho_arquivo):
        return pd.DataFrame()

    separadores = [';', ',', '\t', '|']
    df = None
    for sep in separadores:
        try:
            df_temp = pd.read_csv(caminho_arquivo, sep=sep, encoding='utf-8-sig',
                                   skipinitialspace=True, dtype=str, nrows=5,
                                   index_col=False, on_bad_lines='skip')
            if len(df_temp.columns) > 1:
                df = pd.read_csv(caminho_arquivo, sep=sep, encoding='utf-8-sig',
                                  skipinitialspace=True, dtype=str,
                                  index_col=False, on_bad_lines='skip')
                break
        except Exception:
            continue
    if df is None:
        return pd.DataFrame()

    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    df = df.loc[:, ~df.columns.str.match('^unnamed.*$', case=False)]

    if 'nome' not in df.columns and 'apelido' in df.columns:
        df['nome'] = df['apelido']
    elif 'nome' not in df.columns and 'nome_completo' in df.columns:
        df['nome'] = df['nome_completo']
    if 'nome_completo' not in df.columns:
        df['nome_completo'] = df.get('nome', df.get('apelido', ''))
    if 'apelido' not in df.columns:
        df['apelido'] = df['nome_completo']

    if 'cargo' not in df.columns:
        df['cargo'] = 'Diretor'

    if 'idade' not in df.columns and 'data_nascimento' in df.columns:
        df['idade'] = df['data_nascimento'].apply(
            lambda x: calcular_idade(x) if pd.notna(x) else np.nan)

    if 'cidade_uf' not in df.columns:
        if 'cidade_nascimento' in df.columns and 'uf_nascimento' in df.columns:
            df['cidade_uf'] = df['cidade_nascimento'].fillna('') + ', ' + df['uf_nascimento'].fillna('')
            df['cidade_uf'] = df['cidade_uf'].str.rstrip(', ')
        elif 'cidade' in df.columns and 'uf' in df.columns:
            df['cidade_uf'] = df['cidade'].fillna('') + ', ' + df['uf'].fillna('')
            df['cidade_uf'] = df['cidade_uf'].str.rstrip(', ')
        else:
            df['cidade_uf'] = 'N/I'

    if 'pais' not in df.columns:
        if 'pais_nascimento' in df.columns:
            df['pais'] = df['pais_nascimento']
        else:
            df['pais'] = 'Brasil'

    if 'historico_jogador' not in df.columns:
        for alt in ['historico_como_jogador', 'hist_jogador', 'historico_atleta']:
            if alt in df.columns:
                df['historico_jogador'] = df[alt]
                break
        else:
            df['historico_jogador'] = 'Não informado'
    else:
        df['historico_jogador'] = df['historico_jogador'].fillna('Não informado')

    if 'historico_profissional' not in df.columns:
        if 'historico_diretoria' in df.columns:
            df['historico_profissional'] = df['historico_diretoria']
        elif 'historico' in df.columns:
            df['historico_profissional'] = df['historico']
        else:
            df['historico_profissional'] = 'Não informado'
    else:
        df['historico_profissional'] = df['historico_profissional'].fillna('Não informado')

    if 'historico' not in df.columns:
        df['historico'] = df['historico_profissional']

    if 'nome_canonico' not in df.columns:
        df['nome_canonico'] = df['nome'].apply(mapear_nome_para_canonico)

    return sanitizar_dataframe(df)

@st.cache_data
def carregar_diretoria() -> pd.DataFrame:
    caminho = ARQUIVO_CSV_DIRETORIA
    if not os.path.exists(caminho):
        caminho = os.path.join(DATA_DIR, ARQUIVO_CSV_DIRETORIA)
    return _carregar_diretoria_generico(caminho)

# =============================================
# CRONOGRAMA
# =============================================
@st.cache_data
def carregar_cronograma(categoria="Profissional") -> pd.DataFrame:
    arquivo = {"Profissional": ARQUIVO_CRONO_PROF, "Sub-15": ARQUIVO_CRONO_SUB15,
               "Sub-17": ARQUIVO_CRONO_SUB17}.get(categoria)
    if not arquivo or not os.path.exists(arquivo):
        return pd.DataFrame()
    try:
        df = pd.read_csv(arquivo, sep=';', encoding='utf-8-sig', skipinitialspace=True)
        if 'data' not in df.columns:
            return pd.DataFrame()
        df['data'] = pd.to_datetime(df['data'], errors='coerce')
        if 'competicao' not in df.columns:
            df['competicao'] = 'Desconhecida'
        if 'fase' not in df.columns:
            df['fase'] = ''
        return sanitizar_dataframe(df)
    except Exception as e:
        st.error(f"Erro ao carregar cronograma: {e}")
        return pd.DataFrame()

def obter_proximo_jogo(categoria="Profissional") -> Optional[Dict]:
    df = carregar_cronograma(categoria)
    if df.empty:
        return None
    hoje = datetime.now().date()
    df_futuros = df[df['data'].dt.date >= hoje].sort_values('data')
    return df_futuros.iloc[0].to_dict() if not df_futuros.empty else None

# =============================================
# FOTOS
# =============================================
def obter_caminho_foto(pessoa_row, categoria="Profissional"):
    foto = pessoa_row.get('foto', '')
    if foto and pd.notna(foto) and str(foto).strip():
        caminho = str(foto).strip()
        if os.path.exists(caminho) or caminho.startswith('http'):
            return caminho
    nome = pessoa_row.get('apelido') or pessoa_row.get('nome_completo') or pessoa_row.get('nome')
    if not nome or pd.isna(nome):
        return None
    nome_clean = normalizar_texto(nome).replace(' ', '_')
    nome_sem_acento = normalizar_texto(nome)
    pastas_base = [
        "assets/fotos_jogadores", "assets/fotos_jogadores/Profissional",
        "assets/fotos_jogadores/Sub15", "assets/fotos_jogadores/Sub17",
        "fotos", "fotos/Profissional", "fotos/Sub15", "fotos/Sub17",
        "fotos_sistema_Analise_Elenco/Jogadores",
        "fotos_sistema_Analise_Elenco/Jogadores/Profissional",
        "fotos_sistema_Analise_Elenco/Jogadores/Sub15",
        "fotos_sistema_Analise_Elenco/Jogadores/Sub17",
        "assets/fotos_comissao", "assets/fotos_comissao/Profissional",
        "assets/fotos_comissao/Sub15", "assets/fotos_comissao/Sub17",
        "assets/fotos_tecnicos", "fotos_comissao", "Fotos_Tecnicos",
        "fotos_sistema_Analise_Elenco/Comissao_Tecnica/Profissional",
        "fotos_sistema_Analise_Elenco/Comissao_Tecnica/Sub15",
        "fotos_sistema_Analise_Elenco/Comissao_Tecnica/Sub17",
        "fotos_diretoria", "assets/fotos_diretoria",
        "Fotos_Diretoria",
    ]
    pastas_absolutas = [
        r"C:\BDAnaliseElencoLinharesFC\projeto_web\assets\fotos_jogadores",
        r"C:\BDAnaliseElencoLinharesFC\projeto_web\fotos",
        r"C:\BDAnaliseElencoLinharesFC\projeto_web\fotos_sistema_Analise_Elenco\Jogadores",
        r"C:\BDAnaliseElencoLinharesFC\projeto_web\assets\fotos_comissao",
        r"C:\BDAnaliseElencoLinharesFC\projeto_web\assets\fotos_tecnicos",
        r"C:\BDAnaliseElencoLinharesFC\projeto_web\fotos_diretoria",
    ]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    pastas = pastas_absolutas.copy()
    for p in pastas_base:
        pastas.append(os.path.join(script_dir, p))
        pastas.append(os.path.join(parent_dir, p))
    extensoes = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']

    def arquivo_corresponde(nome_arquivo):
        nome_arquivo_sem_ext = os.path.splitext(nome_arquivo)[0]
        nome_arquivo_clean = normalizar_texto(nome_arquivo_sem_ext).replace(' ', '_')
        return (nome_clean in nome_arquivo_clean) or (nome_arquivo_clean in nome_clean) or (
            nome_sem_acento in normalizar_texto(nome_arquivo_sem_ext))

    for pasta in set(pastas):
        if not os.path.isdir(pasta):
            continue
        for ext in extensoes:
            for nome_tentativa in [nome, nome_clean]:
                caminho = os.path.join(pasta, f"{nome_tentativa}{ext}")
                if os.path.exists(caminho):
                    return os.path.abspath(caminho)
        for arquivo in os.listdir(pasta):
            if any(arquivo.lower().endswith(ext) for ext in extensoes):
                if arquivo_corresponde(arquivo):
                    return os.path.abspath(os.path.join(pasta, arquivo))
    for pasta in set(pastas):
        if not os.path.isdir(pasta):
            continue
        for root, dirs, files in os.walk(pasta):
            for arquivo in files:
                if any(arquivo.lower().endswith(ext) for ext in extensoes):
                    if arquivo_corresponde(arquivo):
                        return os.path.abspath(os.path.join(root, arquivo))
    return None

def obter_caminho_foto_diretoria(pessoa_row) -> Optional[str]:
    if pessoa_row is None:
        return None
    return obter_caminho_foto(pessoa_row, "Diretoria")

def exibir_foto(pessoa_row, categoria="Profissional", width=100):
    caminho = obter_caminho_foto(pessoa_row, categoria)
    if caminho and (caminho.startswith('http') or os.path.exists(caminho)):
        try:
            st.image(caminho, width=width)
            return
        except:
            pass
    st.write("📷")

def obter_caminho_foto_arbitro(nome_arbitro: str) -> Optional[str]:
    if not nome_arbitro or pd.isna(nome_arbitro):
        return None
    base_dir = Path(__file__).resolve().parent
    nome_clean = normalizar_texto(nome_arbitro).replace(' ', '_')
    extensoes = ['.png', '.jpg', '.jpeg', '.webp']
    pastas = [base_dir / "fotos_arbitros", base_dir / "assets" / "fotos_arbitros",
              base_dir / "data" / "fotos_arbitros"]
    for pasta in pastas:
        if not pasta.exists():
            continue
        for ext in extensoes:
            caminho = pasta / f"{nome_arbitro}{ext}"
            if caminho.exists(): return str(caminho.resolve())
            caminho = pasta / f"{nome_clean}{ext}"
            if caminho.exists(): return str(caminho.resolve())
    for pasta in pastas:
        if pasta.exists():
            for ext in extensoes:
                for arquivo in pasta.rglob(f"*{ext}"):
                    if arquivo.stem.lower() == nome_clean.lower() or arquivo.stem == nome_arbitro:
                        return str(arquivo.resolve())
    return None

# =============================================
# LESÕES
# =============================================
def parse_data_flexivel(data_str):
    if pd.isna(data_str) or str(data_str).strip() == '':
        return None
    data_str = str(data_str).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(data_str, fmt).date()
        except ValueError:
            continue
    return None

def formatar_data_br(data_date):
    return data_date.strftime("%d/%m/%Y") if data_date else ''

def carregar_lesoes(categoria):
    csv_path = {'profissional': ARQUIVO_LESOES_PROFISSIONAL, 'sub15': ARQUIVO_LESOES_SUB15,
                'sub17': ARQUIVO_LESOES_SUB17}.get(categoria)
    if not csv_path or not os.path.exists(csv_path):
        return {}, {}
    try:
        df = pd.read_csv(csv_path, delimiter=';', encoding='utf-8-sig', dtype=str)
    except Exception:
        return {}, {}
    lesionados_por_ogol, lesionados_por_nome = {}, {}
    colunas_lesoes = [col for col in df.columns if col.startswith('Lesao_')]
    for idx, row in df.iterrows():
        ogol_id = row.get('ogol_id')
        nome = row.get('nome_completo')
        lesionado = False
        for col in colunas_lesoes:
            valor = row.get(col, '')
            if pd.notna(valor) and valor != '':
                ocorrencias = str(valor).split(',')
                ultima = ocorrencias[-1].strip()
                if '/' in ultima or '-' in ultima:
                    data_obj = parse_data_flexivel(ultima)
                    if data_obj is not None:
                        if '/' not in ultima:
                            lesionado = True
                            break
        if ogol_id and pd.notna(ogol_id):
            try:
                lesionados_por_ogol[int(float(ogol_id))] = lesionado
            except:
                pass
        if nome:
            lesionados_por_nome[nome] = lesionado
    return lesionados_por_ogol, lesionados_por_nome

def adicionar_coluna_lesionado(df, categoria):
    les_ogol, les_nome = carregar_lesoes(categoria)
    def is_lesionado(row):
        ogol = row.get('ogol_id')
        if pd.notna(ogol):
            try:
                if int(float(ogol)) in les_ogol:
                    return les_ogol[int(float(ogol))]
            except:
                pass
        nome = row.get('nome_completo')
        if nome and nome in les_nome:
            return les_nome[nome]
        return False
    df['lesionado'] = df.apply(is_lesionado, axis=1)
    return df

def obter_historico_lesoes_texto(jogador_row, categoria):
    csv_path = {'Profissional': ARQUIVO_LESOES_PROFISSIONAL, 'Sub-15': ARQUIVO_LESOES_SUB15,
                'Sub-17': ARQUIVO_LESOES_SUB17}.get(categoria)
    if not csv_path or not os.path.exists(csv_path):
        return "Arquivo de lesões não encontrado."
    try:
        df_lesoes = pd.read_csv(csv_path, delimiter=';', encoding='utf-8-sig', dtype=str)
    except Exception as e:
        return f"Erro ao ler lesões: {e}"
    ogol_id = jogador_row.get('ogol_id')
    nome = jogador_row.get('nome_completo')
    linha_lesao = None
    if pd.notna(ogol_id):
        try:
            linha_lesao = df_lesoes[df_lesoes['ogol_id'].astype(float).astype(int) == int(float(ogol_id))]
        except:
            pass
    if linha_lesao is None or linha_lesao.empty:
        linha_lesao = df_lesoes[df_lesoes['nome_completo'] == nome]
    if linha_lesao is None or linha_lesao.empty:
        return "Nenhum registro de lesão encontrado."
    colunas_lesoes = [col for col in df_lesoes.columns if col.startswith('Lesao_')]
    linhas, tem_lesao = [], False
    for col in colunas_lesoes:
        valor = linha_lesao.iloc[0].get(col, '')
        if pd.notna(valor) and valor != '':
            tem_lesao = True
            nome_lesao = col.replace('Lesao_', '').replace('_', ' ')
            ocorrencias = str(valor).split(',')
            formatadas = []
            for occ in ocorrencias:
                occ = occ.strip()
                if '/' in occ:
                    if ' - ' in occ:
                        di, dfim = occ.split(' - ', 1)
                    else:
                        di, dfim = occ.split('/', 1)
                    di_obj, df_obj = parse_data_flexivel(di.strip()), parse_data_flexivel(dfim.strip())
                    if di_obj and df_obj:
                        formatadas.append(f"{formatar_data_br(di_obj)} - {formatar_data_br(df_obj)}")
                    else:
                        formatadas.append(occ)
                else:
                    data_obj = parse_data_flexivel(occ)
                    formatadas.append(f"{formatar_data_br(data_obj)} (atual)" if data_obj else occ)
            linhas.append(f"• {nome_lesao}: {', '.join(formatadas)}")
    return "\n".join(linhas) if tem_lesao else "Nenhuma lesão registrada."

def obter_lesao_atual(jogador_row, categoria):
    csv_path = {'Profissional': ARQUIVO_LESOES_PROFISSIONAL, 'Sub-15': ARQUIVO_LESOES_SUB15,
                'Sub-17': ARQUIVO_LESOES_SUB17}.get(categoria)
    if not csv_path or not os.path.exists(csv_path):
        return ""
    try:
        df_lesoes = pd.read_csv(csv_path, delimiter=';', encoding='utf-8-sig', dtype=str)
    except Exception:
        return ""
    ogol_id = jogador_row.get('ogol_id')
    nome = jogador_row.get('nome_completo')
    linha_lesao = None
    if pd.notna(ogol_id):
        try:
            linha_lesao = df_lesoes[df_lesoes['ogol_id'].astype(float).astype(int) == int(float(ogol_id))]
        except:
            pass
    if linha_lesao is None or linha_lesao.empty:
        linha_lesao = df_lesoes[df_lesoes['nome_completo'] == nome]
    if linha_lesao is None or linha_lesao.empty:
        return ""
    for col in [c for c in df_lesoes.columns if c.startswith('Lesao_')]:
        valor = linha_lesao.iloc[0].get(col, '')
        if pd.notna(valor) and str(valor).strip() != '':
            ocorrencias = str(valor).split(',')
            ultima = ocorrencias[-1].strip()
            if ' - ' in ultima or '/' in ultima or '–' in ultima:
                continue
            return col.replace('Lesao_', '').replace('_', ' ')
    return ""

# =============================================
# GESTÃO DE LESÕES
# =============================================
def adicionar_lesao(csv_path, nome_jogador, tipo_lesao, data_inicio, data_fim=None):
    if not os.path.exists(csv_path):
        df = pd.DataFrame(columns=['ogol_id', 'nome_completo'])
    else:
        try:
            df = pd.read_csv(csv_path, delimiter=';', encoding='utf-8-sig', dtype=str, on_bad_lines='skip')
        except Exception as e:
            print(f"Erro ao ler {csv_path}: {e}")
            return
    if 'nome_completo' not in df.columns: df['nome_completo'] = ''
    if 'ogol_id' not in df.columns: df['ogol_id'] = ''
    if nome_jogador in df['nome_completo'].values:
        idx = df[df['nome_completo'] == nome_jogador].index[0]
    else:
        nova_linha = {'nome_completo': nome_jogador, 'ogol_id': ''}
        for col in df.columns:
            if col not in nova_linha: nova_linha[col] = ''
        df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
        idx = len(df) - 1
    df.at[idx, 'nome_completo'] = nome_jogador
    coluna_lesao = f"Lesao_{tipo_lesao.replace(' ', '_').title()}"
    if coluna_lesao not in df.columns:
        df[coluna_lesao] = ''
    valor_atual = df.at[idx, coluna_lesao]
    if pd.isna(valor_atual) or valor_atual == '':
        nova_ocorrencia = data_inicio if data_fim is None else f"{data_inicio} - {data_fim}"
    else:
        if data_fim is None:
            nova_ocorrencia = f"{valor_atual}, {data_inicio}"
        else:
            nova_ocorrencia = f"{valor_atual}, {data_inicio} - {data_fim}"
    df.at[idx, coluna_lesao] = nova_ocorrencia
    df.to_csv(csv_path, sep=';', encoding='utf-8-sig', index=False)

def adicionar_lesao_com_data_fim(csv_path, nome_jogador, tipo_lesao, data_fim):
    if not os.path.exists(csv_path):
        return
    try:
        df = pd.read_csv(csv_path, delimiter=';', encoding='utf-8-sig', dtype=str, on_bad_lines='skip')
    except Exception as e:
        print(f"Erro ao ler {csv_path}: {e}")
        return
    coluna_lesao = f"Lesao_{tipo_lesao.replace(' ', '_').title()}"
    if coluna_lesao not in df.columns:
        return
    if nome_jogador in df['nome_completo'].values:
        idx = df[df['nome_completo'] == nome_jogador].index[0]
    else:
        return
    valor = df.at[idx, coluna_lesao]
    if pd.isna(valor) or valor == '':
        return
    ocorrencias = str(valor).split(',')
    for i in range(len(ocorrencias) - 1, -1, -1):
        occ = ocorrencias[i].strip()
        if ' - ' not in occ:
            ocorrencias[i] = f"{occ} - {data_fim}"
            break
    df.at[idx, coluna_lesao] = ', '.join(ocorrencias)
    df.to_csv(csv_path, sep=';', encoding='utf-8-sig', index=False)

# =============================================
# BIOIMPEDÂNCIA — Cálculo completo (Faulkner, Pollock, Lee)
# Adaptado para atletas do sexo masculino
# =============================================
def para_float(valor):
    if pd.isna(valor) or valor == '':
        return None
    try:
        return float(str(valor).replace(',', '.'))
    except:
        return None


def _float_ou_none(row, *keys):
    """Tenta várias chaves; retorna o primeiro valor numérico válido."""
    for k in keys:
        v = para_float(row.get(k))
        if v is not None:
            return v
    return None


def _calcular_faulkner(triceps, coxa, panturrilha, imc, idade):
    """Faulkner adaptado (3 dobras em mm): %G = 5.783 + 0.153 × Σ3.
    Fallback: Deurenberg (IMC e idade) quando não há dobras."""
    if triceps and coxa and panturrilha:
        soma3 = triceps + coxa + panturrilha
        pct = 5.783 + 0.153 * soma3
        return round(max(2.0, min(60.0, pct)), 1)
    if imc is not None and idade is not None:
        pct = 1.20 * imc + 0.23 * idade - 16.2
        return round(max(2.0, min(60.0, pct)), 1)
    return None


def _calcular_pollock3(triceps, coxa, panturrilha, imc, idade):
    """Jackson & Pollock 3 dobras (adaptado para tríceps/coxa/panturrilha)."""
    if triceps and coxa and panturrilha and idade is not None:
        soma3 = triceps + coxa + panturrilha
        D = (1.10938
             - 0.0008267 * soma3
             + 0.0000016 * (soma3 ** 2)
             - 0.0002574 * idade)
        if D > 0:
            pct = ((4.95 / D) - 4.50) * 100
            return round(max(2.0, min(60.0, pct)), 1)
    if imc is not None and idade is not None:
        pct = 1.20 * imc + 0.23 * idade - 16.2
        return round(max(2.0, min(60.0, pct)), 1)
    return None


def _calcular_pollock7(triceps, coxa, panturrilha, imc, idade):
    """Jackson & Pollock 7 dobras. Como só temos 3, usa a base do Pollock 3."""
    return _calcular_pollock3(triceps, coxa, panturrilha, imc, idade)


def _calcular_lee(altura_cm, peso_kg, idade,
                  per_braco, per_coxa, per_perna,
                  triceps, coxa, panturrilha):
    """Lee et al. (2000) — Massa Muscular (kg). Sexo masculino = 1.
    MM = H*(0.00744*CAG² + 0.00088*CTG² + 0.00441*CCG²) + 2.4 - 0.048*idade + 7.8
    """
    if (altura_cm and per_braco and per_coxa and per_perna
            and triceps and coxa and panturrilha and idade is not None):
        H = altura_cm / 100.0
        CAG = per_braco - (3.14159265 * triceps / 10.0)
        CTG = per_coxa - (3.14159265 * coxa / 10.0)
        CCG = per_perna - (3.14159265 * panturrilha / 10.0)
        mm = (H * (0.00744 * (CAG ** 2)
                   + 0.00088 * (CTG ** 2)
                   + 0.00441 * (CCG ** 2))
              + 2.4
              - 0.048 * idade
              + 7.8)
        return round(max(0.0, mm), 1)
    return None


def _calcular_bioimpedancia_completa(row):
    """Recebe uma linha (dict ou Series) e devolve dict com todas as estimativas.
    Prioriza valores já existentes no CSV; senão calcula pelas equações."""
    altura_cm = _float_ou_none(row, 'altura_cm', 'altura')
    peso_kg = _float_ou_none(row, 'peso_kg', 'peso')
    idade = _float_ou_none(row, 'idade')
    if idade is None:
        idade = calcular_idade(row.get('data_nascimento'))

    triceps = _float_ou_none(row, 'dobra_triceps', 'triceps')
    coxa = _float_ou_none(row, 'dobra_coxa', 'coxa')
    panturrilha = _float_ou_none(row, 'dobra_panturilha', 'dobra_panturrilha', 'panturrilha')

    per_braco = _float_ou_none(row, 'perimetro_braco')
    per_coxa = _float_ou_none(row, 'perimetro_coxa')
    per_perna = _float_ou_none(row, 'perimetro_perna', 'perimetro_panturrilha')

    pct_csv = _float_ou_none(row, 'pct_gordura', 'percentual_gordura',
                             'gordura_corporal', 'body_fat')
    mm_csv = _float_ou_none(row, 'massa_muscular', 'massa_muscular_kg',
                            'muscle_mass', 'mm_kg')
    mmag_csv = _float_ou_none(row, 'massa_magra', 'massa_magra_kg',
                              'lean_mass', 'ffm')
    mgord_csv = _float_ou_none(row, 'massa_gorda', 'massa_gorda_kg',
                               'fat_mass', 'fm')

    imc = None
    if altura_cm and peso_kg and altura_cm > 0:
        imc = round(peso_kg / ((altura_cm / 100.0) ** 2), 1)

    if pct_csv is not None:
        pct_faulkner = pct_csv
        pct_pollock3 = pct_csv
        pct_pollock7 = pct_csv
        origem_pct = 'CSV'
    else:
        pct_faulkner = _calcular_faulkner(triceps, coxa, panturrilha, imc, idade)
        pct_pollock3 = _calcular_pollock3(triceps, coxa, panturrilha, imc, idade)
        pct_pollock7 = _calcular_pollock7(triceps, coxa, panturrilha, imc, idade)
        origem_pct = 'Calculado'

    def _massa_gorda(pct):
        if pct is None or peso_kg is None:
            return None
        return round(peso_kg * (pct / 100.0), 1)

    def _massa_magra(pct):
        if pct is None or peso_kg is None:
            return None
        return round(peso_kg * (1 - pct / 100.0), 1)

    resultados_metodos = {
        'faulkner': {
            'pct': pct_faulkner,
            'massa_gorda': _massa_gorda(pct_faulkner),
            'massa_magra': _massa_magra(pct_faulkner),
        },
        'pollock3': {
            'pct': pct_pollock3,
            'massa_gorda': _massa_gorda(pct_pollock3),
            'massa_magra': _massa_magra(pct_pollock3),
        },
        'pollock7': {
            'pct': pct_pollock7,
            'massa_gorda': _massa_gorda(pct_pollock7),
            'massa_magra': _massa_magra(pct_pollock7),
        },
    }

    if mm_csv is not None:
        massa_muscular = mm_csv
        origem_mm = 'CSV'
    else:
        massa_muscular = _calcular_lee(altura_cm, peso_kg, idade,
                                       per_braco, per_coxa, per_perna,
                                       triceps, coxa, panturrilha)
        if massa_muscular is None:
            mm_ref = resultados_metodos['pollock3']['massa_magra']
            if mm_ref is not None:
                massa_muscular = round(mm_ref * 0.55, 1)
                origem_mm = 'Estimado (55% da massa magra)'
            else:
                origem_mm = 'Indisponível'
        else:
            origem_mm = 'Calculado (Lee 2000)'

    if pct_csv is not None:
        pct_principal = pct_csv
        metodo_principal = 'Bioimpedância (CSV)'
    elif pct_pollock3 is not None:
        pct_principal = pct_pollock3
        metodo_principal = 'Pollock 3'
    elif pct_faulkner is not None:
        pct_principal = pct_faulkner
        metodo_principal = 'Faulkner'
    else:
        pct_principal = None
        metodo_principal = '—'

    massa_gorda_principal = _massa_gorda(pct_principal) if pct_principal else mgord_csv
    massa_magra_principal = _massa_magra(pct_principal) if pct_principal else mmag_csv

    return {
        'imc': imc,
        'peso': peso_kg,
        'altura_cm': altura_cm,
        'idade': idade,
        'pct_gordura': pct_principal,
        'pct_gordura_origem': metodo_principal,
        'pct_origem': origem_pct,
        'metodos': resultados_metodos,
        'massa_gorda': massa_gorda_principal,
        'massa_magra': massa_magra_principal,
        'massa_muscular': massa_muscular,
        'massa_muscular_origem': origem_mm,
        'triceps': triceps, 'coxa': coxa, 'panturrilha': panturrilha,
        'per_braco': per_braco, 'per_coxa': per_coxa, 'per_perna': per_perna,
        'data_coleta': row.get('data_bioimpedancia', ''),
    }


def carregar_dados_bioimpedancia(categoria):
    """Lê o CSV de bioimpedância e devolve dict {ogol_id|nome: dados_completos}.
    Para cada atleta, se o CSV já tem dados medidos, usa-os; senão calcula Faulkner/Pollock/Lee."""
    csv_path = {'profissional': ARQUIVO_BIO_PROFISSIONAL,
                'sub15': ARQUIVO_BIO_SUB15,
                'sub17': ARQUIVO_BIO_SUB17}.get(categoria)
    if not csv_path or not os.path.exists(csv_path):
        return {}
    try:
        df = pd.read_csv(csv_path, delimiter=';', encoding='utf-8-sig', dtype=str)
    except Exception:
        return {}
    resultados = {}
    for idx, row in df.iterrows():
        try:
            nome = str(row.get('nome_completo', '')).strip()
            ogol_id = row.get('ogol_id')
            if pd.notna(ogol_id):
                try:
                    ogol_id = int(float(ogol_id))
                except:
                    ogol_id = None
            dados = _calcular_bioimpedancia_completa(row)
            if ogol_id:
                resultados[ogol_id] = dados
            elif nome:
                resultados[nome] = dados
        except Exception:
            continue
    return resultados


def aplicar_dados_bioimpedancia(df, dados_bio):
    """Aplica os dados calculados do CSV de bioimpedância ao DataFrame do elenco."""
    if not dados_bio:
        return df

    colunas_novas = [
        'PctGordura_Faulkner', 'PctGordura_Pollock3', 'PctGordura_Pollock7',
        'Massa_Gorda_kg', 'Massa_Magra_kg', 'Massa_Muscular_Estimada_kg',
        'Massa_Muscular_Origem', 'Bioimpedancia_Origem',
        'PctGordura_CSV', 'IMC_Bio'
    ]
    for col in colunas_novas:
        if col not in df.columns:
            df[col] = np.nan
    if 'Massa_Muscular_Origem' not in df.columns:
        df['Massa_Muscular_Origem'] = ''
    if 'Bioimpedancia_Origem' not in df.columns:
        df['Bioimpedancia_Origem'] = ''

    for idx, row in df.iterrows():
        ogol_id = row.get('ogol_id')
        nome = row.get('nome_completo')
        bio = None
        if pd.notna(ogol_id) and ogol_id in dados_bio:
            bio = dados_bio[ogol_id]
        elif nome in dados_bio:
            bio = dados_bio[nome]
        if bio is None:
            continue

        if bio.get('peso') is not None:
            df.at[idx, 'peso_kg'] = bio['peso']
        if bio.get('altura_cm') is not None:
            df.at[idx, 'altura_cm'] = bio['altura_cm']

        altura_cm = df.at[idx, 'altura_cm']
        peso_kg = df.at[idx, 'peso_kg']
        if pd.notna(altura_cm) and pd.notna(peso_kg) and altura_cm > 0:
            imc = round(peso_kg / ((altura_cm / 100) ** 2), 1)
        else:
            imc = None
        df.at[idx, 'IMC'] = imc if imc is not None else np.nan
        df.at[idx, 'IMC_Bio'] = bio.get('imc', np.nan)

        metodos = bio.get('metodos', {})
        fk = metodos.get('faulkner', {})
        p3 = metodos.get('pollock3', {})
        p7 = metodos.get('pollock7', {})

        if fk.get('pct') is not None:
            df.at[idx, 'PctGordura_Faulkner'] = fk['pct']
        if p3.get('pct') is not None:
            df.at[idx, 'PctGordura_Pollock3'] = p3['pct']
        if p7.get('pct') is not None:
            df.at[idx, 'PctGordura_Pollock7'] = p7['pct']

        if bio.get('pct_gordura') is not None:
            df.at[idx, 'Gordura_Corporal_%'] = bio['pct_gordura']
            df.at[idx, 'PctGordura_CSV'] = bio['pct_gordura'] if bio.get('pct_origem') == 'CSV' else np.nan
        else:
            df.at[idx, 'Gordura_Corporal_%'] = np.nan

        if bio.get('massa_gorda') is not None:
            df.at[idx, 'Massa_Gorda_kg'] = bio['massa_gorda']
        if bio.get('massa_magra') is not None:
            df.at[idx, 'Massa_Magra_kg'] = bio['massa_magra']

        if bio.get('massa_muscular') is not None:
            df.at[idx, 'Massa_Muscular_Estimada_kg'] = bio['massa_muscular']
            df.at[idx, 'Massa_Muscular_Origem'] = bio.get('massa_muscular_origem', '')
        df.at[idx, 'Bioimpedancia_Origem'] = bio.get('pct_gordura_origem', '')

        gordura_val = df.at[idx, 'Gordura_Corporal_%']
        idade_val = df.at[idx, 'Idade']
        if pd.notna(gordura_val) and pd.notna(idade_val):
            df.at[idx, 'Classificacao_Gordura'] = classif_gordura(gordura_val, idade_val)
        else:
            df.at[idx, 'Classificacao_Gordura'] = "Indefinido"

        imc_val = df.at[idx, 'IMC']
        imc_class = classif_imc(imc_val) if pd.notna(imc_val) else "Indefinido"
        gordura_class = df.at[idx, 'Classificacao_Gordura']
        df.at[idx, 'Estado_Fisico'] = estado_fisico(imc_class, gordura_class)

    return df

# =============================================
# CARTÕES (JSON)
# =============================================
def carregar_cartoes_json(categoria):
    caminho = {
        "profissional": CAMINHO_CARTOES_PROFISSIONAL, "sub15": CAMINHO_CARTOES_SUB15,
        "sub17": CAMINHO_CARTOES_SUB17,
        "comissao_profissional": CAMINHO_CARTOES_COMISSAO_PROFISSIONAL,
        "comissao_sub15": CAMINHO_CARTOES_COMISSAO_SUB15,
        "comissao_sub17": CAMINHO_CARTOES_COMISSAO_SUB17,
    }.get(categoria)
    if not caminho or not os.path.exists(caminho):
        return inicializar_cartoes_por_csvs(categoria, {})
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            cartoes = ordenar_historico_cartoes(dados.get('cartoes', {}))
            return cartoes, dados.get('datas_globais', {})
    except Exception as e:
        print(f"Erro ao carregar JSON: {e}")
        return {}, {}

def salvar_cartoes_json(cartoes, categoria, datas_globais=None):
    caminho = {
        'profissional': CAMINHO_CARTOES_PROFISSIONAL, 'sub15': CAMINHO_CARTOES_SUB15,
        'sub17': CAMINHO_CARTOES_SUB17,
        'comissao_profissional': CAMINHO_CARTOES_COMISSAO_PROFISSIONAL,
        'comissao_sub15': CAMINHO_CARTOES_COMISSAO_SUB15,
        'comissao_sub17': CAMINHO_CARTOES_COMISSAO_SUB17,
    }.get(categoria, os.path.join(DATA_DIR, f"cartoes_{categoria}.json"))
    cartoes = ordenar_historico_cartoes(cartoes)
    dados = {'cartoes': cartoes}
    if datas_globais and isinstance(datas_globais, dict):
        dados_serializaveis = {}
        for id_jogador, lista_datas in datas_globais.items():
            if isinstance(lista_datas, (list, tuple)):
                dados_serializaveis[id_jogador] = [
                    d.strftime("%d/%m/%Y") if hasattr(d, 'strftime') else str(d)
                    for d in lista_datas
                ]
            else:
                dados_serializaveis[id_jogador] = str(lista_datas)
        dados['datas_globais'] = dados_serializaveis
    else:
        dados['datas_globais'] = {}
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

def jogador_suspenso(nome, cartoes):
    if nome not in cartoes:
        return False
    return cartoes[nome].get('suspenso_proxima', False)

def inicializar_cartoes_por_df(df, categoria, canonico_para_ogol_id=None):
    if df.empty:
        return {}, {}
    df = df.sort_values('data_jogo', ascending=True)
    df_crono = carregar_cronograma(categoria.capitalize())
    if not df_crono.empty and 'data' in df_crono.columns:
        df_crono['data'] = pd.to_datetime(df_crono['data'], errors='coerce')
        datas_cronograma = sorted(df_crono['data'].dropna().dt.strftime('%Y-%m-%d').tolist())
    else:
        datas_cronograma = []
    cartoes, datas_globais, jogador_datas = {}, {}, {}
    for _, row in df.iterrows():
        nome = row.get('jogador') or row.get('nome_completo')
        if pd.isna(nome) or str(nome).strip() == '':
            continue
        nome = str(nome).strip()
        data_raw = row.get('data_jogo') or row.get('data')
        if data_raw:
            try:
                if isinstance(data_raw, pd.Timestamp):
                    data = data_raw.strftime('%Y-%m-%d')
                elif '/' in str(data_raw):
                    data = datetime.strptime(str(data_raw).strip(), "%d/%m/%Y").strftime('%Y-%m-%d')
                else:
                    data = pd.to_datetime(data_raw, dayfirst=True).strftime('%Y-%m-%d')
            except:
                data = str(data_raw).strip()
            if nome not in jogador_datas:
                jogador_datas[nome] = set()
            jogador_datas[nome].add(data)
        if nome not in cartoes:
            id_ogol = row.get('id_ogol_jogador')
            if pd.isna(id_ogol):
                id_ogol = None
            else:
                try:
                    id_ogol = str(int(float(id_ogol))) if not pd.isna(id_ogol) else None
                except:
                    id_ogol = None
            cartoes[nome] = {'amarelos': 0, 'vermelho': False, 'suspenso_proxima': False,
                              'historico': [], 'id_ogol': id_ogol,
                              'contador_amarelos_desde_reset': 0,
                              'suspensoes_cumpridas': 0, 'data_suspensao': None}
        adversario = row.get('adversario', 'N/I')
        competicao = row.get('Competicao', '')
        fase = row.get('Fase', '')
        amarelos = int(row.get('cartoes_amarelos', 0))
        vermelhos = int(row.get('cartoes_vermelhos', 0))
        if amarelos > 0:
            for _ in range(amarelos):
                cartoes[nome]['historico'].append({
                    'data': data, 'adversario': adversario, 'cor': 'amarelo',
                    'terceiro_amarelo': False, 'suspenso_causada': False,
                    'suspenso_cumprida': False, 'competicao': competicao, 'fase': fase})
                cartoes[nome]['contador_amarelos_desde_reset'] += 1
                if cartoes[nome]['contador_amarelos_desde_reset'] >= 3:
                    if cartoes[nome]['historico']:
                        cartoes[nome]['historico'][-1]['terceiro_amarelo'] = True
                        cartoes[nome]['historico'][-1]['suspenso_causada'] = True
                    cartoes[nome]['suspenso_proxima'] = True
                    cartoes[nome]['data_suspensao'] = data
        if vermelhos > 0:
            for _ in range(vermelhos):
                cartoes[nome]['vermelho'] = True
                cartoes[nome]['historico'].append({
                    'data': data, 'adversario': adversario, 'cor': 'vermelho',
                    'terceiro_amarelo': False, 'suspenso_causada': True,
                    'suspenso_cumprida': False, 'competicao': competicao, 'fase': fase})
                cartoes[nome]['suspenso_proxima'] = True
                cartoes[nome]['contador_amarelos_desde_reset'] = 0
                cartoes[nome]['data_suspensao'] = data
        cartoes[nome]['amarelos'] = cartoes[nome]['contador_amarelos_desde_reset']
        if cartoes[nome]['vermelho']:
            cartoes[nome]['suspenso_proxima'] = True
        id_ogol = cartoes[nome]['id_ogol']
        if id_ogol:
            if id_ogol not in datas_globais:
                datas_globais[id_ogol] = []
            if data not in datas_globais[id_ogol]:
                datas_globais[id_ogol].append(data)
    hoje = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    for nome, dados in cartoes.items():
        if not dados.get('suspenso_proxima', False):
            continue
        data_susp = dados.get('data_suspensao')
        if not data_susp:
            continue
        try:
            dt_susp = datetime.strptime(data_susp, "%Y-%m-%d").date()
        except:
            continue
        data_proximo_jogo = None
        competicao_susp, fase_susp = '', ''
        if datas_cronograma:
            datas_futuras = [d for d in datas_cronograma if d > data_susp]
            if datas_futuras:
                data_proximo_jogo_str = datas_futuras[0]
                data_proximo_jogo = datetime.strptime(data_proximo_jogo_str, "%Y-%m-%d").date()
                if df_crono is not None and not df_crono.empty:
                    jogos_prox = df_crono[df_crono['data'].dt.strftime('%Y-%m-%d') == data_proximo_jogo_str]
                    if not jogos_prox.empty:
                        competicao_susp = jogos_prox.iloc[0].get('competicao', '')
                        fase_susp = jogos_prox.iloc[0].get('fase', '')
        if data_proximo_jogo is None:
            data_proximo_jogo = dt_susp + timedelta(days=7)
        if data_proximo_jogo < hoje:
            data_str_prox = data_proximo_jogo.strftime("%Y-%m-%d")
            if data_str_prox not in jogador_datas.get(nome, set()):
                cartoes[nome]['historico'].append({
                    'data': data_str_prox,
                    'adversario': 'Suspensão cumprida (não jogou)',
                    'cor': 'suspensao_cumprida', 'terceiro_amarelo': False,
                    'suspenso_causada': False, 'suspenso_cumprida': True,
                    'competicao': competicao_susp, 'fase': fase_susp,
                    'observacao': f"Suspensão cumprida em {data_str_prox}"})
                cartoes[nome]['contador_amarelos_desde_reset'] = 0
                cartoes[nome]['amarelos'] = 0
                cartoes[nome]['suspenso_proxima'] = False
                cartoes[nome]['suspensoes_cumpridas'] = 0
                cartoes[nome]['data_suspensao'] = None
    cartoes = ordenar_historico_cartoes(cartoes)
    salvar_cartoes_json(cartoes, categoria, datas_globais)
    return cartoes, datas_globais

def inicializar_cartoes_por_csvs(categoria, canonico_para_ogol_id):
    return inicializar_cartoes_por_df(carregar_estatisticas_partidas(categoria), categoria, canonico_para_ogol_id)

def inicializar_cartoes_comissao(categoria, df_comissao):
    if categoria == 'comissao_profissional':
        pasta = PASTA_ESTATISTICAS_COMISSAO_PROFISSIONAL
    elif categoria == 'comissao_sub15':
        pasta = PASTA_ESTATISTICAS_COMISSAO_SUB15
    elif categoria == 'comissao_sub17':
        pasta = PASTA_ESTATISTICAS_COMISSAO_SUB17
    else:
        return {}, []
    if not pasta or not os.path.exists(pasta):
        return {}, []
    lista_arquivos = [os.path.join(pasta, f) for f in os.listdir(pasta)
                      if f.endswith('.csv') and f.startswith('jogo_')]
    if not lista_arquivos:
        return {}, []
    arquivos_com_data = []
    for arq in lista_arquivos:
        data_jogo = extrair_data_jogo(arq) or datetime.fromtimestamp(os.path.getmtime(arq))
        arquivos_com_data.append((data_jogo, arq))
    arquivos_com_data.sort(key=lambda x: x[0])
    cartoes = {}
    for data_jogo, arq in arquivos_com_data:
        try:
            df = pd.read_csv(arq, sep=';', encoding='utf-8-sig', on_bad_lines='skip')
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            adversario = df['adversario'].iloc[0] if 'adversario' in df.columns else 'Desconhecido'
            for _, row in df.iterrows():
                nome_raw = row.get('nome') or row.get('membro') or row.get('comissao') or row.get('staff')
                if pd.isna(nome_raw):
                    continue
                nome = mapear_nome_para_canonico(nome_raw)
                amarelos = int(row.get('cartoes_amarelos', 0))
                vermelhos = int(row.get('cartoes_vermelhos', 0))
                if amarelos == 0 and vermelhos == 0:
                    continue
                if nome not in cartoes:
                    cartoes[nome] = {'amarelos': 0, 'vermelho': False,
                                      'suspenso_proxima': False, 'historico': []}
                for _ in range(amarelos):
                    cartoes[nome]['amarelos'] += 1
                    terceiro = cartoes[nome]['amarelos'] >= 3
                    if terceiro:
                        cartoes[nome]['suspenso_proxima'] = True
                    cartoes[nome]['historico'].append({
                        'data': data_jogo.strftime("%d/%m/%Y"), 'adversario': adversario,
                        'competicao': '', 'fase': '', 'cor': 'amarelo',
                        'terceiro_amarelo': terceiro, 'suspenso_causada': terceiro,
                        'suspenso_cumprida': False})
                for _ in range(vermelhos):
                    cartoes[nome]['vermelho'] = True
                    cartoes[nome]['suspenso_proxima'] = True
                    cartoes[nome]['historico'].append({
                        'data': data_jogo.strftime("%d/%m/%Y"), 'adversario': adversario,
                        'competicao': '', 'fase': '', 'cor': 'vermelho',
                        'terceiro_amarelo': False, 'suspenso_causada': True,
                        'suspenso_cumprida': False})
        except Exception as e:
            st.warning(f"Erro ao processar {arq}: {e}")
    cartoes = ordenar_historico_cartoes(cartoes)
    salvar_cartoes_json(cartoes, categoria, None)
    return cartoes, []

# =============================================
# ESTATÍSTICAS DE PARTIDAS
# =============================================
def listar_arquivos_estatisticas(categoria="Profissional") -> List[str]:
    pasta = {"Profissional": PASTA_ESTATISTICAS_PROFISSIONAL,
             "Sub-15": PASTA_ESTATISTICAS_SUB15,
             "Sub-17": PASTA_ESTATISTICAS_SUB17}.get(categoria, PASTA_ESTATISTICAS_PROFISSIONAL)
    if not os.path.exists(pasta):
        return []
    return [os.path.join(pasta, f) for f in os.listdir(pasta)
            if f.endswith('.csv') and f.startswith('jogo_')]

def carregar_estatisticas_partidas(categoria="Profissional") -> pd.DataFrame:
    arquivo = {"Profissional": "estatisticas_jogadores_profissional_2026.csv",
               "Sub-15": "estatisticas_jogadores_sub15_2026.csv",
               "Sub-17": "estatisticas_jogadores_sub17_2026.csv"}.get(categoria)
    if not arquivo:
        return pd.DataFrame()
    pasta = {"Profissional": PASTA_ESTATISTICAS_PROFISSIONAL,
             "Sub-15": PASTA_ESTATISTICAS_SUB15,
             "Sub-17": PASTA_ESTATISTICAS_SUB17}.get(categoria, PASTA_ESTATISTICAS_PROFISSIONAL)
    caminho = os.path.join(pasta, arquivo)
    if not os.path.exists(caminho):
        fallback = os.path.join(DATA_DIR, arquivo)
        if os.path.exists(fallback):
            caminho = fallback
        else:
            return pd.DataFrame()
    try:
        df = pd.read_csv(caminho, sep=';', encoding='utf-8-sig')
        if 'data_jogo' in df.columns:
            df['data_jogo'] = pd.to_datetime(df['data_jogo'], dayfirst=True, errors='coerce')
        for col in ['fase', 'competicao', 'adversario', 'jogador']:
            if col in df.columns:
                df[col] = df[col].astype(str)
        return sanitizar_dataframe(df)
    except Exception as e:
        print(f"Erro ao carregar {caminho}: {e}")
        return pd.DataFrame()

def precomputar_scores_posicionais(df, df_stats_partidas):
    """Agrega estatísticas (starts, jogos_90min, minutos_totais_partidas).
    Cria colunas ausentes com 0 e deriva de 'titular'/'minutos' quando possível."""
    colunas_alvo = ['starts', 'jogos_90min', 'minutos_totais_partidas']

    if df_stats_partidas is None or df_stats_partidas.empty:
        for col in colunas_alvo:
            if col not in df.columns:
                df[col] = 0
        return df

    df_merged = df.copy()
    if 'apelido' in df_merged.columns:
        df_merged['nome_canonico'] = df_merged['apelido'].apply(mapear_nome_para_canonico)
    elif 'nome_completo' in df_merged.columns:
        df_merged['nome_canonico'] = df_merged['nome_completo'].apply(mapear_nome_para_canonico)
    else:
        df_merged['nome_canonico'] = None

    df_stats = df_stats_partidas.copy()

    if 'minutos_totais' in df_stats.columns and 'minutos_totais_partidas' not in df_stats.columns:
        df_stats = df_stats.rename(columns={'minutos_totais': 'minutos_totais_partidas'})

    if 'jogador_canonico' not in df_stats.columns:
        if 'jogador' in df_stats.columns:
            df_stats['jogador_canonico'] = df_stats['jogador'].apply(mapear_nome_para_canonico)
        elif 'nome_completo' in df_stats.columns:
            df_stats['jogador_canonico'] = df_stats['nome_completo'].apply(mapear_nome_para_canonico)
        elif 'apelido' in df_stats.columns:
            df_stats['jogador_canonico'] = df_stats['apelido'].apply(mapear_nome_para_canonico)
        else:
            for col in colunas_alvo:
                if col not in df_merged.columns:
                    df_merged[col] = 0
            return sanitizar_dataframe(df_merged)

    if 'starts' not in df_stats.columns:
        if 'titular' in df_stats.columns:
            df_stats['starts'] = pd.to_numeric(df_stats['titular'], errors='coerce').fillna(0)
        else:
            df_stats['starts'] = 0

    if 'jogos_90min' not in df_stats.columns:
        if 'minutos' in df_stats.columns:
            minutos_num = pd.to_numeric(df_stats['minutos'], errors='coerce').fillna(0)
            df_stats['jogos_90min'] = (minutos_num >= 90).astype(int)
        else:
            df_stats['jogos_90min'] = 0

    if 'minutos_totais_partidas' not in df_stats.columns:
        if 'minutos' in df_stats.columns:
            df_stats['minutos_totais_partidas'] = pd.to_numeric(
                df_stats['minutos'], errors='coerce').fillna(0)
        else:
            df_stats['minutos_totais_partidas'] = 0

    colunas_seguras = ['jogador_canonico'] + colunas_alvo
    df_stats = df_stats[colunas_seguras].copy()

    for col in colunas_alvo:
        df_stats[col] = pd.to_numeric(df_stats[col], errors='coerce').fillna(0)

    df_stats = (df_stats
                .groupby('jogador_canonico', as_index=False)[colunas_alvo]
                .sum())

    df_merged = df_merged.merge(
        df_stats, left_on='nome_canonico', right_on='jogador_canonico', how='left'
    )
    df_merged.drop(columns=['jogador_canonico', 'nome_canonico'],
                   errors='ignore', inplace=True)

    for col in colunas_alvo:
        if col in df_merged.columns:
            df_merged[col] = df_merged[col].fillna(0).astype(int)
        else:
            df_merged[col] = 0

    return sanitizar_dataframe(df_merged)

# =============================================
# FORMAÇÃO E ESCALAÇÃO
# =============================================
def interpretar_formacao(formacao_str):
    if not formacao_str or not isinstance(formacao_str, str):
        return None, None, None, None
    partes = formacao_str.split('-')
    if len(partes) < 3:
        return None, None, None, None
    try:
        nums = [int(p) for p in partes]
        if sum(nums) != 10:
            return None, None, None, None
        defensores = nums[0]
        atacantes = nums[-1]
        meio_campistas = sum(nums[1:-1])
        posicoes = [('Goleiro', 'Goleiro')]
        for i in range(defensores):
            posicoes.append((f'Defensor {i+1}', 'Defensor'))
        for i in range(meio_campistas):
            posicoes.append((f'Meio-Campista {i+1}', 'Meio-Campo'))
        for i in range(atacantes):
            posicoes.append((f'Atacante {i+1}', 'Atacante'))
        return defensores, meio_campistas, atacantes, posicoes
    except:
        return None, None, None, None

def obter_jogadores_para_posicao(df, pos_tipo, excluidos, cartoes, incluir_lesionados=False):
    candidatos = df.copy()
    if pos_tipo == 'Goleiro':
        candidatos = candidatos[candidatos['Posicao_Principal'] == 'Goleiro']
    else:
        candidatos = candidatos[~candidatos['Posicao_Principal'].isin(['Goleiro'])]
    candidatos = candidatos[~candidatos['nome_completo'].isin(excluidos)]
    candidatos = candidatos[~candidatos['nome_completo'].apply(
        lambda x: jogador_suspenso(mapear_nome_para_canonico(x), cartoes))]
    if not incluir_lesionados and 'lesionado' in candidatos.columns:
        candidatos = candidatos[~candidatos['lesionado']]
    return candidatos

def obter_atributos_chave(posicao):
    mapa = {
        'Goleiro': ['reflexos', 'defesas_goleiro', 'jogo_aereo_goleiro', 'comando_area', 'saida_gol'],
        'Zagueiro': ['desarme', 'marcacao', 'cabecada', 'forca_fisica', 'antecipacao', 'posicionamento'],
        'Lateral': ['cruzamentos', 'drible', 'passe', 'velocidade_maxima', 'aceleracao', 'resistencia'],
        'Lateral Direito': ['cruzamentos', 'drible', 'passe', 'velocidade_maxima', 'aceleracao', 'resistencia'],
        'Lateral Esquerdo': ['cruzamentos', 'drible', 'passe', 'velocidade_maxima', 'aceleracao', 'resistencia'],
        'Volante': ['desarme', 'marcacao', 'passe', 'posicionamento', 'intensidade_trabalho', 'visao_jogo'],
        'Meia': ['visao_jogo', 'passe', 'criatividade', 'tecnica', 'primeiro_controle', 'chutes_longe'],
        'Meia-Central': ['visao_jogo', 'passe', 'criatividade', 'tecnica', 'desarme', 'posicionamento'],
        'Meia-Atacante': ['visao_jogo', 'passe', 'criatividade', 'tecnica', 'primeiro_controle', 'finalizacao'],
        'Ponta': ['drible', 'aceleracao', 'velocidade_maxima', 'cruzamentos', 'tecnica', 'finalizacao'],
        'Ponta Direita': ['drible', 'aceleracao', 'velocidade_maxima', 'cruzamentos', 'tecnica', 'finalizacao'],
        'Ponta Esquerda': ['drible', 'aceleracao', 'velocidade_maxima', 'cruzamentos', 'tecnica', 'finalizacao'],
        'Centroavante': ['finalizacao', 'cabecada', 'primeiro_controle', 'composicao', 'forca_fisica', 'movimentacao_sem_bola'],
        'Segundo Atacante': ['movimentacao_sem_bola', 'primeiro_controle', 'tecnica', 'visao_jogo', 'passe', 'drible'],
        'Defensor': ['desarme', 'marcacao', 'cabecada', 'forca_fisica', 'antecipacao', 'posicionamento'],
        'Meio-Campo': ['passe', 'visao_jogo', 'criatividade', 'desarme', 'intensidade_trabalho'],
    }
    return mapa.get(posicao, ['Rating_Geral_FM26'])

# =============================================
# AUTENTICAÇÃO DE USUÁRIOS
# =============================================
ARQUIVO_USUARIOS = "usuarios.json"
ADMIN_FIXOS = ["Guibfpinto", "Ricardosantosr", "YupiSilva", "AdautoMenegussi", "Asamoah",
               "Nanico", "MaryaEduarda", "KarenLoureiro", "FabianoEller", "Delei"]
SENHAS_FIXAS = {
    "Guibfpinto": "@W.d06302005", "Ricardosantosr": "@R.s02011991",
    "YupiSilva": "@J.s10021989", "AdautoMenegussi": "@A.m13071966",
    "Asamoah": "@M.v24061989", "Nanico": "@W.s0511",
    "MaryaEduarda": "@M.e12062002", "KarenLoureiro": "@K.l04082000",
    "FabianoEller": "@F.e1977", "Delei": "Delei20031966"
}

def carregar_usuarios():
    if not os.path.exists(ARQUIVO_USUARIOS):
        usuarios = {}
        for admin in ADMIN_FIXOS:
            senha = SENHAS_FIXAS.get(admin)
            if senha:
                hash_admin = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                usuarios[admin] = {"senha_hash": hash_admin, "is_admin": True}
        with open(ARQUIVO_USUARIOS, 'w', encoding='utf-8') as f:
            json.dump(usuarios, f, indent=2, ensure_ascii=False)
        return usuarios
    try:
        with open(ARQUIVO_USUARIOS, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        usuarios = {}
        for usuario, valor in dados.items():
            if isinstance(valor, dict):
                usuarios[usuario] = valor
            else:
                usuarios[usuario] = {"senha_hash": valor, "is_admin": usuario in ADMIN_FIXOS}
        return usuarios
    except Exception as e:
        print(f"Erro ao carregar usuários: {e}")
        return {}

def salvar_usuarios(usuarios):
    with open(ARQUIVO_USUARIOS, 'w', encoding='utf-8') as f:
        json.dump(usuarios, f, indent=2, ensure_ascii=False)

def autenticar_usuario(usuario, senha):
    if usuario in ADMIN_FIXOS:
        senha_correta = SENHAS_FIXAS.get(usuario)
        if senha_correta and bcrypt.checkpw(senha.encode('utf-8'),
                                            bcrypt.hashpw(senha_correta.encode('utf-8'),
                                                          bcrypt.gensalt())):
            return True, True
    usuarios = carregar_usuarios()
    if usuario not in usuarios:
        return False, False
    dados = usuarios[usuario]
    autenticado = bcrypt.checkpw(senha.encode('utf-8'), dados["senha_hash"].encode('utf-8'))
    return autenticado, dados.get("is_admin", False)

def listar_usuarios():
    return list(carregar_usuarios().keys())

def adicionar_usuario(usuario, senha, is_admin=False):
    usuarios = carregar_usuarios()
    if usuario in usuarios:
        return False
    hash_novo = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    usuarios[usuario] = {"senha_hash": hash_novo, "is_admin": is_admin}
    salvar_usuarios(usuarios)
    return True

def remover_usuario(usuario):
    if usuario in ADMIN_FIXOS:
        return False
    usuarios = carregar_usuarios()
    if usuario in usuarios:
        del usuarios[usuario]
        salvar_usuarios(usuarios)
        return True
    return False

def promover_admin(usuario):
    if usuario in ADMIN_FIXOS:
        return True
    usuarios = carregar_usuarios()
    if usuario not in usuarios:
        return False
    usuarios[usuario]["is_admin"] = True
    salvar_usuarios(usuarios)
    return True

def rebaixar_admin(usuario):
    if usuario in ADMIN_FIXOS:
        return False
    usuarios = carregar_usuarios()
    if usuario not in usuarios:
        return False
    usuarios[usuario]["is_admin"] = False
    salvar_usuarios(usuarios)
    return True

def usuario_eh_admin(usuario):
    if usuario in ADMIN_FIXOS:
        return True
    usuarios = carregar_usuarios()
    return usuarios.get(usuario, {}).get("is_admin", False)

# =============================================
# RELATÓRIOS E EXPORTAÇÃO
# =============================================
def gerar_relatorio_completo_texto(df, nome_categoria):
    if df is None or df.empty:
        return f"Sem dados para {nome_categoria}"
    total = len(df)
    idade_media = df['Idade'].mean() if 'Idade' in df.columns else 0
    altura_media = df['altura_cm'].mean() if 'altura_cm' in df.columns else 0
    peso_media = df['peso_kg'].mean() if 'peso_kg' in df.columns else 0
    imc_media = df['IMC'].mean() if 'IMC' in df.columns else 0
    gordura_media = df['Gordura_Corporal_%'].mean() if 'Gordura_Corporal_%' in df.columns else 0
    massa_magra_media = df['Massa_Magra_kg'].mean() if 'Massa_Magra_kg' in df.columns else 0
    massa_gorda_media = peso_media - massa_magra_media if peso_media and massa_magra_media else 0
    massa_muscular_media = df['Massa_Muscular_Estimada_kg'].mean() if 'Massa_Muscular_Estimada_kg' in df.columns else 0
    ca_media = df['habilidade_atual'].mean() if 'habilidade_atual' in df.columns else 0
    pa_media = df['habilidade_potencial'].mean() if 'habilidade_potencial' in df.columns else 0
    rating_medio = df['Rating_Geral_FM26'].mean() if 'Rating_Geral_FM26' in df.columns else 0
    dist_posicao = df['Posicao_Principal'].value_counts() if 'Posicao_Principal' in df.columns else pd.Series()
    texto = f"""
RELATÓRIO COMPLETO - Linhares FC ({nome_categoria})
TEMPORADA: 2026
======================================================================

📊 ESTATÍSTICAS GERAIS:
• Total jogadores: {total}
• Idade média: {idade_media:.1f} anos
• Altura média: {altura_media:.1f} cm
• Peso médio: {peso_media:.1f} kg
• IMC médio: {imc_media:.1f}

💧 PERCENTUAIS DE GORDURA:
• Média geral (utilizada): {gordura_media:.1f}%
• Massa magra média: {massa_magra_media:.1f} kg
• Massa gorda média: {massa_gorda_media:.1f} kg
• Massa muscular média (geral): {massa_muscular_media:.1f} kg

🎮 DADOS FM26:
• CA médio: {ca_media:.1f}
• PA médio: {pa_media:.1f}
• Rating geral médio: {rating_medio:.1f}

⚽ DISTRIBUIÇÃO POR POSIÇÃO PRINCIPAL:
"""
    for posicao, qtd in dist_posicao.items():
        pct = (qtd / total) * 100 if total > 0 else 0
        texto += f"• {posicao}: {qtd} jogador(es) ({pct:.1f}%)\n"
    return texto

def exportar_para_excel(df, nome_categoria, caminho_arquivo):
    try:
        df.to_excel(caminho_arquivo, index=False, engine='openpyxl')
        return True
    except Exception as e:
        print(f"Erro na exportação: {e}")
        return False

def exportar_para_powerbi(df, nome_categoria, caminho_json_fotos, pasta_fotos, caminho_arquivo):
    return exportar_para_excel(df, nome_categoria, caminho_arquivo)

# =============================================
# CORREÇÕES DE NOMES DE TIMES
# =============================================
CORRECOES_NOMES_TIMES = {
    "Serra Talhada": "Serra-ES",
    "Sport Brasil ES": "Sport Brasil Capixaba",
}

def corrigir_nome_time(nome):
    return CORRECOES_NOMES_TIMES.get(nome, nome)

# =============================================
# FUNÇÕES DA FASTAPI (USANDO BANCO LOCAL)
# =============================================
def _chamar_api(endpoint, params=None, tentativa=1):
    return None

def verificar_jogo_ao_vivo(team_id=None):
    conn = sqlite3.connect('meu_futebol.db')
    cursor = conn.cursor()
    query = "SELECT id FROM jogos WHERE status IN ('1H', '2H', 'HT', 'ET', 'P')"
    params = []
    if team_id:
        query += " AND (time_casa_id = ? OR time_fora_id = ?)"
        params.extend([team_id, team_id])
    query += " LIMIT 1"
    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def obter_detalhes_jogo(fixture_id):
    conn = sqlite3.connect('meu_futebol.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT j.*, tc.nome AS time_casa_nome, tf.nome AS time_fora_nome, v.nome AS estadio
        FROM jogos j LEFT JOIN times tc ON j.time_casa_id = tc.id
        LEFT JOIN times tf ON j.time_fora_id = tf.id
        LEFT JOIN venues v ON j.venue_id = v.id WHERE j.id = ?
    """, (fixture_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    dados = dict(row)
    return {
        "fixture": {"id": dados["id"], "date": dados.get("data_hora", ""),
                    "status": {"short": dados.get("status", "NS")},
                    "venue": {"name": dados.get("estadio", "Estádio")},
                    "referee": dados.get("arbitro", "Não informado")},
        "teams": {"home": {"id": dados["time_casa_id"], "name": dados.get("time_casa_nome", "Casa")},
                  "away": {"id": dados["time_fora_id"], "name": dados.get("time_fora_nome", "Fora")}},
        "goals": {"home": dados.get("gols_casa", 0), "away": dados.get("gols_fora", 0)}
    }

def obter_eventos_jogo(fixture_id):
    conn = sqlite3.connect('meu_futebol.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.*, el.nome AS jogador_nome, el.apelido AS jogador_apelido
        FROM eventos e LEFT JOIN elenco el ON e.jogador_id = el.id
        WHERE e.jogo_id = ? ORDER BY e.tempo ASC
    """, (fixture_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"time": {"elapsed": r["tempo"]}, "type": r["tipo"], "detail": r["detalhes"],
             "player": {"name": r["jogador_nome"] or r["jogador_apelido"] or "Desconhecido"},
             "team": {"name": ""}} for r in rows]

def obter_estatisticas_jogo(fixture_id): return []
def obter_lineups_completos(fixture_id): return []
def obter_players_stats(fixture_id): return []

def buscar_jogos_por_competicao(league_id, season_id, team_id, data_inicio, data_fim):
    return []

def gerar_relatorio_excel(fixture_id, time_casa_titulares=None, time_casa_reservas=None):
    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Relatório"
        ws['A1'] = f"Relatório da Partida {fixture_id}"
        os.makedirs(RELATORIOS_DIR, exist_ok=True)
        caminho = os.path.join(RELATORIOS_DIR,
                               f"relatorio_{fixture_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        wb.save(caminho)
    except Exception as e:
        print(f"⚠️ Erro ao gerar relatório: {e}")

def formatar_planilha(ws, titulo):
    ws.title = titulo
    for col in ws.columns:
        max_length = max((len(str(cell.value)) for cell in col if cell.value), default=0)
        adjusted_width = min(max_length + 2, 50)
        if col:
            ws.column_dimensions[get_column_letter(col[0].column)].width = adjusted_width

def obter_historico_clubes(jogador_row):
    historico = jogador_row.get('historico')
    if pd.isna(historico) or not historico:
        return "Nenhum histórico de clubes registrado."
    return str(historico).strip()

def formatar_cartoes(cartoes: dict, nome_jogador: str = None) -> str:
    if not cartoes:
        return "Nenhum dado de cartões disponível."
    if nome_jogador:
        dados = None
        for chave, valor in cartoes.items():
            if chave.lower() == nome_jogador.lower() or mapear_nome_para_canonico(chave) == nome_jogador:
                dados = valor
                break
            if chave == nome_jogador:
                dados = valor
                break
        if not dados:
            return f"Jogador '{nome_jogador}' não encontrado."
        linhas = [
            f"📋 **Cartões de {nome_jogador}**",
            f"  🟨 Amarelos atuais: {dados.get('amarelos', 0)}",
            f"  🟥 Vermelho direto: {'Sim' if dados.get('vermelho') else 'Não'}",
            f"  ⚠️ Suspenso próximo jogo: {'Sim' if dados.get('suspenso_proxima') else 'Não'}",
            ""
        ]
        historico = dados.get('historico', [])
        for ev in sorted(historico, key=lambda x: x['data'], reverse=True)[-8:]:
            emoji = {"amarelo": "🟨", "vermelho": "🟥", "suspensao_cumprida": "🔄"}.get(ev.get('cor'), "ℹ️")
            linhas.append(f"    {emoji} {ev.get('data')} vs {ev.get('adversario')} - {ev.get('cor')}")
        return "\n".join(linhas)
    else:
        linhas = ["📊 **RESUMO DE CARTÕES**", "",
                  f"{'Jogador':<25} {'Atuais':<10} {'Vermelho':<10} {'Suspenso':<10}", "-" * 60]
        for jog, dados in sorted(cartoes.items()):
            linhas.append(f"{jog:<25} {dados.get('amarelos', 0):<10} "
                          f"{'Sim' if dados.get('vermelho') else 'Não':<10} "
                          f"{'Sim' if dados.get('suspenso_proxima') else 'Não':<10}")
        return "\n".join(linhas)

# =============================================
# CONTROLE DE REINICIALIZAÇÃO
# =============================================
ARQUIVO_CONTROLE_REINICIALIZACAO = os.path.join(DATA_DIR, "ultima_reinicializacao.json")

def _obter_data_brt_atual() -> str:
    return datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d")

def _carregar_ultima_reinicializacao() -> Optional[str]:
    if not os.path.exists(ARQUIVO_CONTROLE_REINICIALIZACAO):
        return None
    try:
        with open(ARQUIVO_CONTROLE_REINICIALIZACAO, 'r', encoding='utf-8') as f:
            return json.load(f).get('data')
    except:
        return None

def _salvar_ultima_reinicializacao(data: str):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(ARQUIVO_CONTROLE_REINICIALIZACAO, 'w', encoding='utf-8') as f:
        json.dump({'data': data}, f, ensure_ascii=False, indent=2)

def verificar_e_reinicializar_cartoes(categoria: str) -> bool:
    data_atual = _obter_data_brt_atual()
    if _carregar_ultima_reinicializacao() != data_atual:
        chave = {"Profissional": "profissional", "Sub-15": "sub15",
                 "Sub-17": "sub17"}.get(categoria, categoria.lower())
        inicializar_cartoes_por_csvs(chave, {})
        _salvar_ultima_reinicializacao(data_atual)
        return True
    return False

# =============================================
# STUBS
# =============================================
def exportar_escalacao_excel(df, nome_arquivo="escalacao.xlsx"):
    try:
        df.to_excel(nome_arquivo, index=False, engine='openpyxl')
        return True
    except: return False

def exportar_escalacao_pdf(df, nome_arquivo="escalacao.pdf"): return True

def gerar_relatorio_diretoria(df, categoria):
    if df is None or df.empty:
        return f"Sem dados – {categoria}"
    return f"RELATÓRIO DIRETORIA – {categoria}\nTotal: {len(df)}"

def gerar_relatorio_jogador(row, categoria):
    if row is None:
        return "Jogador não encontrado."
    return (f"RELATÓRIO – {categoria}\n"
            f"Nome: {row.get('nome_completo', 'N/I')}\n"
            f"Posição: {row.get('Posicao_Principal', 'N/I')}\n"
            f"Idade: {row.get('Idade', 'N/I')}\n"
            f"Rating: {row.get('Rating_Geral_FM26', 'N/I')}")

def gerar_relatorio_comissao(df, categoria):
    if df is None or df.empty:
        return f"Sem dados – {categoria}"
    texto = f"RELATÓRIO COMISSÃO – {categoria}\nTotal: {len(df)}\n"
    if 'cargo' in df.columns:
        for cargo, qtd in df['cargo'].value_counts().items():
            texto += f"  {cargo}: {qtd}\n"
    return texto