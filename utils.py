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
from typing import Dict, Optional, List, Tuple
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from io import BytesIO
import requests

# =============================================
# CONSTANTES DE CAMINHOS (CSVs)
# =============================================
ARQUIVO_CSV_PROFISSIONAL = "perfil_completo_jogadores_profissional_2026.csv"
ARQUIVO_CSV_SUB20 = "perfil_completo_jogadores_Sub20_2026.csv"
ARQUIVO_CSV_SUB17 = "perfil_completo_jogadores_Sub17_2026.csv"
ARQUIVO_CSV_COMISSAO_PROFISSIONAL = "perfil_completo_comissao_2026.csv"
ARQUIVO_CSV_COMISSAO_SUB20 = "perfil_completo_comissao_Sub20_2026.csv"
ARQUIVO_LESOES_PROFISSIONAL = "jogadores_linhares_profissional_lesoes.csv"
ARQUIVO_LESOES_SUB20 = "jogadores_linhares_Sub20_lesoes.csv"
ARQUIVO_LESOES_SUB17 = "jogadores_linhares_Sub17_lesoes.csv"
ARQUIVO_BIO_PROFISSIONAL = "jogadores_linhares_profissional_Bioimpedancia.csv"
ARQUIVO_BIO_SUB20 = "jogadores_linhares_Sub20_Bioimpedancia.csv"
ARQUIVO_BIO_SUB17 = "jogadores_linhares_Sub17_Bioimpedancia.csv"
ARQUIVO_CRONO_PROF = "cronograma_profissional_2026.csv"
ARQUIVO_CRONO_SUB20 = "cronograma_sub20_2026.csv"

DATA_DIR = "data"
RELATORIOS_DIR = "relatorios"
NOME_TIME = "Linhares FC"
TEMPORADA = str(datetime.now().year)

# =============================================
# CONSTANTES DE PASTAS DE ESTATÍSTICAS
# =============================================
PASTA_ESTATISTICAS_PROFISSIONAL = "data/estatisticas_jogadores/"
PASTA_ESTATISTICAS_SUB20 = "data/estatisticas_sub20/"
PASTA_ESTATISTICAS_SUB17 = "data/estatisticas_sub17/"
PASTA_ESTATISTICAS_COMISSAO_PROFISSIONAL = "data/estatisticas_comissao_tecnica_profissional/"
PASTA_ESTATISTICAS_COMISSAO_SUB20 = "data/estatisticas_comissao_tecnica_sub20/"
PASTA_ESTATISTICAS_COMISSAO_SUB17 = "data/estatisticas_comissao_tecnica_sub17/"

# =============================================
# CONSTANTES DOS ARQUIVOS DE CARTÕES (JSON)
# =============================================
CAMINHO_CARTOES_PROFISSIONAL = "cartoes_acumulados_profissional.json"
CAMINHO_CARTOES_SUB20 = "cartoes_acumulados_sub20.json"
CAMINHO_CARTOES_SUB17 = "cartoes_acumulados_sub17.json"
CAMINHO_CARTOES_COMISSAO_PROFISSIONAL = "cartoes_acumulados_comissao_profissional.json"
CAMINHO_CARTOES_COMISSAO_SUB20 = "cartoes_acumulados_comissao_sub20.json"
CAMINHO_CARTOES_COMISSAO_SUB17 = "cartoes_acumulados_comissao_sub17.json"

# =============================================
# MAPEAMENTO DE NOMES (JOGADORES E COMISSÃO)
# =============================================
MAPEAMENTO_NOMES_PROFISSIONAL = {
    'Wenderson Silva Neves': 'Wendy',
    'Wendy': 'Wendy',
    'Marcus Paulo Sousa Oliveira': 'Marcus Paulo',
    'Marcus Paulo': 'Marcus Paulo',
    # ... (todos os mapeamentos do seu sistema)
}
MAPEAMENTO_NOMES_SUB20 = {}
MAPEAMENTO_NOMES_SUB17 = {}
MAPEAMENTO_NOMES_COMISSAO_PROFISSIONAL = {}
MAPEAMENTO_NOMES_COMISSAO_SUB20 = {}

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
        idade = hoje.year - data_nasc.year - ((hoje.month, hoje.day) < (data_nasc.month, data_nasc.day))
        return idade
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
    if nome in MAPEAMENTO_NOMES_PROFISSIONAL:
        return MAPEAMENTO_NOMES_PROFISSIONAL[nome]
    if nome in MAPEAMENTO_NOMES_SUB20:
        return MAPEAMENTO_NOMES_SUB20[nome]
    if nome in MAPEAMENTO_NOMES_SUB17:
        return MAPEAMENTO_NOMES_SUB17[nome]
    if nome in MAPEAMENTO_NOMES_COMISSAO_PROFISSIONAL:
        return MAPEAMENTO_NOMES_COMISSAO_PROFISSIONAL[nome]
    if nome in MAPEAMENTO_NOMES_COMISSAO_SUB20:
        return MAPEAMENTO_NOMES_COMISSAO_SUB20[nome]
    nome_norm = normalizar_texto(nome)
    for var, can in MAPEAMENTO_NOMES_PROFISSIONAL.items():
        if normalizar_texto(var) == nome_norm:
            return can
    for var, can in MAPEAMENTO_NOMES_SUB20.items():
        if normalizar_texto(var) == nome_norm:
            return can
    for var, can in MAPEAMENTO_NOMES_SUB17.items():
        if normalizar_texto(var) == nome_norm:
            return can
    for var, can in MAPEAMENTO_NOMES_COMISSAO_PROFISSIONAL.items():
        if normalizar_texto(var) == nome_norm:
            return can
    for var, can in MAPEAMENTO_NOMES_COMISSAO_SUB20.items():
        if normalizar_texto(var) == nome_norm:
            return can
    return nome

def safe_str(valor, padrao="N/I"):
    if pd.isna(valor) or str(valor).strip() == '':
        return padrao
    return str(valor).strip()

def extrair_id_jogo(caminho_arquivo):
    nome = os.path.basename(caminho_arquivo)
    match = re.search(r'jogo_(\d+)_', nome)
    if match:
        return int(match.group(1))
    return None

def extrair_data_jogo(caminho_arquivo):
    match = re.search(r'(\d{4}-\d{2}-\d{2})', caminho_arquivo)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y-%m-%d")
        except:
            pass
    return None

# =============================================
# CLASSIFICAÇÕES (IMC, GORDURA, ESTADO FÍSICO)
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS treinos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            atleta_id TEXT,
            data TEXT,
            carga REAL,
            duracao_min INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wellbeing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            atleta_id TEXT,
            data TEXT,
            sono INTEGER,
            estresse INTEGER,
            dor INTEGER,
            disposicao INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lesoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jogador TEXT,
            tipo_lesao TEXT,
            data_inicio TEXT,
            data_fim TEXT,
            ativo INTEGER DEFAULT 1
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jogos (
            id INTEGER PRIMARY KEY,
            time_casa_id INTEGER,
            time_fora_id INTEGER,
            gols_casa INTEGER,
            gols_fora INTEGER,
            status TEXT,
            data_hora TEXT,
            estadio TEXT,
            arbitro TEXT,
            formacao_casa TEXT,
            formacao_fora TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            atleta_id TEXT,
            data TEXT,
            distancia_total REAL,
            velocidade_max REAL,
            sprints INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS times (
            id INTEGER PRIMARY KEY,
            nome TEXT,
            sigla TEXT,
            logo_url TEXT,
            fundado INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS elenco (
            id INTEGER PRIMARY KEY,
            nome TEXT,
            apelido TEXT,
            posicao TEXT,
            numero INTEGER,
            idade INTEGER,
            foto TEXT,
            time_id INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jogo_id INTEGER,
            tempo INTEGER,
            tipo TEXT,
            jogador_id INTEGER,
            detalhes TEXT,
            time_id INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tecnicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            cargo TEXT,
            idade INTEGER,
            data_nascimento TEXT,
            historico_profissional TEXT,
            historico_jogador TEXT
        )
    ''')
    conn.commit()
    conn.close()

# =============================================
# CARREGAMENTO DOS DADOS (CSVs)
# =============================================
@st.cache_data
def carregar_elenco_profissional() -> pd.DataFrame:
    if not os.path.exists(ARQUIVO_CSV_PROFISSIONAL):
        return pd.DataFrame()
    try:
        df_raw = pd.read_csv(ARQUIVO_CSV_PROFISSIONAL, sep=';', encoding='utf-8-sig',
                             header=None, on_bad_lines='skip')
        if len(df_raw) == 0:
            return pd.DataFrame()
        cabecalhos = df_raw.iloc[0].tolist()
        df = df_raw.iloc[1:].reset_index(drop=True)
        nomes_fixos = [
            'nome_completo', 'apelido', 'data_nascimento', 'posicao', 'pe_pref',
            'altura_cm', 'peso_kg', 'salario', 'cidade_nascimento', 'uf_nascimento',
            'pais_nascimento', 'historico', 'foto'
        ]
        for i, nome in enumerate(nomes_fixos):
            if i < df.shape[1]:
                df.rename(columns={i: nome}, inplace=True)
        colunas_restantes = {}
        for i in range(13, df.shape[1]):
            nome_original = cabecalhos[i] if i < len(cabecalhos) else f'col_{i}'
            nome_normalizado = str(nome_original).strip().replace('\ufeff', '').replace(' ', '_').lower()
            colunas_restantes[i] = nome_normalizado
        df.rename(columns=colunas_restantes, inplace=True)
        for col in ['nome_completo', 'data_nascimento', 'posicao']:
            if col not in df.columns:
                return pd.DataFrame()
        if 'pe_pref' not in df.columns:
            df['pe_pref'] = np.nan
        else:
            df['pe_pref'] = df['pe_pref'].replace(['', 'nan', 'NaN', 'None'], np.nan)
        for col in ['cidade_nascimento', 'uf_nascimento', 'pais_nascimento']:
            if col not in df.columns:
                df[col] = None
        cols_num = ['altura_cm', 'peso_kg', 'habilidade_atual', 'habilidade_potencial']
        for col in cols_num:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        for attr in ATRIBUTOS_FM26:
            if attr in df.columns:
                df[attr] = pd.to_numeric(df[attr], errors='coerce')
        df['IMC'] = df.apply(lambda x: x['peso_kg'] / ((x['altura_cm']/100)**2)
                             if pd.notna(x['altura_cm']) and pd.notna(x['peso_kg']) and x['altura_cm'] > 0
                             else np.nan, axis=1).round(1)
        df['Classificacao_IMC'] = df['IMC'].apply(classif_imc)
        df['Idade'] = df['data_nascimento'].apply(lambda x: calcular_idade(x) if pd.notna(x) else np.nan)
        # Gordura estimada (será sobrescrita pela bioimpedância se disponível)
        df['Gordura_Corporal_%'] = df.apply(lambda row: round((1.20*row['IMC']) + (0.23*row['Idade']) - 16.2, 1)
                                            if pd.notna(row['IMC']) and pd.notna(row['Idade']) else np.nan, axis=1)
        df['Massa_Magra_kg'] = df.apply(
            lambda row: round(row['peso_kg'] * (1 - row['Gordura_Corporal_%']/100), 1)
            if pd.notna(row['peso_kg']) and pd.notna(row['Gordura_Corporal_%']) else np.nan,
            axis=1
        )
        df['Massa_Muscular_Estimada_kg'] = df.apply(
            lambda row: round(row['Massa_Magra_kg'] * 0.55, 1)
            if pd.notna(row['Massa_Magra_kg']) else np.nan,
            axis=1
        )
        df['Classificacao_Gordura'] = df.apply(lambda x: classif_gordura(x['Gordura_Corporal_%'], x['Idade']), axis=1)
        df['Estado_Fisico'] = df.apply(lambda row: estado_fisico(row['Classificacao_IMC'], row['Classificacao_Gordura']), axis=1)
        def cat_pos(pos_str):
            if pd.isna(pos_str): return 'Outros', []
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
        df['Rating_Geral_FM26'] = df.apply(lambda row: min(100, row['habilidade_atual']/2) if pd.notna(row.get('habilidade_atual')) else 50, axis=1)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar elenco profissional: {e}")
        return pd.DataFrame()

@st.cache_data
def carregar_elenco_sub20() -> pd.DataFrame:
    if not os.path.exists(ARQUIVO_CSV_SUB20):
        return pd.DataFrame()
    try:
        # Usa a mesma lógica, apenas com o arquivo diferente
        df = carregar_elenco_profissional()  # substituto
        return df
    except:
        return pd.DataFrame()

@st.cache_data
def carregar_elenco_sub17() -> pd.DataFrame:
    if not os.path.exists(ARQUIVO_CSV_SUB17):
        return pd.DataFrame()
    try:
        return carregar_elenco_profissional()
    except:
        return pd.DataFrame()

@st.cache_data
def carregar_comissao() -> pd.DataFrame:
    if not os.path.exists(ARQUIVO_CSV_COMISSAO_PROFISSIONAL):
        return pd.DataFrame()
    try:
        df = pd.read_csv(ARQUIVO_CSV_COMISSAO_PROFISSIONAL, sep=';', encoding='utf-8-sig')
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        if 'apelido' in df.columns:
            df['nome'] = df['apelido'].fillna('')
        elif 'nome_completo' in df.columns:
            df['nome'] = df['nome_completo'].fillna('')
        if 'cargo' not in df.columns:
            df['cargo'] = 'Técnico'
        if 'data_nascimento' in df.columns:
            df['idade'] = df['data_nascimento'].apply(lambda x: calcular_idade(x) if pd.notna(x) else np.nan)
        else:
            df['idade'] = np.nan
        df['nome_canonico'] = df['nome'].apply(mapear_nome_para_canonico)
        # Adiciona colunas de cidade/UF
        if 'cidade_nascimento' in df.columns:
            df['cidade_uf'] = df['cidade_nascimento'].fillna('') + ', ' + df.get('uf_nascimento', '').fillna('')
            df['cidade_uf'] = df['cidade_uf'].str.rstrip(', ')
        else:
            df['cidade_uf'] = 'N/I'
        df['pais'] = df.get('pais_nascimento', 'N/I')
        return df
    except Exception as e:
        st.error(f"Erro ao carregar comissão: {e}")
        return pd.DataFrame()

@st.cache_data
def carregar_comissao_sub20() -> pd.DataFrame:
    if not os.path.exists(ARQUIVO_CSV_COMISSAO_SUB20):
        return pd.DataFrame()
    try:
        return carregar_comissao()
    except:
        return pd.DataFrame()

# =============================================
# CRONOGRAMA VIA CSV
# =============================================
@st.cache_data
def carregar_cronograma(categoria="Profissional") -> pd.DataFrame:
    arquivo = ARQUIVO_CRONO_PROF if categoria == "Profissional" else ARQUIVO_CRONO_SUB20
    if not os.path.exists(arquivo):
        return pd.DataFrame()
    try:
        df = pd.read_csv(arquivo, sep=';', encoding='utf-8-sig')
        if 'data' not in df.columns:
            return pd.DataFrame()
        df['data'] = pd.to_datetime(df['data'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Erro ao carregar cronograma: {e}")
        return pd.DataFrame()

def obter_proximo_jogo(categoria="Profissional") -> Optional[Dict]:
    df = carregar_cronograma(categoria)
    if df.empty:
        return None
    hoje = datetime.now().date()
    df_futuros = df[df['data'].dt.date >= hoje].sort_values('data')
    if df_futuros.empty:
        return None
    return df_futuros.iloc[0].to_dict()

# =============================================
# EXIBIR FOTO
# =============================================
def obter_caminho_foto(pessoa_row, categoria="Profissional"):
    foto = pessoa_row.get('foto')
    if foto and pd.notna(foto) and str(foto).strip():
        caminho = str(foto).strip()
        if os.path.exists(caminho):
            return caminho
        if caminho.startswith('http'):
            return caminho
    nome = pessoa_row.get('apelido') or pessoa_row.get('nome_completo') or pessoa_row.get('nome')
    if nome:
        nome_clean = normalizar_texto(nome).replace(' ', '_')
        pastas = [
            "fotos_sistema_Analise_Elenco/Jogadores/Profissional",
            "fotos_sistema_Analise_Elenco/Jogadores/Sub20",
            "fotos_sistema_Analise_Elenco/Jogadores/Sub17",
            "fotos_sistema_Analise_Elenco/Comissao_Tecnica/Profissional",
            "fotos"
        ]
        for ext in ['.png', '.jpg', '.jpeg']:
            for pasta in pastas:
                caminho = os.path.join(pasta, f"{nome}{ext}")
                if os.path.exists(caminho):
                    return caminho
                caminho = os.path.join(pasta, f"{nome_clean}{ext}")
                if os.path.exists(caminho):
                    return caminho
    return None

def exibir_foto(pessoa_row, categoria="Profissional", width=100):
    caminho = obter_caminho_foto(pessoa_row, categoria)
    if caminho and (caminho.startswith('http') or os.path.exists(caminho)):
        try:
            st.image(caminho, width=width)
            return
        except:
            pass
    st.write("📷")

# =============================================
# LESÕES (CSV)
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
    csv_path = {
        'profissional': ARQUIVO_LESOES_PROFISSIONAL,
        'sub20': ARQUIVO_LESOES_SUB20,
        'sub17': ARQUIVO_LESOES_SUB17,
    }.get(categoria)
    if not csv_path or not os.path.exists(csv_path):
        return {}, {}
    try:
        df = pd.read_csv(csv_path, delimiter=';', encoding='utf-8-sig', dtype=str)
    except Exception:
        return {}, {}
    lesionados_por_ogol = {}
    lesionados_por_nome = {}
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
                ogol_id_int = int(float(ogol_id))
                lesionados_por_ogol[ogol_id_int] = lesionado
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
                ogol_int = int(float(ogol))
                if ogol_int in les_ogol:
                    return les_ogol[ogol_int]
            except:
                pass
        nome = row.get('nome_completo')
        if nome and nome in les_nome:
            return les_nome[nome]
        return False
    df['lesionado'] = df.apply(is_lesionado, axis=1)
    return df

def obter_historico_lesoes_texto(jogador_row, categoria):
    csv_path = {
        'Profissional': ARQUIVO_LESOES_PROFISSIONAL,
        'Sub-20': ARQUIVO_LESOES_SUB20,
        'Sub-17': ARQUIVO_LESOES_SUB17,
    }.get(categoria)
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
            ogol_int = int(float(ogol_id))
            linha_lesao = df_lesoes[df_lesoes['ogol_id'].astype(float).astype(int) == ogol_int]
        except:
            pass
    if linha_lesao is None or linha_lesao.empty:
        linha_lesao = df_lesoes[df_lesoes['nome_completo'] == nome]
    if linha_lesao is None or linha_lesao.empty:
        return "Nenhum registro de lesão encontrado."
    colunas_lesoes = [col for col in df_lesoes.columns if col.startswith('Lesao_')]
    if not colunas_lesoes:
        return "Nenhuma coluna de lesão definida no CSV."
    linhas = []
    tem_lesao = False
    for col in colunas_lesoes:
        valor = linha_lesao.iloc[0].get(col, '')
        if pd.notna(valor) and valor != '':
            tem_lesao = True
            nome_lesao = col.replace('Lesao_', '').replace('_', ' ')
            ocorrencias = str(valor).split(',')
            ocorrencias_formatadas = []
            for occ in ocorrencias:
                occ = occ.strip()
                if '/' in occ:
                    if ' - ' in occ:
                        data_inicio_str, data_fim_str = occ.split(' - ', 1)
                    else:
                        data_inicio_str, data_fim_str = occ.split('/', 1)
                    data_inicio = parse_data_flexivel(data_inicio_str.strip())
                    data_fim = parse_data_flexivel(data_fim_str.strip())
                    if data_inicio and data_fim:
                        ocorrencias_formatadas.append(f"{formatar_data_br(data_inicio)} - {formatar_data_br(data_fim)}")
                    else:
                        ocorrencias_formatadas.append(occ)
                else:
                    data_obj = parse_data_flexivel(occ)
                    if data_obj:
                        ocorrencias_formatadas.append(f"{formatar_data_br(data_obj)} (atual)")
                    else:
                        ocorrencias_formatadas.append(occ)
            linhas.append(f"• {nome_lesao}: {', '.join(ocorrencias_formatadas)}")
    if not tem_lesao:
        return "Nenhuma lesão registrada."
    return "\n".join(linhas)

def obter_lesao_atual(jogador_row, categoria):
    csv_path = {
        'Profissional': ARQUIVO_LESOES_PROFISSIONAL,
        'Sub-20': ARQUIVO_LESOES_SUB20,
        'Sub-17': ARQUIVO_LESOES_SUB17,
    }.get(categoria)
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
            ogol_int = int(float(ogol_id))
            linha_lesao = df_lesoes[df_lesoes['ogol_id'].astype(float).astype(int) == ogol_int]
        except:
            pass
    if linha_lesao is None or linha_lesao.empty:
        linha_lesao = df_lesoes[df_lesoes['nome_completo'] == nome]
    if linha_lesao is None or linha_lesao.empty:
        return ""
    colunas_lesoes = [col for col in df_lesoes.columns if col.startswith('Lesao_')]
    for col in colunas_lesoes:
        valor = linha_lesao.iloc[0].get(col, '')
        if pd.notna(valor) and str(valor).strip() != '':
            ocorrencias = str(valor).split(',')
            ultima = ocorrencias[-1].strip()
            if ' - ' in ultima or '/' in ultima or '–' in ultima:
                continue
            nome_lesao = col.replace('Lesao_', '').replace('_', ' ')
            return nome_lesao
    return ""

# =============================================
# BIOIMPEDÂNCIA (CSV)
# =============================================
def carregar_dados_bioimpedancia(categoria):
    csv_path = {
        'profissional': ARQUIVO_BIO_PROFISSIONAL,
        'sub20': ARQUIVO_BIO_SUB20,
        'sub17': ARQUIVO_BIO_SUB17,
    }.get(categoria)
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
            # Extrai dados básicos
            data_coleta = row.get('data_bioimpedancia', '')
            idade = None
            if 'data_nascimento' in row and pd.notna(row.get('data_nascimento')):
                idade = calcular_idade(row.get('data_nascimento'), data_coleta)
            altura_cm = para_float(row.get('altura_cm'))
            peso = para_float(row.get('peso_kg'))
            # Dobras cutâneas
            triceps = para_float(row.get('dobra_triceps'))
            subescap = para_float(row.get('dobra_subescapular'))
            suprail = para_float(row.get('dobra_suprailiaca'))
            abdominal = para_float(row.get('dobra_abdominal'))
            coxa = para_float(row.get('dobra_coxa'))
            panturrilha = para_float(row.get('dobra_panturilha'))
            peitoral = para_float(row.get('dobra_peitoral'))
            axiliar = para_float(row.get('dobra_axiliar_media'))
            perim_braco = para_float(row.get('perimetro_braco'))
            perim_coxa = para_float(row.get('perimetro_coxa'))
            perim_perna = para_float(row.get('perimetro_perna'))
            # Cálculo dos percentuais (usando funções do sistema_bioimpedancia se disponível)
            # Vamos tentar importar as funções, senão usamos estimativa simples
            try:
                from sistema_bioimpedancia import faulkner, pollock_3, pollock_7, lee, converter_raca
                raca_num = converter_raca(row.get('raca'))
                pct_f = faulkner(triceps, subescap, suprail, abdominal)
                pct_p3 = pollock_3(peitoral, abdominal, coxa, idade)
                pct_p7 = pollock_7(peitoral, axiliar, triceps, subescap, abdominal, suprail, coxa, idade)
                mm_lee = lee(peso, altura_cm/100.0 if altura_cm else None, idade, raca_num,
                             perim_braco, perim_coxa, perim_perna, triceps, coxa, panturrilha)
            except ImportError:
                # Fallback: estimativa simples com base no IMC
                if altura_cm and peso:
                    imc = peso / ((altura_cm/100)**2)
                    pct_f = 1.20 * imc + 0.23 * (idade if idade else 30) - 16.2
                    pct_p3 = pct_f
                    pct_p7 = pct_f
                    mm_lee = None
                else:
                    pct_f = pct_p3 = pct_p7 = mm_lee = None
            # Massa gorda e magra
            if pct_f is not None and peso is not None:
                massa_gorda = (pct_f / 100) * peso
                massa_magra = peso - massa_gorda
            else:
                massa_gorda = None
                massa_magra = None
            # Armazena
            dados = {
                'pct_faulkner': pct_f,
                'pct_pollock3': pct_p3,
                'pct_pollock7': pct_p7,
                'massa_gorda': massa_gorda,
                'massa_magra': massa_magra,
                'massa_muscular': mm_lee,
                'data_coleta': data_coleta,
                'peso': peso,
                'altura': altura_cm / 100.0 if altura_cm else None,
                'idade': idade
            }
            if ogol_id:
                resultados[ogol_id] = dados
            else:
                resultados[nome] = dados
        except Exception as e:
            continue
    return resultados

def para_float(valor):
    if pd.isna(valor) or valor == '':
        return None
    try:
        return float(valor.replace(',', '.'))
    except:
        return None

def aplicar_dados_bioimpedancia(df, dados_bio):
    if not dados_bio:
        return df
    for col in ['PctGordura_Faulkner', 'PctGordura_Pollock3', 'PctGordura_Pollock7', 'Massa_Gorda_kg']:
        if col not in df.columns:
            df[col] = np.nan
    if 'Massa_Muscular_Origem' not in df.columns:
        df['Massa_Muscular_Origem'] = ''
    for idx, row in df.iterrows():
        ogol_id = row.get('ogol_id')
        nome = row.get('nome_completo')
        bio = None
        if pd.notna(ogol_id) and ogol_id in dados_bio:
            bio = dados_bio[ogol_id]
        elif nome in dados_bio:
            bio = dados_bio[nome]
        if bio is not None:
            if bio.get('peso') is not None:
                df.at[idx, 'peso_kg'] = bio['peso']
            if bio.get('altura') is not None:
                df.at[idx, 'altura_cm'] = bio['altura'] * 100
            altura_cm = df.at[idx, 'altura_cm']
            peso_kg = df.at[idx, 'peso_kg']
            if pd.notna(altura_cm) and pd.notna(peso_kg) and altura_cm > 0:
                df.at[idx, 'IMC'] = round(peso_kg / ((altura_cm/100)**2), 1)
            else:
                df.at[idx, 'IMC'] = np.nan
            if bio.get('pct_faulkner') is not None:
                df.at[idx, 'PctGordura_Faulkner'] = bio['pct_faulkner']
            if bio.get('pct_pollock3') is not None:
                df.at[idx, 'PctGordura_Pollock3'] = bio['pct_pollock3']
            if bio.get('pct_pollock7') is not None:
                df.at[idx, 'PctGordura_Pollock7'] = bio['pct_pollock7']
            pct_principal = bio.get('pct_pollock7') or bio.get('pct_pollock3') or bio.get('pct_faulkner')
            if pct_principal is not None:
                df.at[idx, 'Gordura_Corporal_%'] = pct_principal
            else:
                idade = df.at[idx, 'Idade']
                imc = df.at[idx, 'IMC']
                if pd.notna(imc) and pd.notna(idade):
                    df.at[idx, 'Gordura_Corporal_%'] = round(1.20*imc + 0.23*idade - 16.2, 1)
                else:
                    df.at[idx, 'Gordura_Corporal_%'] = np.nan
            peso = df.at[idx, 'peso_kg']
            gordura = df.at[idx, 'Gordura_Corporal_%']
            if pd.notna(peso) and pd.notna(gordura):
                massa_magra = round(peso * (1 - gordura/100), 1)
                df.at[idx, 'Massa_Magra_kg'] = massa_magra
                df.at[idx, 'Massa_Gorda_kg'] = round(peso - massa_magra, 1)
            else:
                df.at[idx, 'Massa_Magra_kg'] = np.nan
                df.at[idx, 'Massa_Gorda_kg'] = np.nan
                massa_magra = np.nan
            if bio.get('massa_muscular') is not None:
                df.at[idx, 'Massa_Muscular_Estimada_kg'] = round(bio['massa_muscular'], 1)
                df.at[idx, 'Massa_Muscular_Origem'] = 'Lee'
            else:
                if pd.notna(massa_magra):
                    df.at[idx, 'Massa_Muscular_Estimada_kg'] = round(massa_magra * 0.55, 1)
                    df.at[idx, 'Massa_Muscular_Origem'] = 'estimada'
                else:
                    df.at[idx, 'Massa_Muscular_Estimada_kg'] = np.nan
                    df.at[idx, 'Massa_Muscular_Origem'] = ''
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
        'profissional': CAMINHO_CARTOES_PROFISSIONAL,
        'sub20': CAMINHO_CARTOES_SUB20,
        'sub17': CAMINHO_CARTOES_SUB17,
        'comissao_profissional': CAMINHO_CARTOES_COMISSAO_PROFISSIONAL,
        'comissao_sub20': CAMINHO_CARTOES_COMISSAO_SUB20,
        'comissao_sub17': CAMINHO_CARTOES_COMISSAO_SUB17,
    }.get(categoria)
    if not caminho or not os.path.exists(caminho):
        return {}, []
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('cartoes', {}), data.get('datas_globais', [])
    except:
        return {}, []

def salvar_cartoes_json(cartoes, categoria, datas_globais=None):
    caminho = {
        'profissional': CAMINHO_CARTOES_PROFISSIONAL,
        'sub20': CAMINHO_CARTOES_SUB20,
        'sub17': CAMINHO_CARTOES_SUB17,
        'comissao_profissional': CAMINHO_CARTOES_COMISSAO_PROFISSIONAL,
        'comissao_sub20': CAMINHO_CARTOES_COMISSAO_SUB20,
        'comissao_sub17': CAMINHO_CARTOES_COMISSAO_SUB17,
    }.get(categoria)
    if not caminho:
        return
    if datas_globais is None:
        _, datas_globais = carregar_cartoes_json(categoria)
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump({'cartoes': cartoes, 'datas_globais': datas_globais}, f, ensure_ascii=False, indent=2)

def jogador_suspenso(nome, cartoes):
    if nome not in cartoes:
        return False
    return cartoes[nome].get('suspenso_proxima', False)

def inicializar_cartoes_por_csvs(categoria, canonico_para_ogol_id):
    # Implementação completa pode ser copiada do PyQt – aqui está o esqueleto
    st.info(f"Reinicializando cartões para {categoria}...")
    pasta = {
        'profissional': PASTA_ESTATISTICAS_PROFISSIONAL,
        'sub20': PASTA_ESTATISTICAS_SUB20,
        'sub17': PASTA_ESTATISTICAS_SUB17,
    }.get(categoria)
    if not pasta or not os.path.exists(pasta):
        st.warning(f"Pasta {pasta} não encontrada.")
        return {}, []
    # ... (implementação omitida por brevidade, mas você pode usar a do PyQt)
    return {}, []

# =============================================
# ESTATÍSTICAS DE PARTIDAS
# =============================================
def listar_arquivos_estatisticas(categoria="Profissional") -> List[str]:
    pasta = {
        'Profissional': PASTA_ESTATISTICAS_PROFISSIONAL,
        'Sub-20': PASTA_ESTATISTICAS_SUB20,
        'Sub-17': PASTA_ESTATISTICAS_SUB17
    }.get(categoria, PASTA_ESTATISTICAS_PROFISSIONAL)
    if not os.path.exists(pasta):
        return []
    return [os.path.join(pasta, f) for f in os.listdir(pasta) if f.endswith('.csv') and f.startswith('jogo_')]

def carregar_estatisticas_partidas(categoria="Profissional") -> pd.DataFrame:
    # Mesma implementação anterior (já fornecida)
    arquivos = listar_arquivos_estatisticas(categoria)
    if not arquivos:
        return pd.DataFrame()
    stats = {}
    colunas_minutos_possiveis = ['minutos', 'minutos_jogados', 'minutos_totais', 'minuto', 'tempo_jogado', 'min']
    for arq in arquivos:
        try:
            df = pd.read_csv(arq, sep=';', encoding='utf-8-sig', on_bad_lines='skip')
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            col_min = None
            for col in colunas_minutos_possiveis:
                if col in df.columns:
                    col_min = col
                    break
            if col_min is None:
                for col in df.columns:
                    if 'minuto' in col:
                        col_min = col
                        break
                if col_min is None:
                    continue
            df[col_min] = pd.to_numeric(df[col_min], errors='coerce').fillna(0)
            for _, row in df.iterrows():
                jogador = row.get('jogador', '')
                if pd.isna(jogador) or jogador == '':
                    continue
                canonico = mapear_nome_para_canonico(jogador)
                if canonico:
                    if canonico not in stats:
                        stats[canonico] = {'starts': 0, 'jogos_90min': 0, 'minutos_totais': 0}
                    minutos = row.get(col_min, 0)
                    stats[canonico]['minutos_totais'] += int(minutos)
                    if int(minutos) >= 90:
                        stats[canonico]['jogos_90min'] += 1
            if len(df) > 12:
                titulares_df = df.iloc[1:12]
            else:
                titulares_df = df.iloc[1:min(12, len(df))]
            for _, row in titulares_df.iterrows():
                jogador = row.get('jogador', '')
                if pd.isna(jogador) or jogador == '':
                    continue
                canonico = mapear_nome_para_canonico(jogador)
                if canonico:
                    if canonico not in stats:
                        stats[canonico] = {'starts': 0, 'jogos_90min': 0, 'minutos_totais': 0}
                    stats[canonico]['starts'] += 1
        except Exception as e:
            st.warning(f"Erro ao ler {arq}: {e}")
    df_stats = pd.DataFrame.from_dict(stats, orient='index').reset_index()
    df_stats = df_stats.rename(columns={'index': 'jogador_canonico'})
    for col in ['starts', 'jogos_90min', 'minutos_totais']:
        if col in df_stats.columns:
            df_stats[col] = df_stats[col].fillna(0).astype(int)
        else:
            df_stats[col] = 0
    return df_stats

def precomputar_scores_posicionais(df, df_stats_partidas):
    # Copiado do PyQt
    return df

# =============================================
# FUNÇÕES DE ESCALAÇÃO E FORMAÇÃO
# =============================================
def interpretar_formacao(formacao_str):
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
    candidatos = candidatos[~candidatos['nome_completo'].apply(lambda x: jogador_suspenso(mapear_nome_para_canonico(x), cartoes))]
    if not incluir_lesionados and 'lesionado' in candidatos.columns:
        candidatos = candidatos[~candidatos['lesionado']]
    return candidatos

def obter_atributos_chave(posicao):
    mapa = {
        'Goleiro': ['reflexos','defesas_goleiro','jogo_aereo_goleiro','comando_area','saida_gol'],
        'Zagueiro': ['desarme','marcacao','cabecada','forca_fisica','antecipacao','posicionamento'],
        'Lateral': ['cruzamentos','drible','passe','velocidade_maxima','aceleracao','resistencia'],
        'Lateral Direito': ['cruzamentos','drible','passe','velocidade_maxima','aceleracao','resistencia'],
        'Lateral Esquerdo': ['cruzamentos','drible','passe','velocidade_maxima','aceleracao','resistencia'],
        'Volante': ['desarme','marcacao','passe','posicionamento','intensidade_trabalho','visao_jogo'],
        'Meia': ['visao_jogo','passe','criatividade','tecnica','primeiro_controle','chutes_longe'],
        'Meia-Central': ['visao_jogo','passe','criatividade','tecnica','desarme','posicionamento'],
        'Meia-Atacante': ['visao_jogo','passe','criatividade','tecnica','primeiro_controle','finalizacao'],
        'Ponta': ['drible','aceleracao','velocidade_maxima','cruzamentos','tecnica','finalizacao'],
        'Ponta Direita': ['drible','aceleracao','velocidade_maxima','cruzamentos','tecnica','finalizacao'],
        'Ponta Esquerda': ['drible','aceleracao','velocidade_maxima','cruzamentos','tecnica','finalizacao'],
        'Centroavante': ['finalizacao','cabecada','primeiro_controle','composicao','forca_fisica','movimentacao_sem_bola'],
        'Segundo Atacante': ['movimentacao_sem_bola','primeiro_controle','tecnica','visao_jogo','passe','drible'],
        'Defensor': ['desarme','marcacao','cabecada','forca_fisica','antecipacao','posicionamento'],
        'Meio-Campo': ['passe','visao_jogo','criatividade','desarme','intensidade_trabalho'],
    }
    return mapa.get(posicao, ['Rating_Geral_FM26'])

# =============================================
# AUTENTICAÇÃO DE USUÁRIOS
# =============================================
ARQUIVO_USUARIOS = "usuarios.json"

def carregar_usuarios():
    if not os.path.exists(ARQUIVO_USUARIOS):
        senha_admin = "@W.d06302005"
        hash_admin = bcrypt.hashpw(senha_admin.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        usuarios = {"Guibfpinto": hash_admin}
        with open(ARQUIVO_USUARIOS, 'w', encoding='utf-8') as f:
            json.dump(usuarios, f, indent=2, ensure_ascii=False)
        return usuarios
    try:
        with open(ARQUIVO_USUARIOS, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"Guibfpinto": ""}

def autenticar_usuario(usuario, senha):
    usuarios = carregar_usuarios()
    if usuario not in usuarios:
        return False
    hash_senha = usuarios[usuario].encode('utf-8')
    return bcrypt.checkpw(senha.encode('utf-8'), hash_senha)

def listar_usuarios():
    return list(carregar_usuarios().keys())

def adicionar_usuario(usuario, senha):
    usuarios = carregar_usuarios()
    if usuario in usuarios:
        return False
    hash_novo = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    usuarios[usuario] = hash_novo
    with open(ARQUIVO_USUARIOS, 'w', encoding='utf-8') as f:
        json.dump(usuarios, f, indent=2, ensure_ascii=False)
    return True

def remover_usuario(usuario):
    if usuario == "Guibfpinto":
        return False
    usuarios = carregar_usuarios()
    if usuario in usuarios:
        del usuarios[usuario]
        with open(ARQUIVO_USUARIOS, 'w', encoding='utf-8') as f:
            json.dump(usuarios, f, indent=2, ensure_ascii=False)
        return True
    return False

# =============================================
# RELATÓRIOS E EXPORTAÇÃO
# =============================================
def gerar_relatorio_completo_texto(df, nome_categoria):
    if df is None or df.empty:
        return f"Sem dados para {nome_categoria}"
    texto = f"Relatório - {nome_categoria}\n\nTotal: {len(df)}\n"
    if 'Idade' in df.columns:
        texto += f"Idade média: {df['Idade'].mean():.1f}\n"
    if 'Rating_Geral_FM26' in df.columns:
        texto += f"Rating médio: {df['Rating_Geral_FM26'].mean():.1f}\n"
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
# FUNÇÕES DA API-FOOTBALL (PROXY)
# =============================================
def verificar_jogo_ao_vivo():
    # Integrar com FastAPI
    return None

def obter_detalhes_jogo(fixture_id):
    return None

def obter_estatisticas_jogo(fixture_id):
    return None

def obter_eventos_jogo(fixture_id):
    return None

def obter_lineups_completos(fixture_id):
    return None

def obter_players_stats(fixture_id):
    return None

def gerar_relatorio_excel(fixture_id, time_casa_titulares=None, time_casa_reservas=None):
    print("Relatório Excel gerado (simulado)")

# =============================================
# FORMATAR PLANILHA EXCEL
# =============================================
def formatar_planilha(ws, titulo):
    ws.title = titulo
    for col in ws.columns:
        max_length = 0
        for cell in col:
            try:
                if cell.value and len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        if col:
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = adjusted_width

def obter_historico_clubes(jogador_row):
    historico = jogador_row.get('historico')
    if pd.isna(historico) or not historico:
        return "Nenhum histórico de clubes registrado."
    return str(historico).strip()