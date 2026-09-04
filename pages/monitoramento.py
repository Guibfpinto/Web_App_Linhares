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
    "gol_linhares": "gol_linhares.wav",
    "gol_adversario": "gol_adversario.wav",
    "cartao": "falta.wav",
    "inicio": "inicio_tempo.wav",
    "notificacao": "notificacao.wav",
}

def play_sound(sound_key):
    """Toca um som baseado na chave: gol_linhares, gol_adversario, cartao, inicio, notificacao."""
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
        # Fallback: beep simples
        st.components.v1.html("""
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
                } catch(e) {}
            </script>
        """, height=0)

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
# FUNÇÕES DE BANCO DE DADOS (SQLite)
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
        }
    }

def obter_eventos_jogo_sql(fixture_id):
    conn = conectar_banco()
    cursor = conn.cursor()
    # Garante que a coluna 'fonte' existe
    cursor.execute("PRAGMA table_info(eventos)")
    colunas = [col[1] for col in cursor.fetchall()]
    if 'fonte' not in colunas:
        cursor.execute("ALTER TABLE eventos ADD COLUMN fonte TEXT DEFAULT 'api'")
        conn.commit()
    cursor.execute("""
        SELECT e.*, el.nome AS jogador_nome, el.apelido AS jogador_apelido,
               t.nome AS time_nome
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
            "time": {"elapsed": d.get("tempo", 0)},
            "type": d.get("tipo", ""),
            "detail": d.get("detalhes", ""),
            "player": {"name": d.get("jogador_nome") or d.get("jogador_apelido") or "Desconhecido"},
            "team": {"name": d.get("time_nome", "Time")},
            "fonte": d.get("fonte", "api")
        })
    return eventos

def salvar_evento_sqlite(jogo_id, tempo, tipo, jogador_id, detalhes, fonte="manual"):
    conn = conectar_banco()
    cursor = conn.cursor()
    # Garante que a coluna 'fonte' existe
    cursor.execute("PRAGMA table_info(eventos)")
    colunas = [col[1] for col in cursor.fetchall()]
    if 'fonte' not in colunas:
        cursor.execute("ALTER TABLE eventos ADD COLUMN fonte TEXT DEFAULT 'api'")
        conn.commit()
    cursor.execute('''
        INSERT INTO eventos (jogo_id, tempo, tipo, jogador_id, detalhes, fonte)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (jogo_id, tempo, tipo, jogador_id, detalhes, fonte))
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
# FUNÇÕES DE ESCALAÇÃO
# ============================================================
def montar_time_automatico(df, formacao_str, cartoes):
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
    reservas_df = reservas_df.sort_values('Rating_Geral_FM26', ascending=False)
    for _, row in reservas_df.head(12).iterrows():
        reservas.append({
            'nome': row['nome_completo'],
            'apelido': row['apelido'],
            'row': row
        })
    return titulares, reservas

def salvar_escalacao(jogo_id, titulares, reservas):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM eventos WHERE jogo_id = ? AND tipo = 'Lineup'", (jogo_id,))
    for jog in titulares:
        if jog['row'] is not None:
            cursor.execute(
                "INSERT INTO eventos (jogo_id, tempo, tipo, jogador_id, detalhes, fonte) VALUES (?, 0, 'Lineup', ?, ?, 'manual')",
                (jogo_id, jog['row']['id'], f"Titular - {jog['posicao_exibida']}")
            )
    for jog in reservas:
        if jog['row'] is not None:
            cursor.execute(
                "INSERT INTO eventos (jogo_id, tempo, tipo, jogador_id, detalhes, fonte) VALUES (?, 0, 'Lineup', ?, 'Reserva', 'manual')",
                (jogo_id, jog['row']['id'])
            )
    conn.commit()
    conn.close()

# ============================================================
# FUNÇÕES DE EXIBIÇÃO DE FOTOS (STAFF E ÁRBITRO)
# ============================================================
def caminho_foto_membro(membro):
    foto = membro.get('foto', '')
    if not foto:
        return None
    if foto.startswith('C:') or '\\' in foto:
        nome_arquivo = os.path.basename(foto)
    else:
        nome_arquivo = foto
    nome_clean = normalizar_texto(nome_arquivo).replace(' ', '_')
    extensoes = ['.png', '.jpg', '.jpeg']
    pastas = [
        "assets/fotos_comissao/",
        "assets/fotos_tecnicos/",
        "fotos/",
        "fotos_sistema_Analise_Elenco/Comissao_Tecnica/Profissional",
        "fotos_sistema_Analise_Elenco/Comissao_Tecnica/Sub15",
        "fotos_sistema_Analise_Elenco/Comissao_Tecnica/Sub17",
    ]
    for pasta in pastas:
        for ext in extensoes:
            caminho = os.path.join(pasta, f"{nome_arquivo}{ext}")
            if os.path.exists(caminho):
                return os.path.abspath(caminho)
            caminho = os.path.join(pasta, f"{nome_clean}{ext}")
            if os.path.exists(caminho):
                return os.path.abspath(caminho)
    return None

def obter_staff_completo(time_id, competicao_id=None):
    conn = conectar_banco()
    cursor = conn.cursor()
    query = """
        SELECT id, nome, apelido, cargo, foto, idade, data_nascimento
        FROM comissao
        WHERE time_id = ?
    """
    params = [time_id]
    if competicao_id:
        query += " AND competicao_id = ?"
        params.append(competicao_id)
    query += " ORDER BY nome"
    cursor.execute(query, params)
    comissao = [dict(row) for row in cursor.fetchall()]
    cursor.execute("""
        SELECT id, nome, apelido, foto, idade, data_nascimento,
               'Técnico' as cargo
        FROM tecnicos
        WHERE time_id = ?
    """, params)
    tecnicos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tecnicos + comissao

def obter_arbitro_por_id(arbitro_id):
    if not arbitro_id:
        return None
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, foto, categoria FROM arbitros WHERE id = ?", (arbitro_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

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

    # Garantir que a coluna 'fonte' exista na tabela eventos
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(eventos)")
    colunas = [col[1] for col in cursor.fetchall()]
    if 'fonte' not in colunas:
        cursor.execute("ALTER TABLE eventos ADD COLUMN fonte TEXT DEFAULT 'api'")
        conn.commit()
    conn.close()

    # Seleção de partida
    st.sidebar.header("Selecionar Partida")
    conn = conectar_banco()
    try:
        df_jogos = pd.read_sql_query(f"""
            SELECT j.id, j.time_casa_id, j.time_fora_id, j.gols_casa, j.gols_fora,
                   j.status, j.data_hora, j.formacao_casa, j.arbitro_id,
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
        arbitros_df = pd.read_sql_query("SELECT id, nome, categoria FROM arbitros ORDER BY nome", conn)
    except Exception as e:
        st.error(f"Erro ao carregar times ou árbitros: {e}")
        conn.close()
        return
    conn.close()

    times_dict = dict(zip(times_df['id'], times_df['nome']))
    if df_jogos.empty:
        st.sidebar.warning(f"Nenhum jogo futuro ou em andamento do {nome_time}.")
        st.stop()

    opcoes = []
    for _, row in df_jogos.iterrows():
        tc = times_dict.get(row['time_casa_id'], '?')
        tf = times_dict.get(row['time_fora_id'], '?')
        label = f"{tc} x {tf} ({row['data_hora'][:10]}) - {row['status']}"
        opcoes.append((row['id'], label))

    jogo_selecionado_id = st.sidebar.selectbox(
        "Escolha a partida",
        options=[op[0] for op in opcoes],
        format_func=lambda x: next(op[1] for op in opcoes if op[0] == x),
        index=0
    )

    # Carrega detalhes do jogo
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
    formacao_casa = jogo.get('formacao_casa', '')

    data_jogo = datetime.strptime(data_hora[:10], "%Y-%m-%d").date() if data_hora else None
    hoje = date.today()
    eh_hoje = (data_jogo == hoje) if data_jogo else False

    # ============================================================
    # CABEÇALHO DO JOGO
    # ============================================================
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
            col_foto, col_texto = st.columns([1, 4])
            with col_foto:
                if foto_arb and os.path.exists(foto_arb):
                    st.image(foto_arb, width=80)
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
        st.warning("Nenhum árbitro cadastrado.")

    st.markdown("---")

    # ============================================================
    # MONITORAMENTO AO VIVO (PRIORIDADE MÁXIMA)
    # ============================================================
    st.subheader("🔴 Monitoramento Ao Vivo")

    # Verifica se há jogo ao vivo hoje
    if eh_hoje:
        with st.spinner("Verificando jogo ao vivo..."):
            fixture_id = verificar_jogo_ao_vivo_sql(team_id)
            if fixture_id:
                st.session_state.fixture_id = fixture_id
                st.session_state.monitoramento_ativo = True
            else:
                st.session_state.monitoramento_ativo = False

        if st.session_state.get('monitoramento_ativo', False) and st.session_state.get('fixture_id'):
            st_autorefresh(interval=10000, key="monitor_auto")
            fixture_id = st.session_state.fixture_id
            st.success(f"✅ Jogo ao vivo detectado! ID: {fixture_id}")

            detalhes = obter_detalhes_jogo_sql(fixture_id)
            if detalhes:
                gols_casa_api = detalhes['goals']['home'] or 0
                gols_fora_api = detalhes['goals']['away'] or 0
                status_anterior = status

                # Atualiza placar
                if (gols_casa_api, gols_fora_api) != (gols_casa, gols_fora):
                    atualizar_placar_sqlite(jogo_selecionado_id, gols_casa_api, gols_fora_api)
                    # Toca som de gol (se houve mudança)
                    if gols_casa_api > gols_casa:
                        play_sound('gol_linhares' if team_id == jogo['time_casa_id'] else 'gol_adversario')
                    elif gols_fora_api > gols_fora:
                        play_sound('gol_linhares' if team_id == jogo['time_fora_id'] else 'gol_adversario')
                    st.rerun()

                # Atualiza status
                status_api = detalhes['fixture']['status']['short']
                if status_api != status_anterior:
                    atualizar_status_sqlite(jogo_selecionado_id, status_api)
                    if status_api in ['1H', '2H']:
                        play_sound('inicio')
                    elif status_api in ['FT', 'AET', 'PEN']:
                        play_sound('notificacao')  # fim de jogo (opcional)
                    st.rerun()

                st.info(f"**Status:** {status_api} | **Minuto:** {detalhes['fixture']['status'].get('elapsed', 0)}")

            # Busca eventos da API
            eventos_api = obter_eventos_jogo_sql(fixture_id)
            if eventos_api:
                conn = conectar_banco()
                cursor = conn.cursor()
                novos_eventos = 0
                for ev in eventos_api:
                    jogador_nome = ev.get('player', {}).get('name', '')
                    jogador_id = 0
                    if jogador_nome:
                        cursor.execute("SELECT id FROM elenco WHERE nome = ? OR apelido = ?", (jogador_nome, jogador_nome))
                        jogador = cursor.fetchone()
                        if jogador:
                            jogador_id = jogador['id']
                    cursor.execute("""
                        SELECT id FROM eventos
                        WHERE jogo_id = ? AND tempo = ? AND tipo = ? AND jogador_id = ? AND fonte = 'api'
                    """, (jogo_selecionado_id, ev['time']['elapsed'], ev['type'], jogador_id))
                    if not cursor.fetchone():
                        cursor.execute('''
                            INSERT INTO eventos (jogo_id, tempo, tipo, jogador_id, detalhes, fonte)
                            VALUES (?, ?, ?, ?, ?, 'api')
                        ''', (jogo_selecionado_id, ev['time']['elapsed'], ev['type'], jogador_id, ev.get('detail', '')))
                        novos_eventos += 1
                        # Sons
                        tipo = ev['type'].lower()
                        if tipo == 'goal':
                            time_nome = ev.get('team', {}).get('name', '')
                            if time_nome == config['nome_time']:
                                play_sound('gol_linhares')
                            else:
                                play_sound('gol_adversario')
                        elif tipo == 'card':
                            play_sound('cartao')
                        else:
                            play_sound('notificacao')
                conn.commit()
                conn.close()
                if novos_eventos > 0:
                    st.info(f"{novos_eventos} novo(s) evento(s) sincronizado(s) da API.")
                    st.rerun()
            else:
                st.info("📡 Nenhum evento da API disponível.")

            if st.button("⏹️ Parar Monitoramento", use_container_width=True):
                st.session_state.monitoramento_ativo = False
                st.session_state.fixture_id = None
                st.rerun()
        else:
            st.warning("⏳ Nenhum jogo ao vivo encontrado no momento.")
            st.info("Use o registro manual abaixo apenas se a API não estiver retornando dados.")
    else:
        st.info(f"📅 O jogo está marcado para {data_jogo}. O monitoramento ao vivo estará disponível no dia da partida.")

    st.markdown("---")

    # ============================================================
    # REGISTRO MANUAL DE EVENTOS (FALLBACK)
    # ============================================================
    st.subheader("📝 Registro Manual de Eventos (Fallback)")
    st.caption("Use esta seção apenas se a API não estiver fornecendo os dados corretamente.")

    if status in ['1H', '2H', 'HT', 'ET', 'P']:
        with st.form("evento_manual_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                tipo = st.selectbox("Tipo", ['Gol', 'Cartão', 'Substituição'])
            with col2:
                conn = conectar_banco()
                jogadores_df = pd.read_sql_query(f"""
                    SELECT id, nome, apelido, time_id FROM elenco
                    WHERE time_id IN ({jogo['time_casa_id']}, {jogo['time_fora_id']})
                    ORDER BY nome
                """, conn)
                conn.close()
                opcoes_jogadores = ["Nenhum"] + jogadores_df['nome'].tolist()
                jogador_nome = st.selectbox("Jogador", opcoes_jogadores)
                if jogador_nome != "Nenhum":
                    jogador_id = jogadores_df[jogadores_df['nome'] == jogador_nome]['id'].iloc[0]
                    time_jogador = jogadores_df[jogadores_df['id'] == jogador_id]['time_id'].iloc[0]
                else:
                    jogador_id = 0
                    time_jogador = None
            with col3:
                tempo = st.number_input("Minuto", 0, 120, 0, step=1)
            detalhes = st.text_input("Detalhes (opcional)")
            if st.form_submit_button("Registrar Evento Manualmente", use_container_width=True):
                if tipo == 'Gol' and jogador_id != 0:
                    if time_jogador == jogo['time_casa_id']:
                        atualizar_placar_sqlite(jogo_selecionado_id, gols_casa + 1, gols_fora)
                        play_sound('gol_linhares' if team_id == jogo['time_casa_id'] else 'gol_adversario')
                    else:
                        atualizar_placar_sqlite(jogo_selecionado_id, gols_casa, gols_fora + 1)
                        play_sound('gol_linhares' if team_id == jogo['time_fora_id'] else 'gol_adversario')
                elif tipo == 'Cartão':
                    play_sound('cartao')
                else:
                    play_sound('notificacao')
                salvar_evento_sqlite(jogo_selecionado_id, tempo, tipo, jogador_id, detalhes, fonte="manual")
                st.success("Evento registrado manualmente!")
                st.rerun()
    else:
        st.info("Partida não está em andamento para registrar eventos manuais.")

    st.markdown("---")

    # ============================================================
    # LISTA DE ÚLTIMOS EVENTOS (API + MANUAL)
    # ============================================================
    conn = conectar_banco()
    df_eventos = pd.read_sql_query(f"""
        SELECT e.*, el.nome AS jogador_nome, el.apelido AS jogador_apelido,
               t.nome AS time_nome, e.fonte
        FROM eventos e
        LEFT JOIN elenco el ON e.jogador_id = el.id
        LEFT JOIN times t ON e.time_id = t.id
        WHERE e.jogo_id = {jogo_selecionado_id}
        ORDER BY e.tempo DESC LIMIT 20
    """, conn)
    conn.close()

    if not df_eventos.empty:
        st.write("**📋 Últimos eventos:**")
        for _, ev in df_eventos.iterrows():
            jogador = ev['jogador_nome'] if ev['jogador_nome'] else ev['jogador_apelido'] or 'Desconhecido'
            fonte = ev.get('fonte', 'api')
            icone = "🟢" if fonte == 'api' else "🟡"
            st.write(f"{icone} ⏱️ {ev['tempo']}' - {ev['tipo']} - {jogador} - {ev['detalhes']} ({fonte})")
    else:
        st.info("Nenhum evento registrado ainda.")

    st.markdown("---")

    # ============================================================
    # ESCALAÇÃO MANUAL
    # ============================================================
    st.subheader("📋 Escalação")

    with st.expander("✏️ Definir Escalação", expanded=False):
        formacao_opcoes = ['4-4-2', '4-3-3', '4-2-3-1', '3-5-2', '5-3-2', '4-1-2-1-2', '3-4-3']
        formacao_escolhida = st.selectbox(
            f"Formação do {time_casa}",
            formacao_opcoes,
            index=formacao_opcoes.index(formacao_casa) if formacao_casa in formacao_opcoes else 0
        )
        if formacao_escolhida != formacao_casa:
            conn = conectar_banco()
            cursor = conn.cursor()
            cursor.execute("UPDATE jogos SET formacao_casa = ? WHERE id = ?", (formacao_escolhida, jogo_selecionado_id))
            conn.commit()
            conn.close()
            st.rerun()

        jogadores_disponiveis = df_elenco.copy()
        if 'lesionado' in jogadores_disponiveis.columns:
            jogadores_disponiveis = jogadores_disponiveis[~jogadores_disponiveis['lesionado']]
        jogadores_disponiveis = jogadores_disponiveis[
            ~jogadores_disponiveis['nome_completo'].apply(
                lambda x: jogador_suspenso(mapear_nome_para_canonico(x), cartoes)
            )
        ]

        if jogadores_disponiveis.empty:
            st.warning("Nenhum jogador disponível para escalar.")
        else:
            st.write(f"**Jogadores disponíveis:** {len(jogadores_disponiveis)}")

            defensores, meias, atacantes, posicoes = interpretar_formacao(formacao_escolhida)
            if not posicoes:
                st.error("Formação inválida.")
            else:
                titulares_selecionados = {}
                st.write("**Titulares:**")
                cols = st.columns(3)
                for idx, (pos_exibida, pos_tipo) in enumerate(posicoes):
                    with cols[idx % 3]:
                        if pos_tipo == 'Goleiro':
                            candidatos = jogadores_disponiveis[jogadores_disponiveis['Posicao_Principal'] == 'Goleiro']
                        else:
                            candidatos = jogadores_disponiveis[~jogadores_disponiveis['Posicao_Principal'].isin(['Goleiro'])]
                        candidatos = candidatos[~candidatos['nome_completo'].isin(titulares_selecionados.values())]
                        candidatos = candidatos.sort_values('Rating_Geral_FM26', ascending=False)
                        opcoes = [''] + candidatos['nome_completo'].tolist()
                        selecionado = st.selectbox(
                            pos_exibida,
                            opcoes,
                            key=f"titular_{pos_exibida}_{jogo_selecionado_id}"
                        )
                        if selecionado:
                            titulares_selecionados[pos_exibida] = selecionado

                st.write("**Reservas (máx. 12):**")
                reservas_opcoes = jogadores_disponiveis[
                    ~jogadores_disponiveis['nome_completo'].isin(titulares_selecionados.values())
                ]['nome_completo'].tolist()
                reservas_selecionados = st.multiselect(
                    "Selecione os reservas",
                    reservas_opcoes,
                    default=[],
                    key=f"reservas_{jogo_selecionado_id}"
                )
                if len(reservas_selecionados) > 12:
                    st.warning("Máximo de 12 reservas. Os primeiros 12 serão salvos.")
                    reservas_selecionados = reservas_selecionados[:12]

                col_auto, col_salvar = st.columns(2)
                with col_auto:
                    if st.button("⚽ Gerar Automático", use_container_width=True):
                        titulares, reservas = montar_time_automatico(df_elenco, formacao_escolhida, cartoes)
                        if titulares:
                            salvar_escalacao(jogo_selecionado_id, titulares, reservas)
                            st.success("Escalação automática salva!")
                            st.rerun()
                with col_salvar:
                    if st.button("💾 Salvar Manual", use_container_width=True):
                        if len(titulares_selecionados) < len(posicoes):
                            st.error("Preencha todos os titulares.")
                        else:
                            titulares = []
                            for pos, nome in titulares_selecionados.items():
                                row = df_elenco[df_elenco['nome_completo'] == nome].iloc[0]
                                titulares.append({
                                    'posicao_exibida': pos,
                                    'posicao_tipo': 'Desconhecido',
                                    'nome': nome,
                                    'apelido': row['apelido'],
                                    'row': row
                                })
                            reservas = []
                            for nome in reservas_selecionados:
                                row = df_elenco[df_elenco['nome_completo'] == nome].iloc[0]
                                reservas.append({
                                    'nome': nome,
                                    'apelido': row['apelido'],
                                    'row': row
                                })
                            salvar_escalacao(jogo_selecionado_id, titulares, reservas)
                            st.success("Escalação salva!")
                            st.rerun()

    # Exibe a escalação atual
    conn = conectar_banco()
    df_lineup = pd.read_sql_query(f"""
        SELECT e.*, el.nome, el.apelido, el.foto, e.fonte
        FROM eventos e
        LEFT JOIN elenco el ON e.jogador_id = el.id
        WHERE e.jogo_id = {jogo_selecionado_id} AND e.tipo = 'Lineup'
    """, conn)
    conn.close()

    if not df_lineup.empty:
        st.info("Escalação atual:")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**{time_casa} - Titulares**")
            titulares_casa = df_lineup[~df_lineup['detalhes'].str.contains('Reserva', na=False)]
            for _, row in titulares_casa.iterrows():
                nome = row['nome'] if row['nome'] else row['apelido'] or 'Desconhecido'
                fonte = row.get('fonte', 'api')
                icone = "🟢" if fonte == 'api' else "🟡"
                st.write(f"{icone} • {nome}")
        with col2:
            st.write(f"**{time_casa} - Reservas**")
            reservas_casa = df_lineup[df_lineup['detalhes'].str.contains('Reserva', na=False)]
            for _, row in reservas_casa.iterrows():
                nome = row['nome'] if row['nome'] else row['apelido'] or 'Desconhecido'
                fonte = row.get('fonte', 'api')
                icone = "🟢" if fonte == 'api' else "🟡"
                st.write(f"{icone} • {nome}")
    else:
        st.info("Nenhuma escalação registrada ainda.")

    st.markdown("---")

    # ============================================================
    # STAFF TÉCNICO
    # ============================================================
    st.subheader("👔 Staff Técnico")
    staff_casa = obter_staff_completo(jogo['time_casa_id'])
    staff_fora = obter_staff_completo(jogo['time_fora_id'])

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**{time_casa}**")
        for membro in staff_casa:
            foto = caminho_foto_membro(membro)
            col_foto, col_texto = st.columns([1, 4])
            with col_foto:
                if foto and os.path.exists(foto):
                    st.image(foto, width=60)
                else:
                    st.write("📌")
            with col_texto:
                nome = membro.get('nome') or membro.get('apelido') or 'N/I'
                cargo = membro.get('cargo', 'Técnico')
                st.write(f"**{nome}**")
                st.caption(cargo)
    with col2:
        st.write(f"**{time_fora}**")
        for membro in staff_fora:
            foto = caminho_foto_membro(membro)
            col_foto, col_texto = st.columns([1, 4])
            with col_foto:
                if foto and os.path.exists(foto):
                    st.image(foto, width=60)
                else:
                    st.write("📌")
            with col_texto:
                nome = membro.get('nome') or membro.get('apelido') or 'N/I'
                cargo = membro.get('cargo', 'Técnico')
                st.write(f"**{nome}**")
                st.caption(cargo)

    st.markdown("---")
    st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")