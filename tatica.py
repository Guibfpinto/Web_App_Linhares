# tatica.py
import pandas as pd
import numpy as np
from utils import mapear_nome_para_canonico, jogador_suspenso

# =============================================
# CONSTANTES: ATRIBUTOS FM26
# =============================================
ATRIBUTOS_FM26 = [
    'escanteios', 'cruzamentos', 'drible', 'finalizacao', 'primeiro_controle',
    'cobranca_faltas', 'cabecada', 'chutes_longe', 'arremessos_laterais',
    'marcacao', 'passe', 'cobranca_penaltis', 'desarme', 'tecnica',
    'agressividade', 'antecipacao', 'coragem', 'composicao', 'concentracao',
    'decisao', 'determinacao', 'criatividade', 'lideranca', 'movimentacao_sem_bola',
    'posicionamento', 'trabalho_equipe', 'visao_jogo', 'intensidade_trabalho',
    'aceleracao', 'agilidade', 'equilibrio', 'altura_salto', 'condicao_fisica_natural',
    'velocidade_maxima', 'resistencia', 'forca_fisica', 'reflexos', 'jogo_aereo_goleiro',
    'defesas_goleiro', 'comando_area', 'comunicacao_goleiro', 'chutes_goleiro',
    'um_contra_um_goleiro', 'saida_gol', 'tendencia_socar', 'arremessos_goleiro',
    'excentricidade', 'consistencia', 'jogo_sujo', 'jogos_importantes',
    'propensao_lesao', 'versatilidade', 'adaptabilidade', 'ambicao', 'lealdade',
    'pressao', 'profissionalismo', 'esportividade', 'temperamento', 'controversia'
]

# =============================================
# ROLES FM26 (IN POSSESSION)
# =============================================
ROLES_FM26_PT = {
    'Goleiro': {
        'key': ['jogo_aereo_goleiro', 'comando_area', 'comunicacao_goleiro', 'defesas_goleiro', 'reflexos', 'agilidade', 'concentracao', 'posicionamento'],
        'preferred': ['chutes_goleiro', 'um_contra_um_goleiro', 'arremessos_goleiro', 'antecipacao', 'decisao'],
        'unnecessary': ['excentricidade'],
        'posicao': 'Goleiro'
    },
    'Goleiro de Bola': {
        'key': ['jogo_aereo_goleiro', 'comando_area', 'comunicacao_goleiro', 'defesas_goleiro', 'chutes_goleiro', 'reflexos', 'agilidade', 'concentracao', 'posicionamento'],
        'preferred': ['excentricidade', 'um_contra_um_goleiro', 'arremessos_goleiro', 'antecipacao', 'composicao', 'decisao', 'passe'],
        'unnecessary': [],
        'posicao': 'Goleiro'
    },
    'Goleiro Caxias': {
        'key': ['jogo_aereo_goleiro', 'comando_area', 'comunicacao_goleiro', 'defesas_goleiro', 'reflexos', 'agilidade', 'concentracao', 'posicionamento'],
        'preferred': ['um_contra_um_goleiro', 'antecipacao', 'decisao'],
        'unnecessary': ['excentricidade', 'passe'],
        'posicao': 'Goleiro'
    },
    'Zagueiro Central': {
        'key': ['cabecada', 'marcacao', 'desarme', 'antecipacao', 'posicionamento', 'altura_salto', 'forca_fisica'],
        'preferred': ['agressividade', 'coragem', 'composicao', 'concentracao', 'decisao', 'velocidade_maxima'],
        'unnecessary': ['passe'],
        'posicao': 'Zagueiro'
    },
    'Zagueiro de Bola': {
        'key': ['cabecada', 'marcacao', 'passe', 'desarme', 'antecipacao', 'composicao', 'posicionamento', 'altura_salto', 'forca_fisica'],
        'preferred': ['primeiro_controle', 'tecnica', 'agressividade', 'coragem', 'concentracao', 'decisao', 'visao_jogo', 'velocidade_maxima'],
        'unnecessary': [],
        'posicao': 'Zagueiro'
    },
    'Zagueiro Caxias': {
        'key': ['cabecada', 'marcacao', 'desarme', 'antecipacao', 'posicionamento', 'altura_salto', 'forca_fisica'],
        'preferred': ['agressividade', 'coragem', 'concentracao', 'velocidade_maxima'],
        'unnecessary': ['passe', 'composicao'],
        'posicao': 'Zagueiro'
    },
    'Zagueiro Largo': {
        'key': ['cabecada', 'marcacao', 'desarme', 'antecipacao', 'posicionamento', 'altura_salto', 'forca_fisica'],
        'preferred': ['drible', 'agressividade', 'coragem', 'composicao', 'concentracao', 'decisao', 'intensidade_trabalho', 'aceleracao', 'agilidade', 'velocidade_maxima', 'resistencia'],
        'unnecessary': ['passe'],
        'posicao': 'Zagueiro'
    },
    'Zagueiro Avançado': {
        'key': ['cabecada', 'marcacao', 'passe', 'desarme', 'tecnica', 'antecipacao', 'composicao', 'decisao', 'posicionamento', 'trabalho_equipe', 'altura_salto', 'forca_fisica'],
        'preferred': ['drible', 'primeiro_controle', 'agressividade', 'coragem', 'concentracao', 'visao_jogo', 'velocidade_maxima', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Zagueiro'
    },
    'Zagueiro Sobreposição': {
        'key': ['cruzamentos', 'cabecada', 'marcacao', 'desarme', 'antecipacao', 'intensidade_trabalho', 'altura_salto', 'velocidade_maxima', 'resistencia', 'forca_fisica'],
        'preferred': ['drible', 'tecnica', 'agressividade', 'coragem', 'composicao', 'concentracao', 'decisao', 'movimentacao_sem_bola', 'posicionamento', 'aceleracao', 'agilidade'],
        'unnecessary': [],
        'posicao': 'Zagueiro'
    },
    'Lateral': {
        'key': ['marcacao', 'desarme', 'antecipacao', 'concentracao', 'posicionamento', 'trabalho_equipe', 'aceleracao'],
        'preferred': ['cruzamentos', 'drible', 'passe', 'tecnica', 'decisao', 'intensidade_trabalho', 'agilidade', 'velocidade_maxima', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Lateral'
    },
    'Lateral Interno': {
        'key': ['cabecada', 'marcacao', 'desarme', 'antecipacao', 'posicionamento', 'forca_fisica'],
        'preferred': ['drible', 'agressividade', 'coragem', 'composicao', 'concentracao', 'decisao', 'intensidade_trabalho', 'aceleracao', 'agilidade', 'altura_salto', 'velocidade_maxima', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Lateral'
    },
    'Ala': {
        'key': ['cruzamentos', 'marcacao', 'desarme', 'trabalho_equipe', 'intensidade_trabalho', 'aceleracao', 'velocidade_maxima', 'resistencia'],
        'preferred': ['drible', 'primeiro_controle', 'passe', 'tecnica', 'antecipacao', 'concentracao', 'decisao', 'movimentacao_sem_bola', 'posicionamento', 'agilidade', 'equilibrio'],
        'unnecessary': [],
        'posicao': 'Ala'
    },
    'Ala Avançado': {
        'key': ['cruzamentos', 'drible', 'tecnica', 'movimentacao_sem_bola', 'trabalho_equipe', 'intensidade_trabalho', 'aceleracao', 'agilidade', 'velocidade_maxima', 'resistencia'],
        'preferred': ['primeiro_controle', 'marcacao', 'passe', 'desarme', 'antecipacao', 'decisao', 'criatividade', 'posicionamento', 'equilibrio'],
        'unnecessary': [],
        'posicao': 'Ala'
    },
    'Ala Interno': {
        'key': ['passe', 'desarme', 'antecipacao', 'composicao', 'decisao', 'posicionamento', 'trabalho_equipe', 'aceleracao'],
        'preferred': ['primeiro_controle', 'marcacao', 'tecnica', 'concentracao', 'intensidade_trabalho', 'agilidade', 'velocidade_maxima', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Ala'
    },
    'Ala Armador': {
        'key': ['primeiro_controle', 'passe', 'desarme', 'tecnica', 'composicao', 'decisao', 'posicionamento', 'trabalho_equipe', 'visao_jogo', 'aceleracao'],
        'preferred': ['cruzamentos', 'drible', 'marcacao', 'antecipacao', 'concentracao', 'movimentacao_sem_bola', 'intensidade_trabalho', 'agilidade', 'velocidade_maxima', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Ala'
    },
    'Volante': {
        'key': ['desarme', 'antecipacao', 'concentracao', 'posicionamento', 'trabalho_equipe'],
        'preferred': ['primeiro_controle', 'marcacao', 'passe', 'agressividade', 'composicao', 'decisao', 'intensidade_trabalho', 'resistencia', 'forca_fisica'],
        'unnecessary': [],
        'posicao': 'Volante'
    },
    'Meio-Campo Box-to-Box': {
        'key': ['passe', 'desarme', 'movimentacao_sem_bola', 'trabalho_equipe', 'intensidade_trabalho', 'resistencia'],
        'preferred': ['drible', 'finalizacao', 'primeiro_controle', 'chutes_longe', 'tecnica', 'agressividade', 'antecipacao', 'composicao', 'decisao', 'posicionamento', 'aceleracao', 'equilibrio', 'velocidade_maxima', 'forca_fisica'],
        'unnecessary': [],
        'posicao': 'Meio-Campo'
    },
    'Meio-Campo Box-to-Box Armador': {
        'key': ['primeiro_controle', 'passe', 'tecnica', 'composicao', 'decisao', 'movimentacao_sem_bola', 'trabalho_equipe', 'visao_jogo', 'intensidade_trabalho', 'resistencia'],
        'preferred': ['drible', 'marcacao', 'desarme', 'antecipacao', 'posicionamento', 'aceleracao', 'agilidade', 'equilibrio', 'velocidade_maxima'],
        'unnecessary': [],
        'posicao': 'Meio-Campo'
    },
    'Armador Recuado': {
        'key': ['primeiro_controle', 'passe', 'tecnica', 'composicao', 'decisao', 'movimentacao_sem_bola', 'trabalho_equipe', 'visao_jogo'],
        'preferred': ['marcacao', 'desarme', 'antecipacao', 'concentracao', 'posicionamento', 'intensidade_trabalho', 'equilibrio', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Meio-Campo'
    },
    'Meio-Volante': {
        'key': ['cabecada', 'marcacao', 'desarme', 'antecipacao', 'concentracao', 'posicionamento', 'trabalho_equipe', 'altura_salto', 'forca_fisica'],
        'preferred': ['primeiro_controle', 'passe', 'agressividade', 'coragem', 'composicao', 'decisao', 'intensidade_trabalho', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Volante'
    },
    'Meia Central': {
        'key': ['primeiro_controle', 'passe', 'desarme', 'decisao', 'trabalho_equipe'],
        'preferred': ['tecnica', 'antecipacao', 'composicao', 'concentracao', 'movimentacao_sem_bola', 'posicionamento', 'visao_jogo', 'intensidade_trabalho', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Meio-Campo'
    },
    'Meia Armador Avançado': {
        'key': ['primeiro_controle', 'passe', 'tecnica', 'composicao', 'decisao', 'movimentacao_sem_bola', 'trabalho_equipe', 'visao_jogo'],
        'preferred': ['cruzamentos', 'drible', 'antecipacao', 'criatividade', 'aceleracao', 'agilidade'],
        'unnecessary': [],
        'posicao': 'Meia-Atacante'
    },
    'Meia Armador': {
        'key': ['primeiro_controle', 'passe', 'tecnica', 'composicao', 'decisao', 'movimentacao_sem_bola', 'trabalho_equipe', 'visao_jogo'],
        'preferred': ['drible', 'desarme', 'antecipacao', 'criatividade', 'posicionamento', 'intensidade_trabalho', 'agilidade', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Meio-Campo'
    },
    'Meia Central Largo': {
        'key': ['primeiro_controle', 'passe', 'desarme', 'decisao', 'trabalho_equipe'],
        'preferred': ['cruzamentos', 'drible', 'tecnica', 'antecipacao', 'composicao', 'concentracao', 'movimentacao_sem_bola', 'posicionamento', 'visao_jogo', 'intensidade_trabalho', 'agilidade', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Meio-Campo'
    },
    'Meia Largo': {
        'key': ['cruzamentos', 'passe', 'tecnica', 'trabalho_equipe', 'intensidade_trabalho', 'velocidade_maxima', 'resistencia'],
        'preferred': ['drible', 'primeiro_controle', 'antecipacao', 'composicao', 'movimentacao_sem_bola', 'visao_jogo', 'aceleracao', 'agilidade'],
        'unnecessary': [],
        'posicao': 'Meio-Campo'
    },
    'Ponta Interior': {
        'key': ['drible', 'primeiro_controle', 'tecnica', 'composicao', 'trabalho_equipe', 'aceleracao', 'agilidade'],
        'preferred': ['cruzamentos', 'chutes_longe', 'passe', 'antecipacao', 'criatividade', 'movimentacao_sem_bola', 'visao_jogo', 'intensidade_trabalho', 'equilibrio', 'velocidade_maxima', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Ponta'
    },
    'Ponta Armador': {
        'key': ['cruzamentos', 'drible', 'primeiro_controle', 'passe', 'tecnica', 'composicao', 'decisao', 'movimentacao_sem_bola', 'trabalho_equipe', 'visao_jogo', 'aceleracao'],
        'preferred': ['antecipacao', 'criatividade', 'intensidade_trabalho', 'agilidade', 'velocidade_maxima', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Ponta'
    },
    'Ponta': {
        'key': ['cruzamentos', 'drible', 'tecnica', 'trabalho_equipe', 'aceleracao', 'agilidade', 'velocidade_maxima'],
        'preferred': ['primeiro_controle', 'passe', 'antecipacao', 'criatividade', 'movimentacao_sem_bola', 'intensidade_trabalho', 'equilibrio', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Ponta'
    },
    'Meia-Atacante': {
        'key': ['primeiro_controle', 'chutes_longe', 'passe', 'tecnica', 'composicao', 'criatividade', 'movimentacao_sem_bola'],
        'preferred': ['cruzamentos', 'drible', 'finalizacao', 'antecipacao', 'decisao', 'visao_jogo', 'aceleracao', 'agilidade'],
        'unnecessary': [],
        'posicao': 'Meia-Atacante'
    },
    'Meia de Corredor': {
        'key': ['cruzamentos', 'primeiro_controle', 'passe', 'tecnica', 'composicao', 'movimentacao_sem_bola', 'intensidade_trabalho', 'aceleracao'],
        'preferred': ['drible', 'chutes_longe', 'antecipacao', 'decisao', 'criatividade', 'visao_jogo', 'agilidade', 'velocidade_maxima', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Meia-Atacante'
    },
    'Livre (Free Role)': {
        'key': ['drible', 'primeiro_controle', 'chutes_longe', 'passe', 'tecnica', 'composicao', 'criatividade', 'movimentacao_sem_bola', 'visao_jogo'],
        'preferred': ['cruzamentos', 'finalizacao', 'antecipacao', 'decisao', 'aceleracao', 'agilidade'],
        'unnecessary': [],
        'posicao': 'Meia-Atacante'
    },
    'Segundo Atacante': {
        'key': ['finalizacao', 'primeiro_controle', 'antecipacao', 'composicao', 'movimentacao_sem_bola', 'aceleracao'],
        'preferred': ['drible', 'chutes_longe', 'passe', 'tecnica', 'concentracao', 'decisao', 'intensidade_trabalho', 'agilidade', 'velocidade_maxima', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Atacante'
    },
    'Atacante Largo': {
        'key': ['drible', 'primeiro_controle', 'tecnica', 'antecipacao', 'movimentacao_sem_bola', 'aceleracao', 'agilidade', 'velocidade_maxima'],
        'preferred': ['cruzamentos', 'finalizacao', 'passe', 'composicao', 'criatividade', 'intensidade_trabalho', 'equilibrio', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Ponta'
    },
    'Ponta de Infiltração': {
        'key': ['drible', 'primeiro_controle', 'tecnica', 'antecipacao', 'composicao', 'movimentacao_sem_bola', 'aceleracao', 'agilidade'],
        'preferred': ['cruzamentos', 'finalizacao', 'chutes_longe', 'passe', 'criatividade', 'visao_jogo', 'intensidade_trabalho', 'equilibrio', 'velocidade_maxima', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Ponta'
    },
    'Centroavante': {
        'key': ['finalizacao', 'primeiro_controle', 'cabecada', 'tecnica', 'composicao', 'movimentacao_sem_bola', 'aceleracao', 'forca_fisica'],
        'preferred': ['drible', 'passe', 'antecipacao', 'decisao', 'agilidade', 'equilibrio', 'altura_salto', 'velocidade_maxima'],
        'unnecessary': [],
        'posicao': 'Atacante'
    },
    'Atacante de Corredor': {
        'key': ['drible', 'finalizacao', 'primeiro_controle', 'tecnica', 'composicao', 'movimentacao_sem_bola', 'intensidade_trabalho', 'aceleracao'],
        'preferred': ['cruzamentos', 'cabecada', 'passe', 'antecipacao', 'decisao', 'agilidade', 'equilibrio', 'velocidade_maxima', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Atacante'
    },
    'Atacante Recuado': {
        'key': ['finalizacao', 'primeiro_controle', 'tecnica', 'composicao', 'movimentacao_sem_bola', 'forca_fisica'],
        'preferred': ['drible', 'passe', 'antecipacao', 'decisao', 'trabalho_equipe', 'visao_jogo', 'equilibrio'],
        'unnecessary': [],
        'posicao': 'Atacante'
    },
    'Falso 9': {
        'key': ['drible', 'primeiro_controle', 'passe', 'tecnica', 'composicao', 'decisao', 'movimentacao_sem_bola', 'trabalho_equipe', 'visao_jogo', 'aceleracao'],
        'preferred': ['finalizacao', 'antecipacao', 'criatividade', 'agilidade', 'equilibrio'],
        'unnecessary': [],
        'posicao': 'Atacante'
    },
    'Caçador (Poacher)': {
        'key': ['finalizacao', 'cabecada', 'antecipacao', 'composicao', 'concentracao', 'movimentacao_sem_bola', 'aceleracao'],
        'preferred': ['primeiro_controle', 'tecnica', 'decisao', 'equilibrio'],
        'unnecessary': [],
        'posicao': 'Atacante'
    },
    'Centroavante Alvo': {
        'key': ['finalizacao', 'cabecada', 'agressividade', 'coragem', 'composicao', 'movimentacao_sem_bola', 'equilibrio', 'altura_salto', 'forca_fisica'],
        'preferred': ['primeiro_controle', 'antecipacao', 'decisao', 'trabalho_equipe'],
        'unnecessary': [],
        'posicao': 'Atacante'
    }
}

# =============================================
# ROLES OUT OF POSSESSION
# =============================================
ROLES_OUT_POSSESSION = {
    'Line-Holding Keeper': {
        'key': ['posicionamento', 'concentracao'],
        'preferred': [],
        'unnecessary': [],
        'posicao': 'Goleiro'
    },
    'Sweeper Keeper': {
        'key': ['saida_gol', 'antecipacao', 'decisao'],
        'preferred': ['reflexos', 'agilidade', 'velocidade_maxima'],
        'unnecessary': [],
        'posicao': 'Goleiro'
    },
    'Covering Centre-Back': {
        'key': ['antecipacao', 'velocidade_maxima', 'marcacao'],
        'preferred': ['posicionamento', 'concentracao', 'decisao'],
        'unnecessary': [],
        'posicao': 'Zagueiro'
    },
    'Stopping Centre-Back': {
        'key': ['agressividade', 'desarme', 'forca_fisica'],
        'preferred': ['marcacao', 'antecipacao', 'coragem', 'posicionamento'],
        'unnecessary': [],
        'posicao': 'Zagueiro'
    },
    'Covering Wide Centre-Back': {
        'key': ['antecipacao', 'velocidade_maxima', 'marcacao'],
        'preferred': ['posicionamento', 'concentracao', 'aceleracao', 'agilidade'],
        'unnecessary': [],
        'posicao': 'Zagueiro'
    },
    'Stopping Wide Centre-Back': {
        'key': ['agressividade', 'desarme', 'forca_fisica'],
        'preferred': ['marcacao', 'antecipacao', 'coragem', 'posicionamento', 'velocidade_maxima'],
        'unnecessary': [],
        'posicao': 'Zagueiro'
    },
    'Holding Full-Back': {
        'key': ['posicionamento', 'concentracao', 'marcacao'],
        'preferred': ['desarme', 'antecipacao', 'trabalho_equipe'],
        'unnecessary': [],
        'posicao': 'Lateral'
    },
    'Pressing Full-Back': {
        'key': ['agressividade', 'intensidade_trabalho', 'antecipacao'],
        'preferred': ['desarme', 'marcacao', 'resistencia', 'velocidade_maxima'],
        'unnecessary': [],
        'posicao': 'Lateral'
    },
    'Holding Wing-Back': {
        'key': ['posicionamento', 'concentracao', 'marcacao'],
        'preferred': ['desarme', 'antecipacao', 'trabalho_equipe', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Lateral'
    },
    'Pressing Wing-Back': {
        'key': ['agressividade', 'intensidade_trabalho', 'antecipacao'],
        'preferred': ['desarme', 'marcacao', 'resistencia', 'velocidade_maxima', 'aceleracao'],
        'unnecessary': [],
        'posicao': 'Lateral'
    },
    'Dropping Defensive Midfielder': {
        'key': ['posicionamento', 'decisao', 'antecipacao'],
        'preferred': ['concentracao', 'desarme', 'marcacao', 'trabalho_equipe'],
        'unnecessary': [],
        'posicao': 'Volante'
    },
    'Pressing Defensive Midfielder': {
        'key': ['agressividade', 'intensidade_trabalho', 'antecipacao'],
        'preferred': ['desarme', 'marcacao', 'resistencia', 'forca_fisica'],
        'unnecessary': [],
        'posicao': 'Volante'
    },
    'Screening Defensive Midfielder': {
        'key': ['posicionamento', 'concentracao', 'marcacao'],
        'preferred': ['antecipacao', 'desarme', 'decisao', 'trabalho_equipe'],
        'unnecessary': [],
        'posicao': 'Volante'
    },
    'Wide Covering Defensive Midfielder': {
        'key': ['antecipacao', 'velocidade_maxima', 'intensidade_trabalho'],
        'preferred': ['desarme', 'marcacao', 'posicionamento', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Volante'
    },
    'Pressing Central Midfielder': {
        'key': ['agressividade', 'intensidade_trabalho', 'antecipacao'],
        'preferred': ['desarme', 'marcacao', 'resistencia', 'trabalho_equipe'],
        'unnecessary': [],
        'posicao': 'Meio-Campo'
    },
    'Screening Central Midfielder': {
        'key': ['posicionamento', 'concentracao', 'marcacao'],
        'preferred': ['antecipacao', 'desarme', 'decisao', 'trabalho_equipe'],
        'unnecessary': [],
        'posicao': 'Meio-Campo'
    },
    'Wide Covering Central Midfielder': {
        'key': ['antecipacao', 'velocidade_maxima', 'intensidade_trabalho'],
        'preferred': ['desarme', 'marcacao', 'posicionamento', 'resistencia'],
        'unnecessary': [],
        'posicao': 'Meio-Campo'
    },
    'Tracking Wide Midfielder': {
        'key': ['marcacao', 'intensidade_trabalho', 'resistencia'],
        'preferred': ['desarme', 'antecipacao', 'posicionamento', 'velocidade_maxima'],
        'unnecessary': [],
        'posicao': 'Meio-Campo'
    },
    'Wide Outlet Wide Midfielder': {
        'key': ['movimentacao_sem_bola', 'velocidade_maxima', 'antecipacao'],
        'preferred': ['aceleracao', 'agilidade', 'intensidade_trabalho', 'posicionamento'],
        'unnecessary': [],
        'posicao': 'Meio-Campo'
    },
    'Central Outlet Attacking Midfielder': {
        'key': ['movimentacao_sem_bola', 'decisao', 'antecipacao'],
        'preferred': ['velocidade_maxima', 'aceleracao', 'posicionamento'],
        'unnecessary': [],
        'posicao': 'Meia-Atacante'
    },
    'Splitting Outlet Attacking Midfielder': {
        'key': ['movimentacao_sem_bola', 'velocidade_maxima', 'antecipacao'],
        'preferred': ['decisao', 'aceleracao', 'agilidade', 'finalizacao'],
        'unnecessary': [],
        'posicao': 'Meia-Atacante'
    },
    'Tracking Attacking Midfielder': {
        'key': ['marcacao', 'intensidade_trabalho', 'resistencia'],
        'preferred': ['desarme', 'antecipacao', 'posicionamento', 'trabalho_equipe'],
        'unnecessary': [],
        'posicao': 'Meia-Atacante'
    },
    'Inside Outlet Winger': {
        'key': ['movimentacao_sem_bola', 'decisao', 'antecipacao'],
        'preferred': ['velocidade_maxima', 'drible', 'finalizacao', 'aceleracao'],
        'unnecessary': [],
        'posicao': 'Ponta'
    },
    'Tracking Winger': {
        'key': ['marcacao', 'intensidade_trabalho', 'resistencia'],
        'preferred': ['desarme', 'antecipacao', 'posicionamento', 'velocidade_maxima'],
        'unnecessary': [],
        'posicao': 'Ponta'
    },
    'Wide Outlet Winger': {
        'key': ['movimentacao_sem_bola', 'velocidade_maxima', 'antecipacao'],
        'preferred': ['aceleracao', 'agilidade', 'drible', 'cruzamentos'],
        'unnecessary': [],
        'posicao': 'Ponta'
    },
    'Central Outlet Centre Forward': {
        'key': ['movimentacao_sem_bola', 'decisao', 'antecipacao'],
        'preferred': ['finalizacao', 'velocidade_maxima', 'aceleracao', 'posicionamento'],
        'unnecessary': [],
        'posicao': 'Atacante'
    },
    'Splitting Outlet Centre Forward': {
        'key': ['movimentacao_sem_bola', 'velocidade_maxima', 'antecipacao'],
        'preferred': ['finalizacao', 'aceleracao', 'agilidade', 'drible'],
        'unnecessary': [],
        'posicao': 'Atacante'
    },
    'Tracking Centre Forward': {
        'key': ['marcacao', 'intensidade_trabalho', 'resistencia'],
        'preferred': ['desarme', 'antecipacao', 'posicionamento', 'trabalho_equipe', 'forca_fisica'],
        'unnecessary': [],
        'posicao': 'Atacante'
    }
}

# =============================================
# JUNTA AS ROLES E DEFINE CATEGORIAS
# =============================================
ROLES_FM26_PT.update(ROLES_OUT_POSSESSION)

CATEGORIA_ROLE = {}
for role in ROLES_FM26_PT:
    if role in ROLES_OUT_POSSESSION:
        CATEGORIA_ROLE[role] = 'out'
    else:
        CATEGORIA_ROLE[role] = 'in'

# =============================================
# MAPEAMENTO ROLE -> POSIÇÃO ESPERADA
# =============================================
role_to_pos = {
    'Goleiro': 'Goleiro',
    'Goleiro de Bola': 'Goleiro',
    'Goleiro Caxias': 'Goleiro',
    'Zagueiro Central': 'Zagueiro',
    'Zagueiro de Bola': 'Zagueiro',
    'Zagueiro Caxias': 'Zagueiro',
    'Zagueiro Largo': 'Zagueiro',
    'Zagueiro Avançado': 'Zagueiro',
    'Zagueiro Sobreposição': 'Zagueiro',
    'Lateral': 'Lateral',
    'Lateral Interno': 'Lateral',
    'Ala': 'Lateral',
    'Ala Avançado': 'Lateral',
    'Ala Interno': 'Lateral',
    'Ala Armador': 'Lateral',
    'Volante': 'Volante',
    'Meio-Volante': 'Volante',
    'Armador Recuado': 'Volante',
    'Meia Central': 'Meio-Campo',
    'Meia Armador': 'Meio-Campo',
    'Meia Central Largo': 'Meio-Campo',
    'Meio-Campo Box-to-Box': 'Meio-Campo',
    'Meio-Campo Box-to-Box Armador': 'Meio-Campo',
    'Meia Largo': 'Meio-Campo',
    'Meia-Atacante': 'Meia-Atacante',
    'Meia de Corredor': 'Meia-Atacante',
    'Livre (Free Role)': 'Meia-Atacante',
    'Meia Armador Avançado': 'Meia-Atacante',
    'Ponta': 'Ponta',
    'Ponta Interior': 'Ponta',
    'Ponta Armador': 'Ponta',
    'Atacante Largo': 'Atacante',
    'Ponta de Infiltração': 'Ponta',
    'Centroavante': 'Atacante',
    'Atacante de Corredor': 'Atacante',
    'Atacante Recuado': 'Atacante',
    'Falso 9': 'Atacante',
    'Caçador (Poacher)': 'Atacante',
    'Centroavante Alvo': 'Atacante',
    'Segundo Atacante': 'Atacante',
    'Line-Holding Keeper': 'Goleiro',
    'Sweeper Keeper': 'Goleiro',
    'Covering Centre-Back': 'Zagueiro',
    'Stopping Centre-Back': 'Zagueiro',
    'Covering Wide Centre-Back': 'Zagueiro',
    'Stopping Wide Centre-Back': 'Zagueiro',
    'Holding Full-Back': 'Lateral',
    'Pressing Full-Back': 'Lateral',
    'Holding Wing-Back': 'Lateral',
    'Pressing Wing-Back': 'Lateral',
    'Dropping Defensive Midfielder': 'Volante',
    'Pressing Defensive Midfielder': 'Volante',
    'Screening Defensive Midfielder': 'Volante',
    'Wide Covering Defensive Midfielder': 'Volante',
    'Pressing Central Midfielder': 'Meio-Campo',
    'Screening Central Midfielder': 'Meio-Campo',
    'Wide Covering Central Midfielder': 'Meio-Campo',
    'Tracking Wide Midfielder': 'Meio-Campo',
    'Wide Outlet Wide Midfielder': 'Meio-Campo',
    'Central Outlet Attacking Midfielder': 'Meia-Atacante',
    'Splitting Outlet Attacking Midfielder': 'Meia-Atacante',
    'Tracking Attacking Midfielder': 'Meia-Atacante',
    'Inside Outlet Winger': 'Ponta',
    'Tracking Winger': 'Ponta',
    'Wide Outlet Winger': 'Ponta',
    'Central Outlet Centre Forward': 'Atacante',
    'Splitting Outlet Centre Forward': 'Atacante',
    'Tracking Centre Forward': 'Atacante',
}

# =============================================
# TRADUÇÃO PARA PT-BR
# =============================================
TRADUCAO_ROLES_PT = {
    'Goleiro': 'Goleiro',
    'Goleiro de Bola': 'Goleiro com Bola',
    'Goleiro Caxias': 'Goleiro Caxias',
    'Line-Holding Keeper': 'Goleiro de Linha',
    'Sweeper Keeper': 'Goleiro Líbero',
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
    'Volante': 'Volante',
    'Meio-Volante': 'Meio-Volante',
    'Armador Recuado': 'Armador Recuado',
    'Dropping Defensive Midfielder': 'Volante Recuado',
    'Pressing Defensive Midfielder': 'Volante de Pressão',
    'Screening Defensive Midfielder': 'Volante de Cobertura',
    'Wide Covering Defensive Midfielder': 'Volante Descaído de Cobertura',
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
    'Meia-Atacante': 'Meia-Atacante',
    'Meia de Corredor': 'Meia de Corredor',
    'Livre (Free Role)': 'Função Livre',
    'Meia Armador Avançado': 'Meia Armador Avançado',
    'Central Outlet Attacking Midfielder': 'Meia-Atacante de Saída',
    'Splitting Outlet Attacking Midfielder': 'Meia-Atacante de Ruptura',
    'Tracking Attacking Midfielder': 'Meia-Atacante de Marcação',
    'Ponta': 'Ponta',
    'Ponta Interior': 'Ponta Invertida',
    'Ponta Armador': 'Ponta Construtor',
    'Atacante Largo': 'Atacante Descaído',
    'Ponta de Infiltração': 'Ponta de Infiltração',
    'Inside Outlet Winger': 'Ponta de Saída Interior',
    'Tracking Winger': 'Ponta de Marcação',
    'Wide Outlet Winger': 'Ponta de Saída Larga',
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

# =============================================
# POSIÇÃO ESPERADA PARA GRUPOS GENÉRICOS
# =============================================
POSICAO_ESPERADA_PARA_GRUPO = {
    'Goleiro': 'Goleiro',
    'Zagueiro': 'Defensor',
    'Lateral': 'Defensor',
    'Volante': 'Meio-Campista',
    'Meio-Campo': 'Meio-Campista',
    'Meia-Atacante': 'Meio-Campista',
    'Ponta': 'Atacante',
    'Atacante': 'Atacante',
}

GRUPO_POSICAO_JOGADOR = {
    'Goleiro': 'Goleiro',
    'Zagueiro': 'Defensor',
    'Lateral Direito': 'Defensor',
    'Lateral Esquerdo': 'Defensor',
    'Lateral': 'Defensor',
    'Volante': 'Meio-Campista',
    'Meia-Central': 'Meio-Campista',
    'Meia-Atacante': 'Meio-Campista',
    'Ponta Direita': 'Atacante',
    'Ponta Esquerda': 'Atacante',
    'Ponta': 'Atacante',
    'Centroavante': 'Atacante',
    'Segundo Atacante': 'Atacante',
    'Atacante': 'Atacante',
}

# =============================================
# FUNÇÕES DE CÁLCULO E SELEÇÃO
# =============================================
def calcular_score_role(row, role_name):
    if role_name not in ROLES_FM26_PT:
        return 0
    role = ROLES_FM26_PT[role_name]
    key_attrs = role['key']
    pref_attrs = role['preferred']
    score = 0
    total_weight = 0
    for attr in key_attrs:
        val = row.get(attr, np.nan)
        if pd.notna(val):
            score += val * 2
            total_weight += 2
    for attr in pref_attrs:
        val = row.get(attr, np.nan)
        if pd.notna(val):
            score += val * 1
            total_weight += 1
    return score / total_weight if total_weight > 0 else 0

def selecionar_time_por_funcoes(df, roles_list, excluir_lesionados=True, cartoes=None,
                                usar_rating_fallback=False,
                                priorizar_posicao=True,
                                priorizar_minutagem=True):
    if df is None or df.empty:
        return [], []
    df_copy = df.copy()
    if excluir_lesionados:
        df_copy = df_copy[~df_copy['lesionado']]
    if cartoes:
        df_copy = df_copy[~df_copy['nome_completo'].apply(
            lambda x: jogador_suspenso(mapear_nome_para_canonico(x), cartoes)
        )]
    max_starts = df_copy['total_starts'].max() if 'total_starts' in df_copy.columns else 1
    max_minutos = df_copy['minutos_totais_partidas'].max() if 'minutos_totais_partidas' in df_copy.columns else 1

    posicoes = []
    for role in roles_list:
        scores = []
        posicao_esperada = role_to_pos.get(role, 'Meio-Campo')
        for idx, row in df_copy.iterrows():
            if usar_rating_fallback:
                score_atributos = row.get('Rating_Geral_FM26', 0)
            else:
                score_atributos = calcular_score_role(row, role)
            bonus_posicao_norm = 0
            if priorizar_posicao:
                pos_principal = row.get('Posicao_Principal', '')
                pos_secundarias = row.get('Posicoes_Secundarias', [])
                if isinstance(pos_secundarias, str):
                    pos_secundarias = [p.strip() for p in pos_secundarias.split(',')] if pos_secundarias else []
                grupo_jogador = GRUPO_POSICAO_JOGADOR.get(pos_principal, '')
                grupo_esperado = POSICAO_ESPERADA_PARA_GRUPO.get(posicao_esperada, '')
                if grupo_jogador and grupo_jogador == grupo_esperado:
                    bonus_posicao_norm = 100
                elif any(GRUPO_POSICAO_JOGADOR.get(sec, '') == grupo_esperado for sec in pos_secundarias):
                    bonus_posicao_norm = 50
                elif posicao_esperada == 'Goleiro' and pos_principal == 'Goleiro':
                    bonus_posicao_norm = 100
            bonus_minutagem_norm = 0
            if priorizar_minutagem:
                starts = row.get('total_starts', 0)
                minutos = row.get('minutos_totais_partidas', 0)
                starts_norm = starts / max_starts if max_starts > 0 else 0
                minutos_norm = minutos / max_minutos if max_minutos > 0 else 0
                fator_titularidade = (starts_norm * 0.7) + (minutos_norm * 0.3)
                bonus_minutagem_norm = fator_titularidade * 100
            score_final = (score_atributos * 0.20) + (bonus_posicao_norm * 0.40) + (bonus_minutagem_norm * 0.40)
            scores.append((idx, score_final, row))
        scores.sort(key=lambda x: x[1], reverse=True)
        posicoes.append({
            'role': role,
            'candidates': scores,
            'selected_idx': None,
            'posicao_esperada': posicao_esperada
        })

    used_indices = set()
    titulares = []
    for pos in posicoes:
        selected = None
        for idx, score, row in pos['candidates']:
            if idx not in used_indices:
                used_indices.add(idx)
                selected = {
                    'nome': row['nome_completo'],
                    'apelido': row['apelido'],
                    'role': pos['role'],
                    'row': row,
                    'score': score
                }
                break
        if selected is None:
            for _, row in df_copy[~df_copy.index.isin(used_indices)].iterrows():
                used_indices.add(row.name)
                selected = {
                    'nome': row['nome_completo'],
                    'apelido': row['apelido'],
                    'role': pos['role'],
                    'row': row,
                    'score': row.get('Rating_Geral_FM26', 0)
                }
                break
        if selected:
            titulares.append(selected)
        else:
            titulares.append({
                'nome': 'N/D',
                'apelido': 'N/D',
                'role': pos['role'],
                'row': None,
                'score': 0
            })

    reservas_df = df_copy[~df_copy.index.isin(used_indices)]
    reservas_df['rating'] = reservas_df.apply(lambda row: row.get('Rating_Geral_FM26', 0), axis=1)
    reservas_df = reservas_df.sort_values('rating', ascending=False)
    reservas = []
    for _, row in reservas_df.head(10).iterrows():
        reservas.append({
            'nome': row['nome_completo'],
            'apelido': row['apelido'],
            'row': row
        })
    return titulares, reservas

def gerar_instrucoes_por_role(row, role):
    inst = {'com_bola': [], 'sem_bola': []}
    if 'Goleiro' in role:
        inst['com_bola'].append("Distribua a bola com segurança.")
        inst['sem_bola'].append("Posicione-se bem, saia quando necessário.")
    elif 'Zagueiro' in role or 'Centre-Back' in role:
        inst['com_bola'].append("Passe curto para o meio-campo.")
        inst['sem_bola'].append("Mantenha a linha, marque o atacante.")
    elif 'Lateral' in role or 'Full-Back' in role or 'Wing-Back' in role:
        inst['com_bola'].append("Apoie o ataque pelos lados.")
        inst['sem_bola'].append("Volte rapidamente, proteja o flanco.")
    elif 'Volante' in role or 'Defensive Midfielder' in role:
        inst['com_bola'].append("Proteja a defesa, distribua passes simples.")
        inst['sem_bola'].append("Cubra espaços, marque o meia adversário.")
    elif 'Meia' in role or 'Midfielder' in role or 'Playmaker' in role:
        inst['com_bola'].append("Controle o jogo, distribua passes.")
        inst['sem_bola'].append("Aperte a saída de bola do adversário.")
    elif 'Ponta' in role or 'Winger' in role or 'Forward' in role or 'Atacante' in role:
        inst['com_bola'].append("Finalize com qualidade, movimente-se.")
        inst['sem_bola'].append("Pressione a defesa adversária.")
    else:
        inst['com_bola'].append("Execute sua função com inteligência.")
        inst['sem_bola'].append("Mantenha a organização tática.")
    return inst