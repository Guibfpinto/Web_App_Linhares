# pages/analise.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import (
    carregar_elenco_profissional,
    carregar_comissao,
    exibir_foto,
    carregar_estatisticas_partidas,
    mapear_nome_para_canonico,
    inicializar_banco,
    listar_arquivos_estatisticas
)

def show():
    inicializar_banco()

    st.title("📋 Análise de Elenco")

    categoria = st.selectbox("Categoria", ["Profissional", "Sub-20", "Sub-17", "Comissão Técnica"])

    if categoria == "Profissional":
        df = carregar_elenco_profissional()
        df_stats = carregar_estatisticas_partidas("Profissional")
        if not df_stats.empty:
            df['nome_canonico'] = df['apelido'].apply(mapear_nome_para_canonico)
            df = df.merge(df_stats, left_on='nome_canonico', right_on='jogador_canonico', how='left')
            for col in ['starts', 'jogos_90min', 'minutos_totais']:
                if col not in df.columns:
                    df[col] = 0
                else:
                    df[col] = df[col].fillna(0).astype(int)
            df = df.drop(columns=['jogador_canonico', 'nome_canonico'], errors='ignore')
    elif categoria == "Comissão Técnica":
        df = carregar_comissao()
    else:
        st.warning("Categorias Sub-20 e Sub-17 não implementadas ainda.")
        return

    if df.empty:
        st.warning("Dados não carregados. Verifique se os CSVs estão no diretório.")
        return

    # Filtros
    col1, col2 = st.columns([1, 1])
    with col1:
        if 'Posicao_Principal' in df.columns:
            posicoes = st.multiselect("Posição", df['Posicao_Principal'].unique())
        else:
            posicoes = []
    with col2:
        if 'Estado_Fisico' in df.columns:
            estados = st.multiselect("Estado Físico", df['Estado_Fisico'].unique())
        else:
            estados = []

    df_filtrado = df.copy()
    if posicoes:
        df_filtrado = df_filtrado[df_filtrado['Posicao_Principal'].isin(posicoes)]
    if estados:
        df_filtrado = df_filtrado[df_filtrado['Estado_Fisico'].isin(estados)]

    st.subheader(f"Total: {len(df_filtrado)} registros")

    # Exibição com foto e botão "Ver detalhes"
    for idx, row in df_filtrado.iterrows():
        col1, col2 = st.columns([1, 5])
        with col1:
            exibir_foto(row, categoria="Profissional", width=80)
        with col2:
            nome = row.get('nome_completo', 'N/I')
            apelido = row.get('apelido', 'N/I')
            st.write(f"**{nome}** ({apelido})")
            info = f"{row.get('Posicao_Principal', 'N/I')} | {row.get('Idade', 'N/I')} anos | {row.get('Estado_Fisico', 'N/I')}"
            if 'starts' in row:
                info += f" | ⭐ {row['starts']} titularidades"
            if 'minutos_totais' in row:
                info += f" | ⏱️ {row['minutos_totais']} min"
            st.write(info)
            # Botão para ver detalhes (usa switch_page)
            if st.button("Ver detalhes", key=f"detalhes_{idx}"):
                # Armazena o ID do jogador no session_state
                st.session_state.jogador_id = row.get('id', idx)
                # Navega para a página de detalhes
                st.switch_page("pages/detalhes_jogador.py")
        st.divider()

    # Métricas
    st.subheader("📊 Estatísticas Gerais")
    col1, col2 = st.columns(2)
    with col1:
        if 'Idade' in df_filtrado.columns:
            st.metric("Idade Média", f"{df_filtrado['Idade'].mean():.1f} anos")
        if 'IMC' in df_filtrado.columns:
            st.metric("IMC Médio", f"{df_filtrado['IMC'].mean():.1f}")
        if 'starts' in df_filtrado.columns:
            st.metric("Total Titularidades", f"{df_filtrado['starts'].sum()}")
    with col2:
        if 'Gordura_Corporal_%' in df_filtrado.columns:
            st.metric("% Gordura Médio", f"{df_filtrado['Gordura_Corporal_%'].mean():.1f}%")
        if 'Rating_Geral_FM26' in df_filtrado.columns:
            st.metric("Rating FM26 Médio", f"{df_filtrado['Rating_Geral_FM26'].mean():.1f}")
        if 'minutos_totais' in df_filtrado.columns:
            st.metric("Total Minutos", f"{df_filtrado['minutos_totais'].sum()}")

    # Gráficos
    if 'Posicao_Principal' in df_filtrado.columns:
        st.subheader("Distribuição por Posição")
        fig, ax = plt.subplots()
        df_filtrado['Posicao_Principal'].value_counts().plot(kind='bar', ax=ax)
        ax.set_xlabel("Posição")
        ax.set_ylabel("Quantidade")
        st.pyplot(fig)

    if 'Estado_Fisico' in df_filtrado.columns:
        st.subheader("Estado Físico")
        fig, ax = plt.subplots()
        df_filtrado['Estado_Fisico'].value_counts().plot(kind='pie', autopct='%1.1f%%', ax=ax)
        st.pyplot(fig)

    # ===== MINUTAGEM =====
    st.markdown("---")
    st.subheader("📊 Minutagem por Jogador")

    arquivos = listar_arquivos_estatisticas("Profissional")
    if not arquivos:
        st.info("Nenhum CSV de estatísticas de partidas encontrado.")
    else:
        with st.spinner("Carregando dados de minutagem..."):
            dados_minutos = {}
            jogos_identificadores = []

            for arq in arquivos:
                try:
                    df_csv = pd.read_csv(arq, sep=';', encoding='utf-8-sig')
                    df_csv.columns = df_csv.columns.str.strip().str.lower().str.replace(' ', '_')
                    adversario = df_csv['adversario'].iloc[0] if 'adversario' in df_csv.columns else 'Desconhecido'
                    data_jogo = df_csv['data_jogo'].iloc[0] if 'data_jogo' in df_csv.columns else 'Data Indisponível'
                    jogo_id = f"{data_jogo} - {adversario}"
                    jogos_identificadores.append(jogo_id)

                    for _, row in df_csv.iterrows():
                        nome = row.get('jogador', '')
                        if pd.isna(nome) or nome == '':
                            continue
                        canonico = mapear_nome_para_canonico(nome) or nome
                        if canonico not in dados_minutos:
                            dados_minutos[canonico] = {}
                        minutos = int(row.get('minutos', 0)) if pd.notna(row.get('minutos')) else 0
                        dados_minutos[canonico][jogo_id] = minutos
                except Exception as e:
                    st.warning(f"Erro ao ler {arq}: {e}")

            if not jogos_identificadores:
                st.warning("Nenhum dado de minutagem encontrado.")
            else:
                df_heatmap = pd.DataFrame.from_dict(dados_minutos, orient='index').fillna(0)
                jogos_existentes = [j for j in jogos_identificadores if j in df_heatmap.columns]
                df_heatmap = df_heatmap[jogos_existentes]
                df_heatmap['total'] = df_heatmap.sum(axis=1)
                df_heatmap = df_heatmap.sort_values('total', ascending=False)
                df_heatmap_display = df_heatmap.drop(columns=['total'])

                if len(jogos_existentes) > 1:
                    st.write("**Mapa de calor de minutos por jogo:**")
                    fig, ax = plt.subplots(figsize=(10, max(6, len(df_heatmap_display)*0.3)))
                    sns.heatmap(df_heatmap_display, annot=True, fmt='.0f', cmap='YlOrRd',
                                cbar_kws={'label': 'Minutos'}, ax=ax)
                    ax.set_title('Minutagem por Jogador e Jogo')
                    ax.set_xlabel('Jogo')
                    ax.set_ylabel('Jogador')
                    st.pyplot(fig)

                st.write("**Top 15 jogadores por minutos totais:**")
                df_total = df_heatmap[['total']].sort_values('total', ascending=False).head(15)
                fig2, ax2 = plt.subplots(figsize=(10, 6))
                sns.barplot(data=df_total.reset_index(), x='total', y='index', palette='viridis', ax=ax2)
                ax2.set_title('Top 15 Jogadores por Minutos Totais')
                ax2.set_xlabel('Minutos')
                ax2.set_ylabel('Jogador')
                st.pyplot(fig2)

                with st.expander("Ver lista completa de minutagem"):
                    st.dataframe(df_heatmap, use_container_width=True)