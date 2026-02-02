"""(Lógica de enriquecimento e agregação - Teste 2.2 e 2.3)"""
import pandas as pd
import os
import requests
import zipfile
import io

def baixar_cadastro_operadoras():
    """
    Baixa o CSV de operadoras ativas direto da ANS (fonte oficial de metadados).
    Retorna o DataFrame com os dados cadastrais.
    """
    print(">>> [Enriquecimento] Baixando dados cadastrais das operadoras...")
    url = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/Relatorio_cadop.csv"
    local_path = os.path.join("data", "Relatorio_cadop.csv")

    try:
        if not os.path.exists(local_path):
            r = requests.get(url)
            r.raise_for_status()
            with open(local_path, 'wb') as f:
                f.write(r.content)
            print("   ✅ Download do cadastro concluído.")
        else:
            print("   ℹ️ Arquivo de cadastro já existe localmente.")

        # Tenta ler com diferentes encodings
        try:
            df = pd.read_csv(local_path, sep=';', encoding='latin1', on_bad_lines='skip')
        except:
            df = pd.read_csv(local_path, sep=';', encoding='utf-8', on_bad_lines='skip')
        
        # Mapeamento de colunas (incluindo correções de nomes recentes da ANS)
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
            # 1. Limpeza do RegistroANS (Chave do Join)
            df['RegistroANS'] = df['RegistroANS'].astype(str).str.replace(r'\.0$', '', regex=True)
            
            # 2. CORREÇÃO CRÍTICA DO CNPJ (Preenchimento de zeros)
            if 'CNPJ_Cad' in df.columns:
                # Remove pontos/traços, converte pra string e força 14 dígitos com zeros à esquerda
                df['CNPJ_Cad'] = df['CNPJ_Cad'].astype(str).str.replace(r'[^0-9]', '', regex=True)
                df['CNPJ_Cad'] = df['CNPJ_Cad'].str.zfill(14) 
            
            return df
        else:
            print("❌ Erro: Coluna RegistroANS não encontrada no arquivo de cadastro.")
            print(f"Colunas disponíveis: {list(df.columns)}")
            return pd.DataFrame()

    except Exception as e:
        print(f"❌ Erro ao baixar/ler cadastro: {e}")
        return pd.DataFrame()

# Mantenha baixar_cadastro_operadoras como está.

def apenas_enriquecer(df_despesas_bruto):
    """
    Apenas realiza o Join para trazer CNPJ e Razão Social corretos.
    """
    # ... (Copie sua lógica de Join/Merge aqui) ...
    # Retorne o df_merged no final
    return df_merged

def apenas_agregar(df_completo_validado):
    """
    Realiza o group by e cálculos estatísticos.
    """
    # ... (Copie sua lógica de groupby aqui) ...
    return df_agregado

def enriquecer_dados(df_despesas):
    """
    Realiza o Left Join entre as Despesas e o Cadastro.
    """
    print(">>> [Enriquecimento] Cruzando dados financeiros com cadastrais...")
    
    # --- CORREÇÃO DO ERRO DE TIPO (FLOAT vs OBJECT) ---
    # Convertemos explicitamente para 'object' (texto) para permitir a inserção de strings
    # em colunas que estavam cheias de NaNs (e por isso eram float).
    df_despesas['RazaoSocial'] = df_despesas['RazaoSocial'].astype('object')
    df_despesas['CNPJ'] = df_despesas['CNPJ'].astype('object')
    # --------------------------------------------------

    df_cadop = baixar_cadastro_operadoras()
    
    if df_cadop.empty:
        print("⚠️ Atenção: Cadastro vazio ou inválido. O enriquecimento falhará.")
        return df_despesas

    # Normalização das chaves para o Join
    df_despesas['RegistroANS'] = df_despesas['RegistroANS'].astype(str).str.replace(r'\.0$', '', regex=True)
    df_cadop['RegistroANS'] = df_cadop['RegistroANS'].astype(str).str.replace(r'\.0$', '', regex=True)

    # 1. Merge (Left Join)
    df_merged = pd.merge(df_despesas, df_cadop[['RegistroANS', 'CNPJ_Cad', 'RazaoSocial_Cad', 'Modalidade', 'UF']], 
                         on='RegistroANS', 
                         how='left')
    
    # 2. Backfill (Preencher vazios com dados do cadastro)
    df_merged['CNPJ'] = df_merged['CNPJ'].fillna(df_merged['CNPJ_Cad'])
    
    mask_nome_ruim = df_merged['RazaoSocial'].isin([None, 'NÃO INFORMADO', 'RAZAO SOCIAL NAO INFORMADA', '']) | df_merged['RazaoSocial'].isna()
    
    # Agora isso vai funcionar pois a coluna RazaoSocial já é do tipo object
    df_merged.loc[mask_nome_ruim, 'RazaoSocial'] = df_merged.loc[mask_nome_ruim, 'RazaoSocial_Cad']

    # 3. Limpeza
    df_merged = df_merged.drop(columns=['CNPJ_Cad', 'RazaoSocial_Cad'])
    
    n_sem_uf = df_merged['UF'].isna().sum()
    print(f"   ✅ Enriquecimento concluído.")
    if n_sem_uf > 0:
        print(f"   ⚠️ Alerta: {n_sem_uf} operadoras sem UF identificada.")
    
    return df_merged

def agregar_dados(df):
    """
    Tarefa 2.3: Agregação.
    """
    print(">>> [Agregação] Calculando estatísticas por Operadora...")
    
    if 'UF' not in df.columns:
        print("❌ ERRO: Coluna UF não existe. O enriquecimento falhou.")
        return pd.DataFrame()

    df['ValorDespesas'] = pd.to_numeric(df['ValorDespesas'], errors='coerce').fillna(0)
    df['UF'] = df['UF'].fillna('ND') # Trata UF vazia para não perder no groupby
    
    # Agrupamento
    df_agregado = df.groupby(['RazaoSocial', 'UF', 'RegistroANS'])['ValorDespesas'].agg(['sum', 'mean', 'std', 'count']).reset_index()
    
    df_agregado.columns = ['RazaoSocial', 'UF', 'RegistroANS', 'TotalDespesas', 'MediaTrimestral', 'DesvioPadrao', 'QtdTrimestres']
    df_agregado = df_agregado.sort_values(by='TotalDespesas', ascending=False)
    
    print(f"   📊 Tabela agregada gerada com {len(df_agregado)} operadoras.")
    return df_agregado

if __name__ == "__main__":
    arquivo_entrada = os.path.join("data", "consolidado_despesas.csv")
    arquivo_saida = os.path.join("data", "despesas_agregadas.csv")
    
    if os.path.exists(arquivo_entrada):
        # Lendo forçando object nas colunas críticas para segurança extra
        df_bruto = pd.read_csv(arquivo_entrada, sep=';', encoding='utf-8', dtype={'RazaoSocial': object, 'CNPJ': object})
        
        df_rico = enriquecer_dados(df_bruto)
        
        if 'UF' in df_rico.columns:
            df_agg = agregar_dados(df_rico)
            df_agg.to_csv(arquivo_saida, index=False, sep=';', encoding='utf-8')
            print(f"✅ Arquivo final salvo em: {arquivo_saida}")
            print(df_agg.head())
        else:
            print("❌ Falha na agregação.")
    else:
        print("❌ Arquivo consolidado não encontrado.")