# pages/monitoramento.py
import streamlit as st
import sqlite3
import pandas as pd
import os
import random
import base64
from datetime import datetime, date
from streamlit_autorefresh import st_autorefresh
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
    obter_caminho_foto,
    obter_caminho_foto_arbitro,
    normalizar_texto,
)

# ============================================================
# CONFIGURAÇÕES DE ÁUDIO
# ============================================================
SOUNDS_DIR = "assets/sounds/"
SOUND_FILES = {
    "gol_casa": "gol_linhares.wav",
    "gol_fora": "gol_adversario.wav",
    "cartao": "falta.wav",
    "inicio": "inicio_tempo.wav",
    "fim": "fim_jogo.wav",
    "notificacao": "notificacao.wav",
}

def play_sound(sound_key):
    filename = SOUND_FILES.get(sound_key)
    sound_path = os.path.join(SOUNDS_DIR, filename) if filename else None
    if sound_path and os.path.exists(sound_path):
        with open(sound_path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        audio_html = f"""
            <audio id="player_{random.randint(1,1000000)}" autoplay>
                <source src="data:audio/wav;base64,{b64}" type="audio/wav">
            </audio>
        """
        st.components.v1.html(audio_html, height=0)
    else:
        js_beep = """
        <script>
            try {
                const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                const oscillator = audioCtx.createOscillator();
                const gainNode = audioCtx.createGain();
                oscillator.connect(gainNode);
                gainNode.connect(audioCtx.destination);
                oscillator.frequency.value = 800;
                oscillator.type = 'sine';
                gainNode.gain.value = 0.1;
                oscillator.start();
                setTimeout(() => { oscillator.stop(); }, 300);
            } catch(e) {
                console.warn('Beep falhou:', e);
            }
        </script>
        """
        st.components.v1.html(js_beep, height=0)

# ============================================================
# CONFIGURAÇÕES DA CATEGORIA
# ============================================================
CATEGORIA_CONFIG = {
    "Profissional": {
        "team_id": 12928,
        "nome_time": "Linhares FC",
        "elenco_func": carregar_elenco_profissional,
        "cartoes_key": "profissional",
        "liga_nome": "Campeonato Capixaba Série B"
    },
    "Sub-15": {
        "team_id": 27831,
        "nome_time": "Linhares FC Sub-15",
        "elenco_func": carregar_elenco_sub15,
        "cartoes_key": "sub15",
        "liga_nome": "Copa Espírito Santo Sub-15"
    },
    "Sub-17": {
        "team_id": 27832,
        "nome_time": "Linhares FC Sub-17",
        "elenco_func": carregar_elenco_sub17,
        "cartoes_key": "sub17",
        "liga_nome": "Copa Espírito Santo Sub-17"
    }
}

# ============================================================
# FUNÇÕES DE ACESSO AO BANCO SQLITE (com row_factory)
# ============================================================
DB_PATH = "meu_futebol.db"

def conectar_banco():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def verificar_jogo_ao_vivo_sql(team_id):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM jogos
        WHERE (time_casa_id = ? OR time_fora_id = ?)
        AND status IN ('1H', '2H', 'HT', 'ET', 'P')
        LIMIT 1
    """, (team_id, team_id))
    row = cursor.fetchone()
    conn.close()
    return row['id'] if row else None

def obter_detalhes_jogo_sql(fixture_id):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT j.*,
               tc.nome AS time_casa_nome,
               tf.nome AS time_fora_nome,
               v.nome AS estadio
        FROM jogos j
        LEFT JOIN times tc ON j.time_casa_id = tc.id
        LEFT JOIN times tf ON j.time_fora_id = tf.id
        LEFT JOIN venues v ON j.venue_id = v.id
        WHERE j.id = ?
    """, (fixture_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    dados = dict(row)
    return {
        "fixture": {
            "id": dados["id"],
            "date": dados.get("data_hora", ""),
            "status": {"short": dados.get("status", "NS")},
            "venue": {"name": dados.get("estadio", "Estádio")},
            "referee": dados.get("arbitro", "Não informado")
        },
        "teams": {
            "home": {"id": dados["time_casa_id"], "name": dados.get("time_casa_nome", "Casa")},
            "away": {"id": dados["time_fora_id"], "name": dados.get("time_fora_nome", "Fora")}
        },
        "goals": {
            "home": dados.get("gols_casa", 0),
            "away": dados.get("gols_fora", 0)
        },
        "score": {"penalty": None}
    }

def obter_eventos_jogo_sql(fixture_id):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.*, el.nome AS jogador_nome, t.nome AS time_nome
        FROM eventos e
        LEFT JOIN elenco el ON e.jogador_id = el.id
        LEFT JOIN times t ON e.time_id = t.id
        WHERE e.jogo_id = ?
        ORDER BY e.tempo ASC
    """, (fixture_id,))
    rows = cursor.fetchall()
    conn.close()
    eventos = []
    for r in rows:
        d = dict(r)
        eventos.append({
            "time": {"elapsed": d.get("tempo", 0), "extra": None},
            "type": d.get("tipo", ""),
            "detail": d.get("detalhes", ""),
            "player": {"name": d.get("jogador_nome", "Desconhecido")},
            "team": {"name": d.get("time_nome", "Time")}
        })
    return eventos

def obter_estatisticas_jogo_sql(fixture_id):
    # Mock – substitua por consulta real se tiver tabela de estatísticas
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT time_casa_id, time_fora_id FROM jogos WHERE id = ?", (fixture_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    time_casa = row['time_casa_id']
    time_fora = row['time_fora_id']
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM times WHERE id = ?", (time_casa,))
    nome_casa = cursor.fetchone()['nome'] if cursor.fetchone() else "Casa"
    cursor.execute("SELECT nome FROM times WHERE id = ?", (time_fora,))
    nome_fora = cursor.fetchone()['nome'] if cursor.fetchone() else "Fora"
    conn.close()
    return [
        {
            "team": {"name": nome_casa},
            "statistics": [
                {"type": "Ball Possession", "value": "50%"},
                {"type": "Total Shots", "value": "10"},
                {"type": "Shots on Goal", "value": "4"},
                {"type": "Passes", "value": "300"},
                {"type": "Passes %", "value": "75%"},
                {"type": "Fouls", "value": "12"},
                {"type": "Yellow Cards", "value": "2"},
                {"type": "Red Cards", "value": "0"}
            ]
        },
        {
            "team": {"name": nome_fora},
            "statistics": [
                {"type": "Ball Possession", "value": "50%"},
                {"type": "Total Shots", "value": "8"},
                {"type": "Shots on Goal", "value": "2"},
                {"type": "Passes", "value": "250"},
                {"type": "Passes %", "value": "70%"},
                {"type": "Fouls", "value": "15"},
                {"type": "Yellow Cards", "value": "3"},
                {"type": "Red Cards", "value": "0"}
            ]
        }
    ]

# ============================================================
# FUNÇÕES PARA COMISSÃO, TÉCNICOS E ARBITROS
# ============================================================
def obter_comissao_por_time(time_id, competicao_id=None):
    conn = conectar_banco()
    cursor = conn.cursor()
    query = """
        SELECT id, nome, cargo, foto, data_nascimento, cidade, uf, pais,
               historico_profissional, historico_jogador, apelido, idade
        FROM comissao
        WHERE time_id = ?
    """
    params = [time_id]
    if competicao_id:
        query += " AND competicao_id = ?"
        params.append(competicao_id)
    query += " ORDER BY nome"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def obter_tecnicos_por_time(time_id, competicao_id=None):
    conn = conectar_banco()
    cursor = conn.cursor()
    query = """
        SELECT id, nome, idade, nacionalidade, foto, time_id,
               historico_jogador, historico_profissional,
               data_nascimento, cidade, uf, pais, competicao_id, apelido
        FROM tecnicos
        WHERE time_id = ?
    """
    params = [time_id]
    if competicao_id:
        query += " AND competicao_id = ?"
        params.append(competicao_id)
    query += " ORDER BY nome"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    tecnicos = []
    for r in rows:
        d = dict(r)
        d['cargo'] = 'Técnico'
        tecnicos.append(d)
    return tecnicos

def obter_arbitro_por_id(arbitro_id):
    if not arbitro_id:
        return None
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, foto, categoria, uf, genero FROM arbitros WHERE id = ?", (arbitro_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def obter_staff_completo(time_id, competicao_id=None):
    tecnicos = obter_tecnicos_por_time(time_id, competicao_id)
    comissao = obter_comissao_por_time(time_id, competicao_id)
    for t in tecnicos:
        t['tipo'] = 'Técnico'
        t.setdefault('cargo', 'Técnico')
    for c in comissao:
        c['tipo'] = 'Comissão'
        c.setdefault('cargo', 'Membro')
    return tecnicos + comissao

# ============================================================
# FUNÇÃO DE CAMINHO PARA FOTOS DO STAFF
# ============================================================
PASTA_FOTOS_COMISSAO = "assets/fotos_comissao/"
PASTA_FOTOS_TECNICOS = "assets/fotos_tecnicos/"

def caminho_foto_membro(membro):
    """Busca a foto de um membro da comissão ou técnico."""
    foto = membro.get('foto', '')
    if not foto:
        return None

    if foto.startswith('C:') or '\\' in foto:
        nome_arquivo = os.path.basename(foto)
    else:
        nome_arquivo = foto

    pastas = [
        PASTA_FOTOS_COMISSAO,
        PASTA_FOTOS_TECNICOS,
        "assets/fotos/",
        "fotos/",
    ]

    for pasta in pastas:
        caminho = os.path.join(pasta, nome_arquivo)
        if os.path.exists(caminho):
            return caminho

    for pasta in pastas:
        if os.path.exists(pasta):
            for root, dirs, files in os.walk(pasta):
                if nome_arquivo in files:
                    return os.path.join(root, nome_arquivo)
    return None

# ============================================================
# FUNÇÕES DE ESCRITA (ATUALIZAÇÃO DO BANCO)
# ============================================================
def salvar_evento_sqlite(jogo_id, tempo, tipo, jogador_id, detalhes):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO eventos (jogo_id, tempo, tipo, jogador_id, detalhes)
        VALUES (?, ?, ?, ?, ?)
    ''', (jogo_id, tempo, tipo, jogador_id, detalhes))
    conn.commit()
    conn.close()

def atualizar_placar_sqlite(jogo_id, gols_casa, gols_fora):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("UPDATE jogos SET gols_casa = ?, gols_fora = ? WHERE id = ?", (gols_casa, gols_fora, jogo_id))
    conn.commit()
    conn.close()

def atualizar_status_sqlite(jogo_id, status):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("UPDATE jogos SET status = ? WHERE id = ?", (status, jogo_id))
    conn.commit()
    conn.close()

def atualizar_arbitro_jogo(jogo_id, arbitro_id):
    conn = conectar_banco()
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
    categoria = st.session_state.get("categoria_monitoramento", "Profissional")
    config = CATEGORIA_CONFIG.get(categoria)
    if not config:
        st.error(f"Categoria '{categoria}' inválida.")
        return

    team_id = config["team_id"]
    nome_time = config["nome_time"]
    elenco_func = config["elenco_func"]
    cartoes_key = config["cartoes_key"]

    st.title(f"📊 Monitoramento ao Vivo - {categoria}")
    st.markdown(f"**Time:** {nome_time} (ID: {team_id}) | **Competição:** {config['liga_nome']}")
    st.markdown("---")

    df_elenco = elenco_func()
    cartoes, _ = carregar_cartoes_json(cartoes_key)
    if df_elenco is None or df_elenco.empty:
        st.warning(f"Elenco não disponível para {categoria}.")
        return

    inicializar_banco()

    st.sidebar.header("Selecionar Partida")
    conn = conectar_banco()

    try:
        df_jogos = pd.read_sql_query(f"""
            SELECT j.id, j.time_casa_id, j.time_fora_id, j.gols_casa, j.gols_fora,
                   j.status, j.data_hora, j.formacao_casa, j.formacao_fora,
                   j.arbitro_id,
                   v.nome AS estadio
            FROM jogos j
            LEFT JOIN venues v ON j.venue_id = v.id
            WHERE (j.time_casa_id = {team_id} OR j.time_fora_id = {team_id})
              AND (substr(j.data_hora, 1, 10) >= date('now') OR j.status IN ('1H','2H','HT','ET','P'))
            ORDER BY j.data_hora ASC
        """, conn)
    except Exception as e:
        st.error(f"Erro ao carregar jogos: {e}")
        conn.close()
        return

    try:
        times_df = pd.read_sql_query("SELECT id, nome FROM times", conn)
        arbitros_df = pd.read_sql_query("SELECT id, nome, categoria, foto FROM arbitros ORDER BY nome", conn)
    except Exception as e:
        st.error(f"Erro ao carregar times ou árbitros: {e}")
        conn.close()
        return

    conn.close()

    times_dict = dict(zip(times_df['id'], times_df['nome']))
    arbitros_dict = dict(zip(arbitros_df['id'], arbitros_df['nome']))

    if df_jogos.empty:
        st.sidebar.warning(f"Nenhum jogo futuro ou em andamento do {nome_time}.")
        st.stop()

    opcoes = []
    for _, row in df_jogos.iterrows():
        time_casa = times_dict.get(row['time_casa_id'], '?')
        time_fora = times_dict.get(row['time_fora_id'], '?')
        label = f"{time_casa} x {time_fora} ({row['data_hora'][:10]}) - {row['status']}"
        opcoes.append((row['id'], label))

    jogo_selecionado_id = st.sidebar.selectbox(
        "Escolha a partida",
        options=[op[0] for op in opcoes],
        format_func=lambda x: next(op[1] for op in opcoes if op[0] == x),
        index=0
    )

    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jogos WHERE id = ?", (jogo_selecionado_id,))
    jogo_data = cursor.fetchone()
    conn.close()
    if not jogo_data:
        st.error("Jogo não encontrado.")
        return
    jogo = dict(jogo_data)

    time_casa = times_dict.get(jogo['time_casa_id'], 'Casa')
    time_fora = times_dict.get(jogo['time_fora_id'], 'Fora')
    gols_casa = jogo.get('gols_casa', 0) or 0
    gols_fora = jogo.get('gols_fora', 0) or 0
    status = jogo.get('status', 'NS')
    data_hora = jogo.get('data_hora', '')
    arbitro_id_atual = jogo.get('arbitro_id')

    data_jogo = datetime.strptime(data_hora[:10], "%Y-%m-%d").date() if data_hora else None
    hoje = date.today()
    eh_hoje = (data_jogo == hoje) if data_jogo else False

    st.subheader(f"⚽ {time_casa} {gols_casa} x {gols_fora} {time_fora}")
    col1, col2, col_arb = st.columns([2, 1, 2])
    with col1:
        st.write(f"**Status:** {status} | **Data:** {data_hora}")
    with col2:
        if jogo.get('estadio'):
            st.write(f"**Local:** {jogo['estadio']}")
    with col_arb:
        arbitro = obter_arbitro_por_id(arbitro_id_atual)
        if arbitro:
            nome_arbitro = arbitro['nome']
            foto_arb = obter_caminho_foto_arbitro(nome_arbitro)
            col_foto, col_texto = st.columns([1, 3])
            with col_foto:
                if foto_arb and os.path.exists(foto_arb):
                    st.image(foto_arb, width=150)
                else:
                    st.write("👤")
            with col_texto:
                st.write(f"**🟨 Árbitro:** {nome_arbitro} ({arbitro.get('categoria', 'N/I')})")
        else:
            st.write("**🟨 Árbitro:** Não definido")

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

    conn = conectar_banco()
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

    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("**Controle de Status**")
        if status == 'NS' and st.button("▶️ Iniciar 1º Tempo", width='stretch'):
            atualizar_status_sqlite(jogo_selecionado_id, '1H')
            play_sound('inicio')
            st.rerun()
        elif status == '1H' and st.button("⏸️ Intervalo", width='stretch'):
            atualizar_status_sqlite(jogo_selecionado_id, 'HT')
            st.rerun()
        elif status == 'HT' and st.button("▶️ Iniciar 2º Tempo", width='stretch'):
            atualizar_status_sqlite(jogo_selecionado_id, '2H')
            play_sound('inicio')
            st.rerun()
        elif status == '2H' and st.button("⏹️ Encerrar", width='stretch'):
            atualizar_status_sqlite(jogo_selecionado_id, 'FT')
            play_sound('fim')
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
                play_sound('gol_casa')
                st.rerun()
            if st.button(f"⚽ {time_fora}", width='stretch'):
                atualizar_placar_sqlite(jogo_selecionado_id, gols_casa, gols_fora + 1)
                salvar_evento_sqlite(jogo_selecionado_id, 0, 'Goal', 0, f"Gol do {time_fora}")
                play_sound('gol_fora')
                st.rerun()
        else:
            st.info("Partida não em andamento.")

    with col3:
        st.write("**Registrar Evento**")
        if status in ['1H', '2H', 'HT']:
            with st.form("evento_form"):
                tempo = st.number_input("Minuto", 0, 120, 0, step=1)
                tipo = st.selectbox("Tipo", ['Goal', 'Card', 'subst', 'Var'])
                conn = conectar_banco()
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
                submitted = st.form_submit_button("Adicionar Evento", width='stretch')
                if submitted:
                    salvar_evento_sqlite(jogo_selecionado_id, tempo, tipo, jogador_id, detalhes)
                    if tipo == 'Goal':
                        play_sound('notificacao')
                    elif tipo == 'Card':
                        play_sound('cartao')
                    else:
                        play_sound('notificacao')
                    st.success("Evento adicionado!")
                    st.rerun()
        else:
            st.info("Partida não em andamento.")

    st.markdown("---")

    st.subheader("📋 Escalação e Formação")
    with st.expander("✏️ Definir Formações", expanded=False):
        with st.form("formacao_form"):
            formacao_casa = jogo.get('formacao_casa', '')
            formacao_fora = jogo.get('formacao_fora', '')
            nova_casa = st.text_input(f"Formação {time_casa}", value=formacao_casa)
            nova_fora = st.text_input(f"Formação {time_fora}", value=formacao_fora)
            if st.form_submit_button("Salvar Formações", width='stretch'):
                conn = conectar_banco()
                cursor = conn.cursor()
                cursor.execute("UPDATE jogos SET formacao_casa = ?, formacao_fora = ? WHERE id = ?", (nova_casa, nova_fora, jogo_selecionado_id))
                conn.commit()
                conn.close()
                st.success("Formações atualizadas!")
                st.rerun()

    conn = conectar_banco()
    df_lineup = pd.read_sql_query(f"""
        SELECT e.*, el.nome, el.apelido, el.foto
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
                nome = row['nome'] if row['nome'] else row['apelido'] or 'Desconhecido'
                foto = row.get('foto')
                if foto and os.path.exists(foto):
                    st.image(foto, width=150)
                else:
                    caminho = obter_caminho_foto(row, "Profissional")
                    if caminho and os.path.exists(caminho):
                        st.image(caminho, width=150)
                    else:
                        st.write(f"📷 {nome}")
                st.caption(nome)

        with col2:
            st.write(f"**{time_fora}**")
            titulares_fora = df_lineup[df_lineup['detalhes'].str.contains('Visitante', na=False)]
            for _, row in titulares_fora.iterrows():
                nome = row['nome'] if row['nome'] else row['apelido'] or 'Desconhecido'
                foto = row.get('foto')
                if foto and os.path.exists(foto):
                    st.image(foto, width=150)
                else:
                    caminho = obter_caminho_foto(row, "Profissional")
                    if caminho and os.path.exists(caminho):
                        st.image(caminho, width=150)
                    else:
                        st.write(f"📷 {nome}")
                st.caption(nome)
    else:
        st.write("**Definir escalação manual:**")
        if df_elenco.empty:
            st.warning("Elenco não carregado. Importe os dados primeiro.")
        else:
            formacao_manual = st.text_input("Formação para escalação automática", value="4-4-2")
            if st.button("⚽ Montar Time Automaticamente", width='stretch'):
                titulares, reservas = montar_time(df_elenco, formacao_manual, cartoes)
                if titulares:
                    conn = conectar_banco()
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

    # ===== STAFF TÉCNICO (COMISSÃO + TÉCNICOS) COM FOTOS EM 150px =====
    st.subheader("👔 Staff Técnico")

    staff_casa = obter_staff_completo(jogo['time_casa_id'], jogo.get('competicao_id'))
    staff_fora = obter_staff_completo(jogo['time_fora_id'], jogo.get('competicao_id'))

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**{time_casa}**")
        if staff_casa:
            for membro in staff_casa:
                col_foto, col_texto = st.columns([1, 4])
                with col_foto:
                    foto_path = caminho_foto_membro(membro)
                    if foto_path and os.path.exists(foto_path):
                        st.image(foto_path, width=150)
                    else:
                        st.write("📌")
                with col_texto:
                    cargo = membro.get('cargo', 'Técnico')
                    st.write(f"**{membro['nome']}**")
                    st.caption(cargo)
        else:
            st.write("*Nenhum staff cadastrado.*")

    with col2:
        st.markdown(f"**{time_fora}**")
        if staff_fora:
            for membro in staff_fora:
                col_foto, col_texto = st.columns([1, 4])
                with col_foto:
                    foto_path = caminho_foto_membro(membro)
                    if foto_path and os.path.exists(foto_path):
                        st.image(foto_path, width=150)
                    else:
                        st.write("📌")
                with col_texto:
                    cargo = membro.get('cargo', 'Técnico')
                    st.write(f"**{membro['nome']}**")
                    st.caption(cargo)
        else:
            st.write("*Nenhum staff cadastrado.*")

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
            fixture_id = verificar_jogo_ao_vivo_sql(team_id)
            if fixture_id:
                st.session_state.fixture_id = fixture_id
                st.session_state.monitoramento_ativo = True
                play_sound('inicio')
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

        detalhes = obter_detalhes_jogo_sql(fixture_id)
        if detalhes:
            gols_casa_api = detalhes['goals']['home'] or 0
            gols_fora_api = detalhes['goals']['away'] or 0
            if (gols_casa_api, gols_fora_api) != (gols_casa, gols_fora):
                atualizar_placar_sqlite(jogo_selecionado_id, gols_casa_api, gols_fora_api)
                st.rerun()
            status_api = detalhes['fixture']['status']['short']
            if status_api != status:
                atualizar_status_sqlite(jogo_selecionado_id, status_api)
                if status_api in ['FT', 'AET', 'PEN']:
                    play_sound('fim')
                st.rerun()
            st.write(f"**Status:** {status_api} | **Minuto:** {detalhes['fixture']['status'].get('elapsed', 0)}")

        eventos_api = obter_eventos_jogo_sql(fixture_id)
        if eventos_api:
            conn = conectar_banco()
            cursor = conn.cursor()
            for ev in eventos_api:
                jogador_nome = ev.get('player', {}).get('name', '')
                jogador_id = 0
                if jogador_nome:
                    cursor.execute("SELECT id FROM elenco WHERE nome = ? OR apelido = ?", (jogador_nome, jogador_nome))
                    jogador = cursor.fetchone()
                    if jogador:
                        jogador_id = jogador['id']
                cursor.execute("SELECT id FROM eventos WHERE jogo_id = ? AND tempo = ? AND tipo = ? AND jogador_id = ?",
                               (jogo_selecionado_id, ev['time']['elapsed'], ev['type'], jogador_id))
                if not cursor.fetchone():
                    cursor.execute('''
                        INSERT INTO eventos (jogo_id, tempo, tipo, jogador_id, detalhes)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (jogo_selecionado_id, ev['time']['elapsed'], ev['type'], jogador_id, ev.get('detail', '')))
                    tipo = ev['type'].lower()
                    if tipo == 'goal':
                        time_nome = ev.get('team', {}).get('name', '')
                        if time_nome == config['nome_time']:
                            play_sound('gol_casa')
                        else:
                            play_sound('gol_fora')
                    elif tipo == 'card':
                        play_sound('cartao')
                    else:
                        play_sound('notificacao')
            conn.commit()
            conn.close()
            st.rerun()

        if st.button("⏹️ Parar Monitoramento", width='stretch'):
            st.session_state.monitoramento_ativo = False
            st.session_state.fixture_id = None
            st.rerun()

    st.markdown("---")
    st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")