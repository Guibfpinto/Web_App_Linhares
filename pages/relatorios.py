# pages/relatorios.py
import streamlit as st
import pandas as pd
from datetime import datetime
import os
from utils import (
    carregar_elenco_profissional,
    carregar_elenco_sub15,
    carregar_elenco_sub17,
    carregar_comissao,
    carregar_comissao_sub15,
    carregar_comissao_sub17,
    gerar_relatorio_completo_texto,
    gerar_relatorio_jogador,
    gerar_relatorio_comissao,
    gerar_relatorio_diretoria,
    exportar_para_excel,
)

# ============================================================
# FUNÇÕES AUXILIARES POR CATEGORIA
# ============================================================
def get_elenco(categoria):
    if categoria == "Profissional":
        return carregar_elenco_profissional()
    elif categoria == "Sub-15":
        return carregar_elenco_sub15()
    elif categoria == "Sub-17":
        return carregar_elenco_sub17()
    return None

def get_comissao(categoria):
    if categoria == "Comissão Profissional":
        return carregar_comissao()
    elif categoria == "Comissão Sub-15":
        return carregar_comissao_sub15()
    elif categoria == "Comissão Sub-17":
        return carregar_comissao_sub17()
    return None

def get_categorias_elenco():
    return ["Profissional", "Sub-15", "Sub-17"]

def get_categorias_comissao():
    return ["Comissão Profissional", "Comissão Sub-15", "Comissão Sub-17"]

# ============================================================
# PÁGINA PRINCIPAL
# ============================================================
def show():
    st.title("📄 Relatórios")
    st.markdown("---")

    # ===== SELEÇÃO DE CATEGORIA =====
    cat_elenco = st.selectbox("Categoria (Elenco)", get_categorias_elenco(), key="rel_elenco_categoria")
    cat_comissao = st.selectbox("Categoria (Comissão)", get_categorias_comissao(), key="rel_comissao_categoria")

    df_elenco = get_elenco(cat_elenco)
    df_comissao = get_comissao(cat_comissao)

    # ============================================================
    # RELATÓRIO DO ELENCO
    # ============================================================
    st.subheader(f"📊 Relatório do Elenco - {cat_elenco}")
    if df_elenco is not None and not df_elenco.empty:
        # Estatísticas rápidas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Jogadores", len(df_elenco))
        with col2:
            if 'Idade' in df_elenco.columns:
                st.metric("Idade Média", f"{df_elenco['Idade'].mean():.1f}")
        with col3:
            if 'Rating_Geral_FM26' in df_elenco.columns:
                st.metric("Rating Médio", f"{df_elenco['Rating_Geral_FM26'].mean():.1f}")

        # Relatório completo (texto)
        with st.expander("📋 Ver Relatório Completo (Texto)"):
            texto = gerar_relatorio_completo_texto(df_elenco, cat_elenco)
            st.text_area("Relatório", texto, height=400)

        # Exportar relatório (Excel)
        if st.button(f"📥 Exportar Relatório do Elenco ({cat_elenco}) para Excel"):
            caminho = f"relatorio_elenco_{cat_elenco}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            if exportar_para_excel(df_elenco, cat_elenco, caminho):
                with open(caminho, "rb") as f:
                    st.download_button("Baixar Excel", data=f, file_name=caminho, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                try:
                    os.remove(caminho)
                except:
                    pass
                st.success("Relatório exportado com sucesso!")
            else:
                st.error("Erro na exportação")

        # Relatório individual por jogador
        st.subheader("📄 Relatório Individual do Jogador")
        jogador_sel = st.selectbox("Selecione um jogador", df_elenco['nome_completo'].tolist())
        if jogador_sel:
            row = df_elenco[df_elenco['nome_completo'] == jogador_sel].iloc[0]
            texto_jogador = gerar_relatorio_jogador(row, cat_elenco)
            st.text_area(f"Relatório de {jogador_sel}", texto_jogador, height=200)

            if st.button(f"📥 Exportar Relatório de {jogador_sel}"):
                caminho = f"relatorio_{jogador_sel}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(caminho, "w", encoding='utf-8') as f:
                    f.write(texto_jogador)
                with open(caminho, "rb") as f:
                    st.download_button("Baixar TXT", data=f, file_name=caminho, mime="text/plain")
                try:
                    os.remove(caminho)
                except:
                    pass
    else:
        st.warning(f"Nenhum dado disponível para {cat_elenco}.")

    st.markdown("---")

    # ============================================================
    # RELATÓRIO DA COMISSÃO
    # ============================================================
    st.subheader(f"👥 Relatório da Comissão - {cat_comissao}")
    if df_comissao is not None and not df_comissao.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total de Membros", len(df_comissao))
        with col2:
            if 'idade' in df_comissao.columns:
                st.metric("Idade Média", f"{df_comissao['idade'].mean():.1f}" if df_comissao['idade'].notna().any() else "N/A")

        # Relatório da comissão
        texto_com = gerar_relatorio_comissao(df_comissao, cat_comissao)
        st.text_area(f"Relatório da Comissão ({cat_comissao})", texto_com, height=200)

        # Exportar relatório da comissão
        if st.button(f"📥 Exportar Relatório da Comissão ({cat_comissao})"):
            caminho = f"relatorio_comissao_{cat_comissao}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(caminho, "w", encoding='utf-8') as f:
                f.write(texto_com)
            with open(caminho, "rb") as f:
                st.download_button("Baixar TXT", data=f, file_name=caminho, mime="text/plain")
            try:
                os.remove(caminho)
            except:
                pass
            st.success("Relatório exportado!")
    else:
        st.warning(f"Nenhum dado disponível para {cat_comissao}.")

    st.markdown("---")

    # ============================================================
    # RELATÓRIO PARA DIRETORIA (combina elenco e comissão)
    # ============================================================
    st.subheader("📈 Relatório para Diretoria")
    if df_elenco is not None and not df_elenco.empty and df_comissao is not None and not df_comissao.empty:
        texto_diretoria = gerar_relatorio_diretoria(df_elenco, cat_elenco)
        # Adiciona informações da comissão
        texto_diretoria += "\n\n" + "="*60 + "\n"
        texto_diretoria += f"COMISSÃO TÉCNICA ({cat_comissao})\n"
        texto_diretoria += "="*60 + "\n"
        texto_diretoria += f"Total de membros: {len(df_comissao)}\n"
        if 'cargo' in df_comissao.columns:
            for cargo, qtd in df_comissao['cargo'].value_counts().items():
                texto_diretoria += f"  {cargo}: {qtd}\n"

        st.text_area("Relatório para Diretoria", texto_diretoria, height=300)

        if st.button("📥 Exportar Relatório para Diretoria"):
            caminho = f"relatorio_diretoria_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(caminho, "w", encoding='utf-8') as f:
                f.write(texto_diretoria)
            with open(caminho, "rb") as f:
                st.download_button("Baixar TXT", data=f, file_name=caminho, mime="text/plain")
            try:
                os.remove(caminho)
            except:
                pass
            st.success("Relatório exportado!")
    else:
        st.info("Carregue os dados de elenco e comissão para gerar o relatório para diretoria.")

    st.markdown("---")
    st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")