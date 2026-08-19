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
    """Retorna roles da fase especificada ('in' ou 'out')."""
    return [role for role in ROLES_FM26_PT if CATEGORIA_ROLE.get(role, 'in') == fase]

def _filtrar_roles_por_posicao(roles, posicao_esperada):
    """Filtra roles que são compatíveis com a posição esperada."""
    if not posicao_esperada:
        return roles
    grupo_esperado = POSICAO_ESPERADA_PARA_GRUPO.get(posicao_esperada, '')
    if not grupo_esperado:
        return roles
    return [role for role in roles if POSICAO_ESPERADA_PARA_GRUPO.get(role_to_pos.get(role, ''), '') == grupo_esperado]

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

    # ===== CRIA AS 4 ABAS =====
    nomes_abas = ["⚽ Inicial", "🔄 Construção de Jogada", "⚡ Ofensivo (com bola)", "🛡️ Defensivo (sem bola)"]
    tabs = st.tabs(nomes_abas)

    # Mapeamento de fases: 'in' para as três primeiras, 'out' para defensiva
    fases = {
        "⚽ Inicial": "in",
        "🔄 Construção de Jogada": "in",
        "⚡ Ofensivo (com bola)": "in",
        "🛡️ Defensivo (sem bola)": "out"
    }

    # Mapeamento para armazenar o estado de cada aba
    if "escalacoes_geradas" not in st.session_state:
        st.session_state.escalacoes_geradas = {}

    for idx, (tab, nome_aba) in enumerate(zip(tabs, nomes_abas)):
        fase = fases[nome_aba]
        with tab:
            st.subheader(f"Formação – {nome_aba}")
            chave_prefix = f"tab_{idx}_{fase}"  # usa índice para evitar duplicação

            # ===== INPUT DA FORMAÇÃO =====
            col_form, col_btn = st.columns([3, 1])
            with col_form:
                # key com prefixo único
                formacao = st.text_input(
                    "Formação (ex: 4-4-2)",
                    value="4-4-2",
                    key=f"form_{chave_prefix}"
                )
            with col_btn:
                if st.button("Gerar Posições", key=f"btn_pos_{chave_prefix}", width='stretch'):
                    defensores, meias, atacantes, posicoes = interpretar_formacao(formacao)
                    if posicoes:
                        st.session_state[f"posicoes_{chave_prefix}"] = posicoes
                        st.session_state[f"formacao_{chave_prefix}"] = formacao
                        st.rerun()
                    else:
                        st.error("Formação inválida. Use ex: 4-4-2")

            # ===== EXIBE POSIÇÕES E ROLES =====
            posicoes = st.session_state.get(f"posicoes_{chave_prefix}")
            if posicoes:
                roles_disponiveis = _filtrar_roles_por_fase(fase)
                st.write("**Defina a função (role) para cada posição:**")
                roles_selecionadas = []
                cols = st.columns(2)  # duas colunas para economizar espaço
                for i, (pos_exibida, pos_tipo) in enumerate(posicoes):
                    # Filtra roles por posição esperada (compatibilidade)
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
                        roles_filtradas = roles_disponiveis  # fallback

                    # Tradução para exibição
                    display_roles = [TRADUCAO_ROLES_PT.get(r, r) for r in roles_filtradas]
                    # Mapeia display -> chave original
                    display_to_key = {TRADUCAO_ROLES_PT.get(r, r): r for r in roles_filtradas}

                    # Seleciona a role padrão (baseada na posição)
                    default_key = None
                    if pos_tipo == 'Goleiro':
                        default_key = 'Goleiro' if fase == 'in' else 'Line-Holding Keeper'
                    elif pos_tipo == 'Defensor':
                        default_key = 'Zagueiro Central' if fase == 'in' else 'Covering Centre-Back'
                    elif pos_tipo == 'Meio-Campo':
                        default_key = 'Meia Central' if fase == 'in' else 'Pressing Central Midfielder'
                    elif pos_tipo == 'Atacante':
                        default_key = 'Centroavante' if fase == 'in' else 'Central Outlet Centre Forward'
                    else:
                        default_key = roles_filtradas[0] if roles_filtradas else None
                    default_display = TRADUCAO_ROLES_PT.get(default_key, default_key) if default_key else None
                    default_index = display_roles.index(default_display) if default_display in display_roles else 0

                    with cols[i % 2]:
                        # key com prefixo + índice da posição
                        role_display = st.selectbox(
                            f"{pos_exibida}",
                            options=display_roles,
                            index=default_index,
                            key=f"role_{chave_prefix}_{i}"
                        )
                        # Recupera a chave original
                        role_key = display_to_key.get(role_display, role_display)
                        roles_selecionadas.append(role_key)

                # ===== BOTÃO ESCALAR =====
                if st.button("⚽ Escalar Time", key=f"btn_escalar_{chave_prefix}", width='stretch'):
                    if len(roles_selecionadas) != len(posicoes):
                        st.error("Selecione uma função para cada posição.")
                    else:
                        # Chama a seleção de time
                        titulares, reservas = selecionar_time_por_funcoes(
                            df,
                            roles_selecionadas,
                            excluir_lesionados=True,
                            cartoes=None,  # sem cartões por enquanto
                            usar_rating_fallback=False,
                            priorizar_posicao=True,
                            priorizar_minutagem=True
                        )
                        # Armazena para exibição
                        st.session_state.escalacoes_geradas[chave_prefix] = {
                            'titulares': titulares,
                            'reservas': reservas,
                            'formacao': formacao,
                            'roles': roles_selecionadas,
                            'posicoes': posicoes
                        }
                        st.rerun()

                # ===== EXIBE ESCALAÇÃO GERADA =====
                escalacao = st.session_state.escalacoes_geradas.get(chave_prefix)
                if escalacao:
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

                    # Instruções individuais (apenas para titulares)
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

            else:
                st.info("Clique em 'Gerar Posições' para definir a formação.")

        # ===== RODAPÉ DA ABA =====
        st.caption("As roles defensivas (Out of Possession) só aparecem na aba Defensiva.")

# ============================================================
# EXECUÇÃO LOCAL (opcional)
# ============================================================
if __name__ == "__main__":
    show()