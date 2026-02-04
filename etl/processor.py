"""(Lógica de limpeza e validação - Teste 1.3 e 2.1)"""
import pandas as pd
import re
import os

def validar_cnpj_calculo(cnpj_in):
    """
    Realiza o cálculo matemático (Módulo 11) para validar o CNPJ.
    """
    cnpj = re.sub(r'[^0-9]', '', str(cnpj_in))

    if len(cnpj) != 14 or len(set(cnpj)) == 1:
        return False

    pesos_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    
    soma = sum(int(cnpj[i]) * pesos_1[i] for i in range(12))
    resto = soma % 11
    d1 = 0 if resto < 2 else 11 - resto

    if int(cnpj[12]) != d1:
        return False

    pesos_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    
    soma = sum(int(cnpj[i]) * pesos_2[i] for i in range(13))
    resto = soma % 11
    d2 = 0 if resto < 2 else 11 - resto

    if int(cnpj[13]) != d2:
        return False

    return True

def aplicar_validacoes(df):
    """
    Recebe um DataFrame JÁ COM CNPJ (pós-join) e aplica as validações.
    """
    print(">>> [Validação] Iniciando validação de regras de negócio...")
    
    df['CNPJ'] = df['CNPJ'].astype(str)
    df['flag_cnpj_valido'] = df['CNPJ'].apply(validar_cnpj_calculo)
    
    qtd_invalidos = (~df['flag_cnpj_valido']).sum()
    print(f"   -> CNPJs matematicamente inválidos: {qtd_invalidos}")

    if 'ValorDespesas' in df.columns:
        df['ValorDespesas'] = pd.to_numeric(df['ValorDespesas'], errors='coerce').fillna(0.0).abs()

    return df

def limpar_e_validar_dados(caminho_arquivo_entrada):

    print(f">>> Iniciando processamento e validação de: {caminho_arquivo_entrada}")
    
    if not os.path.exists(caminho_arquivo_entrada):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo_entrada}")

    df = pd.read_csv(caminho_arquivo_entrada, sep=';', encoding='utf-8', dtype={'CNPJ': str})

    print("   Aplicando validação matemática de CNPJ...")
    df['flag_cnpj_valido'] = df['CNPJ'].apply(validar_cnpj_calculo)
    

    invalidos = len(df[~df['flag_cnpj_valido']])
    print(f"   -> CNPJs Inválidos detectados: {invalidos}")

    if 'ValorDespesas' in df.columns:

        df['ValorDespesas'] = pd.to_numeric(df['ValorDespesas'], errors='coerce').fillna(0.0)
        df['ValorDespesas'] = df['ValorDespesas'].abs()

    if 'RazaoSocial' in df.columns:
        df['RazaoSocial'] = df['RazaoSocial'].fillna("RAZAO SOCIAL NAO INFORMADA")
        df['RazaoSocial'] = df['RazaoSocial'].str.strip().str.upper() 
    print(">>> Validação concluída com sucesso.")
    return df

if __name__ == "__main__":
    caminho = os.path.join("data", "consolidado_despesas.csv")
    try:
        df_limpo = limpar_e_validar_dados(caminho)
        print(df_limpo.head())
       
    except Exception as e:
        print(f"Erro: {e}")