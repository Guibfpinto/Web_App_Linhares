# pages/cartoes.py
import streamlit as st
import pandas as pd
from utils import (
    carregar_cartoes_json,
    salvar_cartoes_json,
    formatar_cartoes,
    jogador_suspenso,
    inicializar_cartoes_por_csvs,
    inicializar_cartoes_comissao,
    mapear_nome_para_canonico
)

def show():
    st.title("🟨 Gestão de Cartões")
    st.markdown("---")

    # ============================================================
    # SELEÇÃO DE CATEGORIA
    # ============================================================
    categoria = st.selectbox(
        "Categoria",
        ["Profissional", "Sub-15", "Sub-17", "Comissão Profissional", "Comissão Sub-15", "Comissão Sub-17"],
        key="cartoes_categoria"
    )

    # Mapeia categoria para a chave usada no carregar_cartoes_json
    mapeamento_categoria = {
        "Profissional": "profissional",
        "Sub-15": "sub15",
        "Sub-17": "sub17",
        "Comissão Profissional": "comissao_profissional",
        "Comissão Sub-15": "comissao_sub15",
        "Comissão Sub-17": "comissao_sub17"
    }
    chave_categoria = mapeamento_categoria[categoria]

    # ============================================================
    # CARREGAMENTO DOS DADOS
    # ============================================================
    cartoes, datas_globais = carregar_cartoes_json(chave_categoria)

    if not cartoes:
        st.info(f"Nenhum cartão registrado para {categoria}.")
        return

    # ============================================================
    # EXTRAIR COMPETIÇÕES E FASES ÚNICAS DO HISTÓRICO
    # ============================================================
    competicoes = set()
    fases = set()
    for jogador, dados in cartoes.items():
        for ev in dados.get('historico', []):
            if 'competicao' in ev and ev['competicao']:
                competicoes.add(ev['competicao'])
            if 'fase' in ev and ev['fase']:
                fases.add(ev['fase'])

    competicoes = sorted(list(competicoes))
    fases = sorted(list(fases))

    # ============================================================
    # FILTROS (COMPETIÇÃO E FASE)
    # ============================================================
    col_filtro1, col_filtro2 = st.columns(2)
    with col_filtro1:
        opcoes_competicao = ["Todas"] + competicoes
        competicao_selecionada = st.selectbox(
            "Filtrar por Competição",
            opcoes_competicao,
            key="cartoes_competicao"
        )
    with col_filtro2:
        opcoes_fase = ["Todas"] + fases
        fase_selecionada = st.selectbox(
            "Filtrar por Fase",
            opcoes_fase,
            key="cartoes_fase"
        )

    # ============================================================
    # APLICAR FILTROS
    # ============================================================
    cartoes_filtrados = {}
    for jogador, dados in cartoes.items():
        historico = dados.get('historico', [])
        # Filtra por competição
        if competicao_selecionada != "Todas":
            historico = [ev for ev in historico if ev.get('competicao') == competicao_selecionada]
        # Filtra por fase
        if fase_selecionada != "Todas":
            historico = [ev for ev in historico if ev.get('fase') == fase_selecionada]

        if historico:
            # Cria uma cópia com o histórico filtrado e recalcula amarelos/vermelho
            novos_dados = dados.copy()
            novos_dados['historico'] = historico
            novos_dados['amarelos'] = sum(1 for ev in historico if ev.get('cor') == 'amarelo')
            novos_dados['vermelho'] = any(ev.get('cor') == 'vermelho' for ev in historico)
            # Suspensão é global, mas para o filtro podemos manter o estado original ou resetar
            # Vamos manter o estado original para não enganar o usuário
            novos_dados['suspenso_proxima'] = dados.get('suspenso_proxima', False)
            cartoes_filtrados[jogador] = novos_dados

    if not cartoes_filtrados:
        st.info("Nenhum cartão encontrado com os filtros selecionados.")
        return

    # ============================================================
    # RESUMO EM TABELA
    # ============================================================
    dados_tabela = []
    for jogador, dados in cartoes_filtrados.items():
        amarelos = dados.get('amarelos', 0)
        vermelho = "Sim" if dados.get('vermelho', False) else "Não"
        suspenso = "Sim" if dados.get('suspenso_proxima', False) else "Não"
        total_eventos = len(dados.get('historico', []))
        dados_tabela.append({
            "Jogador": jogador,
            "Amarelos": amarelos,
            "Vermelho": vermelho,
            "Suspenso": suspenso,
            "Total Eventos (filtrados)": total_eventos
        })

    df = pd.DataFrame(dados_tabela)
    st.subheader(f"Resumo de Cartões – {categoria}")
    if competicao_selecionada != "Todas":
        st.caption(f"Filtrado por competição: **{competicao_selecionada}**")
    if fase_selecionada != "Todas":
        st.caption(f"Filtrado por fase: **{fase_selecionada}**")
    st.dataframe(df, use_container_width=True)

    # ============================================================
    # DETALHES INDIVIDUAIS (COM FASE)
    # ============================================================
    st.markdown("---")
    jogador_selecionado = st.selectbox(
        "Ver detalhes de um jogador",
        options=sorted(cartoes_filtrados.keys())
    )

    if jogador_selecionado:
        dados_jogador = cartoes_filtrados[jogador_selecionado]
        historico = dados_jogador.get('historico', [])

        if historico:
            df_hist = pd.DataFrame(historico)
            # Ordena por data (mais recente primeiro)
            if 'data' in df_hist.columns:
                df_hist = df_hist.sort_values('data', ascending=False)
            # Colunas a exibir
            colunas_exibir = ['data', 'adversario', 'cor', 'competicao', 'fase']
            # Garante que as colunas existam
            for col in colunas_exibir:
                if col not in df_hist.columns:
                    df_hist[col] = ''
            st.subheader(f"Histórico de {jogador_selecionado}")
            st.dataframe(df_hist[colunas_exibir], use_container_width=True)

            # Exibe também o texto formatado (opcional)
            with st.expander("Ver texto formatado"):
                st.text(formatar_cartoes({jogador_selecionado: dados_jogador}, jogador_selecionado))
        else:
            st.info("Nenhum evento de cartão para este jogador com os filtros atuais.")

        # ============================================================
        # REINICIALIZAR CARTÕES (USANDO A LÓGICA DE FASES)
        # ============================================================
        if st.button(f"🔄 Reinicializar cartões de {categoria}"):
            # Para jogadores, precisamos do mapeamento nome_canonico -> ogol_id
            if "Comissão" in categoria:
                novos_cartoes, _ = inicializar_cartoes_comissao(chave_categoria, None)
            else:
                # Para jogadores, precisamos do mapeamento (a função já usa o cronograma)
                # Vamos chamar a função sem o mapeamento (ela tentará extrair dos CSVs)
                # Mas podemos passar um dicionário vazio, pois a função usa o cronograma para fase
                canonico_para_ogol_id = {}  # se não tiver, a função tentará extrair
                novos_cartoes, _ = inicializar_cartoes_por_csvs(chave_categoria, canonico_para_ogol_id)
            st.success("Cartões reinicializados com sucesso!")
            st.rerun()


    st.markdown("---")
    st.caption("Os cartões são gerenciados automaticamente pelos CSVs de estatísticas. Reinicialize se necessário.")