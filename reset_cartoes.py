# reset_cartoes.py
import os
import sys
import pandas as pd
from pathlib import Path

# Adiciona o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import inicializar_cartoes_por_df, salvar_cartoes_json

def forcar_reset():
    categoria = "profissional"
    print(f"🔄 Forçando reset para {categoria}...")

    # Caminho absoluto do CSV
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

    # Processa usando a função que recebe DataFrame
    cartoes, datas = inicializar_cartoes_por_df(df, categoria, {})

    if cartoes:
        salvar_cartoes_json(cartoes, categoria, datas)
        print(f"✅ Reset concluído. {len(cartoes)} jogadores processados.")
        print("📋 Primeiros jogadores:")
        for nome in list(cartoes.keys())[:5]:
            print(f"  - {nome}: amarelos={cartoes[nome].get('amarelos', 0)}")
    else:
        print("⚠️ Nenhum jogador processado. Verifique se o CSV tem dados e a lógica está correta.")
        # Mostra alguns nomes para diagnóstico
        print("   Nomes no CSV (primeiros 5):", df['jogador'].head(5).tolist())

if __name__ == "__main__":
    forcar_reset()