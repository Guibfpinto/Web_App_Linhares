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
    carregar_elenco_sub20,
    carregar_elenco_sub17,
    carregar_comissao,
    carregar_comissao_sub20,
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
    ARQUIVO_CSV_SUB20,
    ARQUIVO_CSV_SUB17,
    ARQUIVO_CSV_COMISSAO_PROFISSIONAL,
    ARQUIVO_CSV_COMISSAO_SUB20,
    obter_proximo_jogo,
    exibir_foto,
    formatar_cartoes,
    inicializar_banco,
)

# ======================================================================
# CONFIGURAÇÃO INICIAL & CSS PERSONALIZADO
# ======================================================================
st.set_page_config(layout="wide", page_title=f"{NOME_TIME} - Temporada {TEMPORADA}", page_icon="⚽")

# CSS para mudar a cor do texto de mensagens para preto
st.markdown("""
<style>
    div[data-testid="stAlert"] {
        color: black !important;
    }
    div[data-testid="stAlert"] .stAlert {
        color: black !important;
    }
    .stAlert {
        color: black !important;
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
        .stApp {{ background-color: rgba(0,0,0,0.6); border-radius: 10px; margin: 10px; padding: 10px; }}
        [data-testid="stSidebar"] {{ background-color: rgba(0,0,0,0.75); }}
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
        .stApp { background-color: rgba(0,0,0,0.5); border-radius: 10px; margin: 10px; padding: 10px; }
        [data-testid="stSidebar"] { background-color: rgba(0,0,0,0.8); }
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
# FUNÇÕES DE DETALHES (JOGADOR E COMISSÃO)
# ======================================================================
def exibir_detalhes_jogador(row, categoria, cartoes):
    with st.expander(f"📋 DETALHES COMPLETOS - {row.get('nome_completo', 'Jogador')}", expanded=True):
        col1, col2 = st.columns([1, 2])
        with col1:
            caminho_foto = obter_caminho_foto(row, categoria)
            if caminho_foto:
                st.image(caminho_foto, width=150)
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

def exibir_detalhes_comissao(row, categoria, cartoes):
    with st.expander(f"📋 DETALHES - {row.get('nome', 'Membro')}", expanded=True):
        col1, col2 = st.columns([1,2])
        with col1:
            caminho_foto = obter_caminho_foto(row, categoria)
            if caminho_foto:
                st.image(caminho_foto, width=150)
            else:
                st.write("📷 Sem foto")
        with col2:
            st.write(f"**Nome:** {row.get('nome', 'N/I')}")
            st.write(f"**Cargo:** {row.get('cargo', 'N/I')}")
            st.write(f"**Idade:** {row.get('idade', 'N/I')}")
            st.write(f"**Naturalidade:** {row.get('cidade_uf', 'N/I')}")
            st.write(f"**País:** {row.get('pais', 'N/I')}")
            nome_canonico = row.get('nome_canonico', row['nome'])
            suspenso = "Sim" if jogador_suspenso(nome_canonico, cartoes) else "Não"
            st.write(f"**Suspenso:** {suspenso}")
        st.divider()
        st.subheader("📜 Histórico Profissional")
        st.write(row.get('historico_profissional', 'Não informado'))
        st.subheader("⚽ Histórico como Jogador")
        st.write(row.get('historico_jogador', 'Não informado'))
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
# CARREGAMENTO DE DADOS (CACHE)
# ======================================================================
@st.cache_data
def carregar_dfs():
    resultado = {
        "Profissional": None,
        "Sub-20": None,
        "Sub-17": None,
        "Comissão Profissional": None,
        "Comissão Sub-20": None,
        "Comissão Sub-17": None,
        "cartoes_prof": {},
        "cartoes_sub20": {},
        "cartoes_sub17": {},
        "cartoes_com_prof": {},
        "cartoes_com_sub20": {},
        "cartoes_com_sub17": {},
    }
    try:
        df_prof = carregar_elenco_profissional()
        df_sub20 = carregar_elenco_sub20()
        df_sub17 = carregar_elenco_sub17()

        if df_prof is not None and not df_prof.empty:
            df_prof = adicionar_coluna_lesionado(df_prof, 'profissional')
            bio_prof = carregar_dados_bioimpedancia('profissional')
            df_prof = aplicar_dados_bioimpedancia(df_prof, bio_prof)
        if df_sub20 is not None and not df_sub20.empty:
            df_sub20 = adicionar_coluna_lesionado(df_sub20, 'sub20')
            bio_sub20 = carregar_dados_bioimpedancia('sub20')
            df_sub20 = aplicar_dados_bioimpedancia(df_sub20, bio_sub20)
        if df_sub17 is not None and not df_sub17.empty:
            df_sub17 = adicionar_coluna_lesionado(df_sub17, 'sub17')
            bio_sub17 = carregar_dados_bioimpedancia('sub17')
            df_sub17 = aplicar_dados_bioimpedancia(df_sub17, bio_sub17)

        resultado["Profissional"] = df_prof
        resultado["Sub-20"] = df_sub20
        resultado["Sub-17"] = df_sub17

        resultado["Comissão Profissional"] = carregar_comissao()
        resultado["Comissão Sub-20"] = carregar_comissao_sub20()
        resultado["Comissão Sub-17"] = pd.DataFrame()

        df_stats = carregar_estatisticas_partidas()
        if not df_stats.empty and df_prof is not None:
            resultado["Profissional"] = precomputar_scores_posicionais(df_prof, df_stats)

        for cat, key in [
            ('profissional', 'cartoes_prof'),
            ('sub20', 'cartoes_sub20'),
            ('sub17', 'cartoes_sub17'),
            ('comissao_profissional', 'cartoes_com_prof'),
            ('comissao_sub20', 'cartoes_com_sub20'),
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
        "Sub-20": ("Sub-20", "cartoes_sub20"),
        "Sub-17": ("Sub-17", "cartoes_sub17"),
        "Comissão Profissional": ("Comissão Profissional", "cartoes_com_prof"),
        "Comissão Sub-20": ("Comissão Sub-20", "cartoes_com_sub20"),
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

# ----------------------------------------------------------------------
# ABA 1: ANÁLISE DE ELENCO
# ----------------------------------------------------------------------
with tabs[0]:
    st.header("Análise de Jogadores")
    cat_analise = st.selectbox("Categoria", ["Profissional", "Sub-20", "Sub-17"])
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
            jogador_sel = st.selectbox("Selecione", df_analise['nome_completo'].tolist())
            row = df_analise[df_analise['nome_completo'] == jogador_sel].iloc[0]
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
            for cat in ["Profissional", "Sub-20", "Sub-17"]:
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

# ----------------------------------------------------------------------
# ABA 2: COMISSÃO TÉCNICA
# ----------------------------------------------------------------------
with tabs[1]:
    st.header("Comissão Técnica")
    cat_com = st.selectbox("Categoria", ["Comissão Profissional", "Comissão Sub-20", "Comissão Sub-17"])
    df_com, cartoes_com = get_df_cartoes(cat_com)
    if df_com is not None and not df_com.empty:
        busca = st.text_input("Buscar membro")
        if busca and 'nome' in df_com.columns:
            df_com = df_com[df_com['nome'].str.contains(busca, case=False, na=False)]
        cols = [c for c in ['nome','cargo','idade','cidade_uf','pais'] if c in df_com.columns]
        st.dataframe(df_com[cols], width='stretch')
        if not df_com.empty and 'nome' in df_com.columns:
            membro = st.selectbox("Selecione um membro", df_com['nome'].tolist())
            if membro:
                row = df_com[df_com['nome'] == membro].iloc[0]
                exibir_detalhes_comissao(row, cat_com, cartoes_com)
                if st.button(f"🟨 Registrar cartão para {membro}"):
                    tipo = st.radio("Tipo", ["Amarelo", "Vermelho"], key="tipo_cartao_com")
                    if st.button("Confirmar cartão", key="conf_cartao_com"):
                        nome_canonico = row.get('nome_canonico', row['nome'])
                        if nome_canonico not in cartoes_com:
                            cartoes_com[nome_canonico] = {'amarelos':0, 'vermelho':False, 'suspenso_proxima':False, 'historico':[]}
                        if tipo == "Amarelo":
                            cartoes_com[nome_canonico]['amarelos'] += 1
                            if cartoes_com[nome_canonico]['amarelos'] >= 3:
                                cartoes_com[nome_canonico]['suspenso_proxima'] = True
                            cartoes_com[nome_canonico]['historico'].append({'data': datetime.now().strftime("%d/%m/%Y"), 'adversario': "N/I", 'cor': 'amarelo', 'terceiro_amarelo': cartoes_com[nome_canonico]['amarelos']>=3, 'suspenso_causada': cartoes_com[nome_canonico]['amarelos']>=3, 'suspenso_cumprida': False})
                        else:
                            cartoes_com[nome_canonico]['vermelho'] = True
                            cartoes_com[nome_canonico]['suspenso_proxima'] = True
                            cartoes_com[nome_canonico]['historico'].append({'data': datetime.now().strftime("%d/%m/%Y"), 'adversario': "N/I", 'cor': 'vermelho', 'terceiro_amarelo': False, 'suspenso_causada': True, 'suspenso_cumprida': False})
                        salvar_cartoes_json(cartoes_com, cat_com.replace("Comissão ", "").lower())
                        st.success("Cartão registrado!")
                        st.rerun()
    else:
        st.info("Nenhum dado de comissão disponível.")

# ----------------------------------------------------------------------
# ABA 3: MONITORAMENTO AO VIVO
# ----------------------------------------------------------------------
with tabs[2]:
    try:
        import pages.monitoramento as monitoramento
        monitoramento.show()
    except ImportError as e:
        st.error(f"Erro ao carregar página de monitoramento: {e}")

# ----------------------------------------------------------------------
# ABA 4: CARTÕES
# ----------------------------------------------------------------------
with tabs[3]:
    try:
        import pages.cartoes as cartoes
        cartoes.show()
    except ImportError as e:
        st.error(f"Erro ao carregar página de cartões: {e}")

# ----------------------------------------------------------------------
# ABA 5: PRÓXIMO JOGO
# ----------------------------------------------------------------------
with tabs[4]:
    try:
        import pages.proximo_jogo as proximo_jogo
        proximo_jogo.show()
    except ImportError as e:
        st.error(f"Erro ao carregar página de próximo jogo: {e}")

# ----------------------------------------------------------------------
# ABA 6: ESCALAÇÃO TÁTICA
# ----------------------------------------------------------------------
with tabs[5]:
    try:
        import pages.tatica_page as tatica_page
        tatica_page.show()
    except ImportError as e:
        st.error(f"Erro ao carregar página de tática: {e}")

# ----------------------------------------------------------------------
# ABA 7: GESTÃO
# ----------------------------------------------------------------------
with tabs[6]:
    try:
        import pages.gestao as gestao
        gestao.show()
    except ImportError as e:
        st.error(f"Erro ao carregar página de gestão: {e}")

# ----------------------------------------------------------------------
# ABA 8: RELATÓRIOS
# ----------------------------------------------------------------------
with tabs[7]:
    try:
        import pages.relatorios as relatorios
        relatorios.show()
    except ImportError as e:
        st.error(f"Erro ao carregar página de relatórios: {e}")

# ----------------------------------------------------------------------
# ABA 9: EXPORTAR
# ----------------------------------------------------------------------
with tabs[8]:
    st.header("📤 Exportar Dados")
    cat_export = st.selectbox(
        "Categoria",
        ["Profissional", "Sub-20", "Sub-17", "Comissão Profissional", "Comissão Sub-20", "Comissão Sub-17"],
        key="export_categoria"   # <-- CHAVE ÚNICA para evitar ID duplicado
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

# ----------------------------------------------------------------------
# ABA 10: VISUALIZAÇÃO TÁTICA
# ----------------------------------------------------------------------
with tabs[9]:
    try:
        import pages.visualizacao as visualizacao
        visualizacao.show()
    except ImportError as e:
        st.error(f"Erro ao carregar página de visualização: {e}")