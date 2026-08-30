# pages/monitoramento.py
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
from streamlit_autorefresh import st_autorefresh
import requests
from utils import (
    carregar_elenco_profissional,
    carregar_elenco_sub15,
    carregar_elenco_sub17,
    carregar_cartoes_json,
    salvar_cartoes_json,
    interpretar_formacao,
    mapear_nome_para_canonico,
    inicializar_banco,
    jogador_suspenso,
)

# ============================================================
# MAPEAMENTO DE CATEGORIAS PARA IDs
# ============================================================
CATEGORIA_CONFIG = {
    "Profissional": {
        "team_id": 12928,
        "competicao_id": 2,          # Capixaba Série B
        "nome_time": "Linhares FC",
        "elenco_func": carregar_elenco_profissional,
        "cartoes_key": "profissional",
        "liga_nome": "Campeonato Capixaba Série B"
    },
    "Sub-15": {
        "team_id": 27831,
        "competicao_id": 11,         # Copa Espírito Santo Sub-15
        "nome_time": "Linhares FC Sub-15",
        "elenco_func": carregar_elenco_sub15,
        "cartoes_key": "sub15",
        "liga_nome": "Copa Espírito Santo Sub-15"
    },
    "Sub-17": {
        "team_id": 27832,
        "competicao_id": 10,         # Copa Espírito Santo Sub-17
        "nome_time": "Linhares FC Sub-17",
        "elenco_func": carregar_elenco_sub17,
        "cartoes_key": "sub17",
        "liga_nome": "Copa Espírito Santo Sub-17"
    }
}

# ============================================================
# FUNÇÕES DE ACESSO À API FASTAPI (dinâmicas)
# ============================================================
BASE_URL_FASTAPI = "http://localhost:8000"

def chamar_api(endpoint, params=None):
    try:
        url = f"{BASE_URL_FASTAPI}{endpoint}"
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            return resp.json()
        return None
    except:
        return None

def verificar_jogo_ao_vivo(team_id):
    """Verifica se há um jogo ao vivo do time especificado."""
    dados = chamar_api("/api/fixtures/live", params={"team_id": team_id})
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

def buscar_jogos_competicao(team_id, competicao_id, season=2026):
    """Busca jogos do time em uma competição específica."""
    params = {
        "league": competicao_id,
        "season": season,
        "team": team_id,
        "from": "2026-07-12",
        "to": "2026-08-29"
    }
    jogos = chamar_api("/api/fixtures", params=params)
    if not jogos:
        return []
    jogos_resumidos = []
    for jogo in jogos:
        if jogo['teams']['home']['id'] == team_id:
            adversario = jogo['teams']['away']['name']
            local = "Casa"
        else:
            adversario = jogo['teams']['home']['name']
            local = "Fora"
        status = jogo['fixture']['status']['short']
        data = jogo['fixture']['date'][:10]
        gols_casa = jogo['goals']['home']
        gols_fora = jogo['goals']['away']
        jogos_resumidos.append({
            'id': jogo['fixture']['id'],
            'data': data,
            'adversario': adversario,
            'local': local,
            'status': status,
            'gols_casa': gols_casa,
            'gols_fora': gols_fora
        })
    return jogos_resumidos

# ============================================================
# FUNÇÕES DE ATUALIZAÇÃO DO BANCO (SQLite)
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

def atualizar_arbitro_jogo(jogo_id, arbitro_id):
    conn = sqlite3.connect('meu_futebol.db', timeout=10)
    cursor = conn.cursor()
    cursor.execute("UPDATE jogos SET arbitro_id = ? WHERE id = ?", (arbitro_id, jogo_id))
    conn.commit()
    conn.close()

# ============================================================
# FUNÇÃO AUXILIAR PARA MONTAR TIME
# ============================================================
def montar_time(df, formacao_str, cartoes, incluir_lesionados=False):
    if df.empty:
        return None, None
    defensores, meias, atacantes, posicoes = interpretar_formacao(formacao_str)
    if not posicoes:
        return None, None
    titulares = []
    reservas = []
    jogadores_usados = []
    for pos_exibida, pos_tipo in posicoes:
        candidatos = df.copy()
        if pos_tipo == 'Goleiro':
            candidatos = candidatos[candidatos['Posicao_Principal'] == 'Goleiro']
        else:
            candidatos = candidatos[~candidatos['Posicao_Principal'].isin(['Goleiro'])]
        if not incluir_lesionados and 'lesionado' in candidatos.columns:
            candidatos = candidatos[~candidatos['lesionado']]
        candidatos = candidatos[~candidatos['nome_completo'].isin(jogadores_usados)]
        candidatos = candidatos[~candidatos['nome_completo'].apply(lambda x: jogador_suspenso(mapear_nome_para_canonico(x), cartoes))]
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
    reservas_df = df[~df['nome_completo'].isin(jogadores_usados)]
    if not incluir_lesionados and 'lesionado' in reservas_df.columns:
        reservas_df = reservas_df[~reservas_df['lesionado']]
    reservas_df = reservas_df.sort_values('Rating_Geral_FM26', ascending=False)
    for _, row in reservas_df.head(12).iterrows():
        reservas.append({
            'nome': row['nome_completo'],
            'apelido': row['apelido'],
            'row': row
        })
    return titulares, reservas

# ============================================================
# PÁGINA PRINCIPAL
# ============================================================
def show():
    # ===== OBTÉM A CATEGORIA DO SESSION_STATE =====
    categoria = st.session_state.get("categoria_monitoramento", "Profissional")
    config = CATEGORIA_CONFIG.get(categoria)
    if not config:
        st.error(f"Categoria '{categoria}' inválida.")
        return

    team_id = config["team_id"]
    competicao_id = config["competicao_id"]
    nome_time = config["nome_time"]
    elenco_func = config["elenco_func"]
    cartoes_key = config["cartoes_key"]

    st.title(f"📊 Monitoramento ao Vivo - {categoria}")
    st.markdown(f"**Time:** {nome_time} (ID: {team_id}) | **Competição:** {config['liga_nome']} (ID: {competicao_id})")
    st.markdown("---")

    # ===== CARREGA DADOS DA CATEGORIA =====
    df_elenco = elenco_func()
    cartoes, _ = carregar_cartoes_json(cartoes_key)
    if df_elenco is None or df_elenco.empty:
        st.warning(f"Elenco não disponível para {categoria}.")
        return

    inicializar_banco()

    # ===== SIDEBAR: SELEÇÃO DE JOGO (apenas jogos do time escolhido e futuros) =====
    st.sidebar.header("Selecionar Partida")
    conn = sqlite3.connect('meu_futebol.db', timeout=10)

    try:
        df_jogos = pd.read_sql_query(f"""
            SELECT j.id, j.time_casa_id, j.time_fora_id, j.gols_casa, j.gols_fora, 
                   j.status, j.data_hora, j.formacao_casa, j.formacao_fora,
                   j.arbitro_id,
                   v.nome AS estadio
            FROM jogos j
            LEFT JOIN venues v ON j.venue_id = v.id
            WHERE (j.time_casa_id = {team_id} OR j.time_fora_id = {team_id})
              AND substr(j.data_hora, 1, 10) >= date('now')
            ORDER BY j.data_hora ASC
        """, conn)
    except Exception as e:
        st.error(f"Erro ao carregar jogos: {e}")
        conn.close()
        return

    try:
        times_df = pd.read_sql_query("SELECT id, nome FROM times", conn)
        arbitros_df = pd.read_sql_query("SELECT id, nome, categoria FROM arbitros ORDER BY nome", conn)
    except Exception as e:
        st.error(f"Erro ao carregar times ou árbitros: {e}")
        conn.close()
        return

    conn.close()

    times_dict = dict(zip(times_df['id'], times_df['nome']))
    arbitros_dict = dict(zip(arbitros_df['id'], arbitros_df['nome']))

    if df_jogos.empty:
        st.sidebar.warning(f"Nenhum jogo futuro do {nome_time} cadastrado.")
        if st.sidebar.button("📥 Buscar jogos da competição"):
            jogos_api = buscar_jogos_competicao(team_id, competicao_id)
            if jogos_api:
                conn = sqlite3.connect('meu_futebol.db', timeout=10)
                cursor = conn.cursor()
                for jogo in jogos_api:
                    cursor.execute("SELECT id FROM jogos WHERE id = ?", (jogo['id'],))
                    if not cursor.fetchone():
                        if jogo['local'] == 'Casa':
                            time_casa = team_id
                            time_fora = 0
                        else:
                            time_casa = 0
                            time_fora = team_id
                        cursor.execute('''
                            INSERT INTO jogos (id, time_casa_id, time_fora_id, gols_casa, gols_fora, status, data_hora)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (jogo['id'], time_casa, time_fora, jogo['gols_casa'], jogo['gols_fora'], jogo['status'], jogo['data']))
                conn.commit()
                conn.close()
                st.success(f"{len(jogos_api)} jogos importados!")
                st.rerun()
            else:
                st.error("Erro ao buscar jogos. Verifique o backend FastAPI.")
        st.stop()

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
        format_func=lambda x: next(op[1] for op in opcoes if op[0] == x),
        index=0
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
    arbitro_id_atual = jogo.get('arbitro_id')

    # Verifica se a data do jogo é hoje
    data_jogo = datetime.strptime(data_hora[:10], "%Y-%m-%d").date() if data_hora else None
    hoje = date.today()
    eh_hoje = (data_jogo == hoje) if data_jogo else False

    # ===== PLACAR, STATUS E ÁRBITRO =====
    st.subheader(f"⚽ {time_casa} {gols_casa} x {gols_fora} {time_fora}")
    col1, col2, col_arb = st.columns([2, 1, 1.5])
    with col1:
        st.write(f"**Status:** {status} | **Data:** {data_hora}")
    with col2:
        if jogo.get('estadio'):
            st.write(f"**Local:** {jogo['estadio']}")
    with col_arb:
        nome_arbitro = arbitros_dict.get(arbitro_id_atual, 'Não definido')
        st.write(f"**🟨 Árbitro:** {nome_arbitro}")

    # ===== SELETOR DE ÁRBITRO =====
    if not arbitros_df.empty:
        with st.expander("👨‍⚖️ Associar/Alterar Árbitro", expanded=False):
            with st.form("form_arbitro"):
                current_index = 0
                if arbitro_id_atual in arbitros_df['id'].values:
                    current_index = arbitros_df[arbitros_df['id'] == arbitro_id_atual].index[0]

                novo_arbitro = st.selectbox(
                    "Selecione o árbitro",
                    options=arbitros_df['id'].tolist(),
                    format_func=lambda x: f"{arbitros_df[arbitros_df['id'] == x]['nome'].iloc[0]} ({arbitros_df[arbitros_df['id'] == x]['categoria'].iloc[0]})",
                    index=current_index
                )
                if st.form_submit_button("Salvar Árbitro"):
                    atualizar_arbitro_jogo(jogo_selecionado_id, novo_arbitro)
                    st.success("Árbitro associado com sucesso!")
                    st.rerun()
    else:
        st.warning("Nenhum árbitro cadastrado. Cadastre árbitros na seção apropriada.")

    st.markdown("---")

    # ===== EVENTOS RECENTES =====
    conn = sqlite3.connect('meu_futebol.db', timeout=10)
    df_eventos = pd.read_sql_query(f"""
        SELECT e.*, el.nome AS jogador_nome 
        FROM eventos e
        LEFT JOIN elenco el ON e.jogador_id = el.id
        WHERE e.jogo_id = {jogo_selecionado_id}
        ORDER BY e.tempo DESC LIMIT 10
    """, conn)
    conn.close()
    st.write("**📋 Últimos eventos:**")
    if not df_eventos.empty:
        for _, ev in df_eventos.iterrows():
            jogador = ev['jogador_nome'] if ev['jogador_nome'] else 'Desconhecido'
            st.write(f"- ⏱️ {ev['tempo']}' - {ev['tipo']} - {jogador} - {ev['detalhes']}")
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
                conn = sqlite3.connect('meu_futebol.db', timeout=10)
                jogadores_df = pd.read_sql_query(f"""
                    SELECT id, nome FROM elenco 
                    WHERE time_id IN ({jogo['time_casa_id']}, {jogo['time_fora_id']})
                    ORDER BY nome
                """, conn)
                conn.close()
                jogadores_opcoes = ["Nenhum"] + jogadores_df['nome'].tolist()
                jogador_nome = st.selectbox("Jogador", jogadores_opcoes)
                if jogador_nome != "Nenhum":
                    jogador_id = jogadores_df[jogadores_df['nome'] == jogador_nome]['id'].iloc[0]
                else:
                    jogador_id = 0
                detalhes = st.text_input("Detalhes")
                if st.form_submit_button("Adicionar Evento", width='stretch'):
                    salvar_evento_sqlite(jogo_selecionado_id, tempo, tipo, jogador_id, detalhes)
                    st.success("Evento adicionado!")
                    st.rerun()
        else:
            st.info("Partida não em andamento.")

    st.markdown("---")

    # ===== ESCALAÇÃO E FORMAÇÃO =====
    st.subheader("📋 Escalação e Formação")

    with st.expander("✏️ Definir Formações", expanded=False):
        with st.form("formacao_form"):
            formacao_casa = jogo.get('formacao_casa', '')
            formacao_fora = jogo.get('formacao_fora', '')
            nova_casa = st.text_input(f"Formação {time_casa}", value=formacao_casa)
            nova_fora = st.text_input(f"Formação {time_fora}", value=formacao_fora)
            if st.form_submit_button("Salvar Formações", width='stretch'):
                conn = sqlite3.connect('meu_futebol.db')
                cursor = conn.cursor()
                cursor.execute("UPDATE jogos SET formacao_casa = ?, formacao_fora = ? WHERE id = ?", (nova_casa, nova_fora, jogo_selecionado_id))
                conn.commit()
                conn.close()
                st.success("Formações atualizadas!")
                st.rerun()

    # Escalação
    conn = sqlite3.connect('meu_futebol.db')
    df_lineup = pd.read_sql_query(f"""
        SELECT e.*, el.nome 
        FROM eventos e
        LEFT JOIN elenco el ON e.jogador_id = el.id
        WHERE e.jogo_id = {jogo_selecionado_id} AND e.tipo = 'Lineup'
    """, conn)
    conn.close()

    if not df_lineup.empty:
        st.info("Escalação já registrada.")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**{time_casa}**")
            titulares_casa = df_lineup[df_lineup['detalhes'].str.contains('Titular', na=False)]
            for _, row in titulares_casa.iterrows():
                nome = row['nome'] if row['nome'] else 'Desconhecido'
                st.write(f"• {nome}")
        with col2:
            st.write(f"**{time_fora}**")
            titulares_fora = df_lineup[df_lineup['detalhes'].str.contains('Visitante', na=False)]
            for _, row in titulares_fora.iterrows():
                nome = row['nome'] if row['nome'] else 'Desconhecido'
                st.write(f"• {nome}")
    else:
        st.write("**Definir escalação manual:**")
        if df_elenco.empty:
            st.warning("Elenco não carregado. Importe os dados primeiro.")
        else:
            formacao_manual = st.text_input("Formação para escalação automática", value="4-4-2")
            if st.button("⚽ Montar Time Automaticamente", width='stretch'):
                titulares, reservas = montar_time(df_elenco, formacao_manual, cartoes)
                if titulares:
                    conn = sqlite3.connect('meu_futebol.db')
                    cursor = conn.cursor()
                    for jog in titulares:
                        if jog['row'] is not None:
                            cursor.execute("INSERT INTO eventos (jogo_id, tempo, tipo, jogador_id, detalhes) VALUES (?,0,'Lineup',?,'Titular')",
                                           (jogo_selecionado_id, jog['row']['id']))
                    for jog in reservas:
                        if jog['row'] is not None:
                            cursor.execute("INSERT INTO eventos (jogo_id, tempo, tipo, jogador_id, detalhes) VALUES (?,0,'Lineup',?,'Reserva')",
                                           (jogo_selecionado_id, jog['row']['id']))
                    conn.commit()
                    conn.close()
                    st.success("Escalação salva!")
                    st.rerun()

    st.markdown("---")

    # ===== MONITORAMENTO AUTOMÁTICO =====
    st.subheader("🔄 Monitoramento Automático")

    if not eh_hoje:
        st.warning("⚠️ O monitoramento só pode ser iniciado no dia da partida.")
        monitor_habilitado = False
    else:
        monitor_habilitado = True

    if monitor_habilitado:
        if st.button("🔍 Verificar Jogo ao Vivo", width='stretch'):
            fixture_id = verificar_jogo_ao_vivo(team_id)
            if fixture_id:
                st.session_state.fixture_id = fixture_id
                st.session_state.monitoramento_ativo = True
                st.success(f"Jogo ao vivo encontrado! ID: {fixture_id}")
                st.rerun()
            else:
                st.warning("Nenhum jogo ao vivo encontrado. Tente novamente quando a partida começar.")
    else:
        st.button("🔍 Verificar Jogo ao Vivo", width='stretch', disabled=True)

    if st.session_state.get('monitoramento_ativo', False) and st.session_state.get('fixture_id'):
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
                jogador_nome = ev.get('player', {}).get('name', '')
                jogador_id = 0
                if jogador_nome:
                    cursor.execute("SELECT id FROM elenco WHERE nome = ? OR apelido = ?", (jogador_nome, jogador_nome))
                    jogador = cursor.fetchone()
                    if jogador:
                        jogador_id = jogador[0]
                cursor.execute("SELECT id FROM eventos WHERE jogo_id = ? AND tempo = ? AND tipo = ? AND jogador_id = ?",
                               (jogo_selecionado_id, ev['time']['elapsed'], ev['type'], jogador_id))
                if not cursor.fetchone():
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