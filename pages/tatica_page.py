# pages/tatica_page.py
import streamlit as st
from utils import carregar_elenco_profissional, interpretar_formacao
from tatica import ROLES_FM26_PT, selecionar_time_por_funcoes, gerar_instrucoes_por_role

def show():
    st.title("📐 Escalação Tática")
    df = carregar_elenco_profissional()
    if df.empty:
        st.warning("Elenco não carregado.")
        return

    formacao = st.text_input("Formação (ex: 4-4-2)", value="4-4-2")
    col_form, col_btn = st.columns([3, 1])
    with col_form:
        formacao = st.text_input("Formação", value="4-4-2")
    with col_btn:
        if st.button("Gerar Posições", use_container_width=True):
            defensores, meio, atac, posicoes = interpretar_formacao(formacao)
            if not posicoes:
                st.error("Formação inválida.")
            else:
                st.session_state.posicoes = posicoes

    if "posicoes" in st.session_state:
        posicoes = st.session_state.posicoes
        roles = []
        for i, (pos_exibida, pos_tipo) in enumerate(posicoes):
            role_list = list(ROLES_FM26_PT.keys())
            default = "Meia Central" if "Meio" in pos_tipo else "Centroavante"
            role = st.selectbox(f"{pos_exibida}", role_list, index=role_list.index(default) if default in role_list else 0, key=f"role_{i}")
            roles.append(role)

        if st.button("Gerar Escalação", use_container_width=True):
            titulares, reservas = selecionar_time_por_funcoes(df, roles, excluir_lesionados=True)
            st.subheader("⚽ Titulares")
            for i, jog in enumerate(titulares, 1):
                st.write(f"{i}. {jog['nome']} ({jog['apelido']}) - {jog['role']} (Score: {jog['score']:.1f})")
            st.subheader("🟢 Reservas")
            for i, jog in enumerate(reservas, 1):
                st.write(f"{i}. {jog['nome']} ({jog['apelido']})")
            st.subheader("📝 Instruções")
            for jog in titulares:
                inst = gerar_instrucoes_por_role(jog['row'], jog['role'])
                st.write(f"**{jog['nome']}**")
                st.write(f"- Com bola: {', '.join(inst['com_bola'])}")
                st.write(f"- Sem bola: {', '.join(inst['sem_bola'])}")