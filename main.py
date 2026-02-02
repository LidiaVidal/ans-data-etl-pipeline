import pandas as pd
import os
from etl import downloader
from etl import processor
from etl import aggregator # (ou o nome do seu arquivo de agregação)

def main():
    # 1. DOWNLOAD (Ingestão)
    # Executa o fluxo de download e gera o consolidado bruto (sem CNPJ confiável ainda)
    downloader.baixar_dados()
    downloader.processar_incrementalmente() 
    
    caminho_bruto = os.path.join("data", "consolidado_despesas.csv")
    if not os.path.exists(caminho_bruto):
        print("❌ Erro: Arquivo bruto não gerado.")
        return

    # Carrega o bruto
    print("\n>>> CARREGANDO DADOS BRUTOS...")
    df_bruto = pd.read_csv(caminho_bruto, sep=';', encoding='utf-8', dtype=str)

    # 2. ENRIQUECIMENTO (Passo 2.2 trazido para antes do 2.1)
    # Justificativa: Precisamos do CNPJ do cadastro para poder validá-lo.
    print("\n>>> EXECUTANDO ENRIQUECIMENTO (JOIN)...")
    df_enriquecido = aggregator.enriquecer_dados(df_bruto) # Use a função ajustada

    # 3. VALIDAÇÃO (Passo 2.1)
    # Agora validamos sobre os dados enriquecidos
    print("\n>>> EXECUTANDO VALIDAÇÃO DE DADOS...")
    df_validado = processor.aplicar_validacoes(df_enriquecido) # Use a função ajustada

    # Opcional: Salvar intermediário para auditoria (ponto extra de "análise crítica")
    df_validado.to_csv("data/debug_dados_completos.csv", index=False, sep=';')

    # 4. AGREGAÇÃO (Passo 2.3)
    print("\n>>> EXECUTANDO AGREGAÇÃO FINAL...")
    df_final = aggregator.agregar_dados(df_validado) # Use a função ajustada

    # 5. SALVAR E COMPACTAR
    caminho_final = os.path.join("data", "despesas_agregadas.csv")
    df_final.to_csv(caminho_final, index=False, sep=';', encoding='utf-8')
    print(f"\n✅ PROCESSO CONCLUÍDO! Arquivo final gerado: {caminho_final}")
    
    # Aqui você chamaria a compactação final exigida no PDF

if __name__ == "__main__":
    main()