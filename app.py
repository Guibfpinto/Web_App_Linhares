# app.py
import streamlit as st
import sys
import os
import bcrypt
import json

# Adiciona a pasta pages ao path
sys.path.append(os.path.join(os.path.dirname(__file__), "pages"))

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Linhares FC - Sistema de Análise de Elenco",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# CSS PERSONALIZADO
# ============================================================
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("background.png");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    .main > div {
        background-color: rgba(255,255,255,0.88);
        padding: 20px;
        border-radius: 12px;
        margin: 10px;
    }
    @media (max-width: 640px) {
        .main > div {
            padding: 10px !important;
            margin: 5px !important;
        }
        .stButton button {
            font-size: 16px !important;
            padding: 10px !important;
            width: 100% !important;
        }
        .stSelectbox, .stTextInput {
            font-size: 16px !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# FUNÇÕES DE AUTENTICAÇÃO LOCAL (igual ao PyQt)
# ============================================================
ARQUIVO_USUARIOS = "usuarios.json"

def carregar_usuarios():
    if not os.path.exists(ARQUIVO_USUARIOS):
        # Cria usuário padrão
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

# ============================================================
# SESSÃO E LOGIN
# ============================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""

if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center;'>⚽ Linhares FC</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Sistema de Análise de Elenco</h3>", unsafe_allow_html=True)
    st.markdown("---")
    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")
        if submitted:
            if autenticar_usuario(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Credenciais inválidas")
    st.stop()

# ============================================================
# MENU PRINCIPAL
# ============================================================
st.sidebar.image("logo.png", width=150) if os.path.exists("logo.png") else None
st.sidebar.title(f"Olá, {st.session_state.username}!")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navegação",
    ["📊 Monitoramento ao Vivo",
     "📅 Próximo Jogo",
     "📋 Análise de Elenco",
     "📄 Relatórios",
     "📐 Escalação Tática",
     "⚙️ Gestão Esportiva",
     "📈 Visualização Tática"],
    index=0
)

if st.sidebar.button("Sair"):
    st.session_state.authenticated = False
    st.rerun()

# ============================================================
# ROTEAMENTO
# ============================================================
if menu == "📊 Monitoramento ao Vivo":
    import pages.monitoramento as monitoramento
    monitoramento.show()
elif menu == "📅 Próximo Jogo":
    import pages.proximo_jogo as proximo_jogo
    proximo_jogo.show()
elif menu == "📋 Análise de Elenco":
    import pages.analise as analise
    analise.show()
elif menu == "📄 Relatórios":
    import pages.relatorios as relatorios
    relatorios.show()
elif menu == "📐 Escalação Tática":
    import pages.tatica_page as tatica_page
    tatica_page.show()
elif menu == "⚙️ Gestão Esportiva":
    import pages.gestao as gestao
    gestao.show()
elif menu == "📈 Visualização Tática":
    import pages.visualizacao as visualizacao
    visualizacao.show()