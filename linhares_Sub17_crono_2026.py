#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LINHARES FC SUB 17 CRONO 2026 – VERSÃO 13.2 (APENAS CSVs INDIVIDUAIS)
Gera um arquivo CSV por partida a partir dos dados do OGOL.com.
"""

import requests
import re
import time
import random
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import os
import csv
import json
import unicodedata

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

PASTA_DADOS = r"C:\BDAnaliseElencoLinharesFC"
PASTA_LINHARESFC_CRONO = os.path.join(PASTA_DADOS, "LinharesFCCrono_2026")
PASTA_LOGS = os.path.join(PASTA_LINHARESFC_CRONO, "logs")
PASTA_ESTATISTICAS = os.path.join(PASTA_LINHARESFC_CRONO, "estatisticas_jogadores_Sub17")  # OK
PASTA_BACKUP = os.path.join(PASTA_LINHARESFC_CRONO, "backup")

for pasta in [PASTA_DADOS, PASTA_LINHARESFC_CRONO, PASTA_LOGS, PASTA_ESTATISTICAS, PASTA_BACKUP]:
    os.makedirs(pasta, exist_ok=True)

CAMINHO_JSON_JOGADORES = os.path.join(PASTA_LINHARESFC_CRONO, "mapeamento_jogadores_sub17.json")  # alterado
CAMINHO_LOG = os.path.join(PASTA_LOGS, f"log_sub17_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")  # alterado

# ============================================================================
# MAPEAMENTO DE NOMES – PREENCHA COM OS DADOS DO SUB-17
# ============================================================================
MAPEAMENTO_NOMES = {
    # Exemplo: 'Nome Completo no OGOL': 'Apelido',
    # 'João da Silva': 'Joãozinho',
}

# ============================================================================
# IDS CONHECIDOS (nome CSV -> ID OGOL)
# ============================================================================
IDS_CONHECIDOS = {
    # Exemplo: 'Joãozinho': '1234567',
}

# ============================================================================
# POSIÇÕES CSV (nome CSV -> posição)
# ============================================================================
POSICOES_CSV = {
    # Exemplo: 'Joãozinho': 'Atacante',
}

# Conjunto de IDs válidos para agilizar a verificação
IDS_VALIDOS = set(IDS_CONHECIDOS.values())

# ============================================================================
# CONSTRUÇÃO DO MAPEAMENTO COMPLETO
# ============================================================================
MAPEAMENTO_JOGADORES_LINHARESFC = {}
for nome_csv in IDS_CONHECIDOS.keys():
    nome_completo = next((nc for nc, nc2 in MAPEAMENTO_NOMES.items() if nc2 == nome_csv), nome_csv)
    MAPEAMENTO_JOGADORES_LINHARESFC[nome_csv] = {
        "id_ogol": IDS_CONHECIDOS.get(nome_csv, ""),
        "posicao": POSICOES_CSV.get(nome_csv, "INDEFINIDO"),
        "nome_completo": nome_completo,
        "status": "Ativo"
    }

# ============================================================================
# JOGOS – PREENCHA COM OS JOGOS DO SUB-17
# ============================================================================
JOGOS_TEMPORADA_2026 = [
    # Exemplo:
    # {
    #     "id_jogo": "12345678",
    #     "data_jogo": "12/07/2026",
    #     "adversario": "Audax São Mateus",
    #     "time_casa": "Linhares FC",
    #     "time_fora": "Audax São Mateus",
    #     "local_jogo": "(C)",
    #     "status": "REALIZADO",
    #     "slug": "2026-07-12-linhares-fc-audax-sao-mateus-sub17",
    #     "url_completa": "https://www.ogol.com.br/jogo/2026-07-12-linhares-fc-audax-sao-mateus-sub17/12345678/performance",
    #     "competicao": "Capixabão Sub-17",
    #     "fase": "1ª Fase"
    # },
]

# ============================================================================
# LOGGER
# ============================================================================

class Logger:
    def __init__(self, caminho_log):
        self.caminho_log = caminho_log
    def log(self, msg, tipo="INFO"):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        linha = f"[{ts}] [{tipo}] {msg}"
        print(linha)
        try:
            with open(self.caminho_log, 'a', encoding='utf-8') as f:
                f.write(linha + "\n")
        except: pass
    def log_erro(self, msg, e=None):
        self.log(f"{msg}: {e}" if e else msg, "ERRO")
    def log_sucesso(self, msg):
        self.log(msg, "SUCESSO")

# ============================================================================
# EXTRATOR – UNIVERSAL (COM FILTRO POR ID)
# ============================================================================

class ExtratorEstatisticas:
    def __init__(self, logger):
        self.session = requests.Session()
        self.logger = logger
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        })
        self._preparar_mapeamento()
        self.id_para_nome_csv = {v: k for k, v in IDS_CONHECIDOS.items()}

    def _preparar_mapeamento(self):
        self.busca_nomes = {}
        for variacao, nome_csv in MAPEAMENTO_NOMES.items():
            chave = self._normalizar(variacao)
            self.busca_nomes[chave] = nome_csv
        self.logger.log(f"✅ Mapeamento: {len(self.busca_nomes)} variações")

    def _normalizar(self, texto):
        if not texto: return ""
        texto = texto.lower()
        texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
        texto = re.sub(r'[^a-z\s]', '', texto)
        return ' '.join(texto.split())

    def _limpar_nome_extraido(self, nome):
        if not nome: return ""
        nome = re.sub(r'^\d+\.?\s*', '', nome)
        nome = re.sub(r'(Goleiro|Defensor|Meia|Atacante)$', '', nome)
        nome = re.sub(r'^[^a-zA-Z]+|[^a-zA-Z]+$', '', nome)
        return nome.strip()

    def _encontrar_jogador_por_nome(self, nome_extraido):
        if not nome_extraido: return None
        nome_limpo = self._limpar_nome_extraido(nome_extraido)
        chave = self._normalizar(nome_limpo)
        if chave in self.busca_nomes:
            return self.busca_nomes[chave]
        for k, v in self.busca_nomes.items():
            if chave in k or k in chave:
                return v
        return None

    def _requisicao(self, url, tentativas=2):
        for tent in range(tentativas):
            try:
                time.sleep(random.uniform(1.2, 2.2))
                resp = self.session.get(url, timeout=12)
                if resp.status_code == 200:
                    return resp
            except Exception as e:
                self.logger.log_erro(f"Tentativa {tent+1}", e)
            time.sleep(2)
        return None

    def construir_url(self, jogo):
        if jogo.get('url_completa'):
            return jogo['url_completa']
        return f"https://www.ogol.com.br/jogo/{jogo['slug']}/{jogo['id_jogo']}/performance"

    def testar_url(self, jogo):
        url = self.construir_url(jogo)
        self.logger.log(f"🔗 Testando: {url}")
        resp = self._requisicao(url)
        if not resp: return False
        soup = BeautifulSoup(resp.content, 'html.parser')
        titulo = soup.find('title')
        if titulo: self.logger.log(f"   Título: {titulo.get_text()[:60]}...")
        tabelas = soup.find_all('table')
        ok = any(len(t.find_all('tr')) > 5 for t in tabelas)
        self.logger.log("   ✅ OK" if ok else "   ❌ Sem tabela")
        return ok

    def extrair_jogo(self, jogo):
        self.logger.log(f"\n{'='*80}")
        self.logger.log(f"🚀 {jogo['time_casa']} vs {jogo['time_fora']} – {jogo['data_jogo']}")
        self.logger.log(f"{'='*80}")

        url_base = self.construir_url(jogo)
        url_grupo0 = f"{url_base}?group=0"
        self.logger.log(f"📦 Grupo 0: {url_grupo0}")

        resp = self._requisicao(url_grupo0)
        if not resp:
            self.logger.log("❌ Falha no grupo 0")
            return []

        soup = BeautifulSoup(resp.content, 'html.parser')
        tabela = self._encontrar_tabela(soup)
        if not tabela:
            self.logger.log("❌ Tabela não encontrada")
            return []

        linhas = tabela.find_all('tr')
        cabecalho = None
        for linha in linhas[:5]:
            texto = linha.get_text().lower()
            if 'minutos' in texto or 'gols' in texto:
                cabecalho = linha
                break

        indices = self._mapear_indices(cabecalho)
        if not indices:
            self.logger.log("❌ Não foi possível identificar as colunas")
            return []

        inicio = 0
        for i, linha in enumerate(linhas[:5]):
            if 'jogador' in linha.get_text().lower() or 'player' in linha.get_text().lower():
                inicio = i + 1
                break

        dados_brutos = {}
        ids_encontrados = set()

        for linha in linhas[inicio:]:
            celulas = linha.find_all('td')
            if len(celulas) < max(indices.values()) + 1:
                continue
            link = celulas[0].find('a')
            jogador_id = None
            if link and link.get('href'):
                href = link['href']
                match = re.search(r'/player/(?:\w+-?)+\/(\d+)', href)
                if match:
                    jogador_id = match.group(1)

            nome = celulas[0].get_text(strip=True)
            if not nome or nome.lower() in ['total', 'média']:
                continue

            if jogador_id and jogador_id in IDS_VALIDOS:
                nome_csv = self.id_para_nome_csv.get(jogador_id)
                if nome_csv:
                    dados_brutos[nome_csv] = {
                        'minutos': self._converter(celulas[indices['minutos']].get_text()) if indices.get('minutos') is not None else 0,
                        'gols': self._converter(celulas[indices['gols']].get_text()) if indices.get('gols') is not None else 0,
                        'assistencias': self._converter(celulas[indices['assistencias']].get_text()) if indices.get('assistencias') is not None else 0,
                        'cartoes_amarelos': self._converter(celulas[indices['amarelos']].get_text()) if indices.get('amarelos') is not None else 0,
                        'cartoes_vermelhos': self._converter(celulas[indices['vermelhos']].get_text()) if indices.get('vermelhos') is not None else 0,
                    }
                    ids_encontrados.add(jogador_id)
                else:
                    self.logger.log(f"   ⚠️ ID {jogador_id} válido mas sem nome CSV. Ignorado.")

        self.logger.log(f"📊 {len(dados_brutos)} jogadores do Linhares FC identificados por ID")
        if not dados_brutos:
            self.logger.log("⚠️ Nenhum jogador encontrado por ID. Tentando fallback por nome...")
            for linha in linhas[inicio:]:
                celulas = linha.find_all('td')
                if len(celulas) < max(indices.values()) + 1:
                    continue
                nome = celulas[0].get_text(strip=True)
                if not nome or nome.lower() in ['total', 'média']:
                    continue
                nome_csv = self._encontrar_jogador_por_nome(nome)
                if nome_csv:
                    dados_brutos[nome_csv] = {
                        'minutos': self._converter(celulas[indices['minutos']].get_text()) if indices.get('minutos') is not None else 0,
                        'gols': self._converter(celulas[indices['gols']].get_text()) if indices.get('gols') is not None else 0,
                        'assistencias': self._converter(celulas[indices['assistencias']].get_text()) if indices.get('assistencias') is not None else 0,
                        'cartoes_amarelos': self._converter(celulas[indices['amarelos']].get_text()) if indices.get('amarelos') is not None else 0,
                        'cartoes_vermelhos': self._converter(celulas[indices['vermelhos']].get_text()) if indices.get('vermelhos') is not None else 0,
                    }

        self.logger.log(f"✅ {len(dados_brutos)} jogadores do Linhares FC identificados (após fallback)")

        if not dados_brutos:
            return []

        estatisticas = self._formatar(dados_brutos, jogo)
        self._resumo(estatisticas)
        return estatisticas

    def _mapear_indices(self, cabecalho):
        if not cabecalho:
            return {
                'gols': 1,
                'assistencias': 2,
                'amarelos': 3,
                'vermelhos': 4,
                'minutos': 5
            }

        celulas = cabecalho.find_all(['th', 'td'])
        indices = {}
        for i, cel in enumerate(celulas):
            texto = cel.get_text().strip().lower()
            if 'gol' in texto and 'assist' not in texto:
                indices['gols'] = i
            elif 'assist' in texto:
                indices['assistencias'] = i
            elif 'amarelo' in texto or 'yellow' in texto:
                indices['amarelos'] = i
            elif 'vermelho' in texto or 'red' in texto:
                indices['vermelhos'] = i
            elif 'minuto' in texto or 'min' in texto:
                indices['minutos'] = i

        if 'gols' not in indices:
            indices['gols'] = 1
        if 'assistencias' not in indices:
            indices['assistencias'] = 2
        if 'amarelos' not in indices:
            indices['amarelos'] = 3
        if 'vermelhos' not in indices:
            indices['vermelhos'] = 4
        if 'minutos' not in indices:
            indices['minutos'] = len(celulas) - 1 if len(celulas) > 5 else 5

        self.logger.log(f"   📐 Índices: gols={indices['gols']}, ass={indices['assistencias']}, "
                        f"am={indices['amarelos']}, vm={indices['vermelhos']}, min={indices['minutos']}")
        return indices

    def _encontrar_tabela(self, soup):
        todas = soup.find_all('table')
        maior = None
        maior_linhas = 0
        for t in todas:
            qtd = len(t.find_all('tr'))
            if qtd > maior_linhas:
                maior_linhas = qtd
                maior = t
        return maior if maior_linhas > 10 else None

    def _converter(self, texto):
        if not texto or texto.strip() in ['-', '']:
            return 0
        try:
            txt = re.sub(r'[^\d,\.]', '', texto.strip()).replace(',', '.')
            return float(txt) if '.' in txt else int(txt)
        except:
            return 0

    def _formatar(self, dados, jogo):
        registros = []
        for nome_csv, stats in dados.items():
            info = MAPEAMENTO_JOGADORES_LINHARESFC.get(nome_csv, {})
            registros.append({
                'id_jogo': jogo['id_jogo'],
                'data_jogo': jogo['data_jogo'],
                'adversario': jogo['adversario'],
                'local': jogo['local_jogo'],
                'jogador': nome_csv,
                'posicao': info.get('posicao', 'INDEFINIDO'),
                'id_ogol_jogador': info.get('id_ogol', ''),
                'nome_completo': info.get('nome_completo', ''),
                'data_extracao': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'url_jogo': self.construir_url(jogo),
                'minutos': stats.get('minutos', 0),
                'gols': stats.get('gols', 0),
                'assistencias': stats.get('assistencias', 0),
                'cartoes_amarelos': stats.get('cartoes_amarelos', 0),
                'cartoes_vermelhos': stats.get('cartoes_vermelhos', 0),
                'chutes': 0, 'chutes_ao_gol': 0, 'desarmes': 0,
                'interceptacoes': 0, 'passes_certos': 0, 'passes_chave': 0, 'defesas': 0,
            })
        return registros

    def _resumo(self, stats):
        titulares = [s for s in stats if s['minutos'] > 0]
        reservas = [s for s in stats if s['minutos'] == 0]
        self.logger.log(f"\n📋 RESUMO:")
        self.logger.log(f"   • Total: {len(stats)}")
        self.logger.log(f"   • Titulares (min>0): {len(titulares)}")
        self.logger.log(f"   • Reservas (min=0): {len(reservas)}")
        if titulares:
            top = sorted(titulares, key=lambda x: x['minutos'], reverse=True)[:5]
            self.logger.log("   ⏱️  TOP 5 minutos:")
            for i, j in enumerate(top, 1):
                self.logger.log(f"      {i}. {j['jogador']}: {j['minutos']} min")

    def salvar_csv(self, dados, caminho_esp):
        if not dados:
            self.logger.log("❌ Nada a salvar", "AVISO")
            return False
        if not caminho_esp:
            self.logger.log("❌ Caminho do arquivo não especificado", "ERRO")
            return False

        colunas = ['id_jogo', 'data_jogo', 'adversario', 'local', 'jogador',
                   'posicao', 'minutos', 'gols', 'assistencias', 'cartoes_amarelos',
                   'cartoes_vermelhos', 'chutes', 'chutes_ao_gol', 'desarmes',
                   'interceptacoes', 'passes_certos', 'passes_chave', 'defesas',
                   'id_ogol_jogador', 'nome_completo', 'data_extracao', 'url_jogo']
        modo = 'w' if not os.path.exists(caminho_esp) else 'a'
        try:
            with open(caminho_esp, modo, newline='', encoding='utf-8') as f:
                w = csv.DictWriter(f, fieldnames=colunas, delimiter=';')
                if modo == 'w':
                    w.writeheader()
                for reg in dados:
                    w.writerow({c: reg.get(c, '') for c in colunas})
            self.logger.log_sucesso(f"💾 Salvo: {caminho_esp} ({len(dados)} registros)")
            return True
        except Exception as e:
            self.logger.log_erro("Erro ao salvar CSV", e)
            return False

# ============================================================================
# FUNÇÃO PARA OBTER O PRÓXIMO JOGO
# ============================================================================

def obter_proximo_jogo():
    from datetime import datetime

    if not JOGOS_TEMPORADA_2026:
        return None

    realizados = []
    for jogo in JOGOS_TEMPORADA_2026:
        if jogo.get('status') == 'REALIZADO':
            try:
                data_obj = datetime.strptime(jogo['data_jogo'], "%d/%m/%Y")
                realizados.append((data_obj, jogo))
            except (ValueError, KeyError):
                continue

    if realizados:
        ultimo_realizado = max(realizados, key=lambda x: x[0])[1]
        data_ref = datetime.strptime(ultimo_realizado['data_jogo'], "%d/%m/%Y")
    else:
        data_ref = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    futuros = []
    for jogo in JOGOS_TEMPORADA_2026:
        if jogo.get('status') in ['AGENDADO', 'AGUARDANDO']:
            try:
                data_obj = datetime.strptime(jogo['data_jogo'], "%d/%m/%Y")
                if data_obj > data_ref:
                    futuros.append((data_obj, jogo))
            except (ValueError, KeyError):
                continue

    if not futuros:
        return None

    proximo = min(futuros, key=lambda x: x[0])[1]
    return proximo

# ============================================================================
# SISTEMA PRINCIPAL
# ============================================================================

class SistemaLinharesCrono:
    def __init__(self):
        self.logger = Logger(CAMINHO_LOG)
        self.extrator = ExtratorEstatisticas(self.logger)
        self.jogos = JOGOS_TEMPORADA_2026
        self._salvar_json()

    def _salvar_json(self):
        try:
            with open(CAMINHO_JSON_JOGADORES, 'w', encoding='utf-8') as f:
                json.dump(MAPEAMENTO_JOGADORES_LINHARESFC, f, ensure_ascii=False, indent=2)
            self.logger.log(f"✅ Mapeamento salvo em: {CAMINHO_JSON_JOGADORES}")
        except Exception as e:
            self.logger.log_erro("Erro ao salvar JSON", e)

    def mostrar_banner(self):
        print("\n" + "="*100)
        print(" " * 30 + "🏆 LINHARES FC SUB-17 CRONO 2026 – VERSÃO 13.2 🏆")
        print("="*100)
        print(f"\n📊 CONFIGURAÇÃO:")
        print(f"   • Jogos: {len(self.jogos)}")
        print(f"   • Jogadores mapeados: {len(MAPEAMENTO_JOGADORES_LINHARESFC)}")
        print("="*100)

    def mostrar_menu(self):
        print("\n📋 MENU PRINCIPAL:")
        print("1. 🔍 Extrair estatísticas de um jogo específico")
        print("2. 🚀 Extrair estatísticas de TODOS os jogos")
        print("3. 🔗 Testar todas as URLs")
        print("4. 👥 Listar jogadores mapeados")
        print("5. 📅 Exibir próximo jogo")
        print("0. 🚪 Sair")

    def listar_jogos(self):
        print(f"\n📅 JOGOS ({len(self.jogos)}):")
        for i, j in enumerate(self.jogos, 1):
            emoji = "✅" if j['status'] == "REALIZADO" else "🕒"
            local = "🏠" if j['local_jogo'] == "(C)" else "✈️"
            print(f"\n{i}. {emoji} {j['data_jogo']} - {local} {j['time_casa']} vs {j['time_fora']}")
            print(f"   👥 Adversário: {j['adversario']} | ID: {j['id_jogo']}")

    def extrair_um_jogo(self):
        self.listar_jogos()
        try:
            inp = input("\n🔢 Número do jogo (0 para voltar): ").strip()
            if inp == '0': return
            idx = int(inp)-1
            if 0 <= idx < len(self.jogos):
                jogo = self.jogos[idx]
                print(f"\n🎯 {jogo['data_jogo']} - {jogo['time_casa']} vs {jogo['time_fora']}")
                if input("Confirmar extração? (S/N): ").strip().upper() != 'S':
                    self.logger.log("Cancelado", "AVISO")
                    return
                if self.extrator.testar_url(jogo):
                    stats = self.extrator.extrair_jogo(jogo)
                    if stats:
                        nome = f"jogo_{jogo['id_jogo']}_{jogo['adversario'].replace(' ', '_')}.csv"
                        self.extrator.salvar_csv(stats, os.path.join(PASTA_ESTATISTICAS, nome))
                    else:
                        self.logger.log("❌ Nenhum jogador do Linhares FC encontrado", "ERRO")
                else:
                    self.logger.log("❌ URL inválida", "ERRO")
            else:
                self.logger.log("❌ Número inválido", "ERRO")
        except Exception as e:
            self.logger.log_erro("Erro na extração", e)

    def extrair_todos(self):
        print("\n⚠️  EXTRAÇÃO EM MASSA")
        print(f"{len(self.jogos)} jogos. Continuar? (S/N): ", end='')
        if input().strip().upper() != 'S':
            self.logger.log("Cancelado", "AVISO")
            return
        processados = 0
        erros = []
        for i, jogo in enumerate(self.jogos, 1):
            self.logger.log(f"\n{'='*80}\nJOGO {i}/{len(self.jogos)}\n{'='*80}")
            try:
                if self.extrator.testar_url(jogo):
                    stats = self.extrator.extrair_jogo(jogo)
                    if stats:
                        nome = f"jogo_{jogo['id_jogo']}_{jogo['adversario'].replace(' ', '_')}.csv"
                        self.extrator.salvar_csv(stats, os.path.join(PASTA_ESTATISTICAS, nome))
                        processados += 1
                        self.logger.log_sucesso(f"✅ Jogo {i}: {len(stats)} jogadores")
                    else:
                        erros.append(jogo['id_jogo'])
                        self.logger.log(f"⚠️ Jogo {i} sem jogadores", "AVISO")
                else:
                    erros.append(jogo['id_jogo'])
                    self.logger.log(f"❌ URL {i} inacessível", "ERRO")
            except Exception as e:
                erros.append(jogo['id_jogo'])
                self.logger.log_erro(f"Erro no jogo {i}", e)
            if i < len(self.jogos):
                time.sleep(8)
        print(f"\n📊 RELATÓRIO:")
        print(f"   • Jogos OK: {processados}/{len(self.jogos)}")
        if erros:
            print(f"   • Jogos c/ erro: {len(erros)}")

    def testar_todas_urls(self):
        print(f"\n🔍 Testando {len(self.jogos)} URLs...")
        val = 0
        for i, j in enumerate(self.jogos, 1):
            print(f"\n{i}. {j['time_casa']} vs {j['time_fora']}")
            if self.extrator.testar_url(j):
                val += 1
                print("   ✅ VÁLIDA")
            else:
                print("   ❌ INVÁLIDA")
        print(f"\n📊 Resultado: {val}/{len(self.jogos)} URLs válidas")

    def listar_jogadores(self):
        print(f"\n👥 ELENCO ({len(MAPEAMENTO_JOGADORES_LINHARESFC)}):")
        posicoes = {}
        for nome_csv, info in MAPEAMENTO_JOGADORES_LINHARESFC.items():
            p = info.get('posicao', 'INDEFINIDO')
            posicoes.setdefault(p, []).append(nome_csv)
        for p, nomes in sorted(posicoes.items()):
            print(f"\n{p.upper()} ({len(nomes)}):")
            for n in sorted(nomes):
                print(f"   • {n} (ID: {MAPEAMENTO_JOGADORES_LINHARESFC[n]['id_ogol']})")

    def exibir_proximo_jogo_manual(self):
        prox = obter_proximo_jogo()
        if prox is None:
            print("❌ Nenhum jogo futuro encontrado.")
            return
        print("\n" + "="*60)
        print("📅 PRÓXIMO JOGO")
        print("="*60)
        print(f"🏆 Competição: {prox.get('competicao', 'N/I')}")
        print(f"🆚 Adversário: {prox['adversario']}")
        print(f"📅 Data: {prox['data_jogo']}")
        local = "Casa" if prox['local_jogo'] == '(C)' else "Fora"
        print(f"🏟️ Local: {local}")
        print(f"🆔 ID: {prox['id_jogo']}")
        print(f"🔗 Link: {prox.get('url_completa', 'N/A')}")
        print(f"⏳ Status: {prox['status']}")

    def executar(self):
        self.mostrar_banner()
        while True:
            self.mostrar_menu()
            op = input("\n🔢 Escolha: ").strip()
            if op == '1':
                self.extrair_um_jogo()
            elif op == '2':
                self.extrair_todos()
            elif op == '3':
                self.testar_todas_urls()
            elif op == '4':
                self.listar_jogadores()
            elif op == '5':
                self.exibir_proximo_jogo_manual()
            elif op == '0':
                self.logger.log("👋 Encerrando...")
                print("\n✅ Sistema finalizado.")
                break
            else:
                print("❌ Opção inválida")
            if op != '0':
                input("\n⏎ Enter para continuar...")

if __name__ == "__main__":
    print("\n" + "="*100)
    print(" " * 35 + "LINHARES FC SUB-17 CRONO 2026")
    print(" " * 30 + "Versão 13.2 – CSVs individuais")
    print("="*100)
    try:
        import requests, pandas, bs4
    except ImportError as e:
        print(f"❌ Dependência: {e}")
        print("📦 Instale: pip install requests pandas beautifulsoup4")
        exit()
    SistemaLinharesCrono().executar()