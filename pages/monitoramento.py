# pages/monitoramento.py
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
from streamlit_autorefresh import st_autorefresh
import requests
from utils import (
    carregar_elenco_profissional,
    interpretar_formacao,
    mapear_nome_para_canonico,
    formatar_cartoes,
    inicializar_banco
)

# ============================================================
# CONFIGURAÇÕES
# ============================================================
TEAM_ID = 12928
BASE_URL_FASTAPI = "http://localhost:8000"

# ============================================================
# INICIALIZAÇÃO DO ESTADO DA SESSÃO
# ============================================================
def init_session_state():
    if "monitoramento_ativo" not in st.session_state:
        st.session_state.monitoramento_ativo = False
    if "fixture_id" not in st.session_state:
        st.session_state.fixture_id = None
    if "titulares" not in st.session_state:
        st.session_state.titulares = []
    if "reservas" not in st.session_state:
        st.session_state.reservas = []
    if "gols" not in st.session_state:
        st.session_state.gols = []
    if "eventos" not in st.session_state:
        st.session_state.eventos = []
    if "substituicoes" not in st.session_state:
        st.session_state.substituicoes = []
    if "total_substituicoes" not in st.session_state:
        st.session_state.total_substituicoes = 0
    if "ultimo_placar" not in st.session_state:
        st.session_state.ultimo_placar = (0, 0)
    if "linhares_e_casa" not in st.session_state:
        st.session_state.linhares_e_casa = True
    if "data_jogo" not in st.session_state:
        st.session_state.data_jogo = ""
    if "adversario" not in st.session_state:
        st.session_state.adversario = ""
    if "cartoes" not in st.session_state:
        st.session_state.cartoes = {}
    if "worker_ativo" not in st.session_state:
        st.session_state.worker_ativo = False
    if "ultima_atualizacao" not in st.session_state:
        st.session_state.ultima_atualizacao = None

init_session_state()

# ============================================================
# FUNÇÕES DE COMUNICAÇÃO COM A FASTAPI
# ============================================================
def chamar_api(endpoint, params=None):
    try:
        url = f"{BASE_URL_FASTAPI}{endpoint}"
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            return resp.json()
        return None
    except:
        return None

def verificar_jogo_ao_vivo():
    dados = chamar_api("/api/fixtures/live", params={"team_id": TEAM_ID})
    if dados and dados.get('fixture_id'):
        return dados['fixture_id']
    return None

def obter_detalhes_jogo(fixture_id):
    return chamar_api(f"/api/fixtures/{fixture_id}")

def obter_eventos_jogo(fixture_id):
    return chamar_api(f"/api/fixtures/{fixture_id}/events")

def obter_estatisticas_jogo(fixture_id):
    return chamar_api(f"/api/fixtures/{fixture_id}/statistics")

def obter_lineups_jogo(fixture_id):
    return chamar_api(f"/api/fixtures/{fixture_id}/lineups")

def obter_players_stats(fixture_id):
    return chamar_api(f"/api/fixtures/{fixture_id}/players")

# ============================================================
# FUNÇÕES DE ATUALIZAÇÃO (SQLite)
# ============================================================
def salvar_evento_sqlite(jogo_id, tempo, tipo, jogador_id, detalhes):
    conn = sqlite3.connect('meu_futebol.db', timeout=10)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO eventos (jogo_id, tempo, tipo, jogador_id, detalhes)
        VALUES (?, ?, ?, ?, ?)
    ''', (jogo_id, tempo, tipo, jogador_id, detalhes))
    conn.commit()
    conn.close()

def atualizar_placar_sqlite(jogo_id, gols_casa, gols_fora):
    conn = sqlite3.connect('meu_futebol.db', timeout=10)
    cursor = conn.cursor()
    cursor.execute("UPDATE jogos SET gols_casa = ?, gols_fora = ? WHERE id = ?", (gols_casa, gols_fora, jogo_id))
    conn.commit()
    conn.close()

def atualizar_status_sqlite(jogo_id, status):
    conn = sqlite3.connect('meu_futebol.db', timeout=10)
    cursor = conn.cursor()
    cursor.execute("UPDATE jogos SET status = ? WHERE id = ?", (status, jogo_id))
    conn.commit()
    conn.close()

# ============================================================
# PÁGINA PRINCIPAL
# ============================================================
def show():
    inicializar_banco()

    st.title("📊 Monitoramento ao Vivo")
    st.markdown("---")

    # ===== SIDEBAR: SELEÇÃO DE JOGO (apenas jogos do Linhares) =====
    st.sidebar.header("Selecionar Partida")

    conn = sqlite3.connect('meu_futebol.db', timeout=10)

    # Filtra apenas jogos onde Linhares é time da casa ou visitante
    try:
        df_jogos = pd.read_sql_query(f"""
            SELECT id, time_casa_id, time_fora_id, gols_casa, gols_fora, 
                   status, data_hora, formacao_casa, formacao_fora 
            FROM jogos 
            WHERE time_casa_id = {TEAM_ID} OR time_fora_id = {TEAM_ID}
                AND data_hora >= date('now')
            ORDER BY data_hora ASC
        """, conn)
    except Exception as e:
        st.error(f"Erro ao carregar jogos: {e}")
        conn.close()
        return

    try:
        times_df = pd.read_sql_query("SELECT id, nome FROM times", conn)
    except Exception as e:
        st.error(f"Erro ao carregar times: {e}")
        conn.close()
        return

    conn.close()

    times_dict = dict(zip(times_df['id'], times_df['nome']))

    if df_jogos.empty:
        st.sidebar.warning("Nenhum jogo do Linhares FC cadastrado.")
        if st.sidebar.button("📥 Buscar jogos da competição"):
            from monitoramento import buscar_jogos_competicao
            jogos_api = buscar_jogos_competicao()
            if jogos_api:
                conn = sqlite3.connect('meu_futebol.db', timeout=10)
                cursor = conn.cursor()
                for jogo in jogos_api:
                    cursor.execute("SELECT id FROM jogos WHERE id = ?", (jogo['id'],))
                    if not cursor.fetchone():
                        cursor.execute('''
                            INSERT INTO jogos (id, time_casa_id, time_fora_id, gols_casa, gols_fora, status, data_hora)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (jogo['id'], TEAM_ID if jogo['local'] == 'Casa' else 0, 
                              0 if jogo['local'] == 'Casa' else TEAM_ID,
                              jogo['gols_casa'], jogo['gols_fora'], jogo['status'], jogo['data']))
                conn.commit()
                conn.close()
                st.success(f"{len(jogos_api)} jogos importados!")
                st.rerun()
            else:
                st.error("Erro ao buscar jogos. Verifique o backend FastAPI.")
        st.stop()

    # Opções de jogos
    opcoes = []
    for _, row in df_jogos.iterrows():
        time_casa = times_dict.get(row['time_casa_id'], '?')
        time_fora = times_dict.get(row['time_fora_id'], '?')
        label = f"{time_casa} x {time_fora} ({row['data_hora'][:10]}) - {row['status']}"
        opcoes.append((row['id'], label))

    if not opcoes:
        st.sidebar.warning("Nenhum jogo disponível.")
        st.stop()

    jogo_selecionado_id = st.sidebar.selectbox(
        "Escolha a partida",
        options=[op[0] for op in opcoes],
        format_func=lambda x: next(op[1] for op in opcoes if op[0] == x)
    )

    # ===== CORPO PRINCIPAL =====
    conn = sqlite3.connect('meu_futebol.db', timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jogos WHERE id = ?", (jogo_selecionado_id,))
    colunas = [desc[0] for desc in cursor.description]
    jogo_data = cursor.fetchone()
    conn.close()
    if not jogo_data:
        st.error("Jogo não encontrado.")
        return
    jogo = dict(zip(colunas, jogo_data))

    time_casa = times_dict.get(jogo['time_casa_id'], 'Casa')
    time_fora = times_dict.get(jogo['time_fora_id'], 'Fora')
    gols_casa = jogo['gols_casa'] or 0
    gols_fora = jogo['gols_fora'] or 0
    status = jogo['status']
    data_hora = jogo.get('data_hora', '')

    # Verifica se a data do jogo é hoje (para liberar monitoramento)
    data_jogo = datetime.strptime(data_hora[:10], "%Y-%m-%d").date() if data_hora else None
    hoje = date.today()
    eh_hoje = (data_jogo == hoje) if data_jogo else False

    # ===== PLACAR E STATUS =====
    st.subheader(f"⚽ {time_casa} {gols_casa} x {gols_fora} {time_fora}")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write(f"**Status:** {status} | **Data:** {data_hora}")
    with col2:
        st.write(f"**Data:** {data_hora}")

    st.markdown("---")

    # ===== EVENTOS RECENTES =====
    conn = sqlite3.connect('meu_futebol.db', timeout=10)
    df_eventos = pd.read_sql_query(f"SELECT * FROM eventos WHERE jogo_id = {jogo_selecionado_id} ORDER BY tempo DESC LIMIT 10", conn)
    conn.close()
    st.write("**📋 Últimos eventos:**")
    if not df_eventos.empty:
        for _, ev in df_eventos.iterrows():
            st.write(f"- ⏱️ {ev['tempo']}' - {ev['tipo']} - {ev['detalhes']}")
    else:
        st.write("Nenhum evento registrado ainda.")

    st.markdown("---")

    # ===== CONTROLES =====
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**Controle de Status**")
        if status == 'NS' and st.button("▶️ Iniciar 1º Tempo", width='stretch'):
            atualizar_status_sqlite(jogo_selecionado_id, '1H')
            st.rerun()
        elif status == '1H' and st.button("⏸️ Intervalo", width='stretch'):
            atualizar_status_sqlite(jogo_selecionado_id, 'HT')
            st.rerun()
        elif status == 'HT' and st.button("▶️ Iniciar 2º Tempo", width='stretch'):
            atualizar_status_sqlite(jogo_selecionado_id, '2H')
            st.rerun()
        elif status == '2H' and st.button("⏹️ Encerrar", width='stretch'):
            atualizar_status_sqlite(jogo_selecionado_id, 'FT')
            st.success("Partida encerrada!")
            st.rerun()
        else:
            st.info("Partida não iniciada ou já encerrada.")

    with col2:
        st.write("**Adicionar Gol**")
        if status in ['1H', '2H', 'HT']:
            if st.button(f"⚽ {time_casa}", width='stretch'):
                atualizar_placar_sqlite(jogo_selecionado_id, gols_casa + 1, gols_fora)
                salvar_evento_sqlite(jogo_selecionado_id, 0, 'Goal', 0, f"Gol do {time_casa}")
                st.rerun()
            if st.button(f"⚽ {time_fora}", width='stretch'):
                atualizar_placar_sqlite(jogo_selecionado_id, gols_casa, gols_fora + 1)
                salvar_evento_sqlite(jogo_selecionado_id, 0, 'Goal', 0, f"Gol do {time_fora}")
                st.rerun()
        else:
            st.info("Partida não em andamento.")

    with col3:
        st.write("**Registrar Evento**")
        if status in ['1H', '2H', 'HT']:
            with st.form("evento_form"):
                tempo = st.number_input("Minuto", 0, 120, 0, step=1)
                tipo = st.selectbox("Tipo", ['Goal', 'Card', 'subst', 'Var'])
                detalhes = st.text_input("Detalhes")
                if st.form_submit_button("Adicionar Evento", width='stretch'):
                    salvar_evento_sqlite(jogo_selecionado_id, tempo, tipo, 0, detalhes)
                    st.success("Evento adicionado!")
                    st.rerun()
        else:
            st.info("Partida não em andamento.")

    st.markdown("---")

    # ===== MONITORAMENTO AUTOMÁTICO =====
    st.subheader("🔄 Monitoramento Automático")

    # Verifica se a data do jogo é hoje
    if not eh_hoje:
        st.warning("⚠️ O monitoramento só pode ser iniciado no dia da partida.")
        monitor_habilitado = False
    else:
        monitor_habilitado = True

    if monitor_habilitado:
        if st.button("🔍 Verificar Jogo ao Vivo", width='stretch'):
            fixture_id = verificar_jogo_ao_vivo()
            if fixture_id:
                st.session_state.fixture_id = fixture_id
                st.session_state.monitoramento_ativo = True
                st.success(f"Jogo ao vivo encontrado! ID: {fixture_id}")
                st.rerun()
            else:
                st.warning("Nenhum jogo ao vivo encontrado. Tente novamente quando a partida começar.")
    else:
        st.button("🔍 Verificar Jogo ao Vivo", width='stretch', disabled=True)

    if st.session_state.monitoramento_ativo and st.session_state.fixture_id:
        st_autorefresh(interval=10000, key="monitor_auto")

        fixture_id = st.session_state.fixture_id
        st.info(f"Monitorando partida {fixture_id}...")

        detalhes = obter_detalhes_jogo(fixture_id)
        if detalhes:
            gols_casa_api = detalhes['goals']['home'] or 0
            gols_fora_api = detalhes['goals']['away'] or 0
            if (gols_casa_api, gols_fora_api) != (gols_casa, gols_fora):
                atualizar_placar_sqlite(jogo_selecionado_id, gols_casa_api, gols_fora_api)
                st.rerun()

            status_api = detalhes['fixture']['status']['short']
            if status_api != status:
                atualizar_status_sqlite(jogo_selecionado_id, status_api)
                st.rerun()

            st.write(f"**Status:** {status_api} | **Minuto:** {detalhes['fixture']['status'].get('elapsed', 0)}")

        eventos_api = obter_eventos_jogo(fixture_id)
        if eventos_api:
            conn = sqlite3.connect('meu_futebol.db')
            cursor = conn.cursor()
            for ev in eventos_api:
                cursor.execute("SELECT id FROM eventos WHERE jogo_id = ? AND tempo = ? AND tipo = ? AND jogador_id = ?",
                               (jogo_selecionado_id, ev['time']['elapsed'], ev['type'], ev.get('player', {}).get('id', 0)))
                if not cursor.fetchone():
                    jogador_nome = ev.get('player', {}).get('name', '')
                    if jogador_nome:
                        cursor.execute("SELECT id FROM elenco WHERE nome = ? OR apelido = ?", (jogador_nome, jogador_nome))
                        jogador = cursor.fetchone()
                        jogador_id = jogador[0] if jogador else 0
                    else:
                        jogador_id = 0
                    cursor.execute('''
                        INSERT INTO eventos (jogo_id, tempo, tipo, jogador_id, detalhes)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (jogo_selecionado_id, ev['time']['elapsed'], ev['type'], jogador_id, ev.get('detail', '')))
            conn.commit()
            conn.close()
            st.rerun()

        if st.button("⏹️ Parar Monitoramento", width='stretch'):
            st.session_state.monitoramento_ativo = False
            st.session_state.fixture_id = None
            st.rerun()

    st.markdown("---")
    st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")