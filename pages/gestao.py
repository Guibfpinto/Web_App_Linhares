# pages/gestao.py
import os
import pandas as pd
import streamlit as st
import sqlite3
from utils import carregar_elenco_profissional

# ============================================================
# CONSTANTES
# ============================================================
ARQUIVO_TREINOS = 'dados/treinos.csv'
ARQUIVO_WELLBEING = 'dados/wellbeing.csv'
ARQUIVO_LESOES = 'dados/lesoes.csv'
ARQUIVO_JOGOS = 'dados/jogos.csv'
ARQUIVO_GPS = 'dados/gps.csv'
BANCO_DADOS = 'meu_futebol.db'

# ============================================================
# FUNÇÕES DE ACESSO AO BANCO (thread-safe com check_same_thread=False)
# ============================================================

def get_connection():
    """Retorna uma nova conexão SQLite com check_same_thread=False."""
    return sqlite3.connect(BANCO_DADOS, timeout=10, check_same_thread=False)

def carregar_jogos():
    """Carrega jogos com JOINs, usando conexão local e fechando imediatamente."""
    try:
        with get_connection() as conn:
            query = """
                SELECT 
                    j.id AS Jogo_ID,
                    j.data_hora,
                    j.gols_casa,
                    j.gols_fora,
                    tc.nome AS Mandante,
                    tf.nome AS Visitante,
                    v.nome AS Estadio,
                    a.nome AS Arbitro
                FROM jogos j
                INNER JOIN times tc ON j.time_casa_id = tc.id
                INNER JOIN times tf ON j.time_fora_id = tf.id
                LEFT JOIN venues v ON j.venue_id = v.id
                LEFT JOIN arbitros a ON j.arbitro_id = a.id
                ORDER BY j.data_hora DESC
            """
            return pd.read_sql_query(query, conn)
    except sqlite3.OperationalError as e:
        # Se a tabela venues ou arbitros não existir, tenta sem os JOINs
        if "no such table" in str(e):
            with get_connection() as conn:
                query = """
                    SELECT 
                        j.id AS Jogo_ID,
                        j.data_hora,
                        j.gols_casa,
                        j.gols_fora,
                        tc.nome AS Mandante,
                        tf.nome AS Visitante
                    FROM jogos j
                    INNER JOIN times tc ON j.time_casa_id = tc.id
                    INNER JOIN times tf ON j.time_fora_id = tf.id
                    ORDER BY j.data_hora DESC
                """
                return pd.read_sql_query(query, conn)
        else:
            raise

def adicionar_jogo(time_casa_id, time_fora_id, gols_casa, gols_fora, status, data_hora, arbitro_id=None, venue_id=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO jogos 
            (time_casa_id, time_fora_id, gols_casa, gols_fora, status, data_hora, arbitro_id, venue_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (time_casa_id, time_fora_id, gols_casa, gols_fora, status, data_hora, arbitro_id, venue_id))
        conn.commit()
        return cursor.lastrowid

def carregar_times():
    with get_connection() as conn:
        return pd.read_sql_query("SELECT id, nome FROM times ORDER BY nome", conn)

def carregar_venues():
    try:
        with get_connection() as conn:
            return pd.read_sql_query("SELECT id, nome FROM venues ORDER BY nome", conn)
    except sqlite3.OperationalError:
        return pd.DataFrame(columns=['id', 'nome'])

def carregar_arbitros():
    try:
        with get_connection() as conn:
            return pd.read_sql_query("SELECT id, nome FROM arbitros ORDER BY nome", conn)
    except sqlite3.OperationalError:
        return pd.DataFrame(columns=['id', 'nome'])

# ============================================================
# FUNÇÕES PARA CSV
# ============================================================
def carregar_dados_csv(caminho: str, colunas_padrao: list) -> pd.DataFrame:
    if os.path.exists(caminho):
        try:
            return pd.read_csv(caminho, sep=';', encoding='utf-8-sig')
        except Exception:
            try:
                return pd.read_csv(caminho, sep=',', encoding='utf-8-sig')
            except Exception:
                return pd.DataFrame(columns=colunas_padrao)
    return pd.DataFrame(columns=colunas_padrao)

def salvar_dados_csv(df: pd.DataFrame, caminho: str):
    pasta = os.path.dirname(caminho)
    if pasta:
        os.makedirs(pasta, exist_ok=True)
    df.to_csv(caminho, sep=';', index=False, encoding='utf-8-sig')

# ============================================================
# PÁGINA PRINCIPAL
# ============================================================
def show():
    st.title("⚙️ Gestão")
    tabs = st.tabs(["Atletas", "Treinos", "Well-being", "Lesões", "Jogos", "GPS"])

    # ==========================================================
    # ATLETAS
    # ==========================================================
    with tabs[0]:
        st.subheader("Atletas")
        df_atletas = carregar_elenco_profissional()
        if df_atletas is not None and not df_atletas.empty:
            cols_exibicao = [c for c in ['nome_completo', 'apelido', 'Posicao_Principal', 'Idade', 'Estado_Fisico'] if c in df_atletas.columns]
            st.dataframe(df_atletas[cols_exibicao] if cols_exibicao else df_atletas, use_container_width=True)
        else:
            st.info("Nenhum atleta cadastrado.")

        # Lista de atletas para usar nos outros formulários
        lista_atletas = []
        if df_atletas is not None and not df_atletas.empty:
            if 'nome' in df_atletas.columns:
                lista_atletas = df_atletas['nome'].dropna().tolist()
            elif 'nome_completo' in df_atletas.columns:
                lista_atletas = df_atletas['nome_completo'].dropna().tolist()

    # ==========================================================
    # TREINOS
    # ==========================================================
    with tabs[1]:
        st.subheader("Treinos")
        cols_tr = ['data', 'tipo', 'descricao', 'pse_alvo']
        df_tr = carregar_dados_csv(ARQUIVO_TREINOS, cols_tr)

        with st.expander("➕ Cadastrar Novo Treino"):
            with st.form("form_treino", clear_on_submit=True):
                data = st.date_input("Data do Treino")
                tipo = st.selectbox("Tipo de Treino", ["Tático", "Técnico", "Físico", "Academia", "Recuperação"])
                desc = st.text_area("Descrição/Objetivo")
                pse = st.slider("PSE Alvo (1-10)", 1, 10, 5)

                if st.form_submit_button("Salvar Treino"):
                    novo = pd.DataFrame([{
                        'data': str(data),
                        'tipo': tipo,
                        'descricao': desc,
                        'pse_alvo': pse
                    }])
                    df_tr = pd.concat([df_tr, novo], ignore_index=True)
                    salvar_dados_csv(df_tr, ARQUIVO_TREINOS)
                    st.success("Treino salvo no CSV com sucesso!")
                    st.rerun()
                    return  # Interrompe execução para evitar reexecução

        st.dataframe(df_tr, use_container_width=True)

    # ==========================================================
    # WELL-BEING
    # ==========================================================
    with tabs[2]:
        st.subheader("Well-being")
        cols_wb = ['atleta', 'data', 'sono', 'fadiga', 'dor', 'estresse']
        df_wb = carregar_dados_csv(ARQUIVO_WELLBEING, cols_wb)

        with st.expander("➕ Cadastrar Avaliação de Well-Being"):
            with st.form("form_wb", clear_on_submit=True):
                atleta = st.selectbox("Atleta", lista_atletas if lista_atletas else ["Sem atletas registrados"])
                dt_wb = st.date_input("Data")
                c1, c2 = st.columns(2)
                sono = c1.slider("Sono (1-5)", 1, 5, 3)
                fadiga = c2.slider("Fadiga (1-5)", 1, 5, 3)
                c3, c4 = st.columns(2)
                dor = c3.slider("Dor Muscular (1-5)", 1, 5, 3)
                estresse = c4.slider("Estresse (1-5)", 1, 5, 3)

                if st.form_submit_button("Salvar Well-Being"):
                    novo = pd.DataFrame([{
                        'atleta': atleta,
                        'data': str(dt_wb),
                        'sono': sono,
                        'fadiga': fadiga,
                        'dor': dor,
                        'estresse': estresse
                    }])
                    df_wb = pd.concat([df_wb, novo], ignore_index=True)
                    salvar_dados_csv(df_wb, ARQUIVO_WELLBEING)
                    st.success("Well-being salvo no CSV!")
                    st.rerun()
                    return

        st.dataframe(df_wb, use_container_width=True)

    # ==========================================================
    # LESÕES
    # ==========================================================
    with tabs[3]:
        st.subheader("Lesões / Departamento Médico")
        cols_les = ['atleta', 'lesao', 'data_lesao', 'previsao_retorno', 'status']
        df_les = carregar_dados_csv(ARQUIVO_LESOES, cols_les)

        with st.expander("➕ Cadastrar Registro Médico"):
            with st.form("form_lesao", clear_on_submit=True):
                atleta_l = st.selectbox("Atleta", lista_atletas if lista_atletas else ["Sem atletas registrados"])
                diag = st.text_input("Diagnóstico / Local")
                c1, c2 = st.columns(2)
                dt_l = c1.date_input("Data da Lesão")
                dt_ret = c2.date_input("Previsão de Retorno")
                status = st.selectbox("Status", ["Tratamento", "Transição", "Liberado"])

                if st.form_submit_button("Salvar Lesão"):
                    novo = pd.DataFrame([{
                        'atleta': atleta_l,
                        'lesao': diag,
                        'data_lesao': str(dt_l),
                        'previsao_retorno': str(dt_ret),
                        'status': status
                    }])
                    df_les = pd.concat([df_les, novo], ignore_index=True)
                    salvar_dados_csv(df_les, ARQUIVO_LESOES)
                    st.success("Lesão salva no CSV!")
                    st.rerun()
                    return

        st.dataframe(df_les, use_container_width=True)

    # ==========================================================
    # JOGOS (com conexões SQLite locais)
    # ==========================================================
    with tabs[4]:
        st.subheader("Jogos")

        try:
            df_jogos = carregar_jogos()
            if df_jogos.empty:
                st.info("Nenhum jogo cadastrado.")
            else:
                # Ajuste de fuso horário
                if 'data_hora' in df_jogos.columns:
                    df_jogos['data_hora'] = pd.to_datetime(df_jogos['data_hora']) - pd.Timedelta(hours=3)
                    df_jogos['Data_Hora'] = df_jogos['data_hora'].dt.strftime('%d/%m/%Y %H:%M')
                    df_jogos['Placar'] = df_jogos['gols_casa'].astype(str) + " x " + df_jogos['gols_fora'].astype(str)

                    # Selecionar colunas para exibição
                    colunas_exibicao = ['Jogo_ID', 'Data_Hora', 'Mandante', 'Placar', 'Visitante', 'Estadio', 'Arbitro']
                    colunas_exibicao = [c for c in colunas_exibicao if c in df_jogos.columns]
                    st.dataframe(df_jogos[colunas_exibicao], use_container_width=True)
                else:
                    st.dataframe(df_jogos, use_container_width=True)

        except Exception as e:
            st.error(f"Erro ao carregar jogos: {e}")

        # Formulário para adicionar jogo
        with st.expander("➕ Adicionar Novo Jogo", expanded=False):
            with st.form("form_novo_jogo", clear_on_submit=True):
                times_df = carregar_times()
                venues_df = carregar_venues()
                arbitros_df = carregar_arbitros()

                if times_df.empty:
                    st.warning("Nenhum time cadastrado. Cadastre times primeiro.")
                else:
                    time_casa = st.selectbox("Time da Casa", times_df['id'].tolist(), format_func=lambda x: times_df[times_df['id']==x]['nome'].iloc[0])
                    time_fora = st.selectbox("Time Visitante", times_df['id'].tolist(), format_func=lambda x: times_df[times_df['id']==x]['nome'].iloc[0])
                    gols_casa = st.number_input("Gols Casa", min_value=0, step=1, value=0)
                    gols_fora = st.number_input("Gols Fora", min_value=0, step=1, value=0)
                    status = st.selectbox("Status", ["NS", "1H", "2H", "HT", "FT", "AET", "PEN"])
                    data_hora = st.text_input("Data/Hora (YYYY-MM-DD HH:MM)", value=pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"))

                    if not venues_df.empty:
                        venue_id = st.selectbox("Estádio", venues_df['id'].tolist(), format_func=lambda x: venues_df[venues_df['id']==x]['nome'].iloc[0])
                    else:
                        venue_id = None
                        st.info("Nenhum estádio cadastrado. Cadastre antes na aba 'Estádios'.")

                    if not arbitros_df.empty:
                        arbitro_id = st.selectbox("Árbitro", arbitros_df['id'].tolist(), format_func=lambda x: arbitros_df[arbitros_df['id']==x]['nome'].iloc[0])
                    else:
                        arbitro_id = None
                        st.info("Nenhum árbitro cadastrado. Cadastre antes na aba 'Árbitros'.")

                    if st.form_submit_button("Salvar Jogo"):
                        jogo_id = adicionar_jogo(
                            time_casa_id=time_casa,
                            time_fora_id=time_fora,
                            gols_casa=gols_casa,
                            gols_fora=gols_fora,
                            status=status,
                            data_hora=data_hora,
                            arbitro_id=arbitro_id,
                            venue_id=venue_id
                        )
                        if jogo_id:
                            st.success(f"Jogo {jogo_id} adicionado com sucesso!")
                            st.rerun()
                            return
                        else:
                            st.error("Erro ao adicionar jogo.")

    # ==========================================================
    # GPS
    # ==========================================================
    with tabs[5]:
        st.subheader("Métricas de GPS")
        cols_gps = ['atleta', 'data', 'distancia_m', 'alta_intensidade_m', 'vel_max', 'sprints']
        df_gps = carregar_dados_csv(ARQUIVO_GPS, cols_gps)

        with st.expander("➕ Cadastrar Carga GPS"):
            with st.form("form_gps", clear_on_submit=True):
                atleta_g = st.selectbox("Atleta", lista_atletas if lista_atletas else ["Sem atletas registrados"])
                dt_g = st.date_input("Data da Sessão")
                c1, c2, c3, c4 = st.columns(4)
                dist = c1.number_input("Dist. Total (m)", step=100.0)
                alta_i = c2.number_input("Alta Intensidade (m)", step=10.0)
                v_max = c3.number_input("Vel. Máx (km/h)", step=0.1)
                sprints = c4.number_input("Sprints", min_value=0)

                if st.form_submit_button("Salvar GPS"):
                    novo = pd.DataFrame([{
                        'atleta': atleta_g,
                        'data': str(dt_g),
                        'distancia_m': dist,
                        'alta_intensidade_m': alta_i,
                        'vel_max': v_max,
                        'sprints': sprints
                    }])
                    df_gps = pd.concat([df_gps, novo], ignore_index=True)
                    salvar_dados_csv(df_gps, ARQUIVO_GPS)
                    st.success("Dados de GPS salvos no CSV!")
                    st.rerun()
                    return

        st.dataframe(df_gps, use_container_width=True)