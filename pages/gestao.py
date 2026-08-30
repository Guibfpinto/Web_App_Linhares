# pages/gestao.py
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os
import csv
from utils import (
    carregar_elenco_profissional,
    carregar_elenco_sub15,
    carregar_elenco_sub17,
    obter_lesao_atual,
    obter_historico_lesoes_texto,
    adicionar_lesao,
    adicionar_lesao_com_data_fim,
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

def get_csv_path(categoria, nome_arquivo):
    """Retorna o caminho do CSV com sufixo da categoria."""
    base = "dados"
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, f"{nome_arquivo}_{categoria.lower()}.csv")

def carregar_dados_csv(categoria, nome_arquivo, colunas_padrao):
    caminho = get_csv_path(categoria, nome_arquivo)
    if os.path.exists(caminho):
        try:
            df = pd.read_csv(caminho, sep=';', encoding='utf-8-sig')
            # Garante que todas as colunas existam
            for col in colunas_padrao:
                if col not in df.columns:
                    df[col] = ''
            return df
        except Exception:
            return pd.DataFrame(columns=colunas_padrao)
    return pd.DataFrame(columns=colunas_padrao)

def salvar_dados_csv(df, categoria, nome_arquivo):
    caminho = get_csv_path(categoria, nome_arquivo)
    df.to_csv(caminho, sep=';', index=False, encoding='utf-8-sig')

# ============================================================
# PÁGINA PRINCIPAL
# ============================================================
def show():
    categoria = st.session_state.get("categoria_gestao", "Profissional")
    st.title(f"⚙️ Gestão - {categoria}")
    st.markdown("---")

    df_atletas = get_elenco(categoria)
    if df_atletas is None or df_atletas.empty:
        st.warning(f"Nenhum atleta cadastrado para {categoria}.")
        # Ainda permite gerenciar dados mesmo sem atletas (útil para testes)
        lista_atletas = []
    else:
        # Lista de atletas para os formulários
        if 'apelido' in df_atletas.columns:
            lista_atletas = df_atletas['apelido'].dropna().tolist()
        elif 'nome_completo' in df_atletas.columns:
            lista_atletas = df_atletas['nome_completo'].dropna().tolist()
        else:
            lista_atletas = []

    tabs = st.tabs(["Atletas", "Treinos", "Well-being", "Lesões", "Jogos", "GPS"])

    # ============================================================
    # ABA 1: ATLETAS
    # ============================================================
    with tabs[0]:
        st.subheader("Atletas")
        if df_atletas is not None and not df_atletas.empty:
            cols_exibicao = [c for c in ['nome_completo', 'apelido', 'Posicao_Principal', 'Idade', 'Estado_Fisico'] if c in df_atletas.columns]
            st.dataframe(df_atletas[cols_exibicao] if cols_exibicao else df_atletas, use_container_width=True)
        else:
            st.info(f"Nenhum atleta cadastrado para {categoria}.")

    # ============================================================
    # ABA 2: TREINOS
    # ============================================================
    with tabs[1]:
        st.subheader("Treinos")
        cols_tr = ['data', 'tipo', 'descricao', 'pse_alvo', 'atleta']
        df_tr = carregar_dados_csv(categoria, 'treinos', cols_tr)

        with st.expander("➕ Cadastrar Novo Treino"):
            with st.form("form_treino", clear_on_submit=True):
                atleta = st.selectbox("Atleta", lista_atletas if lista_atletas else ["Sem atletas registrados"])
                data = st.date_input("Data do Treino")
                tipo = st.selectbox("Tipo de Treino", ["Tático", "Técnico", "Físico", "Academia", "Recuperação"])
                desc = st.text_area("Descrição/Objetivo")
                pse = st.slider("PSE Alvo (1-10)", 1, 10, 5)

                if st.form_submit_button("Salvar Treino"):
                    novo = pd.DataFrame([{
                        'data': str(data),
                        'tipo': tipo,
                        'descricao': desc,
                        'pse_alvo': pse,
                        'atleta': atleta
                    }])
                    df_tr = pd.concat([df_tr, novo], ignore_index=True)
                    salvar_dados_csv(df_tr, categoria, 'treinos')
                    st.success("Treino salvo com sucesso!")
                    st.rerun()

        st.dataframe(df_tr, use_container_width=True)

    # ============================================================
    # ABA 3: WELL-BEING
    # ============================================================
    with tabs[2]:
        st.subheader("Well-being")
        cols_wb = ['atleta', 'data', 'sono', 'fadiga', 'dor', 'estresse']
        df_wb = carregar_dados_csv(categoria, 'wellbeing', cols_wb)

        with st.expander("➕ Cadastrar Avaliação de Well-Being"):
            with st.form("form_wb", clear_on_submit=True):
                atleta = st.selectbox("Atleta", lista_atletas if lista_atletas else ["Sem atletas registrados"])
                dt_wb = st.date_input("Data")
                c1, c2 = st.columns(2)
                sono = c1.slider("Sono (1-5)", 1, 5, 3)
                fadiga = c2.slider("Fadiga (1-5)", 1, 5, 3)
                c3, c4 = st.columns(2)
                dor = c3.slider("Dor Muscular (1-5)", 1, 5, 3)
                estresse = c4.slider("Estresse (1-5)", 1, 5, 3)

                if st.form_submit_button("Salvar Well-Being"):
                    novo = pd.DataFrame([{
                        'atleta': atleta,
                        'data': str(dt_wb),
                        'sono': sono,
                        'fadiga': fadiga,
                        'dor': dor,
                        'estresse': estresse
                    }])
                    df_wb = pd.concat([df_wb, novo], ignore_index=True)
                    salvar_dados_csv(df_wb, categoria, 'wellbeing')
                    st.success("Well-being salvo com sucesso!")
                    st.rerun()

        st.dataframe(df_wb, use_container_width=True)

    # ============================================================
    # ABA 4: LESÕES
    # ============================================================
    with tabs[3]:
        st.subheader("Lesões / Departamento Médico")
        cols_les = ['atleta', 'lesao', 'data_inicio', 'data_fim', 'status']
        df_les = carregar_dados_csv(categoria, 'lesoes', cols_les)

        with st.expander("➕ Cadastrar Registro Médico"):
            with st.form("form_lesao", clear_on_submit=True):
                atleta = st.selectbox("Atleta", lista_atletas if lista_atletas else ["Sem atletas registrados"])
                lesao = st.text_input("Diagnóstico / Local")
                c1, c2 = st.columns(2)
                data_inicio = c1.date_input("Data da Lesão")
                data_fim = c2.date_input("Previsão de Retorno (opcional)", value=None)
                status = st.selectbox("Status", ["Tratamento", "Transição", "Liberado"])

                if st.form_submit_button("Salvar Lesão"):
                    # Verifica se já existe lesão ativa para o atleta
                    df_existente = df_les[df_les['atleta'] == atleta]
                    ativa = df_existente[df_existente['data_fim'].isna() | (df_existente['data_fim'] == '')]
                    if not ativa.empty:
                        st.warning(f"{atleta} já possui uma lesão ativa. Encerre a anterior antes de cadastrar uma nova.")
                    else:
                        novo = pd.DataFrame([{
                            'atleta': atleta,
                            'lesao': lesao,
                            'data_inicio': str(data_inicio),
                            'data_fim': str(data_fim) if data_fim else '',
                            'status': status
                        }])
                        df_les = pd.concat([df_les, novo], ignore_index=True)
                        salvar_dados_csv(df_les, categoria, 'lesoes')
                        st.success("Lesão salva com sucesso!")
                        st.rerun()

        st.dataframe(df_les, use_container_width=True)

        # Botão para encerrar lesão ativa
        if not df_les.empty:
            atletas_com_lesao = df_les[df_les['data_fim'].isna() | (df_les['data_fim'] == '')]['atleta'].unique()
            if len(atletas_com_lesao) > 0:
                with st.expander("✅ Encerrar Lesão Ativa"):
                    atleta_encerrar = st.selectbox("Selecione o atleta para encerrar a lesão", atletas_com_lesao)
                    data_encerramento = st.date_input("Data de encerramento")
                    if st.button("Encerrar Lesão"):
                        # Atualiza o CSV
                        idx = df_les[(df_les['atleta'] == atleta_encerrar) & (df_les['data_fim'].isna() | (df_les['data_fim'] == ''))].index
                        if not idx.empty:
                            df_les.loc[idx, 'data_fim'] = str(data_encerramento)
                            df_les.loc[idx, 'status'] = 'Liberado'
                            salvar_dados_csv(df_les, categoria, 'lesoes')
                            st.success(f"Lesão de {atleta_encerrar} encerrada em {data_encerramento}.")
                            st.rerun()

    # ============================================================
    # ABA 5: JOGOS
    # ============================================================
    with tabs[4]:
        st.subheader("Jogos")
        cols_jogos = ['atleta', 'data', 'minutos', 'gols', 'assists']
        df_jogos = carregar_dados_csv(categoria, 'jogos', cols_jogos)

        with st.expander("➕ Cadastrar Desempenho em Jogo"):
            with st.form("form_jogo", clear_on_submit=True):
                atleta = st.selectbox("Atleta", lista_atletas if lista_atletas else ["Sem atletas registrados"])
                data = st.date_input("Data do Jogo")
                minutos = st.number_input("Minutos jogados", min_value=0, max_value=120, step=1)
                gols = st.number_input("Gols", min_value=0, step=1)
                assists = st.number_input("Assistências", min_value=0, step=1)

                if st.form_submit_button("Salvar Jogo"):
                    novo = pd.DataFrame([{
                        'atleta': atleta,
                        'data': str(data),
                        'minutos': minutos,
                        'gols': gols,
                        'assists': assists
                    }])
                    df_jogos = pd.concat([df_jogos, novo], ignore_index=True)
                    salvar_dados_csv(df_jogos, categoria, 'jogos')
                    st.success("Desempenho salvo com sucesso!")
                    st.rerun()

        st.dataframe(df_jogos, use_container_width=True)

    # ============================================================
    # ABA 6: GPS
    # ============================================================
    with tabs[5]:
        st.subheader("Métricas de GPS")
        cols_gps = ['atleta', 'data', 'distancia_total', 'velocidade_max', 'sprints']
        df_gps = carregar_dados_csv(categoria, 'gps', cols_gps)

        with st.expander("➕ Cadastrar Dados GPS"):
            with st.form("form_gps", clear_on_submit=True):
                atleta = st.selectbox("Atleta", lista_atletas if lista_atletas else ["Sem atletas registrados"])
                data = st.date_input("Data da Sessão")
                c1, c2, c3 = st.columns(3)
                distancia = c1.number_input("Distância Total (m)", step=100.0)
                vel_max = c2.number_input("Vel. Máx (km/h)", step=0.1)
                sprints = c3.number_input("Sprints", min_value=0, step=1)

                if st.form_submit_button("Salvar GPS"):
                    novo = pd.DataFrame([{
                        'atleta': atleta,
                        'data': str(data),
                        'distancia_total': distancia,
                        'velocidade_max': vel_max,
                        'sprints': sprints
                    }])
                    df_gps = pd.concat([df_gps, novo], ignore_index=True)
                    salvar_dados_csv(df_gps, categoria, 'gps')
                    st.success("Dados GPS salvos com sucesso!")
                    st.rerun()

        st.dataframe(df_gps, use_container_width=True)

    st.markdown("---")
    st.caption(f"Todos os dados são armazenados em CSVs separados por categoria ({categoria}).")