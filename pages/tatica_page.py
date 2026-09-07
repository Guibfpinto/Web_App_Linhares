# pages/tatica_page.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from utils import (
    interpretar_formacao,
    obter_jogadores_para_posicao,
    jogador_suspenso,
    mapear_nome_para_canonico,
    sanitizar_dataframe,
)
from roles_fm26 import (
    ROLES_FM26_PT,
    COMPATIBILIDADE_POSICAO,
    TRADUCAO_ROLES_PT,
    CATEGORIA_ROLE
)

# ============================================================
# FUNÇÃO PARA DESENHAR O CAMPO
# ============================================================
def desenhar_campo(titulares, titulo, formacao):
    """Desenha um campo de futebol com os jogadores posicionados e suas funções."""
    if not titulares:
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

    # Posições pré-definidas para 11 jogadores (4-4-2)
    posicoes_padrao = [
        (50, 8),   # Goleiro
        (15, 18),  # LE
        (35, 18),  # ZAG
        (65, 18),  # ZAG
        (85, 18),  # LD
        (15, 35),  # ME
        (35, 35),  # MC
        (65, 35),  # MC
        (85, 35),  # MD
        (30, 52),  # AT
        (70, 52)   # AT
    ]

    n = len(titulares)
    if n <= 11:
        posicoes = posicoes_padrao[:n]
    else:
        posicoes = []
        for i in range(n):
            x = 10 + (i / (n-1)) * 80 if n > 1 else 50
            y = 10 + ((i % 5) / 4) * 50 if n > 5 else 10 + (i / (n-1)) * 50
            posicoes.append((x, y))

    for i, (x, y) in enumerate(posicoes):
        if i < len(titulares):
            jog = titulares[i]
            nome = jog.get('apelido', jog.get('nome', 'N/D'))
            funcao = jog.get('funcao', '')
            cor = '#1f77b4'
            if i == 0:
                cor = '#ff7f0e'  # goleiro
            ax.add_patch(Circle((x, y), 3.5, edgecolor='white', facecolor=cor, linewidth=2))
            ax.text(x, y-5, nome, ha='center', va='center', fontsize=7, color='white', weight='bold')
            if funcao:
                ax.text(x, y-8, funcao[:20], ha='center', va='center', fontsize=5, color='yellow', style='italic')

    ax.axis('off')
    plt.tight_layout()
    return fig

# ============================================================
# FUNÇÃO PRINCIPAL DA PÁGINA
# ============================================================
def show():
    st.header("📐 Escalação Tática")
    st.markdown("Defina as **4 formações** (Inicial, Ofensiva sem Bola, Defensiva, Ofensiva com Bola) e escolha as **funções do FM26** para cada jogador.")

    # Obtém a categoria e os dados da sessão
    categoria = st.session_state.get("categoria_tatica", "Profissional")
    df_elenco = st.session_state.get("df_elenco_tatica")
    cartoes = st.session_state.get("cartoes_tatica", {})

    if df_elenco is None or df_elenco.empty:
        st.warning(f"Elenco não disponível para {categoria}. Carregue os dados primeiro.")
        return

    # Tipos de formação
    tipos_formacao = ['inicial', 'ofensiva_sem_bola', 'defensiva', 'ofensiva_com_bola']
    nomes_tipos = {
        'inicial': '📋 Formação Inicial',
        'ofensiva_sem_bola': '⬆️ Ofensiva sem Bola (Out of Possession)',
        'defensiva': '⬇️ Defensiva (In Possession)',
        'ofensiva_com_bola': '⚡ Ofensiva com Bola (In Possession)'
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

    # Seleção do tipo de formação
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

    formacao_input = st.text_input(
        "Formação (ex: 4-4-2, 4-3-3, 3-5-2)",
        value=formacao_atual,
        key=f"formacao_{tipo_selecionado}"
    )

    defensores, meias, atacantes, posicoes = interpretar_formacao(formacao_input)
    if not posicoes:
        st.error("Formação inválida. Use o formato X-Y-Z (ex: 4-4-2, 4-3-3).")
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
        st.warning("Nenhum jogador disponível para escalar.")
        return

    st.write(f"**Jogadores disponíveis:** {len(jogadores_disponiveis)}")

    # ============================================================
    # SELEÇÃO DE TITULARES E FUNÇÕES
    # ============================================================
    st.subheader("🏃 Titulares")

    titulares_salvos = dados_formacao.get('titulares', [])
    funcoes_salvas = dados_formacao.get('funcoes', {})

    titulares_selecionados = {}
    funcoes_selecionadas = {}

    cols = st.columns(3)
    for idx, (pos_exibida, pos_tipo) in enumerate(posicoes):
        with cols[idx % 3]:
            # Filtra candidatos
            if pos_tipo == 'Goleiro':
                candidatos = jogadores_disponiveis[jogadores_disponiveis['Posicao_Principal'] == 'Goleiro']
            else:
                candidatos = jogadores_disponiveis[~jogadores_disponiveis['Posicao_Principal'].isin(['Goleiro'])]
            candidatos = candidatos[~candidatos['nome_completo'].isin(titulares_selecionados.values())]
            candidatos = candidatos.sort_values('Rating_Geral_FM26', ascending=False)

            opcoes = [''] + candidatos['nome_completo'].tolist()
            default_value = ''
            if idx < len(titulares_salvos):
                default_value = titulares_salvos[idx].get('nome', '')

            selecionado = st.selectbox(
                f"{pos_exibida} ({pos_tipo})",
                opcoes,
                index=opcoes.index(default_value) if default_value in opcoes else 0,
                key=f"titular_{tipo_selecionado}_{idx}"
            )

            if selecionado:
                titulares_selecionados[pos_exibida] = selecionado

                # Busca a linha do jogador
                row = df_elenco[df_elenco['nome_completo'] == selecionado].iloc[0]
                posicao_principal = row.get('Posicao_Principal', 'Outros')

                # Obtém funções compatíveis com a posição principal
                funcoes_compativeis = COMPATIBILIDADE_POSICAO.get(posicao_principal, [])

                # Se não houver funções compatíveis, usa todas as roles da mesma categoria (in/out)
                if not funcoes_compativeis:
                    # Filtra roles pela categoria (in/out) baseado no tipo de formação
                    if tipo_selecionado in ['ofensiva_sem_bola']:
                        # Out of possession
                        funcoes_compativeis = [role for role, cat in CATEGORIA_ROLE.items() if cat == 'out']
                    else:
                        # In possession
                        funcoes_compativeis = [role for role, cat in CATEGORIA_ROLE.items() if cat == 'in']

                # Traduz os nomes para exibição
                funcoes_exibicao = [TRADUCAO_ROLES_PT.get(role, role) for role in funcoes_compativeis]
                # Mapeia nome exibido -> role original
                mapa_exibicao = dict(zip(funcoes_exibicao, funcoes_compativeis))

                # Recupera função salva
                funcao_atual = funcoes_salvas.get(selecionado, '')
                # Se a função salva não estiver na lista, adiciona
                if funcao_atual and funcao_atual not in funcoes_compativeis:
                    funcoes_compativeis.append(funcao_atual)
                    funcoes_exibicao.append(TRADUCAO_ROLES_PT.get(funcao_atual, funcao_atual))
                    mapa_exibicao[funcoes_exibicao[-1]] = funcao_atual

                funcao_idx = 0
                if funcao_atual in funcoes_compativeis:
                    funcao_idx = funcoes_compativeis.index(funcao_atual)

                funcao_exibida = st.selectbox(
                    f"Função FM26",
                    funcoes_exibicao,
                    index=funcao_idx,
                    key=f"funcao_{tipo_selecionado}_{idx}"
                )
                funcao_original = mapa_exibicao.get(funcao_exibida, '')
                funcoes_selecionadas[selecionado] = funcao_original

                # Exibe atributos da função (opcional)
                if funcao_original:
                    with st.expander(f"📊 Atributos - {funcao_exibida}"):
                        role_data = ROLES_FM26_PT.get(funcao_original, {})
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
    # SELEÇÃO DE RESERVAS
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
    # BOTÃO SALVAR / LIMPAR
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

                st.success(f"✅ {nomes_tipos[tipo_selecionado]} salva com sucesso!")
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

                fig = desenhar_campo(titulares, f"{nomes_tipos[tipo]} - {formacao}", formacao)
                if fig:
                    st.pyplot(fig)
                    plt.close(fig)
            else:
                st.info("Nenhum titular definido para esta formação.")

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

    st.caption("💡 As funções são baseadas no FM26. A lista exibida é compatível com a posição principal do jogador. Clique em 'Mostrar atributos' para ver os atributos chave, preferidos e desnecessários de cada função.")