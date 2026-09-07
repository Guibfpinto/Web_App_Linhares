# pages/tatica_page.py
import streamlit as st
import pandas as pd
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
)
from roles_fm26 import (
    get_roles_by_posicao,
    get_role_traduzida,
    get_role_attributes,
    CATEGORIA_ROLE,
    TRADUCAO_ROLES_PT,
    COMPATIBILIDADE_POSICAO
)

# ============================================================
# FUNÇÃO PARA CARREGAR ELENCO POR CATEGORIA
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
# FUNÇÃO PARA DESENHAR CAMPO (DINÂMICO POR FORMAÇÃO)
# ============================================================
def desenhar_campo(titulares, titulo, formacao, posicoes_esperadas):
    if not titulares or not posicoes_esperadas:
        return None
    
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 70)
    ax.set_facecolor('#2e7d32')
    ax.set_title(titulo, fontsize=14, fontweight='bold', color='white')
    
    # Linhas do campo
    ax.plot([0, 100], [0, 0], 'w', linewidth=2)
    ax.plot([0, 100], [70, 70], 'w', linewidth=2)
    ax.plot([0, 0], [0, 70], 'w', linewidth=2)
    ax.plot([100, 100], [0, 70], 'w', linewidth=2)
    ax.plot([50, 50], [0, 70], 'w', linestyle='--', linewidth=1)
    ax.add_patch(Circle((50, 35), 7, edgecolor='w', facecolor='none', linewidth=2))
    ax.add_patch(Circle((50, 35), 1, edgecolor='w', facecolor='w', linewidth=1))
    ax.add_patch(Rectangle((40, 18), 20, 34, edgecolor='w', facecolor='none', linewidth=2))
    
    # Posicionamento genérico baseado na formação
    # Ordena os titulares na ordem das posições esperadas
    n = len(posicoes_esperadas)
    posicoes = []
    # Posições relativas (x, y) para 11 jogadores em uma grade 4-4-2
    # Goleiro
    posicoes.append((50, 8))
    # Defensores (linha de 4)
    if n >= 5:
        posicoes.append((15, 18))  # LE
        posicoes.append((35, 18))  # ZAG
        posicoes.append((65, 18))  # ZAG
        posicoes.append((85, 18))  # LD
    elif n >= 4:
        posicoes.append((20, 18))
        posicoes.append((40, 18))
        posicoes.append((60, 18))
        posicoes.append((80, 18))
    elif n >= 3:
        posicoes.append((25, 18))
        posicoes.append((50, 18))
        posicoes.append((75, 18))
    # Meio-campistas (linha de 4)
    if n >= 9:
        posicoes.append((15, 35))  # ME
        posicoes.append((35, 35))  # MC
        posicoes.append((65, 35))  # MC
        posicoes.append((85, 35))  # MD
    elif n >= 8:
        posicoes.append((20, 35))
        posicoes.append((40, 35))
        posicoes.append((60, 35))
        posicoes.append((80, 35))
    elif n >= 7:
        posicoes.append((25, 35))
        posicoes.append((50, 35))
        posicoes.append((75, 35))
    # Atacantes
    if n >= 11:
        posicoes.append((30, 52))  # AT
        posicoes.append((70, 52))  # AT
    elif n >= 10:
        posicoes.append((35, 52))
        posicoes.append((65, 52))
    elif n >= 9:
        posicoes.append((50, 52))
    
    # Caso ainda falte, preenche com posições extras
    while len(posicoes) < n:
        x = 10 + (len(posicoes) / n) * 80
        y = 10 + ((len(posicoes) % 3) / 2) * 50
        posicoes.append((x, y))
    
    # Desenha cada jogador na posição correspondente
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
# FUNÇÃO PARA SUGERIR ESCALAÇÃO (USANDO O MESMO FILTRO DOS DROPDOWNS)
# ============================================================
def sugerir_escalacao(df_elenco, posicoes, cartoes):
    """Sugere titulares e reservas usando obter_jogadores_para_posicao para filtragem."""
    jogadores_disponiveis = df_elenco.copy()
    if 'lesionado' in jogadores_disponiveis.columns:
        jogadores_disponiveis = jogadores_disponiveis[~jogadores_disponiveis['lesionado']]
    
    # Função para verificar suspensão
    def nao_suspenso(nome):
        return not jogador_suspenso(mapear_nome_para_canonico(nome), cartoes)
    jogadores_disponiveis = jogadores_disponiveis[jogadores_disponiveis['nome_completo'].apply(nao_suspenso)]
    
    if jogadores_disponiveis.empty:
        return [], []
    
    titulares = []
    jogadores_usados = []
    
    for pos_exibida, pos_tipo in posicoes:
        # Usa a mesma função de filtro dos dropdowns
        candidatos = obter_jogadores_para_posicao(jogadores_disponiveis, pos_tipo, jogadores_usados, cartoes, incluir_lesionados=False)
        candidatos = candidatos.sort_values('Rating_Geral_FM26', ascending=False)
        
        if not candidatos.empty:
            melhor = candidatos.iloc[0]
            titulares.append({
                'posicao': pos_exibida,
                'nome': melhor['nome_completo'],
                'apelido': melhor['apelido'],
                'row': melhor
            })
            jogadores_usados.append(melhor['nome_completo'])
        else:
            titulares.append({
                'posicao': pos_exibida,
                'nome': '',
                'apelido': '',
                'row': None
            })
    
    # Reservas: melhores não usados
    reservas = []
    for _, row in jogadores_disponiveis[~jogadores_disponiveis['nome_completo'].isin(jogadores_usados)].head(12).iterrows():
        reservas.append({
            'nome': row['nome_completo'],
            'apelido': row['apelido'],
            'row': row
        })
    
    return titulares, reservas

# ============================================================
# FUNÇÃO PARA COPIAR ESCALAÇÃO PARA TODAS AS FORMAÇÕES
# ============================================================
def aplicar_escalacao_para_todas_formacoes(titulares, reservas, tipos_formacao, formacao_atual, funcoes_atuais=None):
    for tipo in tipos_formacao:
        dados = st.session_state.escalacoes_tatica.get(tipo, {})
        funcoes_existentes = dados.get('funcoes', {})
        novos_titulares = []
        for jog in titulares:
            if jog['nome']:
                nome = jog['nome']
                funcao = funcoes_existentes.get(nome, '')
                if not funcao and jog['row'] is not None:
                    posicao_principal = jog['row'].get('Posicao_Principal', 'Outros')
                    roles = get_roles_by_posicao(posicao_principal)
                    funcao = roles[0] if roles else ''
                novos_titulares.append({
                    'posicao': jog['posicao'],
                    'nome': nome,
                    'apelido': jog['apelido'],
                    'row': jog['row'],
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
    
    # Inicializa estado
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
    
    # ============================================================
    # CONFIGURAÇÃO DA FORMAÇÃO
    # ============================================================
    st.subheader(f"⚙️ Configurar {nomes_tipos[tipo_selecionado]}")
    
    col_formacao, col_sugerir, col_copiar = st.columns([2, 1, 1])
    with col_formacao:
        formacao_input = st.text_input(
            "Formação (ex: 4-4-2, 4-3-3)",
            value=formacao_atual,
            key=f"formacao_{tipo_selecionado}"
        )
    with col_sugerir:
        if st.button("⚽ Sugerir Escalação", key=f"sugerir_{tipo_selecionado}", use_container_width=True):
            defensores, meias, atacantes, posicoes = interpretar_formacao(formacao_input)
            if posicoes:
                titulares, reservas = sugerir_escalacao(df_elenco, posicoes, cartoes)
                if titulares:
                    aplicar_escalacao_para_todas_formacoes(
                        titulares, reservas, tipos_formacao, formacao_input, {}
                    )
                    st.success("✅ Escalação sugerida aplicada a TODAS as formações!")
                    st.rerun()
                else:
                    st.warning("Não foi possível sugerir uma escalação.")
            else:
                st.error("Formação inválida.")
    with col_copiar:
        if st.button("📋 Copiar para todas", key=f"copiar_{tipo_selecionado}", use_container_width=True):
            titulares_atuais = dados_formacao.get('titulares', [])
            reservas_atuais = dados_formacao.get('reservas', [])
            aplicar_escalacao_para_todas_formacoes(
                titulares_atuais, reservas_atuais, tipos_formacao, formacao_input, dados_formacao.get('funcoes', {})
            )
            st.success("✅ Titulares e reservas copiados para todas as formações!")
            st.rerun()
    
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
    
    # ============================================================
    # DROPDOWNS DE TITULARES E FUNÇÕES (USANDO obter_jogadores_para_posicao)
    # ============================================================
    st.subheader("🏃 Titulares")
    
    titulares_salvos = dados_formacao.get('titulares', [])
    funcoes_salvas = dados_formacao.get('funcoes', {})
    
    titulares_selecionados = {}
    funcoes_selecionadas = {}
    
    cols = st.columns(3)
    for idx, (pos_exibida, pos_tipo) in enumerate(posicoes):
        with cols[idx % 3]:
            # Usa a função do utils para filtrar candidatos (inclui posições secundárias)
            candidatos = obter_jogadores_para_posicao(jogadores_disponiveis, pos_tipo, list(titulares_selecionados.values()), cartoes, incluir_lesionados=False)
            candidatos = candidatos.sort_values('Rating_Geral_FM26', ascending=False)
            
            opcoes = [''] + candidatos['nome_completo'].tolist()
            default_value = ''
            if idx < len(titulares_salvos):
                default_value = titulares_salvos[idx].get('nome', '')
            
            selecionado = st.selectbox(
                f"{pos_exibida}",
                opcoes,
                index=opcoes.index(default_value) if default_value in opcoes else 0,
                key=f"titular_{tipo_selecionado}_{idx}"
            )
            
            if selecionado:
                titulares_selecionados[pos_exibida] = selecionado
                row = df_elenco[df_elenco['nome_completo'] == selecionado].iloc[0]
                posicao_principal = row.get('Posicao_Principal', 'Outros')
                
                # Funções compatíveis com a posição principal
                roles = get_roles_by_posicao(posicao_principal)
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
                    f"Função FM26",
                    funcoes_exibicao,
                    index=funcao_idx,
                    key=f"funcao_{tipo_selecionado}_{idx}"
                )
                funcao_original = mapa_exibicao.get(funcao_exibida, '')
                funcoes_selecionadas[selecionado] = funcao_original
                
                if funcao_original:
                    with st.expander(f"📊 Atributos - {funcao_exibida}"):
                        role_data = get_role_attributes(funcao_original)
                        key_attrs = role_data.get('key', [])
                        pref_attrs = role_data.get('preferred', [])
                        unnec_attrs = role_data.get('unnecessary', [])
                        if key_attrs:
                            st.write("**Chave:**", ', '.join(key_attrs))
                        if pref_attrs:
                            st.write("**Preferidos:**", ', '.join(pref_attrs))
                        if unnec_attrs:
                            st.write("**Desnecessários:**", ', '.join(unnec_attrs))
    
    # ============================================================
    # RESERVAS
    # ============================================================
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
    
    # ============================================================
    # SALVAR / LIMPAR
    # ============================================================
    col_salvar, col_limpar = st.columns(2)
    with col_salvar:
        if st.button(f"💾 Salvar {nomes_tipos[tipo_selecionado]}", use_container_width=True):
            if len(titulares_selecionados) < len(posicoes):
                st.error("Preencha todos os titulares.")
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
    st.subheader("📋 Visualização das Formações")
    for tipo in tipos_formacao:
        dados = st.session_state.escalacoes_tatica.get(tipo, {})
        titulares = dados.get('titulares', [])
        formacao = dados.get('formacao', '4-4-2')
        # Interpreta a formação para obter posições esperadas
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
    
    st.caption("💡 As funções são baseadas no FM26. Use os dropdowns para escolher manualmente a função de cada jogador.")