import requests
import json

API_BASE_URL = "http://localhost:8000"  # ou o endereço onde a API está rodando

def get_partida(jogo_id):
    """Retorna os dados da partida via API."""
    url = f"{API_BASE_URL}/partida/{jogo_id}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro na API: {response.status_code}")
            return None
    except Exception as e:
        print(f"Erro ao conectar à API: {e}")
        return None

def get_eventos(jogo_id):
    """Retorna a lista de eventos de uma partida."""
    url = f"{API_BASE_URL}/eventos/{jogo_id}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception as e:
        print(f"Erro ao buscar eventos: {e}")
        return []

def update_placar(jogo_id, gols_casa, gols_fora):
    """Atualiza o placar via API (endpoint POST/PUT)."""
    url = f"{API_BASE_URL}/partida/{jogo_id}/placar"
    payload = {"gols_casa": gols_casa, "gols_fora": gols_fora}
    try:
        response = requests.put(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Erro ao atualizar placar: {e}")
        return False

def add_evento(jogo_id, tempo, tipo, jogador_id, detalhes):
    """Adiciona um evento via API."""
    url = f"{API_BASE_URL}/eventos"
    payload = {
        "jogo_id": jogo_id,
        "tempo": tempo,
        "tipo": tipo,
        "jogador_id": jogador_id,
        "detalhes": detalhes
    }
    try:
        response = requests.post(url, json=payload)
        return response.status_code == 201
    except Exception as e:
        print(f"Erro ao adicionar evento: {e}")
        return False

def update_status_jogo(jogo_id, novo_status):
    """Atualiza o status da partida."""
    url = f"{API_BASE_URL}/partida/{jogo_id}/status"
    payload = {"status": novo_status}
    try:
        response = requests.put(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Erro ao atualizar status: {e}")
        return False