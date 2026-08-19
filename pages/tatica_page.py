# pages/tatica_page.py
import streamlit as st
from utils import carregar_elenco_profissional, interpretar_formacao
from tatica import (
    ROLES_FM26_PT,
    TRADUCAO_ROLES_PT,
    selecionar_time_por_funcoes,
    gerar_instrucoes_por_role,
    role_to_pos,
    CATEGORIA_ROLE,
    POSICAO_ESPERADA_PARA_GRUPO,
    GRUPO_POSICAO_JOGADOR
)

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================
def _filtrar_roles_por_fase(fase='in'):
    return [role for role in ROLES_FM26_PT if CATEGORIA_ROLE.get(role, 'in') == fase]

def _filtrar_roles_por_posicao(roles, posicao_esperada):
    if not posicao_esperada:
        return roles
    grupo_esperado = POSICAO_ESPERADA_PARA_GRUPO.get(posicao_esperada, '')
    if not grupo_esperado:
        return roles
    return [role for role in roles if POSICAO_ESPERADA_PARA_GRUPO.get(role_to_pos.get(role, ''), '') == grupo_esperado]

def _traduzir_role(role):
    return TRADUCAO_ROLES_PT.get(role, role)

def _role_display_to_key(display_name):
    for key, val in TRADUCAO_ROLES_PT.items():
        if val == display_name:
            return key
    return display_name

# ============================================================
# PÁGINA PRINCIPAL
# ============================================================
def show():
    st.title("📐 Análise Tática - 4 Formações")

    # Carrega elenco
    df = carregar_elenco_profissional()
    if df.empty:
        st.warning("Dados do elenco não carregados. Verifique o CSV.")
        return

    # ============================================================
    # INICIALIZAÇÃO DO SESSION_STATE
    # ============================================================
    if "time_base_titulares" not in st.session_state:
        st.session_state.time_base_titulares = []
    if "time_base_reservas" not in st.session_state:
        st.session_state.time_base_reservas = []
    if "time_base_posicoes" not in st.session_state:
        st.session_state.time_base_posicoes = []
    if "time_base_formacao" not in st.session_state:
        st.session_state.time_base_formacao = "4-4-2"
    if "time_base_roles_originais" not in st.session_state:
        st.session_state.time_base_roles_originais = []
    if "time_base_definido" not in st.session_state:
        st.session_state.time_base_definido = False

    # ============================================================
    # CRIA AS 4 ABAS
    # ============================================================
    tabs = st.tabs(["⚽ Inicial (Base)", "🔄 Construção de Jogada", "⚡ Ofensivo (com bola)", "🛡️ Defensivo (sem bola)"])

    # Mapeamento de fases: 'in' para as três primeiras, 'out' para defensiva
    fases = {
        "⚽ Inicial (Base)": "in",
        "🔄 Construção de Jogada": "in",
        "⚡ Ofensivo (com bola)": "in",
        "🛡️ Defensivo (sem bola)": "out"
    }

    for tab, fase in zip(tabs, fases.values()):
        with tab:
            st.subheader(f"Formação – {tab}")

            # ===== ABA INICIAL: DEFINE O TIME BASE =====
            if tab == "⚽ Inicial (Base)":
                # Input da formação
                col_form, col_btn = st.columns([3, 1])
                with col_form:
                    formacao = st.text_input("Formação (ex: 4-4-2)", value=st.session_state.time_base_formacao, key="form_base")
                with col_btn:
                    if st.button("Gerar Posições", key="btn_pos_base", width='stretch'):
                        defensores, meias, atacantes, posicoes = interpretar_formacao(formacao)
                        if posicoes:
                            st.session_state.time_base_posicoes = posicoes
                            st.session_state.time_base_formacao = formacao
                            st.session_state.time_base_definido = False  # força redefinição
                            st.rerun()
                        else:
                            st.error("Formação inválida. Use ex: 4-4-2")

                # Se já tem posições definidas, exibe os comboboxes para escolher jogadores e roles
                posicoes = st.session_state.time_base_posicoes
                if posicoes:
                    st.write("**Defina os titulares e suas funções (roles):**")
                    roles_disponiveis = _filtrar_roles_por_fase("in")  # inicial usa roles 'in'
                    jogadores_titulares = []
                    roles_selecionadas = []

                    # Cria um selectbox para cada posição com todos os jogadores do elenco
                    # (para permitir escolha manual)
                    df_elenco = df.copy()
                    df_elenco['display'] = df_elenco['nome_completo'] + " (" + df_elenco['apelido'] + ") - " + df_elenco['Posicao_Principal']

                    for i, (pos_exibida, pos_tipo) in enumerate(posicoes):
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            # Seleciona o jogador
                            jogador_escolhido = st.selectbox(
                                f"**{pos_exibida}**",
                                options=df_elenco['display'].tolist(),
                                key=f"jogador_base_{i}"
                            )
                            # Recupera o nome do jogador
                            nome_jogador = jogador_escolhido.split(' (')[0] if jogador_escolhido else ''
                            jogadores_titulares.append(nome_jogador)
                        with col2:
                            # Seleciona a role
                            pos_esperada = None
                            if pos_tipo == 'Goleiro':
                                pos_esperada = 'Goleiro'
                            elif pos_tipo in ['Defensor', 'Lateral']:
                                pos_esperada = 'Defensor'
                            elif pos_tipo in ['Meio-Campo', 'Volante', 'Meia-Atacante']:
                                pos_esperada = 'Meio-Campista'
                            elif pos_tipo == 'Atacante':
                                pos_esperada = 'Atacante'
                            roles_filtradas = _filtrar_roles_por_posicao(roles_disponiveis, pos_esperada)
                            if not roles_filtradas:
                                roles_filtradas = roles_disponiveis
                            display_roles = [_traduzir_role(r) for r in roles_filtradas]
                            display_to_key = {_traduzir_role(r): r for r in roles_filtradas}
                            default_role_display = _traduzir_role('Meia Central' if 'Meio' in pos_tipo else 'Centroavante')
                            default_index = display_roles.index(default_role_display) if default_role_display in display_roles else 0
                            role_display = st.selectbox(
                                "Função",
                                options=display_roles,
                                index=default_index,
                                key=f"role_base_{i}"
                            )
                            role_key = display_to_key.get(role_display, role_display)
                            roles_selecionadas.append(role_key)

                    # Botão para salvar time base
                    if st.button("✅ Salvar Time Base", key="btn_salvar_base", width='stretch'):
                        # Mapeia nomes para rows do DataFrame
                        titulares = []
                        for nome in jogadores_titulares:
                            row = df[df['nome_completo'] == nome]
                            if not row.empty:
                                titulares.append({
                                    'nome': nome,
                                    'apelido': row.iloc[0]['apelido'],
                                    'row': row.iloc[0],
                                    'role': None  # será preenchido depois
                                })
                        # Gera reservas (jogadores não selecionados)
                        nomes_selecionados = set(jogadores_titulares)
                        reservas_df = df[~df['nome_completo'].isin(nomes_selecionados)]
                        reservas = []
                        for _, row in reservas_df.head(12).iterrows():
                            reservas.append({
                                'nome': row['nome_completo'],
                                'apelido': row['apelido'],
                                'row': row
                            })
                        # Armazena no session_state
                        st.session_state.time_base_titulares = titulares
                        st.session_state.time_base_reservas = reservas
                        st.session_state.time_base_roles_originais = roles_selecionadas
                        st.session_state.time_base_definido = True
                        st.success("✅ Time base salvo com sucesso!")
                        st.rerun()

                else:
                    st.info("Clique em 'Gerar Posições' para definir a formação.")

            # ===== OUTRAS ABAS (CONSTRUÇÃO, OFENSIVA, DEFENSIVA) =====
            else:
                # Verifica se o time base já foi definido
                if not st.session_state.time_base_definido:
                    st.warning("⚠️ Defina o time base na aba **Inicial** primeiro.")
                    continue

                # Exibe o time base (apenas leitura) e permite alterar apenas as roles
                st.write("**Time Base (fixo):**")
                for i, jog in enumerate(st.session_state.time_base_titulares):
                    st.write(f"{i+1}. {jog['nome']} ({jog['apelido']})")

                st.write("---")
                st.write("**Ajuste as funções (roles) para esta fase:**")

                # Recupera posições e roles atuais
                posicoes = st.session_state.time_base_posicoes
                roles_atuais = st.session_state.time_base_roles_originais.copy()  # começa com as originais

                # Para cada posição, exibe um selectbox com as roles disponíveis para a fase
                novas_roles = []
                roles_disponiveis = _filtrar_roles_por_fase(fase)

                for i, (pos_exibida, pos_tipo) in enumerate(posicoes):
                    # Filtra roles por posição esperada
                    pos_esperada = None
                    if pos_tipo == 'Goleiro':
                        pos_esperada = 'Goleiro'
                    elif pos_tipo in ['Defensor', 'Lateral']:
                        pos_esperada = 'Defensor'
                    elif pos_tipo in ['Meio-Campo', 'Volante', 'Meia-Atacante']:
                        pos_esperada = 'Meio-Campista'
                    elif pos_tipo == 'Atacante':
                        pos_esperada = 'Atacante'
                    roles_filtradas = _filtrar_roles_por_posicao(roles_disponiveis, pos_esperada)
                    if not roles_filtradas:
                        roles_filtradas = roles_disponiveis
                    display_roles = [_traduzir_role(r) for r in roles_filtradas]
                    display_to_key = {_traduzir_role(r): r for r in roles_filtradas}

                    # Tenta manter a role anterior se ainda for válida
                    role_anterior = roles_atuais[i] if i < len(roles_atuais) else None
                    default_display = _traduzir_role(role_anterior) if role_anterior in display_to_key else display_roles[0]
                    default_index = display_roles.index(default_display) if default_display in display_roles else 0

                    role_display = st.selectbox(
                        f"{pos_exibida}",
                        options=display_roles,
                        index=default_index,
                        key=f"role_{tab}_{i}"
                    )
                    role_key = display_to_key.get(role_display, role_display)
                    novas_roles.append(role_key)

                # Botão para aplicar as novas roles
                if st.button(f"⚽ Aplicar Roles para {tab}", key=f"btn_aplicar_{tab}", width='stretch'):
                    # Atualiza as roles dos titulares
                    titulares_atualizados = []
                    for i, jog in enumerate(st.session_state.time_base_titulares):
                        novo_jog = jog.copy()
                        novo_jog['role'] = novas_roles[i] if i < len(novas_roles) else jog.get('role', '')
                        titulares_atualizados.append(novo_jog)

                    # Gera a escalação com as novas roles
                    st.session_state.escalacoes_geradas[tab] = {
                        'titulares': titulares_atualizados,
                        'reservas': st.session_state.time_base_reservas,
                        'formacao': st.session_state.time_base_formacao,
                        'roles': novas_roles,
                        'posicoes': posicoes
                    }
                    st.success(f"✅ Roles aplicadas para {tab}!")
                    st.rerun()

                # ===== EXIBE ESCALAÇÃO GERADA PARA ESTA ABA =====
                escalacao = st.session_state.escalacoes_geradas.get(tab)
                if escalacao:
                    st.subheader("⚽ Time Titular")
                    for i, jog in enumerate(escalacao['titulares'], 1):
                        nome = jog.get('nome', 'N/D')
                        apelido = jog.get('apelido', '')
                        role = jog.get('role', '')
                        st.write(f"{i}. {nome} ({apelido}) - {role}")

                    st.subheader("🟢 Reservas")
                    for i, jog in enumerate(escalacao['reservas'], 1):
                        nome = jog.get('nome', 'N/D')
                        apelido = jog.get('apelido', '')
                        st.write(f"{i}. {nome} ({apelido})")

                    # Instruções individuais
                    st.subheader("📝 Instruções Individuais")
                    for jog in escalacao['titulares']:
                        row = jog.get('row')
                        role = jog.get('role')
                        if row is not None and role:
                            inst = gerar_instrucoes_por_role(row, role)
                            st.write(f"**{jog.get('nome', '')}** ({role})")
                            st.write(f"- Com bola: {', '.join(inst.get('com_bola', []))}")
                            st.write(f"- Sem bola: {', '.join(inst.get('sem_bola', []))}")
                            st.write("---")

            st.caption("As roles defensivas (Out of Possession) só aparecem na aba Defensiva.")

# ============================================================
# EXECUÇÃO LOCAL (opcional)
# ============================================================
if __name__ == "__main__":
    show()