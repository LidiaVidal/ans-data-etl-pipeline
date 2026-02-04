import pandas as pd
import os
from etl import downloader
from etl import processor
from etl import aggregator 

def main():
    # 1. DOWNLOAD (Ingestão)
    downloader.baixar_dados()
    downloader.processar_incrementalmente() 
    
    caminho_bruto = os.path.join("data", "consolidado_despesas.csv")
    if not os.path.exists(caminho_bruto):
        print("❌ Erro: Arquivo bruto não gerado.")
        return

    
    print("\n>>> CARREGANDO DADOS BRUTOS...")
    df_bruto = pd.read_csv(caminho_bruto, sep=';', encoding='utf-8', dtype=str)

    # 2. ENRIQUECIMENTO
    print("\n>>> EXECUTANDO ENRIQUECIMENTO (JOIN)...")
    df_enriquecido = aggregator.enriquecer_dados(df_bruto) 

    # 3. VALIDAÇÃO 
    print("\n>>> EXECUTANDO VALIDAÇÃO DE DADOS...")
    df_validado = processor.aplicar_validacoes(df_enriquecido) 

    df_validado.to_csv("data/debug_dados_completos.csv", index=False, sep=';')


    print("\n>>> EXECUTANDO AGREGAÇÃO FINAL...")
    df_final = aggregator.agregar_dados(df_validado)

    # 5. SALVAR E COMPACTAR
    caminho_final = os.path.join("data", "despesas_agregadas.csv")
    df_final.to_csv(caminho_final, index=False, sep=';', encoding='utf-8')
    print(f"\n✅ PROCESSO CONCLUÍDO! Arquivo final gerado: {caminho_final}")


if __name__ == "__main__":
    main()