# pages/visualizacao.py
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from mplsoccer import Pitch, VerticalPitch
from utils import carregar_elenco_profissional, carregar_elenco_sub15, carregar_elenco_sub17, mapear_nome_para_canonico

def get_elenco(categoria):
    if categoria == "Profissional":
        return carregar_elenco_profissional()
    elif categoria == "Sub-15":
        return carregar_elenco_sub15()
    elif categoria == "Sub-17":
        return carregar_elenco_sub17()
    return None

def show():
    categoria = st.session_state.get("categoria_visualizacao", "Profissional")
    st.title(f"🎥 Visualização Tática - {categoria}")
    st.markdown("---")

    df_elenco = get_elenco(categoria)
    if df_elenco is None or df_elenco.empty:
        st.warning(f"Elenco não disponível para {categoria}.")
        return

    st.write(f"Visualização tática para {categoria} - {len(df_elenco)} jogadores")

    # Exemplo: desenhar um campo com os jogadores em posições aproximadas
    # Para simplificar, vamos mostrar um gráfico de barras com a distribuição de posições
    pos_counts = df_elenco['Posicao_Principal'].value_counts()
    st.subheader("Distribuição por Posição")
    fig, ax = plt.subplots(figsize=(10, 5))
    pos_counts.plot(kind='bar', ax=ax, color='skyblue')
    ax.set_title(f"Distribuição de Posições - {categoria}")
    ax.set_xlabel("Posição")
    ax.set_ylabel("Quantidade")
    st.pyplot(fig)

    st.subheader("Campo com posições aproximadas (exemplo)")
    # Desenha um campo
    pitch = Pitch(pitch_type='statsbomb', pitch_color='#22312b', line_color='#efefef')
    fig, ax = pitch.draw(figsize=(10, 7))
    # Posições aproximadas (exemplo)
    posicoes_exemplo = {
        'Goleiro': (50, 5),
        'Zagueiro': (30, 25),
        'Zagueiro': (70, 25),
        'Lateral Direito': (10, 35),
        'Lateral Esquerdo': (90, 35),
        'Volante': (40, 45),
        'Volante': (60, 45),
        'Meia': (50, 60),
        'Ponta Direita': (15, 75),
        'Ponta Esquerda': (85, 75),
        'Centroavante': (50, 85)
    }
    for pos, (x, y) in posicoes_exemplo.items():
        pitch.scatter(x, y, ax=ax, s=100, color='red', label=pos)
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
    st.pyplot(fig)

    st.info("A visualização avançada pode ser expandida com dados de eventos e heatmaps.")