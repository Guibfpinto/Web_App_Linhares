# pages/gestao.py
import os
import pandas as pd
import streamlit as st
import sqlite3
from utils import carregar_elenco_profissional

# ============================================================
# CONSTANTES E CONFIGURAÇÕES
# ============================================================
ARQUIVO_TREINOS = 'dados/treinos.csv'
ARQUIVO_WELLBEING = 'dados/wellbeing.csv'
ARQUIVO_LESOES = 'dados/lesoes.csv'
ARQUIVO_JOGOS = 'dados/jogos.csv'
ARQUIVO_GPS = 'dados/gps.csv'

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
# FUNÇÕES DE ACESSO AO BANCO (cada uma com sua conexão)
# ============================================================
def carregar_jogos():
    """Carrega jogos com JOINs corretos usando conexão local."""
    with sqlite3.connect('dados/database.db', timeout=10) as conn:
        query = """
            SELECT 
                j.id AS Jogo_ID,
                j.data_hora,
                j.gols_casa,
                j.gols_fora,
                tc.nome AS Mandante,
                tc.logo_url AS Escudo_Mandante,
                tf.nome AS Visitante,
                tf.logo_url AS Escudo_Visitante,
                v.nome AS Estadio,
                v.endereco AS Endereco_Estadio,
                v.imagem AS Foto_Estadio
            FROM jogos j
            INNER JOIN times tc ON j.time_casa_id = tc.id
            INNER JOIN times tf ON j.time_fora_id = tf.id
            LEFT JOIN venues v ON j.venue_id = v.id
            ORDER BY j.data_hora DESC
        """
        return pd.read_sql_query(query, conn)

def adicionar_jogo(time_casa_id, time_fora_id, gols_casa, gols_fora, status, data_hora, arbitro_id=None, venue_id=None):
    with sqlite3.connect('dados/database.db', timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO jogos 
            (time_casa_id, time_fora_id, gols_casa, gols_fora, status, data_hora, arbitro_id, venue_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (time_casa_id, time_fora_id, gols_casa, gols_fora, status, data_hora, arbitro_id, venue_id))
        conn.commit()
        return cursor.lastrowid

# ============================================================
# PÁGINA PRINCIPAL
# ============================================================
def show():
    st.title("⚙️ Gestão")
    tabs = st.tabs(["Atletas", "Treinos", "Well-being", "Lesões", "Jogos", "GPS"])

    df_atletas = carregar_elenco_profissional()
    lista_atletas = []
    if not df_atletas.empty:
        if 'nome' in df_atletas.columns:
            lista_atletas = df_atletas['nome'].dropna().tolist()
        elif 'nome_completo' in df_atletas.columns:
            lista_atletas = df_atletas['nome_completo'].dropna().tolist()

    # 1. ATLETAS
    with tabs[0]:
        st.subheader("Atletas")
        cols_exibicao = [c for c in ['nome_completo', 'apelido', 'Posicao_Principal', 'Idade', 'Estado_Fisico'] if c in df_atletas.columns]
        st.dataframe(df_atletas[cols_exibicao] if cols_exibicao else df_atletas, use_container_width=True)

    # 2. TREINOS
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

        st.dataframe(df_tr, use_container_width=True)

    # 3. WELL-BEING
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

        st.dataframe(df_wb, use_container_width=True)

    # 4. LESÕES
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

        st.dataframe(df_les, use_container_width=True)

    # 5. JOGOS (corrigido com conexão local e JOINs certos)
    with tabs[4]:
        st.subheader("Jogos")

        # Carregar dados com função dedicada (conexão local)
        try:
            df_jogos = carregar_jogos()

            if df_jogos.empty:
                st.info("Nenhum jogo cadastrado.")
            else:
                # Ajuste de fuso horário
                df_jogos['data_hora'] = pd.to_datetime(df_jogos['data_hora']) - pd.Timedelta(hours=3)
                df_jogos['Data_Hora'] = df_jogos['data_hora'].dt.strftime('%d/%m/%Y %H:%M')

                # Formatar placar
                df_jogos['Placar'] = df_jogos['gols_casa'].astype(str) + " x " + df_jogos['gols_fora'].astype(str)

                # Selecionar colunas para exibição
                colunas_exibicao = [
                    'Jogo_ID', 'Data_Hora', 'Mandante', 'Escudo_Mandante',
                    'Placar', 'Visitante', 'Escudo_Visitante',
                    'Estadio', 'Endereco_Estadio', 'Foto_Estadio'
                ]
                # Garantir que todas existam
                colunas_exibicao = [c for c in colunas_exibicao if c in df_jogos.columns]
                df_exibicao = df_jogos[colunas_exibicao]
                st.dataframe(df_exibicao, use_container_width=True)

                # Exibir fotos dos estádios (se houver)
                if 'Foto_Estadio' in df_jogos.columns:
                    for _, row in df_jogos.iterrows():
                        if row['Foto_Estadio'] and os.path.exists(row['Foto_Estadio']):
                            st.image(row['Foto_Estadio'], caption=row['Estadio'], width=200)

        except Exception as e:
            st.error(f"Erro ao carregar jogos: {e}")

        # Formulário para adicionar jogo (opcional)
        with st.expander("➕ Adicionar Novo Jogo", expanded=False):
            with st.form("form_novo_jogo", clear_on_submit=True):
                # Carregar times e venues para selects
                with sqlite3.connect('dados/database.db', timeout=10) as conn:
                    times_df = pd.read_sql_query("SELECT id, nome FROM times ORDER BY nome", conn)
                    venues_df = pd.read_sql_query("SELECT id, nome FROM venues ORDER BY nome", conn)

                time_casa = st.selectbox("Time da Casa", times_df['id'].tolist(), format_func=lambda x: times_df[times_df['id']==x]['nome'].iloc[0])
                time_fora = st.selectbox("Time Visitante", times_df['id'].tolist(), format_func=lambda x: times_df[times_df['id']==x]['nome'].iloc[0])
                gols_casa = st.number_input("Gols Casa", min_value=0, step=1, value=0)
                gols_fora = st.number_input("Gols Fora", min_value=0, step=1, value=0)
                status = st.selectbox("Status", ["NS", "1H", "2H", "HT", "FT", "AET", "PEN"])
                data_hora = st.text_input("Data/Hora (YYYY-MM-DD HH:MM)", value=pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"))
                arbitro_id = st.number_input("ID do Árbitro (opcional)", min_value=0, step=1, value=0)
                venue_id = st.selectbox("Estádio", venues_df['id'].tolist(), format_func=lambda x: venues_df[venues_df['id']==x]['nome'].iloc[0] if not venues_df.empty else "Nenhum")

                if st.form_submit_button("Salvar Jogo"):
                    # Inserir no banco
                    jogo_id = adicionar_jogo(
                        time_casa_id=time_casa,
                        time_fora_id=time_fora,
                        gols_casa=gols_casa,
                        gols_fora=gols_fora,
                        status=status,
                        data_hora=data_hora,
                        arbitro_id=arbitro_id if arbitro_id > 0 else None,
                        venue_id=venue_id if venue_id else None
                    )
                    if jogo_id:
                        st.success(f"Jogo {jogo_id} adicionado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao adicionar jogo.")

    # 6. GPS
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

        st.dataframe(df_gps, use_container_width=True)