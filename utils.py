# utils.py
import streamlit as st
import pandas as pd
import numpy as np
import os
import re
import unicodedata
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from io import BytesIO
import reportlab
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# =============================================
# CONSTANTES DE CAMINHOS (CSVs)
# =============================================
ARQUIVO_CSV_PROFISSIONAL = "perfil_completo_jogadores_profissional_2026.csv"
ARQUIVO_CSV_SUB20 = "perfil_completo_jogadores_Sub20_2026.csv"
ARQUIVO_CSV_SUB17 = "perfil_completo_jogadores_Sub17_2026.csv"
ARQUIVO_CSV_COMISSAO_PROF = "perfil_completo_comissao_2026.csv"
ARQUIVO_CSV_COMISSAO_SUB20 = "perfil_completo_comissao_Sub20_2026.csv"
ARQUIVO_CRONO_PROF = "cronograma_profissional_2026.csv"
ARQUIVO_CRONO_SUB20 = "cronograma_sub20_2026.csv"

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
    'Francisco Wesley da Silva Sousa': 'Wesley',
    'Wesley': 'Wesley',
    'Francisco de Assis Rapozo Neto': 'Francisco Neto',
    'Francisco Neto': 'Francisco Neto',
    'Stuart Asafe Ferreira Alves': 'Stuart',
    'Stuart': 'Stuart',
    'Yuri Ribeiro Giovanelli': 'Yuri Ribeiro',
    'Yuri Ribeiro': 'Yuri Ribeiro',
    'João Pedro Firmino Oliveira': 'João Firmino',
    'João Firmino': 'João Firmino',
    'Joao Firmino': 'João Firmino',
    'Lucas Titol Lopes': 'Lucas Titol',
    'Lucas Titol': 'Lucas Titol',
    'Rayner Silva Gomes': 'Rayner',
    'Rayner': 'Rayner',
    'Kayque Santos da Cunha': 'Kayque Santos',
    'Kayque Santos': 'Kayque Santos',
    'Cayque': 'Kayque Santos',
    'Ruan Amaral Rios': 'Ruan Rios',
    'Ruan Rios': 'Ruan Rios',
    'Genilson dos Santos Júnior': 'Júnior Espeto',
    'Júnior Espeto': 'Junior Espeto',
    'Clavis Severo Leão': 'Clavis Neto',
    'Clavis Neto': 'Clavis Neto',
    'Jeferson David Palacios Cantillo': 'Jeferson Palacios',
    'Jeferson Palacios': 'Jeferson Palacios',
    'J. D. Palacios Cantillo': 'Jeferson Palacios',
    'Gabriel Amorim de Aguiar': 'Gabriel Amorim',
    'Gabriel Amorim': 'Gabriel Amorim',
    'Virgílio Santos Borges': 'Borjão',
    'Borjão': 'Borjão',
    'Borjao': 'Borjão',
    'Matheus Toribes Ferreira Souza': 'Matheus Toribes',
    'Matheus Toribes': 'Matheus Toribes',
    'João Marcos Santos Ferraz Luz': 'João Marcos',
    'João Marcos': 'João Marcos',
    'Davi Fornaciari Lima': 'Davi Fornaciari',
    'Davi Fornaciari': 'Davi Fornaciari',
    'Karlos Henrique dos Reis Calavort': 'Kaká',
    'Kaká': 'Kaká',
    'Kaka': 'Kaká',
    'Daniel Olmo Morais Gonçalves': 'Daniel Olmo',
    'Daniel Olmo': 'Daniel Olmo',
    'Arthur Luiz Darros': 'Arthur Darros',
    'Arthur Darros': 'Arthur Darros',
    'Júlio César Fontana Leite': 'Julio César',
    'Julio César': 'Julio César',
    'Matheus Sarmento Mesquita': 'Matheus Sarmento',
    'Matheus Sarmento': 'Matheus Nossa',
    'Gabriel de Jesus Rodrigues': 'Gabriel Jesus',
    'Gabriel Jesus': 'Gabriel Jesus',
}
MAPEAMENTO_NOMES_SUB20 = {}
MAPEAMENTO_NOMES_SUB17 = {}
MAPEAMENTO_NOMES_COMISSAO_PROFISSIONAL = {}
MAPEAMENTO_NOMES_COMISSAO_SUB20 = {}

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
    """Cria todas as tabelas necessárias se não existirem."""
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
        for attr in ATRIBUTOS_FM26:
            if attr in df.columns:
                df[attr] = pd.to_numeric(df[attr], errors='coerce')
        df['IMC'] = df.apply(lambda x: x['peso_kg'] / ((x['altura_cm']/100)**2)
                             if pd.notna(x['altura_cm']) and pd.notna(x['peso_kg']) and x['altura_cm'] > 0
                             else np.nan, axis=1).round(1)
        df['Classificacao_IMC'] = df['IMC'].apply(classif_imc)
        df['Idade'] = df['data_nascimento'].apply(lambda x: calcular_idade(x) if pd.notna(x) else np.nan)
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
        st.error(f"Erro ao carregar elenco: {e}")
        return pd.DataFrame()

@st.cache_data
def carregar_comissao() -> pd.DataFrame:
    if not os.path.exists(ARQUIVO_CSV_COMISSAO_PROF):
        return pd.DataFrame()
    try:
        df = pd.read_csv(ARQUIVO_CSV_COMISSAO_PROF, sep=';', encoding='utf-8-sig')
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
        return df
    except Exception as e:
        st.error(f"Erro ao carregar comissão: {e}")
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
def exibir_foto(pessoa_row, categoria="Profissional", width=100):
    foto = pessoa_row.get('foto')
    if foto and pd.notna(foto) and str(foto).strip():
        caminho = str(foto).strip()
        if caminho.startswith('http'):
            try:
                st.image(caminho, width=width)
                return
            except:
                pass
        elif os.path.exists(caminho):
            st.image(caminho, width=width)
            return
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
                    st.image(caminho, width=width)
                    return
                caminho = os.path.join(pasta, f"{nome_clean}{ext}")
                if os.path.exists(caminho):
                    st.image(caminho, width=width)
                    return
    st.write("📷")

# =============================================
# ESTATÍSTICAS DE PARTIDAS (MINUTAGEM)
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

# =============================================
# FUNÇÕES DE CARTÕES (JSON)
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
    st.info(f"🔄 Reinicializando cartões para {categoria}...")
    if categoria == 'profissional':
        pasta = PASTA_ESTATISTICAS_PROFISSIONAL
    elif categoria == 'sub20':
        pasta = PASTA_ESTATISTICAS_SUB20
    elif categoria == 'sub17':
        pasta = PASTA_ESTATISTICAS_SUB17
    else:
        st.error("Categoria inválida para jogadores.")
        return {}, []
    if not os.path.exists(pasta):
        st.warning(f"Pasta {pasta} não encontrada.")
        return {}, []
    lista_arquivos = [os.path.join(pasta, f) for f in os.listdir(pasta) if f.endswith('.csv') and f.startswith('jogo_')]
    if not lista_arquivos:
        st.warning("Nenhum CSV de estatísticas encontrado.")
        return {}, []
    arquivos_com_data = []
    for arq in lista_arquivos:
        data_jogo = extrair_data_jogo(arq)
        if not data_jogo:
            try:
                data_jogo = datetime.fromtimestamp(os.path.getmtime(arq))
            except:
                continue
        arquivos_com_data.append((data_jogo, arq))
    arquivos_com_data.sort(key=lambda x: x[0])
    datas_globais = [d.strftime("%Y-%m-%d") for d, _ in arquivos_com_data]
    cartoes = {}
    competicao_anterior = None
    ids_processados = set()
    reset_ids = []
    reset_apos_ids = []
    for data_jogo, arq in arquivos_com_data:
        jogo_id = extrair_id_jogo(arq)
        if jogo_id is not None and jogo_id in ids_processados:
            continue
        if jogo_id is not None:
            ids_processados.add(jogo_id)
        try:
            df = pd.read_csv(arq, sep=';', encoding='utf-8-sig', on_bad_lines='skip')
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            competicao_atual = df['competicao'].iloc[0] if 'competicao' in df.columns else 'Desconhecida'
            adversario = df['adversario'].iloc[0] if 'adversario' in df.columns else 'Desconhecido'
            if competicao_anterior is not None and competicao_atual != competicao_anterior:
                for dados in cartoes.values():
                    dados['amarelos'] = 0
                    dados['vermelho'] = False
                    dados['suspenso_proxima'] = False
            competicao_anterior = competicao_atual
            if jogo_id in reset_ids:
                for dados in cartoes.values():
                    dados['amarelos'] = 0
                    dados['vermelho'] = False
                    dados['suspenso_proxima'] = False
            relacionados_ogol_ids = set()
            for _, row in df.iterrows():
                nome = row.get('jogador')
                if pd.isna(nome):
                    continue
                canonico = mapear_nome_para_canonico(nome)
                if canonico and canonico in canonico_para_ogol_id:
                    relacionados_ogol_ids.add(canonico_para_ogol_id[canonico])
            for nome, dados in list(cartoes.items()):
                if dados.get('suspenso_proxima', False):
                    ogol_id = dados.get('ogol_id')
                    if ogol_id and ogol_id in relacionados_ogol_ids:
                        continue
                    if nome in [mapear_nome_para_canonico(row.get('jogador')) for _, row in df.iterrows() if pd.notna(row.get('jogador'))]:
                        continue
                    dados['amarelos'] = 0
                    dados['vermelho'] = False
                    dados['suspenso_proxima'] = False
                    for ev in reversed(dados.get('historico', [])):
                        if ev.get('suspenso_causada') and not ev.get('suspenso_cumprida'):
                            ev['suspenso_cumprida'] = True
                            break
            suspensos_neste_jogo = set()
            for _, row in df.iterrows():
                nome = row.get('jogador')
                if pd.isna(nome):
                    continue
                canonico = mapear_nome_para_canonico(nome)
                if not canonico:
                    continue
                amarelos = int(row.get('cartoes_amarelos', 0))
                vermelhos = int(row.get('cartoes_vermelhos', 0))
                if amarelos == 0 and vermelhos == 0:
                    continue
                if canonico not in cartoes:
                    cartoes[canonico] = {
                        'amarelos': 0,
                        'vermelho': False,
                        'suspenso_proxima': False,
                        'historico': [],
                        'ogol_id': canonico_para_ogol_id.get(canonico)
                    }
                for _ in range(amarelos):
                    cartoes[canonico]['amarelos'] += 1
                    terceiro = cartoes[canonico]['amarelos'] >= 3
                    if terceiro:
                        cartoes[canonico]['suspenso_proxima'] = True
                        suspensos_neste_jogo.add(canonico)
                    cartoes[canonico]['historico'].append({
                        'data': data_jogo.strftime("%d/%m/%Y"),
                        'adversario': adversario,
                        'competicao': competicao_atual,
                        'cor': 'amarelo',
                        'terceiro_amarelo': terceiro,
                        'suspenso_causada': terceiro,
                        'suspenso_cumprida': False
                    })
                for _ in range(vermelhos):
                    cartoes[canonico]['vermelho'] = True
                    cartoes[canonico]['suspenso_proxima'] = True
                    suspensos_neste_jogo.add(canonico)
                    cartoes[canonico]['historico'].append({
                        'data': data_jogo.strftime("%d/%m/%Y"),
                        'adversario': adversario,
                        'competicao': competicao_atual,
                        'cor': 'vermelho',
                        'terceiro_amarelo': False,
                        'suspenso_causada': True,
                        'suspenso_cumprida': False
                    })
            if jogo_id in reset_apos_ids:
                for dados in cartoes.values():
                    dados['amarelos'] = 0
                    dados['vermelho'] = False
                    dados['suspenso_proxima'] = False
                for nome in suspensos_neste_jogo:
                    if nome in cartoes:
                        cartoes[nome]['suspenso_proxima'] = True
        except Exception as e:
            st.warning(f"Erro ao processar {arq}: {e}")
    salvar_cartoes_json(cartoes, categoria, datas_globais)
    st.success(f"✅ Cartões reinicializados para {categoria}.")
    return cartoes, datas_globais

def inicializar_cartoes_comissao(categoria):
    st.info(f"🔄 Reinicializando cartões da comissão para {categoria}...")
    if categoria == 'comissao_profissional':
        pasta = PASTA_ESTATISTICAS_COMISSAO_PROFISSIONAL
        categoria_save = 'comissao_profissional'
    elif categoria == 'comissao_sub20':
        pasta = PASTA_ESTATISTICAS_COMISSAO_SUB20
        categoria_save = 'comissao_sub20'
    elif categoria == 'comissao_sub17':
        pasta = PASTA_ESTATISTICAS_COMISSAO_SUB17
        categoria_save = 'comissao_sub17'
    else:
        st.error("Categoria inválida para comissão.")
        return {}, []
    if not os.path.exists(pasta):
        st.warning(f"Pasta {pasta} não encontrada.")
        return {}, []
    lista_arquivos = [os.path.join(pasta, f) for f in os.listdir(pasta) if f.endswith('.csv') and f.startswith('jogo_')]
    if not lista_arquivos:
        st.warning("Nenhum CSV de estatísticas da comissão encontrado.")
        return {}, []
    arquivos_com_data = []
    for arq in lista_arquivos:
        data_jogo = extrair_data_jogo(arq)
        if not data_jogo:
            try:
                data_jogo = datetime.fromtimestamp(os.path.getmtime(arq))
            except:
                continue
        arquivos_com_data.append((data_jogo, arq))
    arquivos_com_data.sort(key=lambda x: x[0])
    datas_globais = [d.strftime("%Y-%m-%d") for d, _ in arquivos_com_data]
    cartoes = {}
    ids_processados = set()
    competicao_anterior = None
    reset_ids = []
    reset_apos_ids = []
    for data_jogo, arq in arquivos_com_data:
        jogo_id = extrair_id_jogo(arq)
        if jogo_id is not None and jogo_id in ids_processados:
            continue
        if jogo_id is not None:
            ids_processados.add(jogo_id)
        try:
            df = pd.read_csv(arq, sep=';', encoding='utf-8-sig', on_bad_lines='skip')
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            competicao_atual = df['competicao'].iloc[0] if 'competicao' in df.columns else 'Desconhecida'
            adversario = df['adversario'].iloc[0] if 'adversario' in df.columns else 'Desconhecido'
            if competicao_anterior is not None and competicao_atual != competicao_anterior:
                for dados in cartoes.values():
                    dados['amarelos'] = 0
                    dados['vermelho'] = False
                    dados['suspenso_proxima'] = False
            competicao_anterior = competicao_atual
            if jogo_id in reset_ids:
                for dados in cartoes.values():
                    dados['amarelos'] = 0
                    dados['vermelho'] = False
                    dados['suspenso_proxima'] = False
            relacionados_nomes = set()
            for _, row in df.iterrows():
                nome = row.get('nome') or row.get('membro') or row.get('comissao') or row.get('staff')
                if pd.notna(nome) and str(nome).strip():
                    canonico = mapear_nome_para_canonico(nome)
                    if canonico:
                        relacionados_nomes.add(canonico)
            for nome, dados in list(cartoes.items()):
                if dados.get('suspenso_proxima', False):
                    if nome not in relacionados_nomes:
                        dados['amarelos'] = 0
                        dados['vermelho'] = False
                        dados['suspenso_proxima'] = False
                        for ev in reversed(dados.get('historico', [])):
                            if ev.get('suspenso_causada') and not ev.get('suspenso_cumprida'):
                                ev['suspenso_cumprida'] = True
                                break
            suspensos_neste_jogo = set()
            for _, row in df.iterrows():
                nome_raw = row.get('nome') or row.get('membro') or row.get('comissao') or row.get('staff')
                if pd.isna(nome_raw):
                    continue
                nome = mapear_nome_para_canonico(nome_raw)
                if not nome:
                    continue
                amarelos = int(row.get('cartoes_amarelos', 0))
                vermelhos = int(row.get('cartoes_vermelhos', 0))
                if amarelos == 0 and vermelhos == 0:
                    continue
                if nome not in cartoes:
                    cartoes[nome] = {
                        'amarelos': 0,
                        'vermelho': False,
                        'suspenso_proxima': False,
                        'historico': []
                    }
                for _ in range(amarelos):
                    cartoes[nome]['amarelos'] += 1
                    terceiro = cartoes[nome]['amarelos'] >= 3
                    if terceiro:
                        cartoes[nome]['suspenso_proxima'] = True
                        suspensos_neste_jogo.add(nome)
                    cartoes[nome]['historico'].append({
                        'data': data_jogo.strftime("%d/%m/%Y"),
                        'adversario': adversario,
                        'competicao': competicao_atual,
                        'cor': 'amarelo',
                        'terceiro_amarelo': terceiro,
                        'suspenso_causada': terceiro,
                        'suspenso_cumprida': False
                    })
                for _ in range(vermelhos):
                    cartoes[nome]['vermelho'] = True
                    cartoes[nome]['suspenso_proxima'] = True
                    suspensos_neste_jogo.add(nome)
                    cartoes[nome]['historico'].append({
                        'data': data_jogo.strftime("%d/%m/%Y"),
                        'adversario': adversario,
                        'competicao': competicao_atual,
                        'cor': 'vermelho',
                        'terceiro_amarelo': False,
                        'suspenso_causada': True,
                        'suspenso_cumprida': False
                    })
            if jogo_id in reset_apos_ids:
                for dados in cartoes.values():
                    dados['amarelos'] = 0
                    dados['vermelho'] = False
                    dados['suspenso_proxima'] = False
                for nome in suspensos_neste_jogo:
                    if nome in cartoes:
                        cartoes[nome]['suspenso_proxima'] = True
        except Exception as e:
            st.warning(f"Erro ao processar {arq}: {e}")
    salvar_cartoes_json(cartoes, categoria_save, datas_globais)
    st.success(f"✅ Cartões da comissão reinicializados para {categoria}.")
    return cartoes, datas_globais

# =============================================
# DEMAIS FUNÇÕES (INTERPRETAR FORMAÇÃO, ETC.)
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

def analisar_pontos_jogador(row):
    if row is None: return {}, {}
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
    atributos = {attr: row.get(attr, np.nan) for attr in ATRIBUTOS_FM26}
    validos = {k: v for k, v in atributos.items() if pd.notna(v)}
    if not validos: return {}, {}
    sorted_attr = sorted(validos.items(), key=lambda x: x[1], reverse=True)
    return dict(sorted_attr[:5]), dict(sorted_attr[-5:])

def calcular_estilo_jogador(row):
    estilos = {
        'Posse de Bola': ['passe', 'visao_jogo', 'criatividade', 'primeiro_controle', 'tecnica'],
        'Contra-Ataque': ['aceleracao', 'velocidade_maxima', 'drible', 'finalizacao', 'cruzamentos'],
        'Pressing': ['intensidade_trabalho', 'desarme', 'marcacao', 'resistencia', 'agressividade'],
        'Jogo Aéreo': ['cabecada', 'altura_salto', 'forca_fisica', 'posicionamento'],
        'Defensivo': ['desarme', 'marcacao', 'posicionamento', 'concentracao', 'composicao']
    }
    scores = {}
    for estilo, attrs in estilos.items():
        total = 0
        count = 0
        for attr in attrs:
            val = row.get(attr, np.nan)
            if pd.notna(val):
                total += val
                count += 1
        scores[estilo] = total / count if count > 0 else 0
    return max(scores, key=scores.get) if scores else 'Indefinido'

def formatar_cartoes(dados_cartao):
    if not dados_cartao: return ""
    amarelos = dados_cartao.get('amarelos', 0)
    vermelho = dados_cartao.get('vermelho', False)
    partes = []
    if amarelos > 0: partes.append(f"🟨 {amarelos}")
    if vermelho: partes.append("🟥")
    return " ".join(partes)

# =============================================
# RELATÓRIOS (EXCEL E PDF)
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

def gerar_relatorio_diretoria(df_jogadores, df_comissao, output: BytesIO):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Resumo Geral"
    ws['A1'] = "RELATÓRIO EXECUTIVO - LINHARES FC"
    ws['A1'].font = Font(size=16, bold=True)
    ws.merge_cells('A1:D1')
    row = 3
    ws[f'A{row}'] = "Indicador"; ws[f'B{row}'] = "Valor"; row += 1
    ws[f'A{row}'] = "Total de Jogadores"; ws[f'B{row}'] = len(df_jogadores); row += 1
    ws[f'A{row}'] = "Total de Membros da Comissão"; ws[f'B{row}'] = len(df_comissao); row += 1
    for col in ['Idade', 'IMC', 'Gordura_Corporal_%', 'Rating_Geral_FM26']:
        if col in df_jogadores.columns:
            ws[f'A{row}'] = f"{col} Médio"; ws[f'B{row}'] = round(df_jogadores[col].mean(), 1); row += 1
    wb.save(output); output.seek(0)

def gerar_relatorio_jogador(jogador_row, output: BytesIO):
    wb = openpyxl.Workbook(); ws = wb.active
    ws.title = "Relatório Jogador"
    ws['A1'] = f"RELATÓRIO - {jogador_row.get('nome_completo', 'Jogador')}"
    ws['A1'].font = Font(size=16, bold=True)
    ws.merge_cells('A1:D1')
    row = 3
    campos = [
        ('Nome Completo', 'nome_completo'), ('Apelido', 'apelido'),
        ('Data Nascimento', 'data_nascimento'), ('Idade', 'Idade'),
        ('Posição Principal', 'Posicao_Principal'), ('Altura (cm)', 'altura_cm'),
        ('Peso (kg)', 'peso_kg'), ('IMC', 'IMC'), ('% Gordura', 'Gordura_Corporal_%'),
        ('Estado Físico', 'Estado_Fisico')
    ]
    for label, key in campos:
        valor = jogador_row.get(key, 'N/I')
        if pd.isna(valor) or valor == '': valor = 'N/I'
        ws[f'A{row}'] = label; ws[f'B{row}'] = valor; row += 1
    wb.save(output); output.seek(0)

def gerar_relatorio_comissao(membro_row, output: BytesIO):
    wb = openpyxl.Workbook(); ws = wb.active
    ws.title = "Relatório Comissão"
    ws['A1'] = f"RELATÓRIO - {membro_row.get('nome', 'Membro')}"
    ws['A1'].font = Font(size=16, bold=True)
    ws.merge_cells('A1:D1')
    row = 3
    campos = [('Nome', 'nome'), ('Cargo', 'cargo'), ('Idade', 'idade'), ('Data Nascimento', 'data_nascimento')]
    for label, key in campos:
        valor = membro_row.get(key, 'N/I')
        if pd.isna(valor) or valor == '': valor = 'N/I'
        ws[f'A{row}'] = label; ws[f'B{row}'] = valor; row += 1
    wb.save(output); output.seek(0)

def exportar_escalacao_excel(titulares, reservas, instrucoes, formacao, estilo, output: BytesIO):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Escalação"
    ws['A1'] = f"ESCALAÇÃO - {formacao} | ESTILO: {estilo}"
    ws['A1'].font = Font(size=14, bold=True)
    ws.merge_cells('A1:E1')
    row = 3
    ws[f'A{row}'] = "TITULARES"
    ws[f'A{row}'].font = Font(bold=True)
    row += 1
    ws[f'A{row}'] = "Posição"
    ws[f'B{row}'] = "Jogador"
    ws[f'C{row}'] = "Apelido"
    ws[f'D{row}'] = "ID"
    ws[f'E{row}'] = "Rating"
    for col in 'ABCDE':
        ws[col+str(row)].font = Font(bold=True)
    row += 1
    for j in titulares:
        ws[f'A{row}'] = j.get('posicao_exibida', '')
        ws[f'B{row}'] = j.get('nome', '')
        ws[f'C{row}'] = j.get('apelido', '')
        ws[f'D{row}'] = j.get('row', {}).get('ogol_id', '')
        ws[f'E{row}'] = j.get('row', {}).get('Rating_Geral_FM26', '')
        row += 1
    row += 2
    ws[f'A{row}'] = "RESERVAS"
    ws[f'A{row}'].font = Font(bold=True)
    row += 1
    ws[f'A{row}'] = "Posição"
    ws[f'B{row}'] = "Jogador"
    ws[f'C{row}'] = "Apelido"
    ws[f'D{row}'] = "Rating"
    for col in 'ABCD':
        ws[col+str(row)].font = Font(bold=True)
    row += 1
    for j in reservas:
        ws[f'A{row}'] = j.get('posicao_principal', '')
        ws[f'B{row}'] = j.get('nome', '')
        ws[f'C{row}'] = j.get('apelido', '')
        ws[f'D{row}'] = j.get('row', {}).get('Rating_Geral_FM26', '')
        row += 1
    if instrucoes:
        ws2 = wb.create_sheet("Instruções")
        ws2['A1'] = "INSTRUÇÕES INDIVIDUAIS"
        ws2['A1'].font = Font(size=14, bold=True)
        ws2.merge_cells('A1:C1')
        row = 3
        for nome, inst in instrucoes.items():
            ws2[f'A{row}'] = nome
            ws2[f'B{row}'] = "Com bola: " + ", ".join(inst.get('com_bola', []))
            ws2[f'C{row}'] = "Sem bola: " + ", ".join(inst.get('sem_bola', []))
            row += 2
    wb.save(output); output.seek(0)

def exportar_escalacao_pdf(titulares, reservas, instrucoes, formacao, estilo, output: BytesIO):
    try:
        pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
        font_name = 'Arial'
    except:
        font_name = 'Helvetica'
    c = canvas.Canvas(output, pagesize=A4)
    width, height = A4
    c.setFont(font_name, 16)
    c.drawString(30, height - 30, f"ESCALAÇÃO - {formacao} | ESTILO: {estilo}")
    c.setFont(font_name, 12)
    y = height - 60
    c.setFont(font_name, 14)
    c.drawString(30, y, "TITULARES")
    y -= 20
    c.setFont(font_name, 10)
    for j in titulares:
        if y < 50:
            c.showPage()
            y = height - 30
            c.setFont(font_name, 10)
        c.drawString(30, y, f"{j.get('posicao_exibida', '')}: {j.get('nome', '')} ({j.get('apelido', '')})")
        y -= 16
    y -= 20
    c.setFont(font_name, 14)
    c.drawString(30, y, "RESERVAS")
    y -= 20
    c.setFont(font_name, 10)
    for j in reservas:
        if y < 50:
            c.showPage()
            y = height - 30
            c.setFont(font_name, 10)
        c.drawString(30, y, f"{j.get('posicao_principal', '')}: {j.get('nome', '')} ({j.get('apelido', '')})")
        y -= 16
    if instrucoes:
        c.showPage()
        c.setFont(font_name, 14)
        c.drawString(30, height - 30, "INSTRUÇÕES INDIVIDUAIS")
        y = height - 60
        c.setFont(font_name, 10)
        for nome, inst in instrucoes.items():
            if y < 50:
                c.showPage()
                y = height - 30
                c.setFont(font_name, 10)
            c.setFont(font_name, 11)
            c.drawString(30, y, f"{nome}:")
            y -= 16
            c.setFont(font_name, 9)
            c.drawString(40, y, f"Com bola: {', '.join(inst.get('com_bola', []))}")
            y -= 14
            c.drawString(40, y, f"Sem bola: {', '.join(inst.get('sem_bola', []))}")
            y -= 16
    c.save()
    output.seek(0)

def salvar_escalacao_json(titulares, reservas, formacao, estilo, caminho):
    dados = {
        'formacao': formacao,
        'estilo': estilo,
        'titulares': [],
        'reservas': []
    }
    for j in titulares:
        dados['titulares'].append({
            'nome': j.get('nome'),
            'apelido': j.get('apelido'),
            'posicao_exibida': j.get('posicao_exibida'),
            'ogol_id': j.get('row', {}).get('ogol_id', '')
        })
    for j in reservas:
        dados['reservas'].append({
            'nome': j.get('nome'),
            'apelido': j.get('apelido'),
            'posicao_principal': j.get('posicao_principal'),
            'ogol_id': j.get('row', {}).get('ogol_id', '')
        })
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

def carregar_escalacao_json(df, caminho):
    with open(caminho, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    formacao = dados.get('formacao', '4-4-2')
    estilo = dados.get('estilo', 'Posse de Bola')
    titulares = []
    for item in dados.get('titulares', []):
        row = df[df['ogol_id'] == item.get('ogol_id')]
        if not row.empty:
            row = row.iloc[0]
            titulares.append({
                'nome': row['nome_completo'],
                'apelido': row['apelido'],
                'posicao_exibida': item.get('posicao_exibida'),
                'row': row
            })
    reservas = []
    for item in dados.get('reservas', []):
        row = df[df['ogol_id'] == item.get('ogol_id')]
        if not row.empty:
            row = row.iloc[0]
            reservas.append({
                'nome': row['nome_completo'],
                'apelido': row['apelido'],
                'posicao_principal': item.get('posicao_principal'),
                'row': row
            })
    return formacao, estilo, titulares, reservas