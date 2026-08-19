# pages/tatica_page.py
import streamlit as st
from datetime import datetime
from io import BytesIO
from utils import (
    carregar_elenco_profissional,
    interpretar_formacao,
    exportar_escalacao_excel,
    exportar_escalacao_pdf,
    formatar_planilha
)
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

def _posicao_esperada_para_grupo(pos_tipo):
    if pos_tipo == 'Goleiro':
        return 'Goleiro'
    elif pos_tipo in ['Defensor', 'Lateral']:
        return 'Defensor'
    elif pos_tipo in ['Meio-Campo', 'Volante', 'Meia-Atacante']:
        return 'Meio-Campista'
    elif pos_tipo == 'Atacante':
        return 'Atacante'
    return None

def _role_padrao_para_posicao(pos_tipo, fase='in'):
    if pos_tipo == 'Goleiro':
        return 'Goleiro' if fase == 'in' else 'Line-Holding Keeper'
    elif pos_tipo == 'Defensor':
        return 'Zagueiro Central' if fase == 'in' else 'Covering Centre-Back'
    elif pos_tipo == 'Meio-Campo':
        return 'Meia Central' if fase == 'in' else 'Pressing Central Midfielder'
    elif pos_tipo == 'Atacante':
        return 'Centroavante' if fase == 'in' else 'Central Outlet Centre Forward'
    return None

# ============================================================
# PÁGINA PRINCIPAL
# ============================================================
def show():
    st.title("📐 Análise Tática - 4 Formações")

    df = carregar_elenco_profissional()
    if df.empty:
        st.warning("Dados do elenco não carregados. Verifique o CSV.")
        return

    # Inicializa session_state
    if "time_base" not in st.session_state:
        st.session_state.time_base = None
    if "escalacoes_geradas" not in st.session_state:
        st.session_state.escalacoes_geradas = {}
    if "instrucoes_coletivas" not in st.session_state:
        st.session_state.instrucoes_coletivas = {}

    nomes_abas = ["⚽ Inicial", "🔄 Construção de Jogada", "⚡ Ofensivo (com bola)", "🛡️ Defensivo (sem bola)"]
    fases = ["in", "in", "in", "out"]
    tabs = st.tabs(nomes_abas)

    for tab, nome_aba, fase in zip(tabs, nomes_abas, fases):
        with tab:
            # Gera uma chave única para esta aba
            chave_aba = nome_aba.replace(" ", "_").replace("⚽", "").replace("🔄", "").replace("⚡", "").replace("🛡️", "").strip().lower()
            if not chave_aba:
                chave_aba = f"tab_{fase}"

            st.subheader(f"Formação – {nome_aba}")

            # ===== CAMPO DA FORMAÇÃO =====
            col_form, col_btn = st.columns([3, 1])
            with col_form:
                formacao = st.text_input(
                    "Formação (ex: 4-4-2)",
                    value="4-4-2",
                    key=f"form_{chave_aba}"  # chave única
                )
            with col_btn:
                if st.button("Gerar Posições", key=f"btn_pos_{chave_aba}", width='stretch'):
                    defensores, meias, atacantes, posicoes = interpretar_formacao(formacao)
                    if posicoes:
                        st.session_state[f"posicoes_{chave_aba}"] = posicoes
                        st.session_state[f"formacao_{chave_aba}"] = formacao
                        st.rerun()
                    else:
                        st.error("Formação inválida. Use ex: 4-4-2")

            # ===== EXIBE POSIÇÕES E ROLES =====
            posicoes = st.session_state.get(f"posicoes_{chave_aba}")
            if posicoes:
                roles_disponiveis = _filtrar_roles_por_fase(fase)
                st.write("**Defina a função (role) para cada posição:**")
                roles_selecionadas = []
                cols = st.columns(2)
                for i, (pos_exibida, pos_tipo) in enumerate(posicoes):
                    grupo_esperado = _posicao_esperada_para_grupo(pos_tipo)
                    roles_filtradas = _filtrar_roles_por_posicao(roles_disponiveis, grupo_esperado)
                    if not roles_filtradas:
                        roles_filtradas = roles_disponiveis

                    display_roles = [TRADUCAO_ROLES_PT.get(r, r) for r in roles_filtradas]
                    display_to_key = {TRADUCAO_ROLES_PT.get(r, r): r for r in roles_filtradas}

                    default_key = _role_padrao_para_posicao(pos_tipo, fase)
                    if default_key not in roles_filtradas:
                        default_key = roles_filtradas[0] if roles_filtradas else None
                    default_display = TRADUCAO_ROLES_PT.get(default_key, default_key) if default_key else None
                    default_index = display_roles.index(default_display) if default_display in display_roles else 0

                    with cols[i % 2]:
                        role_display = st.selectbox(
                            f"{pos_exibida}",
                            options=display_roles,
                            index=default_index,
                            key=f"role_{chave_aba}_{i}"  # chave única
                        )
                        role_key = display_to_key.get(role_display, role_display)
                        roles_selecionadas.append(role_key)

                # ===== INSTRUÇÕES COLETIVAS =====
                st.markdown("---")
                st.write("**Instruções Coletivas:**")
                placeholder_map = {
                    "inicial": "Ex: Organização inicial, saída de bola...",
                    "construcao": "Ex: Construção de jogada com passes curtos e posse de bola.",
                    "ofensivo": "Ex: Ataque rápido pelas laterais, finalizações de fora da área.",
                    "defensivo": "Ex: Defesa alta, pressão na saída de bola adversária."
                }
                placeholder = placeholder_map.get(chave_aba, "Digite as instruções coletivas...")
                instrucoes = st.text_area(
                    "Instruções Coletivas",
                    value=st.session_state.instrucoes_coletivas.get(chave_aba, ""),
                    placeholder=placeholder,
                    key=f"inst_{chave_aba}",
                    height=68
                )
                if instrucoes.strip():
                    st.session_state.instrucoes_coletivas[chave_aba] = instrucoes
                elif chave_aba in st.session_state.instrucoes_coletivas:
                    del st.session_state.instrucoes_coletivas[chave_aba]

                # ===== BOTÃO ESCALAR =====
                if st.button("⚽ Sugerir Time", key=f"btn_escalar_{chave_aba}", width='stretch'):
                    if len(roles_selecionadas) != len(posicoes):
                        st.error("Selecione uma função para cada posição.")
                    else:
                        if chave_aba == "inicial":
                            titulares, reservas = selecionar_time_por_funcoes(
                                df,
                                roles_selecionadas,
                                excluir_lesionados=True,
                                cartoes=None,
                                usar_rating_fallback=False,
                                priorizar_posicao=True,
                                priorizar_minutagem=True
                            )
                            st.session_state.time_base = {
                                'titulares': titulares,
                                'reservas': reservas
                            }
                        else:
                            if st.session_state.time_base is None:
                                st.warning("Gere primeiro o time base na aba 'Inicial'.")
                                titulares, reservas = selecionar_time_por_funcoes(
                                    df,
                                    roles_selecionadas,
                                    excluir_lesionados=True,
                                    cartoes=None,
                                    usar_rating_fallback=False,
                                    priorizar_posicao=True,
                                    priorizar_minutagem=True
                                )
                                st.session_state.time_base = {
                                    'titulares': titulares,
                                    'reservas': reservas
                                }
                            else:
                                titulares_base = st.session_state.time_base['titulares']
                                reservas_base = st.session_state.time_base['reservas']
                                titulares = []
                                for i, jog in enumerate(titulares_base):
                                    if i < len(roles_selecionadas):
                                        jog['role'] = roles_selecionadas[i]
                                    titulares.append(jog)
                                reservas = reservas_base

                        st.session_state.escalacoes_geradas[chave_aba] = {
                            'titulares': titulares,
                            'reservas': reservas,
                            'formacao': formacao,
                            'estilo': nome_aba.replace(" ", "_").replace("⚽", "").replace("🔄", "").replace("⚡", "").replace("🛡️", "").strip().lower() or chave_aba,
                            'roles': roles_selecionadas
                        }
                        st.rerun()

                # ===== EXIBE ESCALAÇÃO =====
                escalacao = st.session_state.escalacoes_geradas.get(chave_aba)
                if escalacao:
                    st.markdown("---")
                    st.subheader("⚽ Time Titular")
                    for i, jog in enumerate(escalacao['titulares'], 1):
                        nome = jog.get('nome', 'N/D')
                        apelido = jog.get('apelido', '')
                        role = jog.get('role', '')
                        score = jog.get('score', 0)
                        st.write(f"{i}. {nome} ({apelido}) - {role} (Score: {score:.1f})")

                    st.subheader("🟢 Reservas")
                    for i, jog in enumerate(escalacao['reservas'], 1):
                        nome = jog.get('nome', 'N/D')
                        apelido = jog.get('apelido', '')
                        st.write(f"{i}. {nome} ({apelido})")

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

                    if st.session_state.instrucoes_coletivas.get(chave_aba):
                        st.info(f"📋 **Instruções Coletivas:** {st.session_state.instrucoes_coletivas[chave_aba]}")

                    # ===== EXPORTAÇÃO =====
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📊 Exportar Excel", key=f"exp_excel_{chave_aba}", width='stretch'):
                            output = BytesIO()
                            exportar_escalacao_excel(
                                escalacao['titulares'],
                                escalacao['reservas'],
                                {},  # instruções individuais já exibidas
                                escalacao['formacao'],
                                escalacao['estilo'],
                                output
                            )
                            st.download_button(
                                label="Baixar Excel",
                                data=output.getvalue(),
                                file_name=f"escalacao_{escalacao['estilo']}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    with col2:
                        if st.button("📄 Exportar PDF", key=f"exp_pdf_{chave_aba}", width='stretch'):
                            output = BytesIO()
                            exportar_escalacao_pdf(
                                escalacao['titulares'],
                                escalacao['reservas'],
                                {},
                                escalacao['formacao'],
                                escalacao['estilo'],
                                output
                            )
                            st.download_button(
                                label="Baixar PDF",
                                data=output.getvalue(),
                                file_name=f"escalacao_{escalacao['estilo']}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                                mime="application/pdf"
                            )

            else:
                st.info("Clique em 'Gerar Posições' para definir a formação.")

        st.caption("As roles defensivas (Out of Possession) só aparecem na aba Defensiva.")