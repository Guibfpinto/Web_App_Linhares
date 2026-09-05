# pages/minutagem.py
import streamlit as st
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from utils import (
    carregar_elenco_profissional,
    carregar_elenco_sub15,
    carregar_elenco_sub17,
    mapear_nome_para_canonico,
    PASTA_ESTATISTICAS_PROFISSIONAL,
    PASTA_ESTATISTICAS_SUB15,
    PASTA_ESTATISTICAS_SUB17,
)

def show():
    """Página de Minutagem - comparação de minutos jogados por atleta."""
    st.header("📊 Gráfico de Minutagem")
    st.markdown("Comparativo de minutos jogados por atleta em cada partida.")

    # ============================================================
    # FUNÇÕES AUXILIARES (internas)
    # ============================================================
    def listar_arquivos_estatisticas(pasta):
        if not os.path.exists(pasta):
            return []
        return [os.path.join(pasta, f) for f in os.listdir(pasta) if f.endswith('.csv') and f.startswith('jogo_')]

    def carregar_dados_minutagem(categoria):
        if categoria == "Profissional":
            df_jogadores = carregar_elenco_profissional()
            pasta = PASTA_ESTATISTICAS_PROFISSIONAL
        elif categoria == "Sub-17":
            df_jogadores = carregar_elenco_sub17()
            pasta = PASTA_ESTATISTICAS_SUB17
        elif categoria == "Sub-15":
            df_jogadores = carregar_elenco_sub15()
            pasta = PASTA_ESTATISTICAS_SUB15
        else:
            return None, None

        if df_jogadores is None or df_jogadores.empty:
            st.warning(f"Dados do elenco não carregados para {categoria}.")
            return None, None

        arquivos = listar_arquivos_estatisticas(pasta)
        if not arquivos:
            st.warning(f"Nenhum arquivo de estatísticas encontrado para {categoria}.")
            return None, None

        dados_minutos = {}
        todos_jogadores = set(df_jogadores['apelido'].dropna().unique())
        for jog in todos_jogadores:
            dados_minutos[jog] = {}

        jogos_identificadores = []

        for arquivo in arquivos:
            try:
                df = pd.read_csv(arquivo, sep=';', encoding='utf-8-sig')
                df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
                adversario = df['adversario'].iloc[0] if 'adversario' in df.columns else 'Desconhecido'
                data_jogo = df['data_jogo'].iloc[0] if 'data_jogo' in df.columns else 'Data Indisponível'
                jogo_id = f"{data_jogo} - {adversario}"
                jogos_identificadores.append(jogo_id)

                for _, row in df.iterrows():
                    nome = row.get('jogador', '')
                    if pd.isna(nome) or nome == '':
                        continue
                    canonico = mapear_nome_para_canonico(nome) or nome
                    if canonico not in dados_minutos:
                        dados_minutos[canonico] = {}
                    minutos = int(row.get('minutos', 0)) if pd.notna(row.get('minutos')) else 0
                    dados_minutos[canonico][jogo_id] = minutos

            except Exception as e:
                st.warning(f"Erro ao ler {arquivo}: {e}")
                continue

        if not jogos_identificadores:
            st.warning("Nenhum dado de minutagem encontrado.")
            return None, None

        df_heatmap = pd.DataFrame.from_dict(dados_minutos, orient='index')
        df_heatmap = df_heatmap.fillna(0)
        jogos_existentes = [j for j in jogos_identificadores if j in df_heatmap.columns]
        df_heatmap = df_heatmap[jogos_existentes]

        df_heatmap['total'] = df_heatmap.sum(axis=1)
        df_heatmap = df_heatmap.sort_values('total', ascending=True)
        df_heatmap = df_heatmap.drop(columns=['total'])

        return df_heatmap, jogos_existentes

    def gerar_figura(df_heatmap, jogos_existentes):
        if df_heatmap is None or df_heatmap.empty:
            return None

        df_long = df_heatmap.reset_index().melt(id_vars='index', var_name='Jogo', value_name='Minutos')
        df_long = df_long.rename(columns={'index': 'Jogador'})

        fig, ax = plt.subplots(figsize=(10, max(8, len(df_heatmap) * 0.3)))
        sns.set_style('whitegrid')

        cores_por_jogo = {}
        for i, jogo in enumerate(jogos_existentes):
            if i == 0:
                cores_por_jogo[jogo] = '#FF8C00'
            elif i == 1:
                cores_por_jogo[jogo] = '#1E90FF'
            else:
                cores_extras = sns.color_palette("Set2", n_colors=len(jogos_existentes) - 2)
                cores_por_jogo[jogo] = cores_extras[i - 2]

        sns.barplot(data=df_long, x='Minutos', y='Jogador', hue='Jogo',
                    palette=cores_por_jogo, edgecolor='black', linewidth=0.5, ax=ax)

        ax.set_xlabel('Minutos')
        ax.set_ylabel('Jogador')
        ax.set_title(f'Linhares FC - Comparativo de Minutagem ({len(jogos_existentes)} Jogos)')
        ax.legend(title='Jogo', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(axis='x', linestyle='--', alpha=0.7)

        plt.tight_layout()
        return fig

    def fig_to_bytes(fig, formato='png', dpi=150):
        buf = BytesIO()
        if formato == 'png':
            fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
        elif formato == 'pdf':
            fig.savefig(buf, format='pdf', bbox_inches='tight')
        else:
            raise ValueError("Formato não suportado.")
        buf.seek(0)
        return buf

    # ============================================================
    # INTERFACE
    # ============================================================
    categoria = st.selectbox(
        "Selecione a categoria",
        options=["Profissional", "Sub-17", "Sub-15"],
        index=0,
        key="minutagem_categoria"
    )

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if st.button("🔄 Gerar Gráfico", use_container_width=True):
            st.session_state['gerar_minutagem'] = True
    with col2:
        exportar_png = st.button("📥 Exportar PNG", use_container_width=True)
    with col3:
        exportar_pdf = st.button("📥 Exportar PDF", use_container_width=True)

    if 'gerar_minutagem' not in st.session_state:
        st.session_state['gerar_minutagem'] = False

    if st.session_state['gerar_minutagem'] or exportar_png or exportar_pdf:
        with st.spinner("Carregando dados e gerando gráfico..."):
            df_heatmap, jogos_existentes = carregar_dados_minutagem(categoria)

            if df_heatmap is not None and jogos_existentes:
                fig = gerar_figura(df_heatmap, jogos_existentes)
                if fig:
                    st.session_state['fig_minutagem'] = fig
                    st.session_state['df_minutagem'] = df_heatmap
                    st.session_state['jogos_minutagem'] = jogos_existentes
                    st.success(f"Gráfico gerado com sucesso! {len(jogos_existentes)} jogos analisados.")
                else:
                    st.error("Erro ao gerar a figura.")
            else:
                st.warning("Não foi possível gerar o gráfico. Verifique os dados.")

    if 'fig_minutagem' in st.session_state:
        st.pyplot(st.session_state['fig_minutagem'])

        col_export1, col_export2 = st.columns(2)
        with col_export1:
            if st.button("📥 Exportar PNG (novo)", use_container_width=True):
                fig = st.session_state['fig_minutagem']
                buf = fig_to_bytes(fig, 'png')
                st.download_button(
                    label="Baixar PNG",
                    data=buf,
                    file_name=f"minutagem_{categoria}.png",
                    mime="image/png",
                    use_container_width=True
                )
        with col_export2:
            if st.button("📥 Exportar PDF (novo)", use_container_width=True):
                fig = st.session_state['fig_minutagem']
                buf = fig_to_bytes(fig, 'pdf')
                st.download_button(
                    label="Baixar PDF",
                    data=buf,
                    file_name=f"minutagem_{categoria}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

    if exportar_png and 'fig_minutagem' in st.session_state:
        fig = st.session_state['fig_minutagem']
        buf = fig_to_bytes(fig, 'png')
        st.download_button(
            label="Clique para baixar PNG",
            data=buf,
            file_name=f"minutagem_{categoria}.png",
            mime="image/png"
        )
    elif exportar_pdf and 'fig_minutagem' in st.session_state:
        fig = st.session_state['fig_minutagem']
        buf = fig_to_bytes(fig, 'pdf')
        st.download_button(
            label="Clique para baixar PDF",
            data=buf,
            file_name=f"minutagem_{categoria}.pdf",
            mime="application/pdf"
        )

    with st.expander("Ver dados brutos (minutagem)"):
        if 'df_minutagem' in st.session_state:
            st.dataframe(st.session_state['df_minutagem'])
        else:
            st.info("Nenhum dado carregado ainda.")