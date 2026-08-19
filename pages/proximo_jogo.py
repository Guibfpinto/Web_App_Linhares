# pages/proximo_jogo.py
import json
import os
import streamlit as st


def show():
  st.title("📅 Próximo Jogo")

  caminho_json = "dados/jogos.json"

  if os.path.exists(caminho_json):
    with open(caminho_json, "r", encoding="utf-8") as f:
      dados = json.load(f)

    lista_jogos = dados.get("jogos", [])
    jogo = next(
        (j for j in lista_jogos if j.get("status") == "AGENDADO"), None
    )

    if jogo:
      with st.container(border=True):
        col1, col2 = st.columns(2)

        with col1:
          st.subheader("⚽ Dados da Partida")
          st.write(f"**Confronto:** {jogo.get('time_casa')} x {jogo.get('time_fora')}")
          st.write(
              f"**Competição:** {jogo.get('competicao', 'Capixabão Série B')}"
          )
          st.write(f"**Fase:** {jogo.get('fase', '1ª Fase')}")
          st.write(
              f"**Data e Horário:** {jogo.get('data_jogo')} às"
              f" {jogo.get('horario', '15:00')}"
          )

        with col2:
          st.subheader("📍 Localização")
          st.write(f"**Estádio:** {jogo.get('estadio')}")
          st.write(f"**Endereço:** {jogo.get('endereco')}")
          st.write(f"**Cidade:** {jogo.get('cidade')}")
          st.write(
              f"**Mando:** {'Casa' if jogo.get('local_jogo') == '(C)' else 'Fora'}"
          )
    else:
      st.info("Nenhum próximo jogo agendado.")
  else:
    st.error("Arquivo 'dados/jogos.json' não localizado.")