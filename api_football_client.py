# api_football_client.py
# -*- coding: utf-8 -*-
"""
Cliente de monitoramento para o projeto_web (Streamlit).

Ordem de consulta em cada chamada:
  1) API-Football (v3.football.api-sports.io)
  2) Se a API falhar (sem chave, sem internet, cota estourada, erro ou resposta
     vazia), lê direto do meu_futebol.db, somente leitura, no MESMO formato da API.

Mesma interface do antigo FastAPIMonitorClient, então pages/monitoramento.py
só troca o import. Depois de cada chamada, `ultima_fonte` diz de onde veio o
dado: "API-Football" ou "Banco local".

Chave da API (nunca fica no código):
  - variável de ambiente API_FOOTBALL_KEY, ou
  - campo "api_football_key" no config.json

Cota: o Streamlit recarrega a página a cada 10 s. Para não estourar as 100
requisições/dia do plano grátis, cada resposta da API fica em cache por
API_FOOTBALL_CACHE_SEGUNDOS (padrão 60 s).
"""
import json
import os
import sqlite3
import time
from datetime import datetime
from typing import Dict, List, Optional

import requests

API_FOOTBALL_URL = "https://v3.football.api-sports.io"
DB_PATH = "meu_futebol.db"
FUSO_HORARIO_API = "America/Sao_Paulo"

# Liga do Profissional: 611 na API-Football, 12 no meu_futebol.db
LEAGUE_ID_API = 611
COMPETICAO_ID_BANCO = 12
MAPA_LIGA_API_PARA_BANCO = {LEAGUE_ID_API: COMPETICAO_ID_BANCO}

STATUS_AO_VIVO = {'1H', 'HT', '2H', 'ET', 'BT', 'P', 'LIVE', 'INT', 'SUSP'}
CACHE_SEGUNDOS = int(os.getenv("API_FOOTBALL_CACHE_SEGUNDOS", "60"))

# Cache no nível do módulo: sobrevive aos reruns do Streamlit
_CACHE: Dict[tuple, tuple] = {}


def ler_chave_api_football(config_path: str = "config.json") -> str:
    chave = os.getenv("API_FOOTBALL_KEY", "").strip()
    if chave:
        return chave
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return str(json.load(f).get("api_football_key", "")).strip()
    except Exception:
        return ""


# ============================================================
# API-FOOTBALL
# ============================================================
class ApiFootballClient:
    """Retorna a lista 'response' da API, ou None quando a consulta falha."""

    def __init__(self, chave: str, base_url: str = API_FOOTBALL_URL, timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.ativo = bool(chave)
        self.session = requests.Session()
        self.session.headers.update({'x-apisports-key': chave})
        self.ultimo_erro = "" if chave else "API_FOOTBALL_KEY não configurada"
        self.requisicoes_restantes = None

    def _get(self, endpoint: str, **params):
        if not self.ativo:
            return None
        chave_cache = (endpoint, tuple(sorted((k, str(v)) for k, v in params.items())))
        hit = _CACHE.get(chave_cache)
        if hit and time.time() - hit[0] < CACHE_SEGUNDOS:
            return hit[1]
        try:
            r = self.session.get(f"{self.base_url}/{endpoint}", params=params, timeout=self.timeout)
            rest = r.headers.get('x-ratelimit-requests-remaining')
            if rest is not None:
                self.requisicoes_restantes = rest
            if r.status_code != 200:
                self.ultimo_erro = f"HTTP {r.status_code}"
                return None
            j = r.json()
            if j.get('errors'):  # a API devolve 200 com 'errors' (cota, chave inválida...)
                self.ultimo_erro = str(j['errors'])
                return None
            self.ultimo_erro = ""
            resp = j.get('response', [])
            _CACHE[chave_cache] = (time.time(), resp)
            return resp
        except Exception as e:
            self.ultimo_erro = str(e)
            return None

    def get_live_fixture(self, team_id):
        hoje = datetime.now().strftime("%Y-%m-%d")
        resp = self._get("fixtures", team=team_id, date=hoje, timezone=FUSO_HORARIO_API)
        if resp is None:
            return None
        for f in resp:
            if f['fixture']['status']['short'] in STATUS_AO_VIVO:
                return f['fixture']['id']
        return False  # API respondeu, mas sem jogo ao vivo (não dispara fallback)

    def get_fixture_details(self, fixture_id):
        resp = self._get("fixtures", id=fixture_id, timezone=FUSO_HORARIO_API)
        return resp[0] if resp else None

    def get_fixture_events(self, fixture_id):
        return self._get("fixtures/events", fixture=fixture_id)

    def get_fixture_statistics(self, fixture_id):
        return self._get("fixtures/statistics", fixture=fixture_id)

    def get_fixture_players(self, fixture_id):
        return self._get("fixtures/players", fixture=fixture_id)

    def get_fixture_lineups(self, fixture_id):
        return self._get("fixtures/lineups", fixture=fixture_id)

    def get_fixtures(self, team=None, from_date=None, to_date=None, league=None, season=None):
        params = {'timezone': FUSO_HORARIO_API}
        for k, v in (('team', team), ('from', from_date), ('to', to_date),
                     ('league', league), ('season', season)):
            if v:
                params[k] = v
        return self._get("fixtures", **params)


# ============================================================
# BANCO LOCAL (fallback)
# ============================================================
class BancoLocalClient:
    """Lê o meu_futebol.db e devolve os dados no formato da API-Football."""

    _SQL_JOGO = """
        SELECT j.*, tc.nome AS casa, tf.nome AS fora, v.nome AS estadio,
               a.nome AS arbitro, c.nome AS competicao
          FROM jogos j
          LEFT JOIN times tc ON tc.id = j.time_casa_id
          LEFT JOIN times tf ON tf.id = j.time_fora_id
          LEFT JOIN venues v ON v.id = j.venue_id
          LEFT JOIN arbitros a ON a.id = j.arbitro_id
          LEFT JOIN competicoes c ON c.id = j.competicao_id
    """

    def __init__(self, caminho: str = DB_PATH):
        self.caminho = caminho

    def _consultar(self, sql, params=()):
        try:
            if not os.path.exists(self.caminho):
                raise FileNotFoundError(self.caminho)
            uri = "file:" + os.path.abspath(self.caminho).replace("\\", "/") + "?mode=ro"
            with sqlite3.connect(uri, uri=True, timeout=10) as c:
                c.row_factory = sqlite3.Row
                return [dict(r) for r in c.execute(sql, params).fetchall()]
        except Exception as e:
            print(f"⚠️ Banco local: {e}")
            return []

    @staticmethod
    def _formatar_jogo(p):
        return {
            "fixture": {"id": p['id'], "date": p.get('data_hora') or '',
                        "status": {"short": p.get('status') or 'NS', "elapsed": None},
                        "venue": {"name": p.get('estadio') or 'Estádio'},
                        "referee": p.get('arbitro') or 'N/I'},
            "league": {"id": p.get('competicao_id'), "name": p.get('competicao') or 'N/I'},
            "teams": {"home": {"id": p.get('time_casa_id'), "name": p.get('casa') or 'Casa'},
                      "away": {"id": p.get('time_fora_id'), "name": p.get('fora') or 'Fora'}},
            "goals": {"home": p.get('gols_casa'), "away": p.get('gols_fora')},
            "score": {"penalty": None},
        }

    def get_live_fixture(self, team_id):
        r = self._consultar(
            "SELECT id FROM jogos WHERE status IN ('1H','2H','HT','ET','BT','P','LIVE') "
            "AND (time_casa_id = ? OR time_fora_id = ?) ORDER BY data_hora DESC LIMIT 1",
            (team_id, team_id))
        return r[0]['id'] if r else None

    def get_fixture_details(self, fixture_id):
        r = self._consultar(self._SQL_JOGO + " WHERE j.id = ?", (fixture_id,))
        return self._formatar_jogo(r[0]) if r else None

    def get_fixture_events(self, fixture_id):
        rows = self._consultar("""
            SELECT ev.tempo, ev.tipo, ev.detalhes,
                   COALESCE(e.apelido, e.nome, cm.nome) AS jogador, t.nome AS time
              FROM eventos ev
              LEFT JOIN elenco e    ON e.id = ev.jogador_id
              LEFT JOIN comissao cm ON cm.id = ev.membro_id
              LEFT JOIN times t     ON t.id = COALESCE(e.time_id, cm.time_id)
             WHERE ev.jogo_id = ? ORDER BY ev.tempo, ev.id""", (fixture_id,))
        return [{"time": {"elapsed": r['tempo'] or 0, "extra": None},
                 "type": r['tipo'] or '', "detail": r['detalhes'] or '',
                 "player": {"name": r['jogador'] or ''},
                 "team": {"name": r['time'] or 'N/I'}} for r in rows]

    def get_fixture_statistics(self, fixture_id):
        return []  # o banco não guarda estatísticas por time

    def get_fixture_players(self, fixture_id):
        rows = self._consultar("""
            SELECT s.*, COALESCE(e.apelido, e.nome) AS jogador, e.time_id, t.nome AS time
              FROM estatisticas_jogadores s
              LEFT JOIN elenco e ON e.id = s.jogador_id
              LEFT JOIN times t  ON t.id = e.time_id
             WHERE s.jogo_id = ?""", (fixture_id,))
        times = {}
        for r in rows:
            g = times.setdefault(r['time_id'], {"team": {"id": r['time_id'], "name": r['time'] or 'N/I'},
                                                "players": []})
            g["players"].append({
                "player": {"id": r['jogador_id'], "name": r['jogador'] or 'N/I'},
                "statistics": [{
                    "games": {"minutes": r['minutos']},
                    "goals": {"total": r['gols'], "assists": r['assistencias'], "saves": r['defesas']},
                    "shots": {"total": r['chutes'], "on": r['chutes_ao_gol']},
                    "passes": {"accurate": r['passes_certos'], "key": r['passes_chave']},
                    "tackles": {"total": r['desarmes'], "interceptions": r['interceptacoes']},
                    "cards": {"yellow": r['cartoes_amarelos'], "red": r['cartoes_vermelhos']},
                }]})
        return list(times.values())

    def get_fixture_lineups(self, fixture_id):
        rows = self._consultar(
            "SELECT * FROM lineup WHERE jogo_id = ? AND status IN ('Titular','Reserva') "
            "ORDER BY time_id, id", (fixture_id,))
        times = {}
        for r in rows:
            g = times.setdefault(r['time_id'], {"team": {"id": r['time_id'], "name": r['time']},
                                                "formation": r['formacao'],
                                                "startXI": [], "substitutes": []})
            item = {"player": {"id": r['jogador_id'], "name": r['nome'], "number": r['numero'],
                               "pos": r['posicao'], "grid": r['posicao_grid'] or None}}
            g["startXI" if r['status'] == 'Titular' else "substitutes"].append(item)
        return list(times.values())

    def get_fixtures(self, team=None, from_date=None, to_date=None, league=None, season=None):
        sql, p = self._SQL_JOGO + " WHERE 1=1", []
        if team:
            sql += " AND (j.time_casa_id = ? OR j.time_fora_id = ?)"
            p += [team, team]
        if league:
            sql += " AND j.competicao_id = ?"
            p.append(MAPA_LIGA_API_PARA_BANCO.get(league, league))
        if from_date:
            sql += " AND substr(j.data_hora,1,10) >= ?"
            p.append(from_date)
        if to_date:
            sql += " AND substr(j.data_hora,1,10) <= ?"
            p.append(to_date)
        return [self._formatar_jogo(r) for r in self._consultar(sql + " ORDER BY j.data_hora", p)]


# ============================================================
# CLIENTE COMBINADO (o que o monitoramento usa)
# ============================================================
class MonitorClient:
    FONTE_API = "API-Football"
    FONTE_BANCO = "Banco local"

    def __init__(self, chave: Optional[str] = None, db_path: str = DB_PATH):
        self.api = ApiFootballClient(chave if chave is not None else ler_chave_api_football())
        self.banco = BancoLocalClient(db_path)
        self.ultima_fonte: Optional[str] = None

    @property
    def usando_api(self) -> bool:
        return self.ultima_fonte == self.FONTE_API

    def _chamar(self, metodo, *args, vazio_e_falha=False, **kwargs):
        res = getattr(self.api, metodo)(*args, **kwargs)
        if res is not None and not (vazio_e_falha and not res):
            self.ultima_fonte = self.FONTE_API
            return res
        if self.api.ativo:
            print(f"⚠️ API-Football falhou em {metodo} ({self.api.ultimo_erro}) → banco local")
        self.ultima_fonte = self.FONTE_BANCO
        return getattr(self.banco, metodo)(*args, **kwargs)

    def get_live_fixture(self, team_id: Optional[int] = None) -> Optional[int]:
        res = self.api.get_live_fixture(team_id)
        if res is False:
            self.ultima_fonte = self.FONTE_API
            return None
        if res:
            self.ultima_fonte = self.FONTE_API
            return res
        self.ultima_fonte = self.FONTE_BANCO
        return self.banco.get_live_fixture(team_id)

    def get_fixture_details(self, fixture_id: int) -> Optional[Dict]:
        return self._chamar("get_fixture_details", fixture_id)

    def get_fixture_events(self, fixture_id: int) -> List[Dict]:
        return self._chamar("get_fixture_events", fixture_id) or []

    def get_fixture_statistics(self, fixture_id: int) -> List[Dict]:
        return self._chamar("get_fixture_statistics", fixture_id) or []

    def get_fixture_players(self, fixture_id: int) -> List[Dict]:
        return self._chamar("get_fixture_players", fixture_id, vazio_e_falha=True) or []

    def get_fixture_lineups(self, fixture_id: int) -> List[Dict]:
        return self._chamar("get_fixture_lineups", fixture_id, vazio_e_falha=True) or []

    def get_fixtures(self, team=None, from_date=None, to_date=None, league=None, season=None) -> List[Dict]:
        return self._chamar("get_fixtures", team=team, from_date=from_date, to_date=to_date,
                            league=league, season=season, vazio_e_falha=True) or []
