"""(Lógica de enriquecimento e agregação - Teste 2.2 e 2.3)"""
import pandas as pd
import os
import requests
import zipfile
import os

def baixar_cadastro_operadoras():
    """
    Baixa o CSV de operadoras ativas direto da ANS.
    Retorna o DataFrame com os dados cadastrais limpos.
    """
    print(">>> [Enriquecimento] Baixando dados cadastrais das operadoras...")
    url = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/Relatorio_cadop.csv"
    local_path = os.path.join("data", "Relatorio_cadop.csv")

    # Garante que a pasta data existe
    os.makedirs("data", exist_ok=True)

    try:
        if not os.path.exists(local_path):
            r = requests.get(url)
            r.raise_for_status()
            with open(local_path, 'wb') as f:
                f.write(r.content)
            print("   ✅ Download do cadastro concluído.")
        else:
            print("   ℹ️ Arquivo de cadastro já existe localmente.")

        # Tenta ler com diferentes encodings comuns em governo
        try:
            df = pd.read_csv(local_path, sep=';', encoding='latin1', on_bad_lines='skip')
        except:
            df = pd.read_csv(local_path, sep=';', encoding='utf-8', on_bad_lines='skip')
        
        # Mapeamento de colunas para padronizar
        mapa_cols = {
            'REGISTRO_OPERADORA': 'RegistroANS',
            'Registro_ANS': 'RegistroANS',
            'CNPJ': 'CNPJ_Cad',
            'Razao_Social': 'RazaoSocial_Cad',
            'Modalidade': 'Modalidade',
            'UF': 'UF',
            'Reg_ANS': 'RegistroANS', 
            'Codigo_ANS': 'RegistroANS'
        }
        
        df = df.rename(columns=lambda x: mapa_cols.get(x, x))
        
        if 'RegistroANS' in df.columns:
            # Limpeza do RegistroANS (Chave do Join)
            df['RegistroANS'] = df['RegistroANS'].astype(str).str.replace(r'\.0$', '', regex=True)
            
            # Padronização do CNPJ (14 dígitos com zeros à esquerda)
            if 'CNPJ_Cad' in df.columns:
                df['CNPJ_Cad'] = df['CNPJ_Cad'].astype(str).str.replace(r'[^0-9]', '', regex=True)
                df['CNPJ_Cad'] = df['CNPJ_Cad'].str.zfill(14) 
            
            return df
        else:
            print("❌ Erro: Coluna RegistroANS não encontrada no arquivo de cadastro.")
            return pd.DataFrame()

    except Exception as e:
        print(f"❌ Erro ao baixar/ler cadastro: {e}")
        return pd.DataFrame()

def enriquecer_dados(df_despesas):
    """
    Realiza o Left Join entre as Despesas e o Cadastro.
    """
    print(">>> [Enriquecimento] Cruzando dados financeiros com cadastrais...")
    
    # Previne erro de tipo (float vs string) convertendo para object
    df_despesas['RazaoSocial'] = df_despesas['RazaoSocial'].astype('object')
    df_despesas['CNPJ'] = df_despesas['CNPJ'].astype('object')
    df_despesas['RegistroANS'] = df_despesas['RegistroANS'].astype(str).str.replace(r'\.0$', '', regex=True)

    df_cadop = baixar_cadastro_operadoras()
    
    if df_cadop.empty:
        print("⚠️ Atenção: Cadastro vazio ou inválido. O enriquecimento falhará.")
        # Cria colunas vazias para não quebrar o código seguinte
        df_despesas['UF'] = 'ND'
        df_despesas['Modalidade'] = 'Desconhecida'
        return df_despesas

    # 1. Merge (Left Join)
    df_merged = pd.merge(df_despesas, 
                         df_cadop[['RegistroANS', 'CNPJ_Cad', 'RazaoSocial_Cad', 'Modalidade', 'UF']], 
                         on='RegistroANS', 
                         how='left')
    
    # 2. Preencher dados faltantes com o que veio do cadastro
    df_merged['CNPJ'] = df_merged['CNPJ'].fillna(df_merged['CNPJ_Cad'])
    
    # Se Razão Social estiver vazia nas despesas, usa a do cadastro
    mask_nome_ruim = df_merged['RazaoSocial'].isin([None, 'NÃO INFORMADO', 'RAZAO SOCIAL NAO INFORMADA', '', 'nan']) | df_merged['RazaoSocial'].isna()
    df_merged.loc[mask_nome_ruim, 'RazaoSocial'] = df_merged.loc[mask_nome_ruim, 'RazaoSocial_Cad']

    # Preenche UF vazia
    df_merged['UF'] = df_merged['UF'].fillna('ND')

    # 3. Remove colunas auxiliares do join
    df_merged = df_merged.drop(columns=['CNPJ_Cad', 'RazaoSocial_Cad'])
    
    print(f"   ✅ Enriquecimento concluído.")
    return df_merged

def agregar_dados(df):
    """
    Calcula estatísticas (Soma, Média, Desvio Padrão) por Operadora.
    """
    print(">>> [Agregação] Calculando estatísticas por Operadora...")
    
    # Garante que é numérico
    df['ValorDespesas'] = pd.to_numeric(df['ValorDespesas'], errors='coerce').fillna(0)
    
    # Agrupamento
    # Usamos UF e Modalidade no group by para mantê-los no resultado final
    grupos = ['RazaoSocial', 'RegistroANS', 'UF']
    if 'Modalidade' in df.columns:
        grupos.append('Modalidade')

    df_agregado = df.groupby(grupos)['ValorDespesas'].agg(['sum', 'mean', 'std', 'count']).reset_index()
    
    # Renomeia colunas para ficar bonito
    df_agregado = df_agregado.rename(columns={
        'sum': 'TotalDespesas',
        'mean': 'MediaTrimestral',
        'std': 'DesvioPadrao',
        'count': 'QtdTrimestres'
    })
    
    df_agregado = df_agregado.sort_values(by='TotalDespesas', ascending=False)
    
    print(f"   📊 Tabela agregada gerada com {len(df_agregado)} operadoras.")
    return df_agregado

if __name__ == "__main__":
    arquivo_entrada = os.path.join("data", "consolidado_despesas.csv")
    arquivo_saida = os.path.join("data", "despesas_agregadas.csv")
    arquivo_operadoras = os.path.join("data", "operadoras_para_banco.csv")
    
    if os.path.exists(arquivo_entrada):
        print(">>> Iniciando processamento...")
        # Lê os dados brutos de despesas
        df_bruto = pd.read_csv(arquivo_entrada, sep=';', encoding='utf-8', dtype={'RazaoSocial': object, 'CNPJ': object})
        
        # 1. Enriquecer (Juntar com Cadastro da ANS)
        df_rico = enriquecer_dados(df_bruto)
        
        # 2. Gerar Arquivo de Operadoras Únicas (Para o Banco de Dados / Frontend)
        # Isso resolve o problema das colunas Modalidade e UF vazias na tabela
        print("> [Banco de Dados] Preparando arquivo de Operadoras...")
        cols_op = ['RegistroANS', 'CNPJ', 'RazaoSocial', 'Modalidade', 'UF']
        # Filtra apenas colunas que realmente existem
        cols_existentes = [c for c in cols_op if c in df_rico.columns]
        
        df_operadoras_unicas = df_rico[cols_existentes].drop_duplicates(subset=['CNPJ'])
        df_operadoras_unicas.to_csv(arquivo_operadoras, index=False, sep=';', encoding='utf-8')
        print(f"   ✅ Arquivo '{arquivo_operadoras}' gerado para importação no Banco.")

        # 3. Gerar Arquivo de Estatísticas (Para o Gráfico)
        df_final = agregar_dados(df_rico)
        df_final.to_csv(arquivo_saida, index=False, sep=';', encoding='utf-8')
        print(f"   ✅ Arquivo '{arquivo_saida}' gerado com sucesso!")
        
    else:
        print(f"❌ Arquivo de entrada não encontrado: {arquivo_entrada}")
        print("Execute o 'downloader.py' primeiro.")