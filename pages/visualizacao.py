# pages/visualizacao.py
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from mplsoccer import Pitch, VerticalPitch
from utils import carregar_elenco_profissional, carregar_elenco_sub15, carregar_elenco_sub17, mapear_nome_para_canonico

# ============================================================
# FUNÇÕES DE CARREGAMENTO DE ELENCO
# ============================================================
def get_elenco(categoria):
    if categoria == "Profissional":
        return carregar_elenco_profissional()
    elif categoria == "Sub-15":
        return carregar_elenco_sub15()
    elif categoria == "Sub-17":
        return carregar_elenco_sub17()
    return None

# ============================================================
# FUNÇÃO PARA GERAR POSIÇÕES SIMULADAS EM CAMPO
# ============================================================
def gerar_posicoes_simuladas(df_elenco, num_amostras=50):
    """
    Gera coordenadas (x, y) simuladas para cada jogador com base em sua posição principal.
    Retorna um DataFrame com colunas: Nome, Posicao, x, y
    """
    # Zonas aproximadas para cada posição (em coordenadas percentuais do campo 0-100)
    zonas = {
        'Goleiro': (50, 5, 10, 5),           # (x_centro, y_centro, dispersão_x, dispersão_y)
        'Zagueiro': (30, 25, 15, 10),
        'Zagueiro': (70, 25, 15, 10),
        'Lateral Direito': (10, 35, 10, 15),
        'Lateral Esquerdo': (90, 35, 10, 15),
        'Volante': (40, 45, 15, 10),
        'Volante': (60, 45, 15, 10),
        'Meia': (50, 60, 15, 10),
        'Ponta Direita': (15, 75, 10, 15),
        'Ponta Esquerda': (85, 75, 10, 15),
        'Centroavante': (50, 85, 10, 10),
        'Atacante': (50, 80, 15, 15),
        'Meia Atacante': (50, 65, 15, 10),
        'Meia Central': (50, 55, 15, 10),
        'Lateral': (50, 35, 40, 15),         # para laterais genéricos
        'Defensor': (50, 25, 30, 15),
        'Atacante': (50, 80, 20, 15)
    }

    dados = []
    for _, row in df_elenco.iterrows():
        nome = row['Nome']
        pos_principal = row['Posicao_Principal']
        # Tenta encontrar zona exata; se não, usa a posição genérica
        if pos_principal in zonas:
            x_center, y_center, sx, sy = zonas[pos_principal]
        else:
            # Posição desconhecida: coloca no centro com alta dispersão
            x_center, y_center, sx, sy = 50, 50, 30, 30

        # Gera múltiplas amostras para cada jogador (para criar densidade)
        for _ in range(num_amostras):
            # Usa distribuição normal truncada para manter dentro do campo (0-100)
            x = np.clip(np.random.normal(x_center, sx), 0, 100)
            y = np.clip(np.random.normal(y_center, sy), 0, 100)
            dados.append({
                'Nome': nome,
                'Posicao': pos_principal,
                'x': x,
                'y': y
            })
    return pd.DataFrame(dados)

# ============================================================
# FUNÇÃO PARA DESENHAR HEATMAP INDIVIDUAL OU COLETIVO
# ============================================================
def desenhar_heatmap(df_posicoes, titulo, jogador_filtro=None, pitch_type='statsbomb'):
    """
    Desenha um campo com heatmap das posições.
    Se jogador_filtro for None, desenha heatmap de todo o time.
    Caso contrário, filtra por nome do jogador.
    """
    if jogador_filtro:
        df_filtrado = df_posicoes[df_posicoes['Nome'] == jogador_filtro]
        if df_filtrado.empty:
            st.warning(f"Nenhuma posição simulada para {jogador_filtro}. Tente outro jogador.")
            return None
        titulo = f"Heatmap - {jogador_filtro}"
    else:
        df_filtrado = df_posicoes
        titulo = f"Heatmap Coletivo - {titulo}"

    # Cria o pitch
    pitch = Pitch(pitch_type=pitch_type, pitch_color='#22312b', line_color='#efefef')
    fig, ax = pitch.draw(figsize=(10, 7))

    # Para heatmap, usamos a função kde (kernel density estimate) do matplotlib
    # Extrai coordenadas em metros (mplsoccer usa coordenadas em metros)
    # Como simulamos em percentuais (0-100), convertemos para metros (0-120 em x, 0-80 em y para statsbomb)
    # Mas o Pitch do mplsoccer espera coordenadas em metros. Vamos assumir que o campo é 120x80.
    # Para simplificar, mapeamos de 0-100 para 0-120 (x) e 0-80 (y)
    x_metros = df_filtrado['x'] * 1.2  # 0-100 -> 0-120
    y_metros = df_filtrado['y'] * 0.8  # 0-100 -> 0-80

    # Cria o heatmap com a função kdeplot do seaborn? Não, usamos numpy e matplotlib diretamente.
    # Podemos usar a função gaussian_kde da scipy? Melhor usar a função embutida do matplotlib:
    # ax.hexbin pode ser mais rápido, mas prefiro um smooth com gaussian_kde.
    from scipy.stats import gaussian_kde
    try:
        # Calcula a densidade
        xy = np.vstack([x_metros, y_metros])
        kde = gaussian_kde(xy)
        # Cria uma grade para avaliar
        x_grid = np.linspace(0, 120, 200)
        y_grid = np.linspace(0, 80, 200)
        xx, yy = np.meshgrid(x_grid, y_grid)
        positions = np.vstack([xx.ravel(), yy.ravel()])
        z = kde(positions).reshape(xx.shape)
        # Plotar o heatmap
        ax.imshow(z, extent=[0, 120, 0, 80], origin='lower', cmap='hot', alpha=0.6, aspect='auto')
        # Ajustar limites
        ax.set_xlim(0, 120)
        ax.set_ylim(0, 80)
    except ImportError:
        st.warning("Biblioteca scipy não instalada. Usando scatter simples.")
        # Fallback: scatter com transparência
        ax.scatter(x_metros, y_metros, alpha=0.2, s=10, color='red')

    # Título
    ax.set_title(titulo, fontsize=16, color='white')
    return fig

# ============================================================
# PÁGINA PRINCIPAL
# ============================================================
def show():
    # Define categoria via session_state (padrão 'Profissional')
    categoria = st.session_state.get("categoria_visualizacao", "Profissional")
    st.title(f"🎥 Visualização Tática - {categoria}")
    st.markdown("---")

    df_elenco = get_elenco(categoria)
    if df_elenco is None or df_elenco.empty:
        st.warning(f"Elenco não disponível para {categoria}.")
        return

    st.write(f"**{len(df_elenco)} jogadores** carregados para {categoria}.")

    # ============================================================
    # DISTRIBUIÇÃO POR POSIÇÃO (gráfico de barras)
    # ============================================================
    st.subheader("📊 Distribuição por Posição")
    pos_counts = df_elenco['Posicao_Principal'].value_counts()
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    pos_counts.plot(kind='bar', ax=ax1, color='skyblue')
    ax1.set_title(f"Distribuição de Posições - {categoria}")
    ax1.set_xlabel("Posição")
    ax1.set_ylabel("Quantidade")
    ax1.tick_params(axis='x', rotation=45)
    st.pyplot(fig1)

    # ============================================================
    # SEÇÃO DE HEATMAP
    # ============================================================
    st.subheader("🔥 Mapa de Calor (Heatmap) em Campo")

    # Gerar posições simuladas (usando os jogadores reais)
    with st.spinner("Gerando posições simuladas..."):
        df_posicoes = gerar_posicoes_simuladas(df_elenco, num_amostras=30)  # 30 amostras por jogador

    # Opção de filtro: todos ou um jogador específico
    opcao = st.radio("Visualizar:", ["Time inteiro", "Jogador específico"], horizontal=True)

    if opcao == "Jogador específico":
        jogadores = sorted(df_elenco['Nome'].unique())
        jogador_sel = st.selectbox("Selecione o jogador:", jogadores)
        fig_heat = desenhar_heatmap(df_posicoes, categoria, jogador_filtro=jogador_sel)
    else:
        fig_heat = desenhar_heatmap(df_posicoes, categoria, jogador_filtro=None)

    if fig_heat:
        st.pyplot(fig_heat)

    # ============================================================
    # CAMPO COM POSIÇÕES MÉDIAS (exemplo estático)
    # ============================================================
    st.subheader("📍 Posições médias dos jogadores (aproximado)")
    # Calcular a posição média de cada jogador (centroide)
    pos_media = df_posicoes.groupby('Nome').agg({'x': 'mean', 'y': 'mean'}).reset_index()
    # Juntar com a posição principal
    pos_media = pos_media.merge(df_elenco[['Nome', 'Posicao_Principal']], on='Nome', how='left')

    # Desenhar campo
    pitch = Pitch(pitch_type='statsbomb', pitch_color='#22312b', line_color='#efefef')
    fig2, ax2 = pitch.draw(figsize=(10, 7))

    # Plotar cada jogador
    for _, row in pos_media.iterrows():
        x = row['x'] * 1.2
        y = row['y'] * 0.8
        ax2.scatter(x, y, s=150, color='red', alpha=0.7, edgecolors='white', linewidth=1)
        ax2.annotate(row['Nome'][:3], (x, y), color='white', fontsize=8, ha='center', va='center')

    st.pyplot(fig2)

    # ============================================================
    # INFORMAÇÕES ADICIONAIS
    # ============================================================
    with st.expander("ℹ️ Sobre a simulação"):
        st.write("As posições mostradas são **simuladas** a partir da posição principal de cada jogador, utilizando distribuições normais para gerar uma nuvem de pontos.")
        st.write("Isso permite visualizar a área de atuação típica de cada atleta em campo.")
        st.write("Para uma análise real, substitua a simulação por dados reais de eventos (GPS ou tracking).")