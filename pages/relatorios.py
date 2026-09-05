# pages/relatorios.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from utils import (
    carregar_elenco_profissional,
    carregar_elenco_sub15,
    carregar_elenco_sub17,
    carregar_comissao,
    carregar_comissao_sub15,
    carregar_comissao_sub17,
    gerar_relatorio_completo_texto,
    gerar_relatorio_diretoria,
    gerar_relatorio_jogador,
    gerar_relatorio_comissao,
    sanitizar_dataframe,
    DATA_DIR,
)

def show():
    st.header("📄 Relatórios")
    st.markdown("Geração de relatórios detalhados para diretoria, comissão técnica e jogadores.")

    # ============================================================
    # SEÇÃO: RELATÓRIO FINANCEIRO (NOVO)
    # ============================================================
    st.subheader("💰 Dados Financeiros")

    caminho_financeiro = "dados_financeiros.csv"
    if not os.path.exists(caminho_financeiro):
        caminho_financeiro = os.path.join(DATA_DIR, "dados_financeiros.csv")

    if os.path.exists(caminho_financeiro):
        try:
            df_financeiro = pd.read_csv(caminho_financeiro, sep=';', encoding='utf-8-sig')
            st.success(f"Arquivo carregado: {caminho_financeiro} ({len(df_financeiro)} registros)")

            # Exibe a tabela
            df_financeiro_sanitizado = sanitizar_dataframe(df_financeiro)
            st.dataframe(df_financeiro_sanitizado, use_container_width=True)

            # Opção de download
            csv = df_financeiro.to_csv(index=False, sep=';', encoding='utf-8-sig')
            st.download_button(
                label="📥 Baixar dados financeiros (CSV)",
                data=csv,
                file_name="dados_financeiros.csv",
                mime="text/csv"
            )

            # Gráficos simples (opcional)
            st.subheader("📈 Visualização rápida")
            colunas_numericas = df_financeiro.select_dtypes(include=['float64', 'int64']).columns.tolist()
            if colunas_numericas:
                coluna_grafico = st.selectbox(
                    "Selecione uma coluna para gráfico de barras",
                    colunas_numericas,
                    key="financeiro_grafico_coluna"
                )
                st.bar_chart(df_financeiro[coluna_grafico])
            else:
                st.info("Nenhuma coluna numérica para gráfico.")

        except Exception as e:
            st.error(f"Erro ao ler o arquivo financeiro: {e}")
    else:
        st.warning("Arquivo 'dados_financeiros.csv' não encontrado. Coloque-o na raiz do projeto ou na pasta 'data/'.")

    st.divider()

    # ============================================================
    # SEÇÃO: RELATÓRIO DA DIRETORIA
    # ============================================================
    st.subheader("📊 Relatório para Diretoria")

    opcao_diretoria = st.selectbox(
        "Selecione o tipo de relatório",
        [
            "Visão geral do clube",
            "Elenco profissional",
            "Elenco Sub-15",
            "Elenco Sub-17",
            "Comissão técnica profissional",
            "Comissão técnica Sub-15",
            "Comissão técnica Sub-17",
        ],
        key="diretoria_tipo"
    )

    if st.button("Gerar Relatório para Diretoria", key="btn_diretoria"):
        with st.spinner("Gerando relatório..."):
            if opcao_diretoria == "Visão geral do clube":
                texto = "RELATÓRIO GERAL DO CLUBE\n\n"
                for cat in ["Profissional", "Sub-15", "Sub-17"]:
                    df_elenco = None
                    if cat == "Profissional":
                        df_elenco = carregar_elenco_profissional()
                    elif cat == "Sub-15":
                        df_elenco = carregar_elenco_sub15()
                    else:
                        df_elenco = carregar_elenco_sub17()
                    if df_elenco is not None and not df_elenco.empty:
                        texto += f"\n{cat}:\n"
                        texto += f"  Total: {len(df_elenco)} jogadores\n"
                        if 'Idade' in df_elenco.columns:
                            texto += f"  Idade média: {df_elenco['Idade'].mean():.1f}\n"
                        if 'Rating_Geral_FM26' in df_elenco.columns:
                            texto += f"  Rating médio: {df_elenco['Rating_Geral_FM26'].mean():.1f}\n"
                        if 'Estado_Fisico' in df_elenco.columns:
                            criticos = df_elenco[df_elenco['Estado_Fisico'] == 'Crítico']
                            texto += f"  Críticos: {len(criticos)}\n"
                st.text_area("Relatório", texto, height=400)

            elif opcao_diretoria.startswith("Elenco"):
                cat = opcao_diretoria.replace("Elenco ", "")
                df_elenco = None
                if cat == "profissional":
                    df_elenco = carregar_elenco_profissional()
                elif cat == "Sub-15":
                    df_elenco = carregar_elenco_sub15()
                elif cat == "Sub-17":
                    df_elenco = carregar_elenco_sub17()
                if df_elenco is not None and not df_elenco.empty:
                    texto = gerar_relatorio_diretoria(df_elenco, cat)
                    st.text_area(f"Relatório - {cat}", texto, height=400)
                else:
                    st.warning(f"Nenhum dado disponível para {cat}")

            elif opcao_diretoria.startswith("Comissão"):
                cat = opcao_diretoria.replace("Comissão técnica ", "")
                df_com = None
                if cat == "profissional":
                    df_com = carregar_comissao()
                elif cat == "Sub-15":
                    df_com = carregar_comissao_sub15()
                elif cat == "Sub-17":
                    df_com = carregar_comissao_sub17()
                if df_com is not None and not df_com.empty:
                    texto = gerar_relatorio_comissao(df_com, cat)
                    st.text_area(f"Relatório - {cat}", texto, height=400)
                else:
                    st.warning(f"Nenhum dado disponível para {cat}")

    st.divider()

    # ============================================================
    # SEÇÃO: RELATÓRIO DE JOGADOR
    # ============================================================
    st.subheader("📋 Relatório Individual de Jogador")

    col1, col2 = st.columns(2)
    with col1:
        cat_jogador = st.selectbox(
            "Categoria",
            ["Profissional", "Sub-15", "Sub-17"],
            key="jogador_categoria"
        )
    with col2:
        df_elenco_jogador = None
        if cat_jogador == "Profissional":
            df_elenco_jogador = carregar_elenco_profissional()
        elif cat_jogador == "Sub-15":
            df_elenco_jogador = carregar_elenco_sub15()
        elif cat_jogador == "Sub-17":
            df_elenco_jogador = carregar_elenco_sub17()

        if df_elenco_jogador is not None and not df_elenco_jogador.empty:
            col_nome = None
            for possivel in ['nome_completo', 'apelido', 'nome']:
                if possivel in df_elenco_jogador.columns:
                    col_nome = possivel
                    break
            if col_nome:
                jogador_selecionado = st.selectbox(
                    "Selecione o jogador",
                    df_elenco_jogador[col_nome].tolist(),
                    key="jogador_selecionado"
                )
            else:
                st.warning("Coluna de nome não encontrada.")
                jogador_selecionado = None
        else:
            st.warning("Elenco não disponível.")
            jogador_selecionado = None

    if jogador_selecionado and st.button("Gerar Relatório do Jogador", key="btn_jogador"):
        if df_elenco_jogador is not None and not df_elenco_jogador.empty:
            row = df_elenco_jogador[df_elenco_jogador[col_nome] == jogador_selecionado].iloc[0]
            texto = gerar_relatorio_jogador(row, cat_jogador)
            st.text_area(f"Relatório - {jogador_selecionado}", texto, height=300)
        else:
            st.error("Erro ao carregar dados do jogador.")

    st.divider()

    # ============================================================
    # SEÇÃO: RELATÓRIO DA COMISSÃO TÉCNICA (INDIVIDUAL)
    # ============================================================
    st.subheader("👤 Relatório Individual de Membro da Comissão")

    col1, col2 = st.columns(2)
    with col1:
        cat_comissao = st.selectbox(
            "Categoria",
            ["Comissão Profissional", "Comissão Sub-15", "Comissão Sub-17"],
            key="comissao_categoria"
        )
    with col2:
        df_comissao = None
        if cat_comissao == "Comissão Profissional":
            df_comissao = carregar_comissao()
        elif cat_comissao == "Comissão Sub-15":
            df_comissao = carregar_comissao_sub15()
        elif cat_comissao == "Comissão Sub-17":
            df_comissao = carregar_comissao_sub17()

        if df_comissao is not None and not df_comissao.empty:
            col_nome = None
            for possivel in ['nome', 'apelido', 'nome_completo']:
                if possivel in df_comissao.columns:
                    col_nome = possivel
                    break
            if col_nome:
                membro_selecionado = st.selectbox(
                    "Selecione o membro",
                    df_comissao[col_nome].tolist(),
                    key="membro_selecionado"
                )
            else:
                st.warning("Coluna de nome não encontrada.")
                membro_selecionado = None
        else:
            st.warning("Comissão não disponível.")
            membro_selecionado = None

    if membro_selecionado and st.button("Gerar Relatório do Membro", key="btn_membro"):
        if df_comissao is not None and not df_comissao.empty:
            row = df_comissao[df_comissao[col_nome] == membro_selecionado].iloc[0]
            texto = f"RELATÓRIO DE MEMBRO DA COMISSÃO – {cat_comissao}\n\n"
            texto += f"Nome: {row.get('nome', 'N/I')}\n"
            texto += f"Apelido: {row.get('apelido', 'N/I')}\n"
            texto += f"Cargo: {row.get('cargo', 'N/I')}\n"
            texto += f"Idade: {row.get('idade', 'N/I')}\n"
            texto += f"Cidade/UF: {row.get('cidade_nascimento', 'N/I')} / {row.get('uf_nascimento', 'N/I')}\n"
            texto += f"País: {row.get('pais_nascimento', row.get('pais', 'N/I'))}\n"
            st.text_area(f"Relatório - {membro_selecionado}", texto, height=300)
        else:
            st.error("Erro ao carregar dados do membro.")