# roles_fm26.py
"""
Dicionário completo de Funções (Roles) do Football Manager 26 em Português.
Contém atributos chave, preferidos e desnecessários para cada função,
além de mapeamentos de compatibilidade por posição e tradução.

Estrutura de cada role:
    'Nome da Role': {
        'key': ['atributo1', 'atributo2', ...],        # atributos essenciais
        'preferred': ['atributo1', ...],               # atributos importantes
        'unnecessary': ['atributo1', ...],            # atributos que podem ser negligenciados
        'posicao': 'Posição Esperada',                 # posição principal para a role
        'categoria': 'in' | 'out'                     # com bola (in) ou sem bola (out)
    }
"""

# ============================================================
# ROLES "IN POSSESSION" (COM BOLA)
# ============================================================
ROLES_IN_POSSESSION = {
    # ==================== GOLEIROS ====================
    'Goleiro': {
        'key': ['jogo_aereo_goleiro', 'comando_area', 'comunicacao_goleiro', 'defesas_goleiro', 'reflexos', 'agilidade', 'concentracao', 'posicionamento'],
        'preferred': ['chutes_goleiro', 'um_contra_um_goleiro', 'arremessos_goleiro', 'antecipacao', 'decisao'],
        'unnecessary': ['excentricidade'],
        'posicao': 'Goleiro',
        'categoria': 'in'
    },
    'Goleiro de Bola': {
        'key': ['jogo_aereo_goleiro', 'comando_area', 'comunicacao_goleiro', 'defesas_goleiro', 'chutes_goleiro', 'reflexos', 'agilidade', 'concentracao', 'posicionamento'],
        'preferred': ['excentricidade', 'um_contra_um_goleiro', 'arremessos_goleiro', 'antecipacao', 'composicao', 'decisao', 'passe'],
        'unnecessary': [],
        'posicao': 'Goleiro',
        'categoria': 'in'
    },
    'Goleiro Caxias': {
        'key': ['jogo_aereo_goleiro', 'comando_area', 'comunicacao_goleiro', 'defesas_goleiro', 'reflexos', 'agilidade', 'concentracao', 'posicionamento'],
        'preferred': ['um_contra_um_goleiro', 'antecipacao', 'decisao'],
        'unnecessary': ['excentricidade', 'passe'],
        'posicao': 'Goleiro',
        'categoria': 'in'
    },

    # ==================== ZAGUEIROS ====================
    'Zagueiro Central': {
        'key': ['cabecada', 'marcacao', 'desarme', 'antecipacao', 'posicionamento', 'altura_salto', 'forca_fisica'],
        'preferred': ['agressividade', 'coragem', 'composicao', 'concentracao', 'decisao', 'velocidade_maxima'],
        'unnecessary': ['passe'],
        'posicao': 'Zagueiro',
        'categoria': 'in'
    },
    'Zagueiro de Bola': {
        'key': ['cabecada', 'marcacao', 'passe', 'desarme', 'antecipacao', 'composicao', 'posicionamento', 'altura_salto', 'forca_fisica'],
        'preferred': ['primeiro_controle', 'tecnica', 'agressividade', 'coragem', 'concentracao', 'decisao', 'visao_jogo', 'velocidade_maxima'],
        'unnecessary': [],
        'posicao': 'Zagueiro',
        'categoria': 'in'
    },
    'Zagueiro Caxias': {
        'key': ['cabecada', 'marcacao', 'desarme', 'antecipacao', 'posicionamento', 'altura_salto', 'forca_fisica'],
        'preferred': ['agressividade', 'coragem', 'concentracao', 'velocidade_maxima'],
        'unnecessary': ['passe', 'composicao'],
        'posicao': 'Zagueiro',
        'categoria': 'in'
    },
    'Zagueiro Largo': {
        'key': ['cabecada', 'marcacao', 'desarme', 'antecipacao', 'posicionamento', 'altura_salto', 'forca_fisica'],
        'preferred': ['drible', 'agressividade', 'coragem', 'composicao', 'concentracao', 'decisao', 'intensidade_trabalho', 'aceleracao', 'agilidade', 'velocidade_maxima', 'resistencia'],
        'unnecessary': ['passe'],
        'posicao': 'Zagueiro',
        'categoria': 'in'
    },
    'Zagueiro Avançado': {
        'key': ['cabecada', 'marcacao', 'passe', 'desarme', 'tecnica', 'antecipacao', 'composicao', 'decisao', 'posicionamento', 'trabalho_equipe', 'altura_salto', 'forca_fisica'],
        'preferred': ['drible', 'primeiro_controle', 'agressividade', 'coragem', 'concentracao', 'visao_jogo', 'velocidade_maxima', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Zagueiro',
        'categoria': 'in'
    },
    'Zagueiro Sobreposição': {
        'key': ['cruzamentos', 'cabecada', 'marcacao', 'desarme', 'antecipacao', 'intensidade_trabalho', 'altura_salto', 'velocidade_maxima', 'resistencia', 'forca_fisica'],
        'preferred': ['drible', 'tecnica', 'agressividade', 'coragem', 'composicao', 'concentracao', 'decisao', 'movimentacao_sem_bola', 'posicionamento', 'aceleracao', 'agilidade'],
        'unnecessary': [],
        'posicao': 'Zagueiro',
        'categoria': 'in'
    },

    # ==================== LATERAIS ====================
    'Lateral': {
        'key': ['marcacao', 'desarme', 'antecipacao', 'concentracao', 'posicionamento', 'trabalho_equipe', 'aceleracao'],
        'preferred': ['cruzamentos', 'drible', 'passe', 'tecnica', 'decisao', 'intensidade_trabalho', 'agilidade', 'velocidade_maxima', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Lateral',
        'categoria': 'in'
    },
    'Lateral Interno': {
        'key': ['cabecada', 'marcacao', 'desarme', 'antecipacao', 'posicionamento', 'forca_fisica'],
        'preferred': ['drible', 'agressividade', 'coragem', 'composicao', 'concentracao', 'decisao', 'intensidade_trabalho', 'aceleracao', 'agilidade', 'altura_salto', 'velocidade_maxima', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Lateral',
        'categoria': 'in'
    },

    # ==================== ALAS ====================
    'Ala': {
        'key': ['cruzamentos', 'marcacao', 'desarme', 'trabalho_equipe', 'intensidade_trabalho', 'aceleracao', 'velocidade_maxima', 'resistencia'],
        'preferred': ['drible', 'primeiro_controle', 'passe', 'tecnica', 'antecipacao', 'concentracao', 'decisao', 'movimentacao_sem_bola', 'posicionamento', 'agilidade', 'equilibrio'],
        'unnecessary': [],
        'posicao': 'Lateral',
        'categoria': 'in'
    },
    'Ala Avançado': {
        'key': ['cruzamentos', 'drible', 'tecnica', 'movimentacao_sem_bola', 'trabalho_equipe', 'intensidade_trabalho', 'aceleracao', 'agilidade', 'velocidade_maxima', 'resistencia'],
        'preferred': ['primeiro_controle', 'marcacao', 'passe', 'desarme', 'antecipacao', 'decisao', 'criatividade', 'posicionamento', 'equilibrio'],
        'unnecessary': [],
        'posicao': 'Lateral',
        'categoria': 'in'
    },
    'Ala Interno': {
        'key': ['passe', 'desarme', 'antecipacao', 'composicao', 'decisao', 'posicionamento', 'trabalho_equipe', 'aceleracao'],
        'preferred': ['primeiro_controle', 'marcacao', 'tecnica', 'concentracao', 'intensidade_trabalho', 'agilidade', 'velocidade_maxima', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Lateral',
        'categoria': 'in'
    },
    'Ala Armador': {
        'key': ['primeiro_controle', 'passe', 'desarme', 'tecnica', 'composicao', 'decisao', 'posicionamento', 'trabalho_equipe', 'visao_jogo', 'aceleracao'],
        'preferred': ['cruzamentos', 'drible', 'marcacao', 'antecipacao', 'concentracao', 'movimentacao_sem_bola', 'intensidade_trabalho', 'agilidade', 'velocidade_maxima', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Lateral',
        'categoria': 'in'
    },

    # ==================== VOLANTES ====================
    'Volante': {
        'key': ['desarme', 'antecipacao', 'concentracao', 'posicionamento', 'trabalho_equipe'],
        'preferred': ['primeiro_controle', 'marcacao', 'passe', 'agressividade', 'composicao', 'decisao', 'intensidade_trabalho', 'resistencia', 'forca_fisica'],
        'unnecessary': [],
        'posicao': 'Volante',
        'categoria': 'in'
    },
    'Meio-Campo Box-to-Box': {
        'key': ['passe', 'desarme', 'movimentacao_sem_bola', 'trabalho_equipe', 'intensidade_trabalho', 'resistencia'],
        'preferred': ['drible', 'finalizacao', 'primeiro_controle', 'chutes_longe', 'tecnica', 'agressividade', 'antecipacao', 'composicao', 'decisao', 'posicionamento', 'aceleracao', 'equilibrio', 'velocidade_maxima', 'forca_fisica'],
        'unnecessary': [],
        'posicao': 'Meio-Campo',
        'categoria': 'in'
    },
    'Meio-Campo Box-to-Box Armador': {
        'key': ['primeiro_controle', 'passe', 'tecnica', 'composicao', 'decisao', 'movimentacao_sem_bola', 'trabalho_equipe', 'visao_jogo', 'intensidade_trabalho', 'resistencia'],
        'preferred': ['drible', 'marcacao', 'desarme', 'antecipacao', 'posicionamento', 'aceleracao', 'agilidade', 'equilibrio', 'velocidade_maxima'],
        'unnecessary': [],
        'posicao': 'Meio-Campo',
        'categoria': 'in'
    },
    'Armador Recuado': {
        'key': ['primeiro_controle', 'passe', 'tecnica', 'composicao', 'decisao', 'movimentacao_sem_bola', 'trabalho_equipe', 'visao_jogo'],
        'preferred': ['marcacao', 'desarme', 'antecipacao', 'concentracao', 'posicionamento', 'intensidade_trabalho', 'equilibrio', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Volante',
        'categoria': 'in'
    },
    'Meio-Volante': {
        'key': ['cabecada', 'marcacao', 'desarme', 'antecipacao', 'concentracao', 'posicionamento', 'trabalho_equipe', 'altura_salto', 'forca_fisica'],
        'preferred': ['primeiro_controle', 'passe', 'agressividade', 'coragem', 'composicao', 'decisao', 'intensidade_trabalho', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Volante',
        'categoria': 'in'
    },

    # ==================== MEIAS CENTRAIS ====================
    'Meia Central': {
        'key': ['primeiro_controle', 'passe', 'desarme', 'decisao', 'trabalho_equipe'],
        'preferred': ['tecnica', 'antecipacao', 'composicao', 'concentracao', 'movimentacao_sem_bola', 'posicionamento', 'visao_jogo', 'intensidade_trabalho', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Meio-Campo',
        'categoria': 'in'
    },
    'Meia Armador Avançado': {
        'key': ['primeiro_controle', 'passe', 'tecnica', 'composicao', 'decisao', 'movimentacao_sem_bola', 'trabalho_equipe', 'visao_jogo'],
        'preferred': ['cruzamentos', 'drible', 'antecipacao', 'criatividade', 'aceleracao', 'agilidade'],
        'unnecessary': [],
        'posicao': 'Meia-Atacante',
        'categoria': 'in'
    },
    'Meia Armador': {
        'key': ['primeiro_controle', 'passe', 'tecnica', 'composicao', 'decisao', 'movimentacao_sem_bola', 'trabalho_equipe', 'visao_jogo'],
        'preferred': ['drible', 'desarme', 'antecipacao', 'criatividade', 'posicionamento', 'intensidade_trabalho', 'agilidade', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Meio-Campo',
        'categoria': 'in'
    },
    'Meia Central Largo': {
        'key': ['primeiro_controle', 'passe', 'desarme', 'decisao', 'trabalho_equipe'],
        'preferred': ['cruzamentos', 'drible', 'tecnica', 'antecipacao', 'composicao', 'concentracao', 'movimentacao_sem_bola', 'posicionamento', 'visao_jogo', 'intensidade_trabalho', 'agilidade', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Meio-Campo',
        'categoria': 'in'
    },

    # ==================== MEIAS LATERAIS ====================
    'Meia Largo': {
        'key': ['cruzamentos', 'passe', 'tecnica', 'trabalho_equipe', 'intensidade_trabalho', 'velocidade_maxima', 'resistencia'],
        'preferred': ['drible', 'primeiro_controle', 'antecipacao', 'composicao', 'movimentacao_sem_bola', 'visao_jogo', 'aceleracao', 'agilidade'],
        'unnecessary': [],
        'posicao': 'Meio-Campo',
        'categoria': 'in'
    },
    'Ponta Interior': {
        'key': ['drible', 'primeiro_controle', 'tecnica', 'composicao', 'trabalho_equipe', 'aceleracao', 'agilidade'],
        'preferred': ['cruzamentos', 'chutes_longe', 'passe', 'antecipacao', 'criatividade', 'movimentacao_sem_bola', 'visao_jogo', 'intensidade_trabalho', 'equilibrio', 'velocidade_maxima', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Ponta',
        'categoria': 'in'
    },
    'Ponta Armador': {
        'key': ['cruzamentos', 'drible', 'primeiro_controle', 'passe', 'tecnica', 'composicao', 'decisao', 'movimentacao_sem_bola', 'trabalho_equipe', 'visao_jogo', 'aceleracao'],
        'preferred': ['antecipacao', 'criatividade', 'intensidade_trabalho', 'agilidade', 'velocidade_maxima', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Ponta',
        'categoria': 'in'
    },
    'Ponta': {
        'key': ['cruzamentos', 'drible', 'tecnica', 'trabalho_equipe', 'aceleracao', 'agilidade', 'velocidade_maxima'],
        'preferred': ['primeiro_controle', 'passe', 'antecipacao', 'criatividade', 'movimentacao_sem_bola', 'intensidade_trabalho', 'equilibrio', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Ponta',
        'categoria': 'in'
    },

    # ==================== MEIAS-ATACANTES ====================
    'Meia-Atacante': {
        'key': ['primeiro_controle', 'chutes_longe', 'passe', 'tecnica', 'composicao', 'criatividade', 'movimentacao_sem_bola'],
        'preferred': ['cruzamentos', 'drible', 'finalizacao', 'antecipacao', 'decisao', 'visao_jogo', 'aceleracao', 'agilidade'],
        'unnecessary': [],
        'posicao': 'Meia-Atacante',
        'categoria': 'in'
    },
    'Meia de Corredor': {
        'key': ['cruzamentos', 'primeiro_controle', 'passe', 'tecnica', 'composicao', 'movimentacao_sem_bola', 'intensidade_trabalho', 'aceleracao'],
        'preferred': ['drible', 'chutes_longe', 'antecipacao', 'decisao', 'criatividade', 'visao_jogo', 'agilidade', 'velocidade_maxima', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Meia-Atacante',
        'categoria': 'in'
    },
    'Livre (Free Role)': {
        'key': ['drible', 'primeiro_controle', 'chutes_longe', 'passe', 'tecnica', 'composicao', 'criatividade', 'movimentacao_sem_bola', 'visao_jogo'],
        'preferred': ['cruzamentos', 'finalizacao', 'antecipacao', 'decisao', 'aceleracao', 'agilidade'],
        'unnecessary': [],
        'posicao': 'Meia-Atacante',
        'categoria': 'in'
    },
    'Segundo Atacante': {
        'key': ['finalizacao', 'primeiro_controle', 'antecipacao', 'composicao', 'movimentacao_sem_bola', 'aceleracao'],
        'preferred': ['drible', 'chutes_longe', 'passe', 'tecnica', 'concentracao', 'decisao', 'intensidade_trabalho', 'agilidade', 'velocidade_maxima', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Atacante',
        'categoria': 'in'
    },

    # ==================== PONTAS / ATACANTES LATERAIS ====================
    'Atacante Largo': {
        'key': ['drible', 'primeiro_controle', 'tecnica', 'antecipacao', 'movimentacao_sem_bola', 'aceleracao', 'agilidade', 'velocidade_maxima'],
        'preferred': ['cruzamentos', 'finalizacao', 'passe', 'composicao', 'criatividade', 'intensidade_trabalho', 'equilibrio', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Ponta',
        'categoria': 'in'
    },
    'Ponta de Infiltração': {
        'key': ['drible', 'primeiro_controle', 'tecnica', 'antecipacao', 'composicao', 'movimentacao_sem_bola', 'aceleracao', 'agilidade'],
        'preferred': ['cruzamentos', 'finalizacao', 'chutes_longe', 'passe', 'criatividade', 'visao_jogo', 'intensidade_trabalho', 'equilibrio', 'velocidade_maxima', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Ponta',
        'categoria': 'in'
    },

    # ==================== CENTROAVANTES ====================
    'Centroavante': {
        'key': ['finalizacao', 'primeiro_controle', 'cabecada', 'tecnica', 'composicao', 'movimentacao_sem_bola', 'aceleracao', 'forca_fisica'],
        'preferred': ['drible', 'passe', 'antecipacao', 'decisao', 'agilidade', 'equilibrio', 'altura_salto', 'velocidade_maxima'],
        'unnecessary': [],
        'posicao': 'Atacante',
        'categoria': 'in'
    },
    'Atacante de Corredor': {
        'key': ['drible', 'finalizacao', 'primeiro_controle', 'tecnica', 'composicao', 'movimentacao_sem_bola', 'intensidade_trabalho', 'aceleracao'],
        'preferred': ['cruzamentos', 'cabecada', 'passe', 'antecipacao', 'decisao', 'agilidade', 'equilibrio', 'velocidade_maxima', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Atacante',
        'categoria': 'in'
    },
    'Atacante Recuado': {
        'key': ['finalizacao', 'primeiro_controle', 'tecnica', 'composicao', 'movimentacao_sem_bola', 'forca_fisica'],
        'preferred': ['drible', 'passe', 'antecipacao', 'decisao', 'trabalho_equipe', 'visao_jogo', 'equilibrio'],
        'unnecessary': [],
        'posicao': 'Atacante',
        'categoria': 'in'
    },
    'Falso 9': {
        'key': ['drible', 'primeiro_controle', 'passe', 'tecnica', 'composicao', 'decisao', 'movimentacao_sem_bola', 'trabalho_equipe', 'visao_jogo', 'aceleracao'],
        'preferred': ['finalizacao', 'antecipacao', 'criatividade', 'agilidade', 'equilibrio'],
        'unnecessary': [],
        'posicao': 'Atacante',
        'categoria': 'in'
    },
    'Caçador (Poacher)': {
        'key': ['finalizacao', 'cabecada', 'antecipacao', 'composicao', 'concentracao', 'movimentacao_sem_bola', 'aceleracao'],
        'preferred': ['primeiro_controle', 'tecnica', 'decisao', 'equilibrio'],
        'unnecessary': [],
        'posicao': 'Atacante',
        'categoria': 'in'
    },
    'Centroavante Alvo': {
        'key': ['finalizacao', 'cabecada', 'agressividade', 'coragem', 'composicao', 'movimentacao_sem_bola', 'equilibrio', 'altura_salto', 'forca_fisica'],
        'preferred': ['primeiro_controle', 'antecipacao', 'decisao', 'trabalho_equipe'],
        'unnecessary': [],
        'posicao': 'Atacante',
        'categoria': 'in'
    },
}

# ============================================================
# ROLES "OUT OF POSSESSION" (SEM BOLA)
# ============================================================
ROLES_OUT_POSSESSION = {
    # ==================== GOLEIROS ====================
    'Line-Holding Keeper': {
        'key': ['posicionamento', 'concentracao'],
        'preferred': ['antecipacao', 'decisao', 'comando_area'],
        'unnecessary': [],
        'posicao': 'Goleiro',
        'categoria': 'out'
    },
    'Sweeper Keeper': {
        'key': ['saida_gol', 'antecipacao', 'decisao'],
        'preferred': ['reflexos', 'agilidade', 'velocidade_maxima', 'um_contra_um_goleiro'],
        'unnecessary': [],
        'posicao': 'Goleiro',
        'categoria': 'out'
    },

    # ==================== ZAGUEIROS ====================
    'Covering Centre-Back': {
        'key': ['antecipacao', 'velocidade_maxima', 'marcacao'],
        'preferred': ['posicionamento', 'concentracao', 'decisao', 'desarme'],
        'unnecessary': [],
        'posicao': 'Zagueiro',
        'categoria': 'out'
    },
    'Stopping Centre-Back': {
        'key': ['agressividade', 'desarme', 'forca_fisica'],
        'preferred': ['marcacao', 'antecipacao', 'coragem', 'posicionamento', 'forca_fisica'],
        'unnecessary': [],
        'posicao': 'Zagueiro',
        'categoria': 'out'
    },
    'Covering Wide Centre-Back': {
        'key': ['antecipacao', 'velocidade_maxima', 'marcacao'],
        'preferred': ['posicionamento', 'concentracao', 'aceleracao', 'agilidade'],
        'unnecessary': [],
        'posicao': 'Zagueiro',
        'categoria': 'out'
    },
    'Stopping Wide Centre-Back': {
        'key': ['agressividade', 'desarme', 'forca_fisica'],
        'preferred': ['marcacao', 'antecipacao', 'coragem', 'posicionamento', 'velocidade_maxima'],
        'unnecessary': [],
        'posicao': 'Zagueiro',
        'categoria': 'out'
    },

    # ==================== LATERAIS ====================
    'Holding Full-Back': {
        'key': ['posicionamento', 'concentracao', 'marcacao'],
        'preferred': ['desarme', 'antecipacao', 'trabalho_equipe'],
        'unnecessary': [],
        'posicao': 'Lateral',
        'categoria': 'out'
    },
    'Pressing Full-Back': {
        'key': ['agressividade', 'intensidade_trabalho', 'antecipacao'],
        'preferred': ['desarme', 'marcacao', 'resistencia', 'velocidade_maxima'],
        'unnecessary': [],
        'posicao': 'Lateral',
        'categoria': 'out'
    },
    'Holding Wing-Back': {
        'key': ['posicionamento', 'concentracao', 'marcacao'],
        'preferred': ['desarme', 'antecipacao', 'trabalho_equipe', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Lateral',
        'categoria': 'out'
    },
    'Pressing Wing-Back': {
        'key': ['agressividade', 'intensidade_trabalho', 'antecipacao'],
        'preferred': ['desarme', 'marcacao', 'resistencia', 'velocidade_maxima', 'aceleracao'],
        'unnecessary': [],
        'posicao': 'Lateral',
        'categoria': 'out'
    },

    # ==================== VOLANTES ====================
    'Dropping Defensive Midfielder': {
        'key': ['posicionamento', 'decisao', 'antecipacao'],
        'preferred': ['concentracao', 'desarme', 'marcacao', 'trabalho_equipe'],
        'unnecessary': [],
        'posicao': 'Volante',
        'categoria': 'out'
    },
    'Pressing Defensive Midfielder': {
        'key': ['agressividade', 'intensidade_trabalho', 'antecipacao'],
        'preferred': ['desarme', 'marcacao', 'resistencia', 'forca_fisica'],
        'unnecessary': [],
        'posicao': 'Volante',
        'categoria': 'out'
    },
    'Screening Defensive Midfielder': {
        'key': ['posicionamento', 'concentracao', 'marcacao'],
        'preferred': ['antecipacao', 'desarme', 'decisao', 'trabalho_equipe'],
        'unnecessary': [],
        'posicao': 'Volante',
        'categoria': 'out'
    },
    'Wide Covering Defensive Midfielder': {
        'key': ['antecipacao', 'velocidade_maxima', 'intensidade_trabalho'],
        'preferred': ['desarme', 'marcacao', 'posicionamento', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Volante',
        'categoria': 'out'
    },

    # ==================== MEIAS CENTRAIS ====================
    'Pressing Central Midfielder': {
        'key': ['agressividade', 'intensidade_trabalho', 'antecipacao'],
        'preferred': ['desarme', 'marcacao', 'resistencia', 'trabalho_equipe'],
        'unnecessary': [],
        'posicao': 'Meio-Campo',
        'categoria': 'out'
    },
    'Screening Central Midfielder': {
        'key': ['posicionamento', 'concentracao', 'marcacao'],
        'preferred': ['antecipacao', 'desarme', 'decisao', 'trabalho_equipe'],
        'unnecessary': [],
        'posicao': 'Meio-Campo',
        'categoria': 'out'
    },
    'Wide Covering Central Midfielder': {
        'key': ['antecipacao', 'velocidade_maxima', 'intensidade_trabalho'],
        'preferred': ['desarme', 'marcacao', 'posicionamento', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Meio-Campo',
        'categoria': 'out'
    },

    # ==================== MEIAS LATERAIS ====================
    'Tracking Wide Midfielder': {
        'key': ['marcacao', 'intensidade_trabalho', 'resistencia'],
        'preferred': ['desarme', 'antecipacao', 'posicionamento', 'velocidade_maxima'],
        'unnecessary': [],
        'posicao': 'Meio-Campo',
        'categoria': 'out'
    },
    'Wide Outlet Wide Midfielder': {
        'key': ['movimentacao_sem_bola', 'velocidade_maxima', 'antecipacao'],
        'preferred': ['aceleracao', 'agilidade', 'intensidade_trabalho', 'posicionamento'],
        'unnecessary': [],
        'posicao': 'Meio-Campo',
        'categoria': 'out'
    },

    # ==================== MEIAS-ATACANTES ====================
    'Central Outlet Attacking Midfielder': {
        'key': ['movimentacao_sem_bola', 'decisao', 'antecipacao'],
        'preferred': ['velocidade_maxima', 'aceleracao', 'posicionamento'],
        'unnecessary': [],
        'posicao': 'Meia-Atacante',
        'categoria': 'out'
    },
    'Splitting Outlet Attacking Midfielder': {
        'key': ['movimentacao_sem_bola', 'velocidade_maxima', 'antecipacao'],
        'preferred': ['decisao', 'aceleracao', 'agilidade', 'finalizacao'],
        'unnecessary': [],
        'posicao': 'Meia-Atacante',
        'categoria': 'out'
    },
    'Tracking Attacking Midfielder': {
        'key': ['marcacao', 'intensidade_trabalho', 'resistencia'],
        'preferred': ['desarme', 'antecipacao', 'posicionamento', 'trabalho_equipe'],
        'unnecessary': [],
        'posicao': 'Meia-Atacante',
        'categoria': 'out'
    },

    # ==================== PONTAS ====================
    'Inside Outlet Winger': {
        'key': ['movimentacao_sem_bola', 'decisao', 'antecipacao'],
        'preferred': ['velocidade_maxima', 'drible', 'finalizacao', 'aceleracao'],
        'unnecessary': [],
        'posicao': 'Ponta',
        'categoria': 'out'
    },
    'Tracking Winger': {
        'key': ['marcacao', 'intensidade_trabalho', 'resistencia'],
        'preferred': ['desarme', 'antecipacao', 'posicionamento', 'velocidade_maxima'],
        'unnecessary': [],
        'posicao': 'Ponta',
        'categoria': 'out'
    },
    'Wide Outlet Winger': {
        'key': ['movimentacao_sem_bola', 'velocidade_maxima', 'antecipacao'],
        'preferred': ['aceleracao', 'agilidade', 'drible', 'cruzamentos'],
        'unnecessary': [],
        'posicao': 'Ponta',
        'categoria': 'out'
    },

    # ==================== ATACANTES ====================
    'Central Outlet Centre Forward': {
        'key': ['movimentacao_sem_bola', 'decisao', 'antecipacao'],
        'preferred': ['finalizacao', 'velocidade_maxima', 'aceleracao', 'posicionamento'],
        'unnecessary': [],
        'posicao': 'Atacante',
        'categoria': 'out'
    },
    'Splitting Outlet Centre Forward': {
        'key': ['movimentacao_sem_bola', 'velocidade_maxima', 'antecipacao'],
        'preferred': ['finalizacao', 'aceleracao', 'agilidade', 'drible'],
        'unnecessary': [],
        'posicao': 'Atacante',
        'categoria': 'out'
    },
    'Tracking Centre Forward': {
        'key': ['marcacao', 'intensidade_trabalho', 'resistencia'],
        'preferred': ['desarme', 'antecipacao', 'posicionamento', 'trabalho_equipe', 'forca_fisica'],
        'unnecessary': [],
        'posicao': 'Atacante',
        'categoria': 'out'
    },
}

# ============================================================
# UNIFICAÇÃO DOS DICIONÁRIOS
# ============================================================
ROLES_FM26_PT = {**ROLES_IN_POSSESSION, **ROLES_OUT_POSSESSION}

# ============================================================
# MAPEAMENTO DE CATEGORIA (IN/OUT) PARA CADA ROLE
# ============================================================
CATEGORIA_ROLE = {role: data['categoria'] for role, data in ROLES_FM26_PT.items()}

# ============================================================
# TRADUÇÃO OFICIAL PARA EXIBIÇÃO EM PORTUGUÊS
# ============================================================
TRADUCAO_ROLES_PT = {
    # GOLEIROS
    'Goleiro': 'Goleiro',
    'Goleiro de Bola': 'Goleiro com Bola',
    'Goleiro Caxias': 'Goleiro Caxias',
    'Line-Holding Keeper': 'Goleiro de Linha',
    'Sweeper Keeper': 'Goleiro Líbero',
    # ZAGUEIROS
    'Zagueiro Central': 'Zagueiro Central',
    'Zagueiro de Bola': 'Zagueiro com Bola',
    'Zagueiro Caxias': 'Zagueiro Caxias',
    'Zagueiro Largo': 'Zagueiro Descaído',
    'Zagueiro Avançado': 'Zagueiro Avançado',
    'Zagueiro Sobreposição': 'Zagueiro de Dobra',
    'Covering Centre-Back': 'Zagueiro de Cobertura',
    'Stopping Centre-Back': 'Zagueiro de Contenção',
    'Covering Wide Centre-Back': 'Zagueiro Descaído de Cobertura',
    'Stopping Wide Centre-Back': 'Zagueiro Descaído de Contenção',
    # LATERAIS E ALAS
    'Lateral': 'Lateral',
    'Lateral Interno': 'Lateral Invertido',
    'Ala': 'Ala',
    'Ala Avançado': 'Ala Avançado',
    'Ala Interno': 'Ala Invertido',
    'Ala Armador': 'Ala Construtor',
    'Holding Full-Back': 'Lateral de Cobertura',
    'Pressing Full-Back': 'Lateral de Pressão',
    'Holding Wing-Back': 'Ala de Cobertura',
    'Pressing Wing-Back': 'Ala de Pressão',
    # VOLANTES
    'Volante': 'Volante',
    'Meio-Volante': 'Meio-Volante',
    'Armador Recuado': 'Armador Recuado',
    'Dropping Defensive Midfielder': 'Volante Recuado',
    'Pressing Defensive Midfielder': 'Volante de Pressão',
    'Screening Defensive Midfielder': 'Volante de Cobertura',
    'Wide Covering Defensive Midfielder': 'Volante Descaído de Cobertura',
    # MEIAS CENTRAIS
    'Meia Central': 'Meia Central',
    'Meia Armador': 'Meia Armador',
    'Meia Central Largo': 'Meia Central Descaído',
    'Meia Largo': 'Meia de Ala',
    'Meio-Campo Box-to-Box': 'Meia Box-to-Box',
    'Meio-Campo Box-to-Box Armador': 'Meia Box-to-Box Armador',
    'Pressing Central Midfielder': 'Meia Central de Pressão',
    'Screening Central Midfielder': 'Meia Central de Cobertura',
    'Wide Covering Central Midfielder': 'Meia Central Descaído de Cobertura',
    'Tracking Wide Midfielder': 'Meia de Ala de Cobertura',
    'Wide Outlet Wide Midfielder': 'Meia de Ala de Saída',
    # MEIAS-ATACANTES
    'Meia-Atacante': 'Meia-Atacante',
    'Meia de Corredor': 'Meia de Corredor',
    'Livre (Free Role)': 'Função Livre',
    'Meia Armador Avançado': 'Meia Armador Avançado',
    'Central Outlet Attacking Midfielder': 'Meia-Atacante de Saída',
    'Splitting Outlet Attacking Midfielder': 'Meia-Atacante de Ruptura',
    'Tracking Attacking Midfielder': 'Meia-Atacante de Marcação',
    # PONTAS
    'Ponta': 'Ponta',
    'Ponta Interior': 'Ponta Invertida',
    'Ponta Armador': 'Ponta Construtor',
    'Atacante Largo': 'Atacante Descaído',
    'Ponta de Infiltração': 'Ponta de Infiltração',
    'Inside Outlet Winger': 'Ponta de Saída Interior',
    'Tracking Winger': 'Ponta de Marcação',
    'Wide Outlet Winger': 'Ponta de Saída Larga',
    # ATACANTES
    'Centroavante': 'Centroavante',
    'Atacante de Corredor': 'Atacante de Corredor',
    'Atacante Recuado': 'Atacante Recuado',
    'Falso 9': 'Falso 9',
    'Caçador (Poacher)': 'Caçador (Poacher)',
    'Centroavante Alvo': 'Centroavante Alvo',
    'Segundo Atacante': 'Segundo Atacante',
    'Central Outlet Centre Forward': 'Centroavante de Saída',
    'Splitting Outlet Centre Forward': 'Centroavante de Ruptura',
    'Tracking Centre Forward': 'Centroavante de Marcação',
}

# ============================================================
# COMPATIBILIDADE: POSIÇÃO -> ROLES PERMITIDAS
# ============================================================
COMPATIBILIDADE_POSICAO = {
    'Goleiro': ['Goleiro', 'Goleiro de Bola', 'Goleiro Caxias', 'Line-Holding Keeper', 'Sweeper Keeper'],
    'Zagueiro': [
        'Zagueiro Central', 'Zagueiro de Bola', 'Zagueiro Caxias', 'Zagueiro Largo',
        'Zagueiro Avançado', 'Zagueiro Sobreposição', 'Covering Centre-Back', 'Stopping Centre-Back',
        'Covering Wide Centre-Back', 'Stopping Wide Centre-Back'
    ],
    'Lateral': [
        'Lateral', 'Lateral Interno', 'Ala', 'Ala Avançado', 'Ala Interno', 'Ala Armador',
        'Holding Full-Back', 'Pressing Full-Back', 'Holding Wing-Back', 'Pressing Wing-Back'
    ],
    'Volante': [
        'Volante', 'Meio-Volante', 'Armador Recuado',
        'Dropping Defensive Midfielder', 'Pressing Defensive Midfielder',
        'Screening Defensive Midfielder', 'Wide Covering Defensive Midfielder'
    ],
    'Meio-Campo': [
        'Meia Central', 'Meia Armador', 'Meia Central Largo', 'Meio-Campo Box-to-Box',
        'Meio-Campo Box-to-Box Armador', 'Meia Largo',
        'Pressing Central Midfielder', 'Screening Central Midfielder',
        'Wide Covering Central Midfielder', 'Tracking Wide Midfielder', 'Wide Outlet Wide Midfielder'
    ],
    'Meia-Atacante': [
        'Meia-Atacante', 'Meia de Corredor', 'Livre (Free Role)', 'Meia Armador Avançado',
        'Central Outlet Attacking Midfielder', 'Splitting Outlet Attacking Midfielder',
        'Tracking Attacking Midfielder'
    ],
    'Ponta': [
        'Ponta', 'Ponta Interior', 'Ponta Armador', 'Atacante Largo', 'Ponta de Infiltração',
        'Inside Outlet Winger', 'Tracking Winger', 'Wide Outlet Winger'
    ],
    'Atacante': [
        'Centroavante', 'Atacante de Corredor', 'Atacante Recuado', 'Falso 9', 'Caçador (Poacher)',
        'Centroavante Alvo', 'Segundo Atacante',
        'Central Outlet Centre Forward', 'Splitting Outlet Centre Forward', 'Tracking Centre Forward'
    ]
}

# ============================================================
# FUNÇÃO HELPER PARA OBTER ROLES POR POSIÇÃO
# ============================================================
def get_roles_by_posicao(posicao: str, categoria: str = None) -> list:
    """Retorna lista de roles compatíveis com a posição, opcionalmente filtradas por categoria (in/out)."""
    roles = COMPATIBILIDADE_POSICAO.get(posicao, [])
    if categoria:
        roles = [r for r in roles if CATEGORIA_ROLE.get(r) == categoria]
    return roles

def get_roles_by_categoria(categoria: str) -> list:
    """Retorna todas as roles de uma categoria (in/out)."""
    return [role for role, cat in CATEGORIA_ROLE.items() if cat == categoria]

def get_role_traduzida(role: str) -> str:
    """Retorna a tradução da role para exibição."""
    return TRADUCAO_ROLES_PT.get(role, role)

# ============================================================
# ATRIBUTOS DE UMA ROLE (KEY, PREFERRED, UNNECESSARY)
# ============================================================
def get_role_attributes(role: str) -> dict:
    """Retorna os atributos (key, preferred, unnecessary) de uma role."""
    return ROLES_FM26_PT.get(role, {})