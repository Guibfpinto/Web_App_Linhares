# pages/tatica_page.py
import streamlit as st
import pandas as pd
from datetime import datetime
from utils import (
    carregar_elenco_profissional,
    carregar_elenco_sub15,
    carregar_elenco_sub17,
    carregar_cartoes_json,
    interpretar_formacao,
    obter_jogadores_para_posicao,
    jogador_suspenso,
    mapear_nome_para_canonico,
    exportar_escalacao_excel,
    exportar_escalacao_pdf,
    sanitizar_dataframe,
)

def get_elenco(categoria):
    if categoria == "Profissional":
        return carregar_elenco_profissional()
    elif categoria == "Sub-15":
        return carregar_elenco_sub15()
    elif categoria == "Sub-17":
        return carregar_elenco_sub17()
    return None

def get_cartoes(categoria):
    mapeamento = {
        "Profissional": "profissional",
        "Sub-15": "sub15",
        "Sub-17": "sub17",
    }
    chave = mapeamento.get(categoria)
    if chave:
        cart, _ = carregar_cartoes_json(chave)
        return cart
    return {}

def montar_time_completo(df, formacao, cartoes, incluir_lesionados=False):
    defensores, meias, atacantes, posicoes = interpretar_formacao(formacao)
    if not posicoes:
        return None, None
    titulares = []
    reservas = []
    jogadores_usados = []
    for pos_exibida, pos_tipo in posicoes:
        candidatos = obter_jogadores_para_posicao(df, pos_tipo, jogadores_usados, cartoes, incluir_lesionados)
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

def show():
    categoria = st.session_state.get("categoria_tatica", "Profissional")
    st.title(f"📐 Escalação Tática - {categoria}")
    st.markdown("---")

    df_elenco = get_elenco(categoria)
    cartoes = get_cartoes(categoria)

    if df_elenco is None or df_elenco.empty:
        st.warning(f"Elenco não disponível para {categoria}.")
        return

    col1, col2 = st.columns(2)
    with col1:
        formacao = st.text_input("Formação (ex: 4-4-2)", value="4-4-2")
    with col2:
        incluir_lesionados = st.checkbox("Incluir lesionados na escalação", value=False)

    if st.button("⚽ Gerar Escalação", width='stretch'):
        titulares, reservas = montar_time_completo(df_elenco, formacao, cartoes, incluir_lesionados)
        if titulares is None:
            st.error("Formação inválida.")
        else:
            st.session_state.titulares = titulares
            st.session_state.reservas = reservas
            st.session_state.formacao_atual = formacao
            st.rerun()

    if "titulares" in st.session_state and st.session_state.titulares:
        titulares = st.session_state.titulares
        reservas = st.session_state.reservas
        formacao = st.session_state.formacao_atual

        st.subheader(f"⚽ Time Titular ({formacao})")
        for i, jog in enumerate(titulares, 1):
            if jog['row'] is not None:
                st.write(f"{i}. **{jog['posicao_exibida']}**: {jog['nome']} ({jog['apelido']}) - Rating: {jog['row'].get('Rating_Geral_FM26', 0):.1f}")
            else:
                st.write(f"{i}. **{jog['posicao_exibida']}**: N/D")

        st.subheader("🟢 Reservas")
        for i, jog in enumerate(reservas, 1):
            if jog['row'] is not None:
                st.write(f"{i}. {jog['nome']} ({jog['apelido']}) - {jog['row'].get('Posicao_Principal', '')}")
            else:
                st.write(f"{i}. N/D")

        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            if st.button("📊 Exportar Escalação (Excel)", width='stretch'):
                df_exp = pd.DataFrame([{
                    'Posição': j['posicao_exibida'],
                    'Jogador': j['nome'],
                    'Apelido': j['apelido'],
                    'Rating': j['row'].get('Rating_Geral_FM26', 0) if j['row'] is not None else 0,
                    'Posição Principal': j['row'].get('Posicao_Principal', '') if j['row'] is not None else '',
                } for j in titulares])
                nome_arquivo = f"escalacao_{categoria}_{formacao}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                if exportar_escalacao_excel(df_exp, nome_arquivo):
                    with open(nome_arquivo, "rb") as f:
                        st.download_button("Baixar Excel", data=f, file_name=nome_arquivo, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                else:
                    st.error("Erro ao exportar Excel")
        with col_exp2:
            if st.button("📄 Exportar Escalação (PDF)", width='stretch'):
                df_exp = pd.DataFrame([{
                    'Posição': j['posicao_exibida'],
                    'Jogador': j['nome'],
                    'Apelido': j['apelido'],
                    'Rating': j['row'].get('Rating_Geral_FM26', 0) if j['row'] is not None else 0,
                    'Posição Principal': j['row'].get('Posicao_Principal', '') if j['row'] is not None else '',
                } for j in titulares])
                nome_arquivo = f"escalacao_{categoria}_{formacao}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                if exportar_escalacao_pdf(df_exp, nome_arquivo):
                    with open(nome_arquivo, "rb") as f:
                        st.download_button("Baixar PDF", data=f, file_name=nome_arquivo, mime="application/pdf")
                else:
                    st.error("Erro ao exportar PDF")

    st.markdown("---")
    st.caption("A escalação é gerada com base no Rating Geral FM26 e nas restrições de posição e suspensão.")