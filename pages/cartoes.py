# pages/cartoes.py
import streamlit as st
import pandas as pd
from utils import (
    carregar_cartoes_json,
    salvar_cartoes_json,
    inicializar_cartoes_por_csvs,
    inicializar_cartoes_comissao,
    jogador_suspenso,
    carregar_elenco_profissional,
    mapear_nome_para_canonico,
    inicializar_banco
)

def show():
    inicializar_banco()
    st.title("🟨 Cartões e Suspensões")

    # Seletor de categoria
    categoria = st.selectbox(
        "Categoria",
        ["profissional", "sub20", "sub17", "comissao_profissional", "comissao_sub20", "comissao_sub17"],
        format_func=lambda x: {
            'profissional': 'Profissional',
            'sub20': 'Sub-20',
            'sub17': 'Sub-17',
            'comissao_profissional': 'Comissão Profissional',
            'comissao_sub20': 'Comissão Sub-20',
            'comissao_sub17': 'Comissão Sub-17'
        }[x]
    )

    # Carrega cartões do JSON
    cartoes, datas_globais = carregar_cartoes_json(categoria)

    if not cartoes:
        st.warning("Nenhum cartão encontrado para esta categoria.")
        if st.button("🔄 Reinicializar Cartões (via CSVs)", use_container_width=True):
            if categoria.startswith('comissao_'):
                cartoes, datas = inicializar_cartoes_comissao(categoria)
            else:
                # Para jogadores, precisamos do mapeamento apelido -> ogol_id
                df = carregar_elenco_profissional()
                canonico_para_ogol_id = {}
                for _, row in df.iterrows():
                    canonico = mapear_nome_para_canonico(row.get('apelido'))
                    if canonico and pd.notna(row.get('ogol_id')):
                        canonico_para_ogol_id[canonico] = int(row['ogol_id'])
                cartoes, datas = inicializar_cartoes_por_csvs(categoria, canonico_para_ogol_id)
            st.rerun()
        return

    # Exibe lista de jogadores/membros com cartões
    st.subheader(f"📋 {len(cartoes)} pessoas com cartões")

    # Tabela resumo
    data = []
    for nome, dados in cartoes.items():
        amarelos = dados.get('amarelos', 0)
        vermelho = dados.get('vermelho', False)
        suspenso = dados.get('suspenso_proxima', False)
        data.append({
            'Nome': nome,
            '🟨 Amarelos': amarelos,
            '🟥 Vermelhos': 'Sim' if vermelho else 'Não',
            '⚠️ Suspenso': 'Sim' if suspenso else 'Não'
        })
    df_cartoes = pd.DataFrame(data)
    st.dataframe(df_cartoes, use_container_width=True)

    # Histórico detalhado de um jogador selecionado
    st.subheader("🔍 Histórico de Cartões por Pessoa")
    nomes = sorted(cartoes.keys())
    escolha = st.selectbox("Selecione uma pessoa", nomes)
    if escolha:
        historico = cartoes[escolha].get('historico', [])
        if historico:
            df_hist = pd.DataFrame(historico)
            st.dataframe(df_hist, use_container_width=True)
        else:
            st.write("Nenhum evento de cartão registrado.")

    # Botão para reinicializar
    st.markdown("---")
    if st.button("🔄 Reinicializar Cartões a partir dos CSVs", use_container_width=True):
        if categoria.startswith('comissao_'):
            cartoes, datas = inicializar_cartoes_comissao(categoria)
        else:
            df = carregar_elenco_profissional()
            canonico_para_ogol_id = {}
            for _, row in df.iterrows():
                canonico = mapear_nome_para_canonico(row.get('apelido'))
                if canonico and pd.notna(row.get('ogol_id')):
                    canonico_para_ogol_id[canonico] = int(row['ogol_id'])
            cartoes, datas = inicializar_cartoes_por_csvs(categoria, canonico_para_ogol_id)
        st.rerun()

    # Explicação
    with st.expander("ℹ️ Sobre os cartões"):
        st.write("""
        - **Amarelos:** Acumulados por jogador/membro.
        - **3º Amarelo:** Gera suspensão automática para o próximo jogo.
        - **Vermelho:** Gera suspensão imediata.
        - **Suspensão:** O jogador/membro fica suspenso até que cumpra um jogo.
        - **Reinicialização:** Recalcula todos os cartões a partir dos CSVs de estatísticas.
        """)