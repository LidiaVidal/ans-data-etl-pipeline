"""(Lógica de limpeza e validação - Teste 1.3 e 2.1)"""
import pandas as pd
import re
import os

def validar_cnpj_calculo(cnpj_in):
    """
    Realiza o cálculo matemático (Módulo 11) para validar o CNPJ.
    Retorna True se válido, False se inválido.
    """
    # 1. Limpeza básica: remove tudo que não for dígito
    cnpj = re.sub(r'[^0-9]', '', str(cnpj_in))

    # 2. Verifica tamanho e sequências repetidas (ex: 00000000000000)
    if len(cnpj) != 14 or len(set(cnpj)) == 1:
        return False

    # 3. Cálculo dos Dígitos Verificadores (Algoritmo Módulo 11)
    # Lista de pesos para o primeiro dígito
    pesos_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    
    # Cálculo do primeiro dígito
    soma = sum(int(cnpj[i]) * pesos_1[i] for i in range(12))
    resto = soma % 11
    d1 = 0 if resto < 2 else 11 - resto

    if int(cnpj[12]) != d1:
        return False

    # Lista de pesos para o segundo dígito (inclui o d1 calculado)
    pesos_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    
    # Cálculo do segundo dígito
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
    
    # Validação 1: CNPJ (Agora temos certeza que a coluna existe e está preenchida)
    # Importante: Garantir que CNPJ é string
    df['CNPJ'] = df['CNPJ'].astype(str)
    df['flag_cnpj_valido'] = df['CNPJ'].apply(validar_cnpj_calculo)
    
    qtd_invalidos = (~df['flag_cnpj_valido']).sum()
    print(f"   -> CNPJs matematicamente inválidos: {qtd_invalidos}")

    # Validação 2: Valores
    # (Sua lógica existente de converter para numérico e abs())
    if 'ValorDespesas' in df.columns:
        df['ValorDespesas'] = pd.to_numeric(df['ValorDespesas'], errors='coerce').fillna(0.0).abs()

    return df

def limpar_e_validar_dados(caminho_arquivo_entrada):
    """
    Lê o CSV consolidado, aplica regras de negócio e validações.
    Retorna o DataFrame limpo pronto para o próximo passo.
    """
    print(f">>> Iniciando processamento e validação de: {caminho_arquivo_entrada}")
    
    if not os.path.exists(caminho_arquivo_entrada):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo_entrada}")

    # Carregamos como string primeiro para não perder zeros à esquerda do CNPJ
    df = pd.read_csv(caminho_arquivo_entrada, sep=';', encoding='utf-8', dtype={'CNPJ': str})
    
    # --- 1. Validação de CNPJ (Trade-off: Flagging) ---
    # Aplicamos a função matemática linha a linha
    # Justificativa: Preservar dados para auditoria em vez de dropar linhas (Requisito 2.1 PDF)
    print("   Aplicando validação matemática de CNPJ...")
    df['flag_cnpj_valido'] = df['CNPJ'].apply(validar_cnpj_calculo)
    
    # Estatística rápida para você ver no console
    invalidos = len(df[~df['flag_cnpj_valido']])
    print(f"   -> CNPJs Inválidos detectados: {invalidos}")

    # --- 2. Tratamento de Valores Numéricos ---
    # Requisito 2.1: Valores numéricos positivos
    # Usamos abs() para garantir que despesas (mesmo que venham negativas do balanço) sejam tratadas como magnitude
    if 'ValorDespesas' in df.columns:
        # Garante que é float
        df['ValorDespesas'] = pd.to_numeric(df['ValorDespesas'], errors='coerce').fillna(0.0)
        df['ValorDespesas'] = df['ValorDespesas'].abs()
    
    # --- 3. Tratamento de Razão Social ---
    # Requisito 2.1: Razão Social não vazia
    # Estratégia: Preencher com valor padrão para não perder o registro financeiro
    if 'RazaoSocial' in df.columns:
        df['RazaoSocial'] = df['RazaoSocial'].fillna("RAZAO SOCIAL NAO INFORMADA")
        df['RazaoSocial'] = df['RazaoSocial'].str.strip().str.upper() # Padronização extra
    
    print(">>> Validação concluída com sucesso.")
    return df

# Bloco para teste isolado (se você rodar python etl/processor.py)
if __name__ == "__main__":
    caminho = os.path.join("data", "consolidado_despesas.csv")
    try:
        df_limpo = limpar_e_validar_dados(caminho)
        print(df_limpo.head())
        # Opcional: Salvar para conferência
        # df_limpo.to_csv("data/debug_processor.csv", index=False, sep=';')
    except Exception as e:
        print(f"Erro: {e}")