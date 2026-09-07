# pages/tatica_page.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
import difflib
from utils import (
    interpretar_formacao,
    obter_jogadores_para_posicao,
    jogador_suspenso,
    mapear_nome_para_canonico,
    sanitizar_dataframe,
    carregar_elenco_profissional,
    carregar_elenco_sub15,
    carregar_elenco_sub17,
    carregar_cartoes_json,
    adicionar_coluna_lesionado,
    carregar_dados_bioimpedancia,
    aplicar_dados_bioimpedancia,
    carregar_estatisticas_partidas,
    precomputar_scores_posicionais,
    ATRIBUTOS_FM26,
)
from roles_fm26 import (
    get_roles_by_posicao,
    get_role_traduzida,
    get_role_attributes,
    CATEGORIA_ROLE,
    TRADUCAO_ROLES_PT,
    COMPATIBILIDADE_POSICAO,
    ROLES_FM26_PT,
)

# ============================================================
# PESOS DA SUGESTÃO
# ============================================================
PESO_POSICAO = 0.70
PESO_ATRIBUTOS = 0.15
PESO_ROLES = 0.15

# ============================================================
# DICIONÁRIO DE PRIORIDADES (NOME COMPLETO/APELIDO -> POSIÇÃO)
# ============================================================
PRIORIDADES = {
    'Ruan Amaral Rios': 'Goleiro',
    'Genilson dos Santos Júnior': 'Lateral Esquerdo',   # Júnior Espeto
    'Karlos Henrique dos Reis Calavort': 'Zagueiro',    # Kaká
    'Gabriel Amorim de Aguiar': 'Meia Direita',
    'Francisco Wesley da Silva Sousa': 'Meia Esquerda',
    'Lucas Titol Lopes': 'Meia Central',
    'Wenderson Silva Neves': 'Centroavante',            # Wendy
}

# ============================================================
# MAPEAMENTO DE GRUPOS DE POSIÇÃO PARA ROLES FM26
# ============================================================
GRUPO_POSICAO = {
    'Goleiro': ['Goleiro'],
    'Defensor': ['Zagueiro', 'Lateral Direito', 'Lateral Esquerdo', 'Lateral'],
    'Meio-Campo': ['Volante', 'Meia-Central', 'Meia-Atacante', 'Meio-Campo'],
    'Atacante': ['Ponta Direita', 'Ponta Esquerda', 'Ponta', 'Centroavante', 'Segundo Atacante', 'Atacante']
}

def get_roles_by_grupo(grupo):
    """
    Retorna todas as roles FM26 compatíveis com um grupo de posição
    (Goleiro, Defensor, Meio-Campo, Atacante) baseado no COMPATIBILIDADE_POSICAO.
    """
    posicoes_do_grupo = GRUPO_POSICAO.get(grupo, [])
    roles = set()
    for pos in posicoes_do_grupo:
        # Busca roles compatíveis com essa posição específica
        roles.update(COMPATIBILIDADE_POSICAO.get(pos, []))
    # Também inclui roles que têm essa posição como esperada (via role_to_pos)
    # Mas como role_to_pos não está disponível, vamos fazer um mapeamento inverso:
    # Para cada role, verificar se sua posição esperada está no grupo.
    # role_to_pos está definido no roles_fm26, mas não importamos. Vamos reconstruir localmente.
    # Para evitar erros, vamos usar COMPATIBILIDADE_POSICAO que já mapeia posição -> roles.
    # O mapeamento inverso pode ser feito: para cada role, vemos se ela aparece em alguma posição do grupo.
    # Como COMPATIBILIDADE_POSICAO tem mapeamento posição -> roles, podemos inverter.
    # Mas para simplificar, vamos apenas retornar as roles das posições do grupo.
    # Se ainda estiver vazio, adicionamos roles de posições relacionadas.
    if not roles:
        # Fallback: adicionar roles de posições semelhantes
        all_roles = set(ROLES_FM26_PT.keys())
        # Filtra roles pela categoria se disponível
        # Mas como não temos role_to_pos, vamos apenas retornar todas as roles se estiver vazio
        roles = all_roles
    return list(roles)

# ============================================================
# FUNÇÃO PARA CARREGAR ELENCO
# ============================================================
@st.cache_data
def carregar_elenco_com_lesoes(categoria):
    if categoria == "Profissional":
        df = carregar_elenco_profissional()
        if df is not None and not df.empty:
            df = adicionar_coluna_lesionado(df, 'profissional')
            bio = carregar_dados_bioimpedancia('profissional')
            df = aplicar_dados_bioimpedancia(df, bio)
            stats = carregar_estatisticas_partidas("Profissional")
            if not stats.empty:
                df = precomputar_scores_posicionais(df, stats)
    elif categoria == "Sub-15":
        df = carregar_elenco_sub15()
        if df is not None and not df.empty:
            df = adicionar_coluna_lesionado(df, 'sub15')
            bio = carregar_dados_bioimpedancia('sub15')
            df = aplicar_dados_bioimpedancia(df, bio)
            stats = carregar_estatisticas_partidas("Sub-15")
            if not stats.empty:
                df = precomputar_scores_posicionais(df, stats)
    elif categoria == "Sub-17":
        df = carregar_elenco_sub17()
        if df is not None and not df.empty:
            df = adicionar_coluna_lesionado(df, 'sub17')
            bio = carregar_dados_bioimpedancia('sub17')
            df = aplicar_dados_bioimpedancia(df, bio)
            stats = carregar_estatisticas_partidas("Sub-17")
            if not stats.empty:
                df = precomputar_scores_posicionais(df, stats)
    else:
        df = None
    return df

# ============================================================
# FUNÇÃO PARA DESENHAR CAMPO
# ============================================================
def desenhar_campo(titulares, titulo, formacao, posicoes_esperadas):
    if not titulares or not posicoes_esperadas:
        return None
    
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 70)
    ax.set_facecolor('#2e7d32')
    ax.set_title(titulo, fontsize=14, fontweight='bold', color='white')
    
    ax.plot([0, 100], [0, 0], 'w', linewidth=2)
    ax.plot([0, 100], [70, 70], 'w', linewidth=2)
    ax.plot([0, 0], [0, 70], 'w', linewidth=2)
    ax.plot([100, 100], [0, 70], 'w', linewidth=2)
    ax.plot([50, 50], [0, 70], 'w', linestyle='--', linewidth=1)
    ax.add_patch(Circle((50, 35), 7, edgecolor='w', facecolor='none', linewidth=2))
    ax.add_patch(Circle((50, 35), 1, edgecolor='w', facecolor='w', linewidth=1))
    ax.add_patch(Rectangle((40, 18), 20, 34, edgecolor='w', facecolor='none', linewidth=2))
    
    n = len(titulares)
    posicoes = []
    if n >= 1:
        posicoes.append((50, 8))
    if n >= 5:
        posicoes.extend([(15, 18), (35, 18), (65, 18), (85, 18)])
    elif n >= 4:
        posicoes.extend([(20, 18), (40, 18), (60, 18), (80, 18)])
    elif n >= 3:
        posicoes.extend([(25, 18), (50, 18), (75, 18)])
    elif n >= 2:
        posicoes.extend([(30, 18), (70, 18)])
    if n >= 9:
        posicoes.extend([(15, 35), (35, 35), (65, 35), (85, 35)])
    elif n >= 8:
        posicoes.extend([(20, 35), (40, 35), (60, 35), (80, 35)])
    elif n >= 7:
        posicoes.extend([(25, 35), (50, 35), (75, 35)])
    elif n >= 6:
        posicoes.extend([(30, 35), (70, 35)])
    if n >= 11:
        posicoes.extend([(30, 52), (70, 52)])
    elif n >= 10:
        posicoes.extend([(35, 52), (65, 52)])
    elif n >= 9:
        posicoes.extend([(50, 52)])
    while len(posicoes) < n:
        x = 10 + (len(posicoes) / n) * 80
        y = 10 + ((len(posicoes) % 3) / 2) * 50
        posicoes.append((x, y))
    
    for i, (x, y) in enumerate(posicoes[:n]):
        if i < len(titulares):
            jog = titulares[i]
            nome = jog.get('apelido', jog.get('nome', 'N/D'))
            funcao = jog.get('funcao', '')
            cor = '#ff7f0e' if i == 0 else '#1f77b4'
            ax.add_patch(Circle((x, y), 3.5, edgecolor='white', facecolor=cor, linewidth=2))
            ax.text(x, y-5, nome[:15], ha='center', va='center', fontsize=7, color='white', weight='bold')
            if funcao:
                ax.text(x, y-8, funcao[:15], ha='center', va='center', fontsize=5, color='yellow', style='italic')
    
    ax.axis('off')
    plt.tight_layout()
    return fig

# ============================================================
# FUNÇÃO PARA CALCULAR SCORE
# ============================================================
def calcular_score_jogador(row, pos_tipo, posicao_exibida):
    pos_principal = row.get('Posicao_Principal', 'Outros')
    pos_secundarias = row.get('Posicoes_Secundarias', [])
    if isinstance(pos_secundarias, str):
        pos_secundarias = [p.strip() for p in pos_secundarias.split(',')] if pos_secundarias else []
    elif not isinstance(pos_secundarias, list):
        pos_secundarias = []
    
    grupo_esperado = GRUPO_POSICAO.get(pos_tipo, [])
    
    if pos_principal in grupo_esperado:
        score_posicao = 1.0
    elif pos_principal in GRUPO_POSICAO.get(pos_tipo, []):
        score_posicao = 0.8
    else:
        if any(p in grupo_esperado for p in pos_secundarias):
            score_posicao = 0.7
        else:
            score_posicao = 0.3
    
    roles = get_roles_by_posicao(pos_principal)
    if not roles:
        roles = get_roles_by_grupo(pos_tipo)
    if not roles:
        roles = ['Versátil']
    
    role_data = get_role_attributes(roles[0])
    key_attrs = role_data.get('key', [])
    if not key_attrs:
        key_attrs = ATRIBUTOS_FM26
    
    valores = []
    for attr in key_attrs:
        if attr in row and pd.notna(row[attr]):
            valores.append(float(row[attr]))
    if valores:
        media_atributos = np.mean(valores)
        media_atributos = min(100, max(0, media_atributos))
    else:
        media_atributos = 50
    score_atributos = media_atributos / 100.0
    
    if pos_principal in grupo_esperado:
        score_roles = 1.0
    elif any(p in grupo_esperado for p in pos_secundarias):
        score_roles = 0.7
    else:
        score_roles = 0.3
    
    score_final = (PESO_POSICAO * score_posicao) + (PESO_ATRIBUTOS * score_atributos) + (PESO_ROLES * score_roles)
    
    return {
        'score': score_final,
        'score_posicao': score_posicao,
        'score_atributos': score_atributos,
        'score_roles': score_roles,
        'media_atributos': media_atributos,
        'roles': roles
    }

# ============================================================
# FUNÇÃO PARA OBTER ROLES COMPATÍVEIS (COM BASE NA POSIÇÃO TÁTICA)
# ============================================================
def get_roles_compativel(jogador_row, pos_tipo):
    """
    Retorna uma lista de roles FM26 compatíveis com a posição tática (pos_tipo)
    e também inclui roles da posição principal do jogador.
    """
    pos_principal = jogador_row.get('Posicao_Principal', 'Outros')
    
    # Roles baseadas na posição tática (grupo)
    roles_tatica = get_roles_by_grupo(pos_tipo)
    
    # Roles baseadas na posição principal do jogador
    roles_principal = get_roles_by_posicao(pos_principal)
    
    # Combinar: manter a ordem, priorizar roles_tatica, mas incluir roles_principal que não estão na lista
    roles_combinadas = roles_tatica.copy()
    for role in roles_principal:
        if role not in roles_combinadas:
            roles_combinadas.append(role)
    
    # Se ainda estiver vazio, usar todas as roles (fallback)
    if not roles_combinadas:
        roles_combinadas = list(ROLES_FM26_PT.keys())
    
    return roles_combinadas

# ============================================================
# FUNÇÃO PARA ENCONTRAR JOGADOR POR NOME (FUZZY)
# ============================================================
def encontrar_jogador(nome_digitado, df_elenco, cutoff=0.6):
    if not nome_digitado or pd.isna(nome_digitado):
        return None
    nome_digitado = nome_digitado.strip().lower()
    nomes_disponiveis = []
    for _, row in df_elenco.iterrows():
        nome_completo = row.get('nome_completo', '')
        apelido = row.get('apelido', '')
        if nome_completo:
            nomes_disponiveis.append((nome_completo, row))
        if apelido and apelido != nome_completo:
            nomes_disponiveis.append((apelido, row))
    for nome, row in nomes_disponiveis:
        if nome.lower() == nome_digitado:
            return row
    nomes_unicos = list(set([nome for nome, _ in nomes_disponiveis]))
    matches = difflib.get_close_matches(nome_digitado, [n.lower() for n in nomes_unicos], n=1, cutoff=cutoff)
    if matches:
        nome_encontrado = next((n for n in nomes_unicos if n.lower() == matches[0]), None)
        if nome_encontrado:
            for nome, row in nomes_disponiveis:
                if nome == nome_encontrado:
                    return row
    return None

# ============================================================
# FUNÇÃO PARA PROCESSAR TEXTO DA ESCALAÇÃO DIGITADA
# ============================================================
def processar_escalacao_digitada(texto, df_elenco, posicoes_esperadas):
    linhas = [linha.strip() for linha in texto.strip().split('\n') if linha.strip()]
    if not linhas:
        return None, "Nenhum jogador informado."
    
    resultados = []
    erros = []
    tem_posicao = any(':' in linha for linha in linhas)
    pos_to_tipo = {pos: tipo for pos, tipo in posicoes_esperadas}
    posicoes_disponiveis = list(pos_to_tipo.keys())
    
    if tem_posicao:
        for linha in linhas:
            if ':' in linha:
                posicao, resto = linha.split(':', 1)
                posicao = posicao.strip()
                resto = resto.strip()
                if not resto:
                    continue
                funcao = ''
                if '(' in resto and ')' in resto:
                    nome, funcao = resto.split('(', 1)
                    nome = nome.strip()
                    funcao = funcao.replace(')', '').strip()
                else:
                    nome = resto
                if not nome:
                    continue
                row = encontrar_jogador(nome, df_elenco)
                if row is not None:
                    if funcao:
                        all_roles = list(TRADUCAO_ROLES_PT.keys())
                        if funcao not in all_roles:
                            for role, trad in TRADUCAO_ROLES_PT.items():
                                if trad.lower() == funcao.lower():
                                    funcao = role
                                    break
                    resultados.append({
                        'posicao': posicao,
                        'row': row,
                        'nome': row.get('nome_completo', ''),
                        'funcao': funcao
                    })
                else:
                    erros.append(f"Não encontrado: '{nome}' para posição '{posicao}'")
            else:
                erros.append(f"Linha sem ':' ignorada: '{linha}'")
    else:
        if len(linhas) > len(posicoes_disponiveis):
            erros.append(f"Mais nomes ({len(linhas)}) do que posições ({len(posicoes_disponiveis)}). Os excedentes serão ignorados.")
        for i, linha in enumerate(linhas[:len(posicoes_disponiveis)]):
            funcao = ''
            if '(' in linha and ')' in linha:
                nome, funcao = linha.split('(', 1)
                nome = nome.strip()
                funcao = funcao.replace(')', '').strip()
            else:
                nome = linha.strip()
            if not nome:
                continue
            row = encontrar_jogador(nome, df_elenco)
            if row is not None:
                pos_exibida = posicoes_disponiveis[i] if i < len(posicoes_disponiveis) else f"Posição {i+1}"
                if funcao:
                    all_roles = list(TRADUCAO_ROLES_PT.keys())
                    if funcao not in all_roles:
                        for role, trad in TRADUCAO_ROLES_PT.items():
                            if trad.lower() == funcao.lower():
                                funcao = role
                                break
                resultados.append({
                    'posicao': pos_exibida,
                    'row': row,
                    'nome': row.get('nome_completo', ''),
                    'funcao': funcao
                })
            else:
                erros.append(f"Não encontrado: '{nome}'")
    
    return resultados, "\n".join(erros) if erros else ""

# ============================================================
# FUNÇÃO PARA SUGERIR ESCALAÇÃO (COM PRIORIDADES)
# ============================================================
def sugerir_escalacao(df_elenco, posicoes, cartoes, titulares_atuais):
    jogadores_disponiveis = df_elenco.copy()
    if 'lesionado' in jogadores_disponiveis.columns:
        jogadores_disponiveis = jogadores_disponiveis[~jogadores_disponiveis['lesionado']]
    jogadores_disponiveis = jogadores_disponiveis[
        ~jogadores_disponiveis['nome_completo'].apply(
            lambda x: jogador_suspenso(mapear_nome_para_canonico(x), cartoes)
        )
    ]
    if jogadores_disponiveis.empty:
        return titulares_atuais
    
    titulares_existentes = {item['posicao']: item for item in titulares_atuais if item.get('nome')}
    jogadores_usados = [item['nome'] for item in titulares_existentes.values() if item.get('nome')]
    
    sugestoes = {}
    
    # PASSO 1: Aplicar prioridades
    for nome_prioritario, posicao_esperada in PRIORIDADES.items():
        if nome_prioritario in jogadores_usados:
            continue
        jogador_row = jogadores_disponiveis[jogadores_disponiveis['nome_completo'] == nome_prioritario]
        if jogador_row.empty:
            continue
        if posicao_esperada in titulares_existentes:
            continue
        if posicao_esperada in sugestoes:
            continue
        row = jogador_row.iloc[0]
        # Atribui função compatível com a posição tática (usa a posição esperada)
        # Mas para prioridades, a posição esperada é uma string, precisamos mapear para pos_tipo
        # Para simplificar, vamos usar a posição principal do jogador para a função
        pos_principal = row.get('Posicao_Principal', 'Outros')
        roles = get_roles_by_posicao(pos_principal)
        funcao = roles[0] if roles else ''
        sugestoes[posicao_esperada] = {
            'posicao': posicao_esperada,
            'nome': nome_prioritario,
            'apelido': row['apelido'],
            'row': row,
            'funcao': funcao
        }
        jogadores_usados.append(nome_prioritario)
    
    # PASSO 2: Preencher posições vazias
    novos_titulares = []
    for pos_exibida, pos_tipo in posicoes:
        if pos_exibida in sugestoes:
            novos_titulares.append(sugestoes[pos_exibida])
            continue
        if pos_exibida in titulares_existentes:
            novos_titulares.append(titulares_existentes[pos_exibida])
            continue
        candidatos = obter_jogadores_para_posicao(jogadores_disponiveis, pos_tipo, jogadores_usados, cartoes, incluir_lesionados=False)
        if candidatos.empty:
            novos_titulares.append({
                'posicao': pos_exibida,
                'nome': '',
                'apelido': '',
                'row': None,
                'funcao': ''
            })
            continue
        scores = []
        for idx, row in candidatos.iterrows():
            score_info = calcular_score_jogador(row, pos_tipo, pos_exibida)
            scores.append({
                'row': row,
                'score': score_info['score'],
            })
        scores.sort(key=lambda x: x['score'], reverse=True)
        melhor = scores[0]
        # Atribui função compatível com a posição tática
        roles = get_roles_compativel(melhor['row'], pos_tipo)
        funcao = roles[0] if roles else ''
        novos_titulares.append({
            'posicao': pos_exibida,
            'nome': melhor['row']['nome_completo'],
            'apelido': melhor['row']['apelido'],
            'row': melhor['row'],
            'funcao': funcao
        })
        jogadores_usados.append(melhor['row']['nome_completo'])
    
    return novos_titulares

# ============================================================
# FUNÇÃO PARA COPIAR ESCALAÇÃO PARA TODAS AS FORMAÇÕES
# ============================================================
def copiar_para_todas_formacoes(titulares, reservas, tipos_formacao, formacao_atual, funcoes_atuais=None):
    for tipo in tipos_formacao:
        dados = st.session_state.escalacoes_tatica.get(tipo, {})
        funcoes_existentes = dados.get('funcoes', {})
        novos_titulares = []
        for jog in titulares:
            if jog['nome']:
                nome = jog['nome']
                funcao = funcoes_existentes.get(nome, '')
                if not funcao and jog.get('row') is not None:
                    # Se não tem função, tenta atribuir compatível com a posição tática
                    # Para isso, precisamos saber qual a posição tática (usamos a posição do jog)
                    pos_tipo = GRUPO_POSICAO.get(jog.get('posicao', 'Outros'), [])
                    # fallback: usa posição principal
                    pos_principal = jog['row'].get('Posicao_Principal', 'Outros')
                    roles = get_roles_by_posicao(pos_principal)
                    funcao = roles[0] if roles else ''
                novos_titulares.append({
                    'posicao': jog['posicao'],
                    'nome': nome,
                    'apelido': jog['apelido'],
                    'row': jog.get('row'),
                    'funcao': funcao
                })
            else:
                novos_titulares.append({
                    'posicao': jog['posicao'],
                    'nome': '',
                    'apelido': '',
                    'row': None,
                    'funcao': ''
                })
        novas_reservas = []
        for res in reservas:
            novas_reservas.append({
                'nome': res['nome'],
                'apelido': res['apelido'],
                'row': res['row']
            })
        st.session_state.escalacoes_tatica[tipo] = {
            'formacao': dados.get('formacao', '4-4-2'),
            'titulares': novos_titulares,
            'reservas': novas_reservas,
            'funcoes': funcoes_existentes
        }

# ============================================================
# FUNÇÃO PARA APLICAR SUGESTÃO A TODAS AS FORMAÇÕES
# ============================================================
def aplicar_sugestao_todas_formacoes(tipos_formacao, df_elenco, cartoes):
    for tipo in tipos_formacao:
        dados = st.session_state.escalacoes_tatica.get(tipo, {})
        formacao = dados.get('formacao', '4-4-2')
        posicoes_atual = dados.get('titulares', [])
        _, _, _, posicoes = interpretar_formacao(formacao)
        if not posicoes:
            continue
        novos_titulares = sugerir_escalacao(df_elenco, posicoes, cartoes, posicoes_atual)
        st.session_state.escalacoes_tatica[tipo]['titulares'] = novos_titulares

# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================
def show():
    st.header("📐 Escalação Tática")
    st.markdown("Defina as **4 formações** e escolha as **funções do FM26** para cada jogador.")
    
    categoria = st.session_state.get("categoria_tatica", "Profissional")
    df_elenco = carregar_elenco_com_lesoes(categoria)
    if df_elenco is None or df_elenco.empty:
        st.warning(f"Elenco não disponível para {categoria}. Verifique os arquivos CSV.")
        return
    
    cartoes_key = {"Profissional": "profissional", "Sub-15": "sub15", "Sub-17": "sub17"}.get(categoria, "profissional")
    cartoes, _ = carregar_cartoes_json(cartoes_key)
    
    tipos_formacao = ['inicial', 'ofensiva_sem_bola', 'defensiva', 'ofensiva_com_bola']
    nomes_tipos = {
        'inicial': '📋 Formação Inicial',
        'ofensiva_sem_bola': '⬆️ Ofensiva sem Bola',
        'defensiva': '⬇️ Defensiva',
        'ofensiva_com_bola': '⚡ Ofensiva com Bola'
    }
    
    if 'escalacoes_tatica' not in st.session_state:
        st.session_state.escalacoes_tatica = {}
        for tipo in tipos_formacao:
            st.session_state.escalacoes_tatica[tipo] = {
                'formacao': '4-4-2',
                'titulares': [],
                'reservas': [],
                'funcoes': {}
            }
    
    tipo_selecionado = st.radio(
        "Selecione a formação para configurar",
        options=tipos_formacao,
        format_func=lambda x: nomes_tipos[x],
        horizontal=True
    )
    st.divider()
    
    dados_formacao = st.session_state.escalacoes_tatica[tipo_selecionado]
    formacao_atual = dados_formacao.get('formacao', '4-4-2')
    
    st.subheader(f"⚙️ Configurar {nomes_tipos[tipo_selecionado]}")
    
    col_formacao, col_sugerir, col_copiar = st.columns([2, 1, 1])
    with col_formacao:
        formacao_input = st.text_input(
            "Formação (ex: 4-4-2, 4-3-3)",
            value=formacao_atual,
            key=f"formacao_{tipo_selecionado}"
        )
        if st.button("🔄 Atualizar Formação", key=f"atualizar_formacao_{tipo_selecionado}"):
            st.session_state.escalacoes_tatica[tipo_selecionado]['formacao'] = formacao_input
            st.success(f"Formação atualizada para {formacao_input}")
            st.rerun()
    with col_sugerir:
        if st.button("⚽ Sugerir Escalação", key=f"sugerir_{tipo_selecionado}", use_container_width=True):
            aplicar_sugestao_todas_formacoes(tipos_formacao, df_elenco, cartoes)
            st.success("✅ Sugestão aplicada a TODAS as formações! (Posições vazias preenchidas, prioridades respeitadas)")
            st.rerun()
    with col_copiar:
        if st.button("📋 Copiar para todas", key=f"copiar_{tipo_selecionado}", use_container_width=True):
            titulares_atuais = dados_formacao.get('titulares', [])
            reservas_atuais = dados_formacao.get('reservas', [])
            copiar_para_todas_formacoes(
                titulares_atuais, reservas_atuais, tipos_formacao, formacao_input, dados_formacao.get('funcoes', {})
            )
            st.success("✅ Titulares e reservas copiados para todas as formações!")
            st.rerun()
    
    # Interpreta a formação
    defensores, meias, atacantes, posicoes = interpretar_formacao(formacao_input)
    if not posicoes:
        st.error("Formação inválida. Use X-Y-Z (ex: 4-4-2).")
        return
    
    # Filtra jogadores disponíveis
    jogadores_disponiveis = df_elenco.copy()
    if 'lesionado' in jogadores_disponiveis.columns:
        jogadores_disponiveis = jogadores_disponiveis[~jogadores_disponiveis['lesionado']]
    jogadores_disponiveis = jogadores_disponiveis[
        ~jogadores_disponiveis['nome_completo'].apply(
            lambda x: jogador_suspenso(mapear_nome_para_canonico(x), cartoes)
        )
    ]
    if jogadores_disponiveis.empty:
        st.warning("Nenhum jogador disponível.")
        return
    st.write(f"**Jogadores disponíveis:** {len(jogadores_disponiveis)}")
    
    # CAMPO VISUAL
    st.subheader("🏟️ Campo")
    titulares_atuais = dados_formacao.get('titulares', [])
    fig = desenhar_campo(titulares_atuais, f"{nomes_tipos[tipo_selecionado]} - {formacao_input}", formacao_input, posicoes)
    if fig:
        st.pyplot(fig)
        plt.close(fig)
    else:
        st.info("Nenhum titular definido ainda. Use a sugestão, digite a escalação ou preencha manualmente.")
    
    # ============================================================
    # ESCALAÇÃO DIGITADA (PARA CADA UMA DAS 4 FORMAÇÕES)
    # ============================================================
    st.subheader("✏️ Digitar Escalação")
    st.markdown("Digite a escalação para **cada formação** separadamente. Formato: `Posição: Nome (Função)` ou apenas `Nome` (na ordem das posições).")
    
    for tipo in tipos_formacao:
        with st.expander(f"📝 Digitar {nomes_tipos[tipo]}", expanded=(tipo == tipo_selecionado)):
            dados_tipo = st.session_state.escalacoes_tatica.get(tipo, {})
            formacao_tipo = dados_tipo.get('formacao', '4-4-2')
            _, _, _, posicoes_tipo = interpretar_formacao(formacao_tipo)
            
            if not posicoes_tipo:
                st.warning(f"Formação inválida para {nomes_tipos[tipo]}. Configure a formação primeiro.")
                continue
            
            posicoes_exemplo = ", ".join([f"{p}" for p, _ in posicoes_tipo])
            st.caption(f"**Posições esperadas:** {posicoes_exemplo}")
            
            texto_escalacao = st.text_area(
                f"Digite a escalação para {nomes_tipos[tipo]}",
                placeholder=f"Exemplo:\nGoleiro: Ruan Rios (Goleiro)\nLateral Esquerdo: Júnior Espeto\nZagueiro: Kaká\n...",
                height=150,
                key=f"texto_escalacao_{tipo}"
            )
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button(f"📥 Aplicar em {nomes_tipos[tipo]}", key=f"aplicar_texto_{tipo}"):
                    if not texto_escalacao.strip():
                        st.warning("Digite pelo menos um nome.")
                    else:
                        resultados, erros = processar_escalacao_digitada(
                            texto_escalacao, df_elenco, posicoes_tipo
                        )
                        if erros:
                            st.warning(f"Alguns jogadores não foram encontrados:\n{erros}")
                        if resultados:
                            titulares = []
                            funcoes = {}
                            for item in resultados:
                                pos = item['posicao']
                                nome = item['nome']
                                funcao = item['funcao']
                                if not funcao and item['row'] is not None:
                                    # Usa a posição tática para atribuir função
                                    pos_tipo_item = dict(posicoes_tipo).get(pos, 'Meio-Campo')
                                    roles = get_roles_compativel(item['row'], pos_tipo_item)
                                    funcao = roles[0] if roles else ''
                                titulares.append({
                                    'posicao': pos,
                                    'nome': nome,
                                    'apelido': item['row']['apelido'],
                                    'row': item['row'],
                                    'funcao': funcao
                                })
                                if funcao:
                                    funcoes[nome] = funcao
                            
                            reservas_atuais = dados_tipo.get('reservas', [])
                            
                            st.session_state.escalacoes_tatica[tipo] = {
                                'formacao': formacao_tipo,
                                'titulares': titulares,
                                'reservas': reservas_atuais,
                                'funcoes': funcoes
                            }
                            st.success(f"✅ {nomes_tipos[tipo]} preenchida com {len(titulares)} jogadores!")
                            st.rerun()
            
            with col_btn2:
                if st.button(f"📋 Copiar para todas as formações", key=f"copiar_texto_{tipo}"):
                    if not texto_escalacao.strip():
                        st.warning("Digite pelo menos um nome.")
                    else:
                        resultados, erros = processar_escalacao_digitada(
                            texto_escalacao, df_elenco, posicoes_tipo
                        )
                        if erros:
                            st.warning(f"Alguns jogadores não foram encontrados:\n{erros}")
                        if resultados:
                            titulares = []
                            funcoes = {}
                            for item in resultados:
                                pos = item['posicao']
                                nome = item['nome']
                                funcao = item['funcao']
                                if not funcao and item['row'] is not None:
                                    pos_tipo_item = dict(posicoes_tipo).get(pos, 'Meio-Campo')
                                    roles = get_roles_compativel(item['row'], pos_tipo_item)
                                    funcao = roles[0] if roles else ''
                                titulares.append({
                                    'posicao': pos,
                                    'nome': nome,
                                    'apelido': item['row']['apelido'],
                                    'row': item['row'],
                                    'funcao': funcao
                                })
                                if funcao:
                                    funcoes[nome] = funcao
                            
                            for t in tipos_formacao:
                                dados_t = st.session_state.escalacoes_tatica.get(t, {})
                                reservas_t = dados_t.get('reservas', [])
                                st.session_state.escalacoes_tatica[t] = {
                                    'formacao': dados_t.get('formacao', '4-4-2'),
                                    'titulares': titulares.copy(),
                                    'reservas': reservas_t,
                                    'funcoes': funcoes.copy()
                                }
                            st.success(f"✅ Escalação copiada para TODAS as formações!")
                            st.rerun()
    
    # ============================================================
    # DROPDOWNS MANUAIS (COM FUNÇÕES CORRIGIDAS)
    # ============================================================
    st.subheader("📋 Preencher Titulares (Dropdowns)")
    st.markdown("Selecione um jogador e sua função para cada posição. Posições preenchidas serão preservadas ao sugerir.")
    
    titulares_salvos = dados_formacao.get('titulares', [])
    funcoes_salvas = dados_formacao.get('funcoes', {})
    
    titulares_selecionados = {}
    funcoes_selecionadas = {}
    
    for idx, (pos_exibida, pos_tipo) in enumerate(posicoes):
        col1, col2, col3 = st.columns([1.5, 2, 2])
        with col1:
            st.write(pos_exibida)
        with col2:
            # Candidatos
            candidatos = obter_jogadores_para_posicao(jogadores_disponiveis, pos_tipo, list(titulares_selecionados.values()), cartoes, incluir_lesionados=False)
            candidatos = candidatos.sort_values('Rating_Geral_FM26', ascending=False)
            opcoes = [''] + candidatos['nome_completo'].tolist()
            default_value = ''
            if idx < len(titulares_salvos):
                default_value = titulares_salvos[idx].get('nome', '')
            selecionado = st.selectbox(
                f"Jogador {idx}",
                opcoes,
                index=opcoes.index(default_value) if default_value in opcoes else 0,
                key=f"titular_{tipo_selecionado}_{idx}",
                label_visibility="collapsed"
            )
            if selecionado:
                titulares_selecionados[pos_exibida] = selecionado
        with col3:
            if selecionado:
                row = df_elenco[df_elenco['nome_completo'] == selecionado].iloc[0]
                # Obtém funções compatíveis com a posição tática (pos_tipo)
                roles = get_roles_compativel(row, pos_tipo)
                
                # Também filtra por categoria (in/out) se necessário
                if tipo_selecionado == 'ofensiva_sem_bola':
                    roles = [r for r in roles if CATEGORIA_ROLE.get(r) == 'out']
                else:
                    roles = [r for r in roles if CATEGORIA_ROLE.get(r) == 'in']
                
                # Se ainda estiver vazio, usa todas as roles da categoria
                if not roles:
                    if tipo_selecionado == 'ofensiva_sem_bola':
                        roles = [r for r, cat in CATEGORIA_ROLE.items() if cat == 'out']
                    else:
                        roles = [r for r, cat in CATEGORIA_ROLE.items() if cat == 'in']
                
                funcoes_exibicao = [TRADUCAO_ROLES_PT.get(r, r) for r in roles]
                mapa_exibicao = dict(zip(funcoes_exibicao, roles))
                
                funcao_atual = funcoes_salvas.get(selecionado, '')
                if funcao_atual and funcao_atual not in roles:
                    roles.append(funcao_atual)
                    funcoes_exibicao.append(TRADUCAO_ROLES_PT.get(funcao_atual, funcao_atual))
                    mapa_exibicao[funcoes_exibicao[-1]] = funcao_atual
                
                funcao_idx = roles.index(funcao_atual) if funcao_atual in roles else 0
                funcao_exibida = st.selectbox(
                    f"Função {idx}",
                    funcoes_exibicao,
                    index=funcao_idx,
                    key=f"funcao_{tipo_selecionado}_{idx}",
                    label_visibility="collapsed"
                )
                funcao_original = mapa_exibicao.get(funcao_exibida, '')
                funcoes_selecionadas[selecionado] = funcao_original
            else:
                st.write("")
    
    # RESERVAS
    st.subheader("🔄 Reservas (máx. 12)")
    reservas_salvas = dados_formacao.get('reservas', [])
    jogadores_reserva = jogadores_disponiveis[
        ~jogadores_disponiveis['nome_completo'].isin(titulares_selecionados.values())
    ]['nome_completo'].tolist()
    
    default_reservas = [r.get('nome', '') for r in reservas_salvas if r.get('nome') in jogadores_reserva]
    reservas_selecionados = st.multiselect(
        "Selecione os reservas",
        jogadores_reserva,
        default=default_reservas[:12],
        key=f"reservas_{tipo_selecionado}"
    )
    if len(reservas_selecionados) > 12:
        st.warning("Máximo de 12 reservas. Os primeiros 12 serão salvos.")
        reservas_selecionados = reservas_selecionados[:12]
    
    # SALVAR
    col_salvar, col_limpar = st.columns(2)
    with col_salvar:
        if st.button(f"💾 Salvar {nomes_tipos[tipo_selecionado]}", use_container_width=True):
            posicoes_faltando = []
            for pos_exibida, _ in posicoes:
                if pos_exibida not in titulares_selecionados:
                    posicoes_faltando.append(pos_exibida)
            if posicoes_faltando:
                st.error(f"Preencha os titulares para: {', '.join(posicoes_faltando)}")
            else:
                titulares = []
                for pos, nome in titulares_selecionados.items():
                    row = df_elenco[df_elenco['nome_completo'] == nome].iloc[0]
                    funcao = funcoes_selecionadas.get(nome, '')
                    titulares.append({
                        'posicao': pos,
                        'nome': nome,
                        'apelido': row['apelido'],
                        'row': row,
                        'funcao': funcao
                    })
                reservas = []
                for nome in reservas_selecionados:
                    row = df_elenco[df_elenco['nome_completo'] == nome].iloc[0]
                    reservas.append({
                        'nome': nome,
                        'apelido': row['apelido'],
                        'row': row
                    })
                st.session_state.escalacoes_tatica[tipo_selecionado] = {
                    'formacao': formacao_input,
                    'titulares': titulares,
                    'reservas': reservas,
                    'funcoes': funcoes_selecionadas
                }
                st.success(f"✅ {nomes_tipos[tipo_selecionado]} salva!")
                st.rerun()
    
    with col_limpar:
        if st.button(f"🗑️ Limpar {nomes_tipos[tipo_selecionado]}", use_container_width=True):
            st.session_state.escalacoes_tatica[tipo_selecionado] = {
                'formacao': '4-4-2',
                'titulares': [],
                'reservas': [],
                'funcoes': {}
            }
            st.success(f"🧹 {nomes_tipos[tipo_selecionado]} limpa!")
            st.rerun()
    
    # ============================================================
    # VISUALIZAÇÃO DAS FORMAÇÕES SALVAS
    # ============================================================
    st.divider()
    st.subheader("📋 Visualização de todas as formações")
    for tipo in tipos_formacao:
        dados = st.session_state.escalacoes_tatica.get(tipo, {})
        titulares = dados.get('titulares', [])
        formacao = dados.get('formacao', '4-4-2')
        _, _, _, posicoes_esperadas = interpretar_formacao(formacao)
        with st.expander(f"{nomes_tipos[tipo]} - {formacao} ({len(titulares)} jogadores)"):
            if titulares:
                data = []
                for jog in titulares:
                    funcao_original = jog.get('funcao', '')
                    funcao_exibida = TRADUCAO_ROLES_PT.get(funcao_original, funcao_original)
                    data.append({
                        'Posição': jog.get('posicao', ''),
                        'Jogador': jog.get('apelido', jog.get('nome', 'N/D')),
                        'Função FM26': funcao_exibida
                    })
                df_exib = pd.DataFrame(data)
                st.dataframe(df_exib, use_container_width=True)
                
                fig = desenhar_campo(titulares, f"{nomes_tipos[tipo]} - {formacao}", formacao, posicoes_esperadas)
                if fig:
                    st.pyplot(fig)
                    plt.close(fig)
            else:
                st.info("Nenhum titular definido.")
    
    # ============================================================
    # EXPORTAÇÃO
    # ============================================================
    st.divider()
    if st.button("📤 Exportar todas as formações (CSV)"):
        rows = []
        for tipo in tipos_formacao:
            dados = st.session_state.escalacoes_tatica.get(tipo, {})
            for jog in dados.get('titulares', []):
                funcao_original = jog.get('funcao', '')
                funcao_exibida = TRADUCAO_ROLES_PT.get(funcao_original, funcao_original)
                rows.append({
                    'Formação': nomes_tipos[tipo],
                    'Posição': jog.get('posicao', ''),
                    'Jogador': jog.get('nome', ''),
                    'Apelido': jog.get('apelido', ''),
                    'Função FM26': funcao_exibida
                })
        if rows:
            df_export = pd.DataFrame(rows)
            csv = df_export.to_csv(index=False, sep=';', encoding='utf-8-sig')
            st.download_button(
                label="Baixar CSV",
                data=csv,
                file_name="escalacoes_taticas.csv",
                mime="text/csv"
            )
        else:
            st.warning("Nenhuma formação salva para exportar.")
    
    st.caption("💡 As funções são baseadas no FM26. Use os dropdowns, a digitação ou a sugestão para montar sua escalação. A sugestão preserva suas escolhas manuais e aplica as prioridades definidas.")