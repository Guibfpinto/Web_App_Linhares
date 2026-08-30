# pages/proximo_jogo.py
import streamlit as st
import pandas as pd
from datetime import datetime
import json
from pathlib import Path
import os

# ============================================================
# CONFIGURAÇÃO DE CAMINHOS (ajuste se necessário)
# ============================================================
# Se este arquivo está em pages/, a raiz do projeto é um nível acima
BASE_DIR = Path(__file__).resolve().parent.parent
DADOS_DIR = BASE_DIR / "dados"

# Caso o arquivo esteja na raiz, use:
# BASE_DIR = Path(__file__).resolve().parent
# DADOS_DIR = BASE_DIR / "dados"

# ============================================================
# FUNÇÕES DE CARREGAMENTO
# ============================================================
@st.cache_data(ttl=300)  # cache de 5 minutos
def carregar_jogos_do_json(categoria):
    """
    Carrega a lista de jogos do arquivo JSON da categoria.
    Retorna (jogos, mensagem, caminho_absoluto)
    """
    nome_arquivo = {
        "Profissional": "jogos_profissional.json",
        "Sub-15": "jogos_sub15.json",
        "Sub-17": "jogos_sub17.json"
    }.get(categoria)
    if not nome_arquivo:
        return None, "Categoria inválida", None

    caminho = DADOS_DIR / nome_arquivo
    caminho_abs = caminho.resolve()

    if not caminho.exists():
        return None, f"Arquivo não encontrado: {caminho_abs}", caminho_abs

    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            jogos = dados.get('jogos', [])
            if not jogos:
                return None, "O arquivo JSON está vazio ou não contém a chave 'jogos'.", caminho_abs
            return jogos, f"Carregado com sucesso ({len(jogos)} jogos)", caminho_abs
    except json.JSONDecodeError as e:
        return None, f"Erro de sintaxe JSON: {e}", caminho_abs
    except Exception as e:
        return None, f"Erro inesperado: {e}", caminho_abs

def carregar_jogos_do_csv(categoria):
    """
    Fallback: tenta carregar de um arquivo CSV (caso não haja JSON).
    Espera que exista um arquivo 'cronograma_{categoria}.csv' na pasta dados.
    """
    nome_csv = {
        "Profissional": "cronograma_profissional.csv",
        "Sub-15": "cronograma_sub15.csv",
        "Sub-17": "cronograma_sub17.csv"
    }.get(categoria)
    if not nome_csv:
        return None, "Categoria inválida para CSV", None

    caminho = DADOS_DIR / nome_csv
    caminho_abs = caminho.resolve()
    if not caminho.exists():
        return None, f"CSV não encontrado: {caminho_abs}", caminho_abs

    try:
        df = pd.read_csv(caminho, encoding='utf-8')
        if df.empty:
            return None, "CSV vazio", caminho_abs
        # Converter DataFrame para lista de dicionários
        jogos = df.to_dict('records')
        return jogos, f"Carregado do CSV ({len(jogos)} jogos)", caminho_abs
    except Exception as e:
        return None, f"Erro ao ler CSV: {e}", caminho_abs

# ============================================================
# FUNÇÃO PARA CALCULAR O PRÓXIMO JOGO
# ============================================================
def calcular_proximo_jogo(jogos):
    """
    Retorna o próximo jogo (dict) com base nas seguintes regras:
      1. Data >= hoje
      2. Prioridade para status AGENDADO ou AGUARDANDO
      3. Se nenhum com esses status, retorna o mais próximo no futuro
    """
    hoje = datetime.now().date()
    futuros = []

    for jogo in jogos:
        data_str = jogo.get('data_jogo') or jogo.get('data')
        if not data_str:
            continue
        data_str = data_str.strip()
        # Tenta dd/mm/aaaa
        try:
            data_obj = datetime.strptime(data_str, "%d/%m/%Y").date()
        except ValueError:
            # Tenta aaaa-mm-dd
            try:
                data_obj = datetime.strptime(data_str, "%Y-%m-%d").date()
            except ValueError:
                continue

        if data_obj < hoje:
            continue
        futuros.append((data_obj, jogo))

    if not futuros:
        return None

    # Ordena por data
    futuros.sort(key=lambda x: x[0])

    # Prioriza status AGENDADO ou AGUARDANDO
    for _, jogo in futuros:
        status = jogo.get('status', '').upper()
        if status in ['AGENDADO', 'AGUARDANDO']:
            return jogo

    # Caso contrário, retorna o mais próximo
    return futuros[0][1]

# ============================================================
# PÁGINA PRINCIPAL
# ============================================================
def show():
    st.set_page_config(page_title="Próximo Jogo", page_icon="📅", layout="centered")
    st.title("📅 Próximo Jogo")
    st.markdown("---")

    # --- Seleção de categoria ---
    categoria = st.selectbox(
        "Selecione a categoria",
        ["Profissional", "Sub-15", "Sub-17"],
        key="proximo_jogo_categoria"
    )

    # --- Botão recarregar ---
    if st.button("🔄 Recarregar Dados"):
        st.cache_data.clear()
        st.rerun()

    # --- Carregar dados (tenta JSON primeiro, depois CSV) ---
    jogos, mensagem, caminho = carregar_jogos_do_json(categoria)

    # Se não carregou JSON, tenta CSV
    if jogos is None:
        st.warning(f"⚠️ JSON não disponível: {mensagem}. Tentando CSV...")
        jogos, mensagem, caminho = carregar_jogos_do_csv(categoria)

    # Se ainda não carregou, exibe erro e para
    if jogos is None:
        st.error(f"❌ {mensagem}")
        st.info(f"Caminho procurado: `{caminho}`")
        st.info("Certifique-se de que a pasta 'dados' existe na raiz do projeto e contém os arquivos adequados.")
        return

    st.success(f"✅ {mensagem}")

    # ============================================================
    # DIAGNÓSTICO COMPLETO (sempre visível para depuração)
    # ============================================================
    st.subheader("🔍 Diagnóstico dos dados carregados")
    col1, col2, col3 = st.columns(3)
    col1.metric("Data do sistema", datetime.now().date())
    col2.metric("Total de jogos", len(jogos))
    col3.metric("Categoria", categoria)

    # Exibe a tabela completa
    st.dataframe(pd.DataFrame(jogos), use_container_width=True)

    # Mostra quantos jogos são futuros (data >= hoje)
    hoje = datetime.now().date()
    futuros_count = 0
    for j in jogos:
        data_str = j.get('data_jogo') or j.get('data')
        if data_str:
            try:
                data_obj = datetime.strptime(data_str.strip(), "%d/%m/%Y").date()
            except:
                try:
                    data_obj = datetime.strptime(data_str.strip(), "%Y-%m-%d").date()
                except:
                    data_obj = None
            if data_obj and data_obj >= hoje:
                futuros_count += 1
    st.write(f"**Jogos com data >= hoje:** {futuros_count}")

    # ============================================================
    # PRÓXIMO JOGO
    # ============================================================
    st.markdown("---")
    prox = calcular_proximo_jogo(jogos)

    if prox:
        st.subheader("🔜 Próximo Jogo")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Adversário:** {prox.get('adversario', 'N/I')}")
            st.write(f"**Data:** {prox.get('data_jogo', prox.get('data', 'N/I'))}")
            st.write(f"**Horário:** {prox.get('horario', 'N/I')}")
            st.write(f"**Local:** {prox.get('local_jogo', prox.get('local', 'N/I'))}")
        with col2:
            st.write(f"**Competição:** {prox.get('competicao', 'N/I')}")
            st.write(f"**Fase:** {prox.get('fase', 'N/I')}")
            st.write(f"**Status:** {prox.get('status', 'N/I')}")
            if prox.get('estadio'):
                st.write(f"**Estádio:** {prox['estadio']}")
            if prox.get('cidade'):
                st.write(f"**Cidade:** {prox['cidade']}")
        if prox.get('url_completa'):
            st.markdown(f"[🔗 Link do jogo]({prox['url_completa']})")
    else:
        st.warning("⚠️ Nenhum jogo futuro encontrado.")
        st.info("Verifique se existem jogos com data a partir de hoje. Se houver, mas estiverem com status diferente de 'AGENDADO' ou 'AGUARDANDO', eles aparecerão na lista abaixo, mas não serão marcados como próximo.")

    # ============================================================
    # LISTA DE TODOS OS JOGOS FUTUROS
    # ============================================================
    st.markdown("---")
    st.subheader("📋 Todos os jogos futuros")

    df = pd.DataFrame(jogos)

    # Identifica coluna de data
    col_data = None
    for col in ['data_jogo', 'data', 'Data']:
        if col in df.columns:
            col_data = col
            break

    if col_data:
        df[col_data] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce')
        df_futuros = df[df[col_data].dt.date >= hoje].sort_values(col_data)
    else:
        df_futuros = df

    if df_futuros.empty:
        st.info("📭 Nenhum jogo futuro para exibir.")
    else:
        # Seleciona colunas amigáveis
        colunas_exibir = ['data_jogo', 'adversario', 'local_jogo', 'competicao', 'fase', 'status', 'estadio', 'horario']
        colunas_existentes = [c for c in colunas_exibir if c in df_futuros.columns]
        if not colunas_existentes:
            st.dataframe(df_futuros, use_container_width=True)
        else:
            renomear = {
                'data_jogo': 'Data',
                'adversario': 'Adversário',
                'local_jogo': 'Local',
                'competicao': 'Competição',
                'fase': 'Fase',
                'status': 'Status',
                'estadio': 'Estádio',
                'horario': 'Horário'
            }
            df_exibicao = df_futuros[colunas_existentes].rename(columns=renomear)
            st.dataframe(df_exibicao, use_container_width=True)

    # ============================================================
    # DETALHES DO ARQUIVO CARREGADO
    # ============================================================
    with st.expander("📁 Detalhes do arquivo carregado"):
        st.write(f"**Caminho absoluto:** `{caminho}`")
        st.write(f"**Total de registros:** {len(jogos)}")
        st.write(f"**Categoria:** {categoria}")

# ============================================================
# PONTO DE ENTRADA PARA TESTE DIRETO (opcional)
# ============================================================
if __name__ == "__main__":
    show()