# pages/visualizacao.py
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from mplsoccer import Pitch
from utils import carregar_elenco_profissional, carregar_elenco_sub15, carregar_elenco_sub17, sanitizar_dataframe

def get_elenco(categoria):
    if categoria == "Profissional":
        return carregar_elenco_profissional()
    elif categoria == "Sub-15":
        return carregar_elenco_sub15()
    elif categoria == "Sub-17":
        return carregar_elenco_sub17()
    return None

def detectar_coluna(df, possiveis, fallback=None):
    for col in df.columns:
        if col.lower() in [p.lower() for p in possiveis]:
            return col
    return fallback

ZONAS = {
    'goleiro': (50, 5, 8, 5),
    'zagueiro': (30, 25, 20, 10),
    'lateral direito': (10, 35, 10, 15),
    'lateral esquerdo': (90, 35, 10, 15),
    'volante': (40, 45, 15, 10),
    'meia central': (50, 55, 15, 10),
    'meia atacante': (50, 65, 15, 10),
    'ponta direita': (15, 75, 10, 15),
    'ponta esquerda': (85, 75, 10, 15),
    'centroavante': (50, 85, 10, 10),
    'atacante': (50, 80, 15, 15),
    'lateral': (50, 35, 40, 15),
    'defensor': (50, 25, 30, 15),
}

def obter_zona(posicao):
    pos = posicao.lower().strip()
    for chave, zona in ZONAS.items():
        if chave in pos or pos in chave:
            return zona
    return (50, 50, 30, 30)

def gerar_posicoes_simuladas(df_elenco, num_amostras=30):
    if df_elenco.empty:
        return pd.DataFrame(columns=['Nome', 'Posicao', 'x', 'y'])

    col_nome = detectar_coluna(df_elenco, ['apelido', 'nome_completo', 'nome', 'jogador'], fallback=df_elenco.columns[0])
    col_pos = detectar_coluna(df_elenco, ['posicao', 'posição', 'position'], fallback=None)

    if col_pos is None:
        df_elenco['Posicao_Generica'] = 'Atacante'
        col_pos = 'Posicao_Generica'

    dados = []
    for _, row in df_elenco.iterrows():
        nome = str(row[col_nome]) if col_nome in df_elenco else 'Jogador'
        pos_original = str(row[col_pos]) if col_pos in df_elenco else 'Atacante'
        pos_principal = pos_original.split('/')[0].strip()
        x_center, y_center, sx, sy = obter_zona(pos_principal)
        for _ in range(num_amostras):
            x = np.clip(np.random.normal(x_center, sx), 0, 100)
            y = np.clip(np.random.normal(y_center, sy), 0, 100)
            dados.append({
                'Nome': nome,
                'Posicao': pos_principal,
                'x': x,
                'y': y
            })
    return pd.DataFrame(dados)

def desenhar_heatmap(df_posicoes, titulo, jogador_filtro=None, pitch_type='statsbomb'):
    if df_posicoes.empty:
        return None
    if jogador_filtro:
        df_filtrado = df_posicoes[df_posicoes['Nome'] == jogador_filtro]
        if df_filtrado.empty:
            return None
        titulo = f"Heatmap - {jogador_filtro}"
    else:
        df_filtrado = df_posicoes
        titulo = f"Heatmap Coletivo - {titulo}"

    pitch = Pitch(pitch_type=pitch_type, pitch_color='#22312b', line_color='#efefef')
    fig, ax = pitch.draw(figsize=(10, 7))

    x_metros = df_filtrado['x'] * 1.2
    y_metros = df_filtrado['y'] * 0.8

    try:
        from scipy.stats import gaussian_kde
        xy = np.vstack([x_metros, y_metros])
        if xy.shape[1] < 2:
            raise ValueError
        kde = gaussian_kde(xy)
        x_grid = np.linspace(0, 120, 200)
        y_grid = np.linspace(0, 80, 200)
        xx, yy = np.meshgrid(x_grid, y_grid)
        positions = np.vstack([xx.ravel(), yy.ravel()])
        z = kde(positions).reshape(xx.shape)
        ax.imshow(z, extent=[0, 120, 0, 80], origin='lower', cmap='hot', alpha=0.6, aspect='auto')
        ax.set_xlim(0, 120)
        ax.set_ylim(0, 80)
    except:
        ax.scatter(x_metros, y_metros, alpha=0.3, s=15, color='red')

    ax.set_title(titulo, fontsize=16, color='white')
    return fig

def show():
    categoria = st.session_state.get("categoria_visualizacao", "Profissional")
    st.title(f"🎥 Visualização Tática - {categoria}")
    st.markdown("---")

    df_elenco = get_elenco(categoria)
    if df_elenco is None or df_elenco.empty:
        st.warning(f"Elenco não disponível para {categoria}.")
        if df_elenco is not None:
            st.write("Colunas disponíveis:", df_elenco.columns.tolist())
            df_exib = sanitizar_dataframe(df_elenco.head())
            st.dataframe(df_exib, width='stretch')
        return

    st.write(f"**{len(df_elenco)} jogadores** carregados para {categoria}.")

    with st.expander("🔍 Diagnóstico: dados carregados"):
        st.write("Colunas:", df_elenco.columns.tolist())
        df_exib = sanitizar_dataframe(df_elenco.head(5))
        st.dataframe(df_exib, width='stretch')

    col_pos = detectar_coluna(df_elenco, ['posicao', 'posição', 'position'])
    if col_pos:
        pos_principais = df_elenco[col_pos].apply(lambda x: x.split('/')[0].strip() if pd.notna(x) else 'Desconhecido')
        pos_counts = pos_principais.value_counts()
        st.subheader("📊 Distribuição por Posição")
        fig1, ax1 = plt.subplots(figsize=(10, 5))
        pos_counts.plot(kind='bar', ax=ax1, color='skyblue')
        ax1.set_title(f"Distribuição de Posições - {categoria}")
        ax1.set_xlabel("Posição")
        ax1.set_ylabel("Quantidade")
        ax1.tick_params(axis='x', rotation=45)
        st.pyplot(fig1)

    st.subheader("🔥 Mapa de Calor (Heatmap) em Campo")
    with st.spinner("Gerando posições simuladas..."):
        df_posicoes = gerar_posicoes_simuladas(df_elenco, num_amostras=30)

    if df_posicoes.empty:
        st.warning("Não foi possível gerar posições simuladas.")
    else:
        opcao = st.radio("Visualizar:", ["Time inteiro", "Jogador específico"], horizontal=True)
        if opcao == "Jogador específico":
            col_nome = detectar_coluna(df_elenco, ['apelido', 'nome_completo', 'nome', 'jogador'])
            if col_nome:
                jogadores = sorted(df_elenco[col_nome].unique())
                jogador_sel = st.selectbox("Selecione o jogador:", jogadores)
                fig_heat = desenhar_heatmap(df_posicoes, categoria, jogador_filtro=jogador_sel)
            else:
                st.warning("Coluna de nomes não encontrada. Mostrando heatmap coletivo.")
                fig_heat = desenhar_heatmap(df_posicoes, categoria, jogador_filtro=None)
        else:
            fig_heat = desenhar_heatmap(df_posicoes, categoria, jogador_filtro=None)

        if fig_heat:
            st.pyplot(fig_heat)

    st.subheader("📍 Posições médias dos jogadores")
    if not df_posicoes.empty:
        pos_media = df_posicoes.groupby('Nome').agg({'x': 'mean', 'y': 'mean'}).reset_index()
        col_nome = detectar_coluna(df_elenco, ['apelido', 'nome_completo', 'nome', 'jogador'])
        col_pos = detectar_coluna(df_elenco, ['posicao', 'posição', 'position'])
        if col_nome and col_pos:
            df_aux = df_elenco[[col_nome, col_pos]].copy()
            df_aux['Posicao_Simplificada'] = df_aux[col_pos].apply(lambda x: x.split('/')[0].strip() if pd.notna(x) else 'Atacante')
            pos_media = pos_media.merge(df_aux[[col_nome, 'Posicao_Simplificada']],
                                        left_on='Nome', right_on=col_nome, how='left')
        else:
            pos_media['Posicao_Simplificada'] = 'Atacante'

        pitch = Pitch(pitch_type='statsbomb', pitch_color='#22312b', line_color='#efefef')
        fig2, ax2 = pitch.draw(figsize=(10, 7))

        for _, row in pos_media.iterrows():
            x = row['x'] * 1.2
            y = row['y'] * 0.8
            ax2.scatter(x, y, s=150, color='red', alpha=0.7, edgecolors='white', linewidth=1)
            nome_abrev = row['Nome'][:3] if len(row['Nome']) > 3 else row['Nome']
            ax2.annotate(nome_abrev, (x, y), color='white', fontsize=8, ha='center', va='center')

        st.pyplot(fig2)

    with st.expander("ℹ️ Sobre a simulação"):
        st.write("""
        - As posições são **simuladas** a partir da posição principal, usando distribuição normal.
        - O heatmap usa KDE (scipy) se disponível; senão, scatter.
        - Para dados reais, substitua a simulação por dados de tracking.
        """)