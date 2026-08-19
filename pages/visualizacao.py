# pages/visualizacao.py
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from mplsoccer import Pitch
from utils import carregar_elenco_profissional

def show():
    st.title("📈 Visualização Tática")
    df = carregar_elenco_profissional()
    if df.empty:
        st.warning("Elenco não carregado.")
        return

    jogador = st.selectbox("Jogador", df['nome_completo'].tolist())
    tipo = st.selectbox("Tipo", ["Mapa de Calor", "Finalizações", "Passes"])

    # key adicionada para resolver o erro StreamlitDuplicateElementId
    if st.button("Gerar", use_container_width=True, key="btn_gerar_visualizacao"):
        np.random.seed(42)
        x = np.random.uniform(0, 120, 30)
        y = np.random.uniform(0, 80, 30)

        fig, ax = plt.subplots(figsize=(10, 7))
        pitch = Pitch(
            pitch_type='statsbomb', 
            line_zorder=2, 
            pitch_color='#22312b', 
            line_color='#efefef'
        )
        pitch.draw(ax=ax)
        
        if tipo == "Mapa de Calor":
            pitch.heatmap(pitch.bin_statistic(x, y, bins=(50, 50)), ax=ax, cmap='Reds')
        else:
            color = 'blue' if tipo == "Passes" else 'red'
            pitch.scatter(x, y, ax=ax, c=color, s=50, alpha=0.7)
            
        st.pyplot(fig)