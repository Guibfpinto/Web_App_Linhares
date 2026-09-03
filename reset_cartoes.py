# reset_cartoes.py
import os
import sys
import json
import pandas as pd
from pathlib import Path

# Adiciona o diretório do projeto ao path (opcional, mas mantido)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import inicializar_cartoes_por_df

def forcar_reset():
    categoria = "profissional"
    print(f"🔄 Forçando reset para {categoria}...")

    # Caminho absoluto do CSV de estatísticas
    script_dir = Path(__file__).resolve().parent
    csv_path = script_dir / "data" / "estatisticas_jogadores" / "estatisticas_jogadores_profissional_2026.csv"

    if not csv_path.exists():
        print(f"❌ CSV não encontrado em: {csv_path}")
        return

    print(f"✅ CSV encontrado em: {csv_path}")

    try:
        df = pd.read_csv(csv_path, sep=';', encoding='utf-8-sig')
        print(f"   Colunas: {df.columns.tolist()}")
        print(f"   Linhas: {len(df)}")
    except Exception as e:
        print(f"❌ Erro ao ler CSV: {e}")
        return

    # Processa os cartões a partir do DataFrame
    cartoes, datas = inicializar_cartoes_por_df(df, categoria, {})

    if not cartoes:
        print("⚠️ Nenhum jogador processado. Verifique o CSV.")
        return

    # ============================================================
    # SALVA O JSON NO CAMINHO ABSOLUTO ESPECIFICADO
    # ============================================================
    caminho_json = Path(r"C:\BDAnaliseElencoLinharesFC\projeto_web\cartoes_acumulados_profissional.json")

    # Garante que a pasta exista
    caminho_json.parent.mkdir(parents=True, exist_ok=True)

    # Prepara os dados para serialização
    dados = {
        'cartoes': cartoes,
        'datas_globais': datas
    }

    try:
        with open(caminho_json, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON salvo em: {caminho_json}")
    except Exception as e:
        print(f"❌ Erro ao salvar JSON: {e}")
        return

    # Exibe um resumo
    print(f"✅ Reset concluído. {len(cartoes)} jogadores processados.")
    print("📋 Primeiros jogadores:")
    for nome in list(cartoes.keys())[:5]:
        print(f"  - {nome}: amarelos={cartoes[nome].get('amarelos', 0)}")

if __name__ == "__main__":
    forcar_reset()