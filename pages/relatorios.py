# pages/relatorios.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import json
import requests
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
    sanitizar_dataframe,
    ATRIBUTOS_FM26,
    NOME_TIME,
    TEMPORADA,
)

# ============================================================
# CONFIGURAÇÃO DE CÂMBIO EUR/BRL
# ============================================================
ARQUIVO_CAMBIO = os.path.join("data", "cambio_eur_brl.json")

def obter_taxa_cambio_euro_real():
    """
    Obtém a cotação EUR/BRL do dia.
    Retorna a taxa (float) ou None em caso de falha.
    """
    os.makedirs("data", exist_ok=True)
    try:
        # Tenta ler do cache (válido por 24 horas)
        if os.path.exists(ARQUIVO_CAMBIO):
            with open(ARQUIVO_CAMBIO, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                data_cache = datetime.fromisoformat(dados['data'])
                if datetime.now() - data_cache < timedelta(hours=24):
                    return dados['taxa']
        
        # Se cache expirado ou não existe, faz requisição
        url = "https://api.frankfurter.app/latest?from=EUR&to=BRL"
        resposta = requests.get(url, timeout=10)
        if resposta.status_code == 200:
            dados = resposta.json()
            taxa = dados['rates']['BRL']
            # Salva no cache
            with open(ARQUIVO_CAMBIO, 'w', encoding='utf-8') as f:
                json.dump({
                    'data': datetime.now().isoformat(),
                    'taxa': taxa
                }, f)
            return taxa
        else:
            print(f"⚠️ Erro ao obter câmbio: {resposta.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erro na requisição de câmbio: {e}")
        return None

def obter_taxa_cambio_com_fallback():
    """
    Tenta obter a taxa online; se falhar, usa um valor fixo de fallback.
    """
    taxa = obter_taxa_cambio_euro_real()
    if taxa is None:
        print("⚠️ Usando taxa de câmbio fixa de fallback (1 EUR = 5,50 BRL)")
        return 5.50  # valor fixo de fallback
    return taxa

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
# CARREGAR DADOS FINANCEIROS
# ============================================================
def carregar_dados_financeiros():
    """Carrega o CSV de dados financeiros e adiciona colunas com valores convertidos para BRL."""
    caminho = "dados_financeiros.csv"
    if not os.path.exists(caminho):
        return None
    try:
        df = pd.read_csv(caminho, sep=';', encoding='utf-8-sig')
        # Converte colunas numéricas, tratando 'OTH' como 0
        for col in ['valor_compra_eur', 'salario_mensal_brl', 'valor_passe_atual_eur']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Obtém taxa de câmbio
        taxa = obter_taxa_cambio_com_fallback()
        
        # Adiciona colunas em BRL
        df['valor_compra_brl'] = df['valor_compra_eur'] * taxa
        df['valor_passe_atual_brl'] = df['valor_passe_atual_eur'] * taxa
        # Salário já está em BRL, mas mantemos a coluna original
        
        return df, taxa
    except Exception as e:
        print(f"Erro ao ler dados financeiros: {e}")
        return None, None

# ============================================================
# GERADORES DE RELATÓRIOS ESPECÍFICOS
# ============================================================
def gerar_relatorio_para_diretoria(df_elenco, df_comissao, cat_elenco, cat_comissao):
    """Gera um relatório executivo para a diretoria, incluindo dados financeiros convertidos."""
    if df_elenco is None or df_elenco.empty:
        return "Elenco não disponível para gerar relatório."
    
    # Carrega dados financeiros
    df_financeiro, taxa = carregar_dados_financeiros()
    
    linhas = []
    linhas.append("="*70)
    linhas.append(f"RELATÓRIO PARA DIRETORIA – {NOME_TIME} – Temporada {TEMPORADA}")
    linhas.append("="*70)
    linhas.append(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    if taxa:
        linhas.append(f"Cotação EUR/BRL: R$ {taxa:.2f}")
    linhas.append("")
    
    # 1. Resumo do Elenco
    linhas.append("1. RESUMO DO ELENCO")
    linhas.append("-"*40)
    linhas.append(f"Categoria: {cat_elenco}")
    linhas.append(f"Total de jogadores: {len(df_elenco)}")
    if 'Idade' in df_elenco.columns:
        media_idade = df_elenco['Idade'].mean()
        linhas.append(f"Idade média: {media_idade:.1f} anos")
    if 'Rating_Geral_FM26' in df_elenco.columns:
        media_rating = df_elenco['Rating_Geral_FM26'].mean()
        linhas.append(f"Rating FM26 médio: {media_rating:.1f}")
    if 'Posicao_Principal' in df_elenco.columns:
        cont_pos = df_elenco['Posicao_Principal'].value_counts()
        linhas.append("Distribuição por posição:")
        for pos, qtd in cont_pos.items():
            linhas.append(f"  - {pos}: {qtd}")
    linhas.append("")
    
    # 2. Destaques individuais
    if 'Rating_Geral_FM26' in df_elenco.columns and 'nome_completo' in df_elenco.columns:
        linhas.append("2. DESTAQUES INDIVIDUAIS (Top 5 por Rating)")
        linhas.append("-"*40)
        top5 = df_elenco.nlargest(5, 'Rating_Geral_FM26')[['nome_completo', 'Rating_Geral_FM26', 'Posicao_Principal']]
        for _, row in top5.iterrows():
            linhas.append(f"  - {row['nome_completo']} ({row['Posicao_Principal']}) – Rating: {row['Rating_Geral_FM26']:.1f}")
    linhas.append("")
    
    # 3. Condição física
    if 'Estado_Fisico' in df_elenco.columns:
        linhas.append("3. CONDIÇÃO FÍSICA")
        linhas.append("-"*40)
        cont_estado = df_elenco['Estado_Fisico'].value_counts()
        for estado, qtd in cont_estado.items():
            linhas.append(f"  - {estado}: {qtd}")
        criticos = df_elenco[df_elenco['Estado_Fisico'] == 'Crítico']
        if not criticos.empty:
            linhas.append("  Jogadores em estado crítico:")
            for _, row in criticos.iterrows():
                linhas.append(f"    - {row.get('nome_completo', 'N/I')} (IMC: {row.get('IMC', 'N/I')})")
    linhas.append("")
    
    # 4. Lesões
    if 'lesionado' in df_elenco.columns:
        lesionados = df_elenco[df_elenco['lesionado'] == True]
        linhas.append("4. LESÕES")
        linhas.append("-"*40)
        if not lesionados.empty:
            linhas.append(f"Total de lesionados: {len(lesionados)}")
            for _, row in lesionados.iterrows():
                linhas.append(f"  - {row.get('nome_completo', 'N/I')}")
        else:
            linhas.append("  Nenhum jogador lesionado.")
    linhas.append("")
    
    # 5. Comissão Técnica
    if df_comissao is not None and not df_comissao.empty:
        linhas.append("5. COMISSÃO TÉCNICA")
        linhas.append("-"*40)
        linhas.append(f"Categoria: {cat_comissao}")
        linhas.append(f"Total de membros: {len(df_comissao)}")
        if 'cargo' in df_comissao.columns:
            cont_cargo = df_comissao['cargo'].value_counts()
            linhas.append("Distribuição por cargo:")
            for cargo, qtd in cont_cargo.items():
                linhas.append(f"  - {cargo}: {qtd}")
        if 'idade' in df_comissao.columns:
            media_idade_com = df_comissao['idade'].mean()
            linhas.append(f"Idade média: {media_idade_com:.1f} anos")
    linhas.append("")
    
    # 6. DADOS FINANCEIROS (com conversão)
    if df_financeiro is not None and not df_financeiro.empty:
        linhas.append("6. DADOS FINANCEIROS DOS JOGADORES")
        linhas.append("-"*40)
        # Resumo financeiro
        total_compra_eur = df_financeiro['valor_compra_eur'].sum()
        total_compra_brl = df_financeiro['valor_compra_brl'].sum()
        total_salario = df_financeiro['salario_mensal_brl'].sum()
        total_passe_eur = df_financeiro['valor_passe_atual_eur'].sum()
        total_passe_brl = df_financeiro['valor_passe_atual_brl'].sum()
        
        linhas.append(f"  💰 Total investido em compras: € {total_compra_eur:,.2f} (R$ {total_compra_brl:,.2f})")
        linhas.append(f"  💰 Total de salários mensais: R$ {total_salario:,.2f}")
        linhas.append(f"  💰 Valor total de passe: € {total_passe_eur:,.2f} (R$ {total_passe_brl:,.2f})")
        linhas.append("")
        # Lista detalhada
        linhas.append("  Detalhamento por jogador:")
        for _, row in df_financeiro.iterrows():
            apelido = row.get('apelido', 'N/I')
            data_compra = row.get('data_compra', 'N/I')
            valor_compra_eur = row.get('valor_compra_eur', 0)
            valor_compra_brl = row.get('valor_compra_brl', 0)
            salario = row.get('salario_mensal_brl', 0)
            valor_passe_eur = row.get('valor_passe_atual_eur', 0)
            valor_passe_brl = row.get('valor_passe_atual_brl', 0)
            linhas.append(f"    - {apelido}: compra em {data_compra} (€ {valor_compra_eur:,.2f} / R$ {valor_compra_brl:,.2f}), salário R$ {salario:,.2f}, passe € {valor_passe_eur:,.2f} (R$ {valor_passe_brl:,.2f})")
        linhas.append("")
    else:
        linhas.append("6. DADOS FINANCEIROS")
        linhas.append("-"*40)
        linhas.append("  ⚠️ Arquivo de dados financeiros não encontrado (dados_financeiros.csv).")
        linhas.append("")
    
    # 7. Recomendações
    linhas.append("7. RECOMENDAÇÕES E OBSERVAÇÕES")
    linhas.append("-"*40)
    if 'Posicao_Principal' in df_elenco.columns:
        cont_pos = df_elenco['Posicao_Principal'].value_counts()
        carencias = cont_pos[cont_pos < 3]
        if not carencias.empty:
            linhas.append("  ⚠️ Posições carentes (menos de 3 jogadores):")
            for pos, qtd in carencias.items():
                linhas.append(f"    - {pos}: {qtd}")
        else:
            linhas.append("  ✅ Todas as posições têm pelo menos 3 jogadores.")
    if 'Idade' in df_elenco.columns and 'Rating_Geral_FM26' in df_elenco.columns:
        jovens = df_elenco[(df_elenco['Idade'] < 20) & (df_elenco['Rating_Geral_FM26'] >= 70)]
        if not jovens.empty:
            linhas.append("  🌟 Jovens promessas (idade < 20 e rating >= 70):")
            for _, row in jovens.iterrows():
                linhas.append(f"    - {row.get('nome_completo', 'N/I')} ({row['Idade']} anos, rating {row['Rating_Geral_FM26']:.1f})")
    if df_financeiro is not None and not df_financeiro.empty:
        jogadores_com_passe = df_financeiro[df_financeiro['valor_passe_atual_eur'] > 0]
        if not jogadores_com_passe.empty:
            linhas.append("  💰 Jogadores com valor de passe positivo (ativos comercializáveis):")
            for _, row in jogadores_com_passe.iterrows():
                linhas.append(f"    - {row['apelido']}: € {row['valor_passe_atual_eur']:,.2f} (R$ {row['valor_passe_atual_brl']:,.2f})")
    linhas.append("")
    linhas.append("="*70)
    linhas.append("Fim do relatório")
    return "\n".join(linhas)

def gerar_relatorio_para_comissao(df_comissao, cat_comissao):
    """Gera um relatório focado na comissão técnica."""
    if df_comissao is None or df_comissao.empty:
        return "Dados da comissão não disponíveis."
    
    linhas = []
    linhas.append("="*70)
    linhas.append(f"RELATÓRIO PARA COMISSÃO TÉCNICA – {NOME_TIME} – Temporada {TEMPORADA}")
    linhas.append("="*70)
    linhas.append(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    linhas.append("")
    
    linhas.append("1. COMPOSIÇÃO DA COMISSÃO")
    linhas.append("-"*40)
    linhas.append(f"Categoria: {cat_comissao}")
    linhas.append(f"Total de membros: {len(df_comissao)}")
    if 'cargo' in df_comissao.columns:
        linhas.append("Distribuição por cargo:")
        for cargo, qtd in df_comissao['cargo'].value_counts().items():
            linhas.append(f"  - {cargo}: {qtd}")
    linhas.append("")
    
    linhas.append("2. PERFIL DOS MEMBROS")
    linhas.append("-"*40)
    for _, row in df_comissao.iterrows():
        nome = row.get('nome', 'N/I')
        cargo = row.get('cargo', 'N/I')
        idade = row.get('idade', 'N/I')
        linhas.append(f"  - {nome} – {cargo} (idade: {idade} anos)")
        if 'historico_profissional' in row and row.get('historico_profissional'):
            linhas.append(f"    Histórico: {row['historico_profissional']}")
    linhas.append("")
    
    atributos_staff = [col for col in df_comissao.columns if col.startswith('staff_')]
    if atributos_staff:
        linhas.append("3. ATRIBUTOS DE STAFF (média por cargo)")
        linhas.append("-"*40)
        for cargo in df_comissao['cargo'].unique():
            df_cargo = df_comissao[df_comissao['cargo'] == cargo]
            linhas.append(f"Cargo: {cargo}")
            for attr in atributos_staff:
                media = df_cargo[attr].mean()
                if pd.notna(media):
                    nome_attr = attr.replace('staff_', '').replace('_', ' ').title()
                    linhas.append(f"  - {nome_attr}: {media:.1f}")
            linhas.append("")
    
    linhas.append("="*70)
    linhas.append("Fim do relatório")
    return "\n".join(linhas)

def gerar_relatorio_para_jogadores(df_elenco, cat_elenco):
    """Gera um relatório focado nos jogadores."""
    if df_elenco is None or df_elenco.empty:
        return "Elenco não disponível."
    
    linhas = []
    linhas.append("="*70)
    linhas.append(f"RELATÓRIO PARA JOGADORES – {NOME_TIME} – Temporada {TEMPORADA}")
    linhas.append("="*70)
    linhas.append(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    linhas.append("")
    
    linhas.append("1. VISÃO GERAL DO ELENCO")
    linhas.append("-"*40)
    linhas.append(f"Categoria: {cat_elenco}")
    linhas.append(f"Total de jogadores: {len(df_elenco)}")
    if 'Idade' in df_elenco.columns:
        linhas.append(f"Idade média: {df_elenco['Idade'].mean():.1f} anos")
    if 'Rating_Geral_FM26' in df_elenco.columns:
        linhas.append(f"Rating FM26 médio: {df_elenco['Rating_Geral_FM26'].mean():.1f}")
    linhas.append("")
    
    linhas.append("2. LISTA COMPLETA DE JOGADORES")
    linhas.append("-"*40)
    cols = ['nome_completo', 'apelido', 'Posicao_Principal', 'Idade', 'Rating_Geral_FM26', 'Estado_Fisico']
    cols_existentes = [c for c in cols if c in df_elenco.columns]
    df_exib = df_elenco[cols_existentes].copy()
    for _, row in df_exib.iterrows():
        nome = row.get('nome_completo', 'N/I')
        apelido = row.get('apelido', '')
        pos = row.get('Posicao_Principal', '')
        idade = row.get('Idade', '')
        rating = row.get('Rating_Geral_FM26', '')
        estado = row.get('Estado_Fisico', '')
        linha = f"  - {nome}"
        if apelido:
            linha += f" ({apelido})"
        if pos:
            linha += f" – {pos}"
        if idade:
            linha += f", {idade} anos"
        if rating:
            linha += f", rating {rating:.1f}"
        if estado:
            linha += f", estado: {estado}"
        linhas.append(linha)
    linhas.append("")
    
    if 'starts' in df_elenco.columns or 'minutos_totais_partidas' in df_elenco.columns:
        linhas.append("3. ESTATÍSTICAS DE MINUTAGEM")
        linhas.append("-"*40)
        if 'starts' in df_elenco.columns:
            total_starts = df_elenco['starts'].sum()
            linhas.append(f"  Total de titularidades: {total_starts}")
        if 'minutos_totais_partidas' in df_elenco.columns:
            total_min = df_elenco['minutos_totais_partidas'].sum()
            linhas.append(f"  Total de minutos jogados: {total_min}")
        if 'minutos_totais_partidas' in df_elenco.columns and 'nome_completo' in df_elenco.columns:
            top5 = df_elenco.nlargest(5, 'minutos_totais_partidas')[['nome_completo', 'minutos_totais_partidas']]
            linhas.append("  Top 5 em minutos:")
            for _, row in top5.iterrows():
                linhas.append(f"    - {row['nome_completo']}: {row['minutos_totais_partidas']} min")
    linhas.append("")
    
    if 'Estado_Fisico' in df_elenco.columns:
        linhas.append("4. CONDIÇÃO FÍSICA")
        linhas.append("-"*40)
        cont_estado = df_elenco['Estado_Fisico'].value_counts()
        for estado, qtd in cont_estado.items():
            linhas.append(f"  - {estado}: {qtd}")
        criticos = df_elenco[df_elenco['Estado_Fisico'] == 'Crítico']
        if not criticos.empty:
            linhas.append("  Jogadores em estado crítico:")
            for _, row in criticos.iterrows():
                linhas.append(f"    - {row.get('nome_completo', 'N/I')}")
    linhas.append("")
    
    if 'lesionado' in df_elenco.columns:
        lesionados = df_elenco[df_elenco['lesionado'] == True]
        if not lesionados.empty:
            linhas.append("5. LESIONADOS")
            linhas.append("-"*40)
            for _, row in lesionados.iterrows():
                linhas.append(f"  - {row.get('nome_completo', 'N/I')}")
            linhas.append("")
    
    linhas.append("="*70)
    linhas.append("Fim do relatório")
    return "\n".join(linhas)

# ============================================================
# PÁGINA PRINCIPAL
# ============================================================
def show():
    st.title("📄 Relatórios")
    st.markdown("---")

    cat_elenco = st.selectbox("Categoria (Elenco)", get_categorias_elenco(), key="rel_elenco_categoria")
    cat_comissao = st.selectbox("Categoria (Comissão)", get_categorias_comissao(), key="rel_comissao_categoria")

    df_elenco = get_elenco(cat_elenco)
    df_comissao = get_comissao(cat_comissao)

    # ============================================================
    # RELATÓRIO PARA DIRETORIA
    # ============================================================
    with st.expander("📈 Relatório para Diretoria", expanded=False):
        if df_elenco is not None and not df_elenco.empty:
            st.info("Este relatório contém resumo executivo, dados financeiros (EUR/BRL), destaques e recomendações.")
            texto = gerar_relatorio_para_diretoria(df_elenco, df_comissao, cat_elenco, cat_comissao)
            st.text_area("Conteúdo do relatório", texto, height=400)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Baixar TXT (Diretoria)", key="btn_dir_txt"):
                    st.download_button(
                        label="Clique para baixar",
                        data=texto,
                        file_name=f"relatorio_diretoria_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain",
                        key="download_dir_txt"
                    )
            with col2:
                if st.button("📊 Baixar Excel (Diretoria)", key="btn_dir_excel"):
                    # Carrega dados financeiros com conversão
                    df_financeiro, taxa = carregar_dados_financeiros()
                    
                    # Cria um DataFrame com as informações principais
                    dados = []
                    if df_elenco is not None:
                        dados.append(("Categoria", cat_elenco))
                        dados.append(("Total de jogadores", len(df_elenco)))
                        if 'Idade' in df_elenco.columns:
                            dados.append(("Idade média", f"{df_elenco['Idade'].mean():.1f}"))
                        if 'Rating_Geral_FM26' in df_elenco.columns:
                            dados.append(("Rating médio", f"{df_elenco['Rating_Geral_FM26'].mean():.1f}"))
                        if 'Estado_Fisico' in df_elenco.columns:
                            for estado, qtd in df_elenco['Estado_Fisico'].value_counts().items():
                                dados.append((f"Estado Físico - {estado}", qtd))
                    if df_comissao is not None:
                        dados.append(("Membros comissão", len(df_comissao)))
                    # Dados financeiros resumidos
                    if df_financeiro is not None and not df_financeiro.empty:
                        dados.append(("Total compras (€)", df_financeiro['valor_compra_eur'].sum()))
                        dados.append(("Total compras (R$)", df_financeiro['valor_compra_brl'].sum()))
                        dados.append(("Total salários mensais (R$)", df_financeiro['salario_mensal_brl'].sum()))
                        dados.append(("Total valor de passe (€)", df_financeiro['valor_passe_atual_eur'].sum()))
                        dados.append(("Total valor de passe (R$)", df_financeiro['valor_passe_atual_brl'].sum()))
                    
                    df_excel = pd.DataFrame(dados, columns=["Item", "Valor"])
                    # Lista de jogadores
                    if df_elenco is not None:
                        cols = ['nome_completo', 'apelido', 'Posicao_Principal', 'Idade', 'Rating_Geral_FM26', 'Estado_Fisico']
                        cols_exist = [c for c in cols if c in df_elenco.columns]
                        df_jogadores = df_elenco[cols_exist].copy()
                        df_excel = pd.concat([df_excel, pd.DataFrame([["", ""]]), pd.DataFrame([["LISTA DE JOGADORES", ""]])], ignore_index=True)
                        df_excel = pd.concat([df_excel, df_jogadores], ignore_index=True)
                    
                    # Cria um escritor Excel com múltiplas abas
                    caminho_excel = f"relatorio_diretoria_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                    with pd.ExcelWriter(caminho_excel, engine='openpyxl') as writer:
                        df_excel.to_excel(writer, sheet_name='Resumo', index=False)
                        if df_financeiro is not None and not df_financeiro.empty:
                            # Adiciona colunas com os valores convertidos (já estão no df)
                            df_financeiro.to_excel(writer, sheet_name='Financeiro', index=False)
                    
                    # Download do Excel
                    with open(caminho_excel, "rb") as f:
                        st.download_button("Baixar Excel", data=f, file_name=caminho_excel, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    try:
                        os.remove(caminho_excel)
                    except:
                        pass
        else:
            st.warning(f"Elenco não disponível para {cat_elenco}. Carregue os dados primeiro.")

    # ============================================================
    # RELATÓRIO PARA COMISSÃO TÉCNICA
    # ============================================================
    with st.expander("👥 Relatório para Comissão Técnica", expanded=False):
        if df_comissao is not None and not df_comissao.empty:
            st.info("Composição da comissão, perfil dos membros e atributos de staff.")
            texto = gerar_relatorio_para_comissao(df_comissao, cat_comissao)
            st.text_area("Conteúdo do relatório", texto, height=300)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Baixar TXT (Comissão)", key="btn_com_txt"):
                    st.download_button(
                        label="Clique para baixar",
                        data=texto,
                        file_name=f"relatorio_comissao_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain",
                        key="download_com_txt"
                    )
            with col2:
                if st.button("📊 Baixar Excel (Comissão)", key="btn_com_excel"):
                    df_excel = df_comissao.copy()
                    caminho = f"relatorio_comissao_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                    if exportar_para_excel(df_excel, "Comissão Técnica", caminho):
                        with open(caminho, "rb") as f:
                            st.download_button("Baixar Excel", data=f, file_name=caminho, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                        try:
                            os.remove(caminho)
                        except:
                            pass
                    else:
                        st.error("Erro ao exportar Excel")
        else:
            st.warning(f"Dados da comissão não disponíveis para {cat_comissao}.")

    # ============================================================
    # RELATÓRIO PARA JOGADORES
    # ============================================================
    with st.expander("⚽ Relatório para Jogadores", expanded=False):
        if df_elenco is not None and not df_elenco.empty:
            st.info("Lista completa de jogadores, estatísticas de minutagem e condição física.")
            texto = gerar_relatorio_para_jogadores(df_elenco, cat_elenco)
            st.text_area("Conteúdo do relatório", texto, height=300)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Baixar TXT (Jogadores)", key="btn_jog_txt"):
                    st.download_button(
                        label="Clique para baixar",
                        data=texto,
                        file_name=f"relatorio_jogadores_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain",
                        key="download_jog_txt"
                    )
            with col2:
                if st.button("📊 Baixar Excel (Jogadores)", key="btn_jog_excel"):
                    cols = ['nome_completo', 'apelido', 'Posicao_Principal', 'Idade', 'Rating_Geral_FM26', 'Estado_Fisico', 'lesionado']
                    cols_exist = [c for c in cols if c in df_elenco.columns]
                    df_excel = df_elenco[cols_exist].copy()
                    caminho = f"relatorio_jogadores_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                    if exportar_para_excel(df_excel, "Jogadores", caminho):
                        with open(caminho, "rb") as f:
                            st.download_button("Baixar Excel", data=f, file_name=caminho, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                        try:
                            os.remove(caminho)
                        except:
                            pass
                    else:
                        st.error("Erro ao exportar Excel")
        else:
            st.warning(f"Elenco não disponível para {cat_elenco}.")

    st.markdown("---")
    st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")