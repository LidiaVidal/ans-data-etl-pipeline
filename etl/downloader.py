import requests
import os
import zipfile
import gc
import re
import pandas as pd
from bs4 import BeautifulSoup
import shutil

# --- CONFIGURAÇÕES GLOBAIS ---
# --- ATUALIZAÇÃO NAS CONFIGURAÇÕES GLOBAIS ---
MAPA_COLUNAS = {
    'CNPJ': ['nr_cnpj', 'cnp', 'cnpj', 'cd_operadora', 'reg_ans', 'cnpj_operadora'],
    'RazaoSocial': ['nm_raz_soc', 'nm_razao_social', 'razao_social', 'operadora', 'nome_fantasia'],
    'Valor': ['vl_saldo_final', 'valor', 'vl_despesa', 'valor_despesa', 'vl_evento'],
    # Novas colunas essenciais para filtragem
    'Conta': ['cd_conta_contabil', 'cd_conta', 'nr_conta', 'codigo_conta_contabil'],
    'Descricao': ['ds_conta', 'nm_conta_contabil', 'descricao', 'ds_conta_contabil']
}

# --- PARTE 1: DOWNLOADER (Baixar Arquivos) ---
def baixar_dados():
    print(">>> 1. Iniciando processo de download...")
    url_base = "https://dadosabertos.ans.gov.br/FTP/PDA/"
    url_categoria = url_base + "demonstracoes_contabeis/"

    try:
        print(f"   Acessando {url_categoria}...")
        resposta_categoria = requests.get(url_categoria)
        soup_categoria = BeautifulSoup(resposta_categoria.text, 'html.parser')
        # Filtra apenas links que parecem anos (4 dígitos)
        lista_de_anos = [link.get('href').strip('/') for link in soup_categoria.find_all('a') 
                         if link.get('href') and link.get('href').strip('/').isdigit() and len(link.get('href').strip('/')) == 4]
    except Exception as e:
        print(f"❌ Erro ao acessar site da ANS: {e}")
        return

    arquivos_encontrados = []

    # Varrer anos para achar trimestres
    for ano in lista_de_anos:
        url_ano = url_categoria + ano + "/"
        try: 
            soup_ano = BeautifulSoup(requests.get(url_ano).text, 'html.parser')
            for link in soup_ano.find_all('a'):
                nome = link.get('href')
                if not nome or not nome.lower().endswith('.zip'): continue
                
                # Detecção de trimestre
                trim = 0
                n_low = nome.lower()
                if '1t' in n_low or '1_trimestre' in n_low: trim = 1
                elif '2t' in n_low or '2_trimestre' in n_low: trim = 2
                elif '3t' in n_low or '3_trimestre' in n_low: trim = 3
                
                if trim > 0:
                    arquivos_encontrados.append({
                        "ano": int(ano), "trimestre": trim, 
                        "url": url_ano + nome, "nome": nome
                    })
        except: pass

    # Pegar os 3 mais recentes
    arquivos_encontrados.sort(key=lambda x: (x['ano'], x['trimestre']), reverse=True)
    ultimos_3 = arquivos_encontrados[:3]
    
    if not ultimos_3:
        print("❌ Nenhum arquivo de trimestre encontrado no site da ANS.")
        return

    pasta_root = os.path.join(os.getcwd(), "data")
    if not os.path.exists(pasta_root): os.makedirs(pasta_root)

    # 3. Baixar e Extrair
    for item in ultimos_3:
        pasta_destino = os.path.join(pasta_root, f"{item['ano']}_{item['trimestre']}")
        
        # CORREÇÃO: Verifica se a pasta existe E se não está vazia
        precisa_baixar = True
        if os.path.exists(pasta_destino):
            arquivos_na_pasta = os.listdir(pasta_destino)
            if arquivos_na_pasta:
                print(f"   Pasta {item['ano']}_{item['trimestre']} já existe e contém arquivos. Pulando.")
                precisa_baixar = False
            else:
                print(f"   ⚠️ Pasta {item['ano']}_{item['trimestre']} existe mas está VAZIA. Baixando novamente...")
                shutil.rmtree(pasta_destino) # Apaga a pasta vazia/corrompida
        
        if precisa_baixar:
            if not os.path.exists(pasta_destino): os.makedirs(pasta_destino)
            print(f"   Baixando {item['ano']} T{item['trimestre']} ({item['nome']})...")
            try:
                r = requests.get(item['url'], stream=True)
                caminho_zip = os.path.join(pasta_root, "temp.zip")
                with open(caminho_zip, 'wb') as f: 
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print("   Extraindo...")
                with zipfile.ZipFile(caminho_zip, 'r') as z: z.extractall(pasta_destino)
                os.remove(caminho_zip)
            except Exception as e:
                print(f"   ❌ Falha ao baixar {item['url']}: {e}")

# --- PARTE 2: FUNÇÕES AUXILIARES ---

def limpar_valor_monetario(valor):
    if pd.isna(valor) or str(valor).strip() == '': return 0.0
    v = str(valor).strip()
    mult = -1 if '(' in v or ')' in v else 1
    v = re.sub(r'[^\d.,-]', '', v) 
    try:
        if ',' in v and '.' in v: v = v.replace('.', '').replace(',', '.') 
        elif ',' in v: v = v.replace(',', '.') 
        return float(v) * mult
    except: return 0.0

def validar_cnpj(cnpj_input):
    cnpj = re.sub(r'[^0-9]', '', str(cnpj_input))
    if len(cnpj) != 14 or len(set(cnpj)) == 1: return False
    return True # Simplificado

def normalizar_colunas(df):
    cols_novas = {}
    for col_atual in df.columns:
        col_lower = col_atual.lower().strip()
        for col_padrao, possiveis in MAPA_COLUNAS.items():
            if col_lower in possiveis or col_atual in possiveis:
                cols_novas[col_atual] = col_padrao
                break
    
    df = df.rename(columns=cols_novas)
    cols_finais = [c for c in df.columns if c in MAPA_COLUNAS.keys()]
    if not cols_finais: return pd.DataFrame() 
    return df[cols_finais]

def identificar_arquivos_nas_pastas(pasta_raiz):
    """ Procura CSVs de forma recursiva e mostra o que encontrou """
    arquivos = []
    print(f"\n   🔎 Varrendo pasta '{pasta_raiz}' em busca de arquivos...")
    
    if not os.path.exists(pasta_raiz):
        print("   ❌ Pasta 'data' não existe. O download falhou?")
        return []

    for root, dirs, files in os.walk(pasta_raiz):
        # Tenta descobrir Ano/Trimestre pelo nome da pasta pai
        # Ex: data/2023_1/Anexo ou data/2023_1
        ano, trim = 0, 0
        path_parts = root.split(os.sep)
        for part in path_parts:
            if '_' in part and part.replace('_', '').isdigit():
                try:
                    a, t = map(int, part.split('_'))
                    if 2000 < a < 2030 and 1 <= t <= 4:
                        ano, trim = a, t
                        break
                except: pass
        
        if ano == 0: continue # Se não achou ano/trimestre na pasta, ignora

        for file in files:
            if file.lower().endswith(('.csv', '.txt', '.xlsx')):
                # DEBUG: Mostra arquivos encontrados para você ver se o nome bate
                # print(f"      Encontrado: {file} (Pasta: {os.path.basename(root)})") 
                
                termos_chave = ['evento', 'sinistro', 'despesa', 'demonstracao', 'contabeis', '1t', '2t', '3t', '4t']
                if any(x in file.lower() for x in termos_chave):
                    arquivos.append((os.path.join(root, file), ano, trim))
                else:
                    print(f"      ⚠️ Arquivo ignorado (nome não contém palavras-chave): {file}")

    return arquivos

def carregar_arquivo_robusto(caminho):
    if caminho.endswith('.xlsx'): return pd.read_excel(caminho)
    try: return pd.read_csv(caminho, sep=';', encoding='latin1', on_bad_lines='skip', low_memory=False)
    except: return pd.read_csv(caminho, sep=',', encoding='utf-8', on_bad_lines='skip', low_memory=False)

# --- PARTE 3: PROCESSOR ---
# --- PARTE 3: PROCESSOR (Corrigido para incluir Razão Social e Nomes Certos) ---
def processar_incrementalmente():
    print(">>> 2. Iniciando processamento incremental com FILTRAGEM CONTÁBIL...")
    arquivo_saida = os.path.join("data", "consolidado_despesas.csv")
    
    # Se existir arquivo anterior, remove para não duplicar em testes repetidos
    if os.path.exists(arquivo_saida): os.remove(arquivo_saida)
    
    arquivos = identificar_arquivos_nas_pastas("data")
    
    if not arquivos:
        print("\n❌ ERRO FATAL: Nenhum arquivo válido encontrado.")
        return

    arquivos.sort(key=lambda x: (x[1], x[2])) # Ordena por Ano/Trimestre
    primeira_vez = True
    total_registros = 0
    
    print(f"\n   Processando {len(arquivos)} arquivos encontrados...")

    for caminho, ano, trim in arquivos:
        print(f"   -> Lendo: {os.path.basename(caminho)}...")
        
        try:
            # Carrega o arquivo
            df = carregar_arquivo_robusto(caminho)
            
            # Normaliza nomes das colunas (agora inclui Conta e Descricao)
            df = normalizar_colunas(df)
            
            # --- FILTRAGEM CRÍTICA (AQUI ESTÁ O AJUSTE) ---
            # Verifica se conseguimos identificar o que é despesa
            tem_conta = 'Conta' in df.columns
            tem_descricao = 'Descricao' in df.columns
            
            if not tem_conta and not tem_descricao:
                print(f"      ⚠️ [Ignorado] Impossível filtrar despesas (sem colunas de Conta ou Descrição).")
                continue

            # Logica de Filtro:
            # 1. Pelo Código da Conta (Mais preciso): Contas de Despesa Assistencial começam com '41' (Eventos Indenizáveis)
            # 2. Pela Descrição (Fallback): Contém "EVENTOS", "SINISTROS"
            
            mascara_despesa = pd.Series(False, index=df.index)
            
            
           # --- FILTRAGEM CRÍTICA (CORRIGIDO) ---
            
            # 1. Verifica se temos a coluna essencial (Conta)
            if 'Conta' not in df.columns:
                print(f"      ⚠️ [Ignorado] Arquivo sem coluna de Conta Contábil identificada.")
                continue

            # 2. Limpeza da Conta: Transforma em string e remove pontos (ex: '4.1.1.01' vira '41101')
            # Isso é crucial porque alguns arquivos vêm com pontos, outros sem.
            col_conta_limpa = df['Conta'].astype(str).str.replace(r'[^0-9]', '', regex=True)

            # 3. Criação da Máscara (Filtro)
            # A conta '41' representa especificamente "Eventos/Sinistros".
            # Se você usar .startswith('4'), pegará Despesas Administrativas e Comerciais também.
            mascara_despesa = col_conta_limpa.str.startswith('41', na=False)

            # 4. Aplica o filtro
            df_filtrado = df[mascara_despesa].copy()
            
            # --- FIM DA FILTRAGEM ---

            
            qtd_original = len(df)
            qtd_filtrada = len(df_filtrado)
            
            if qtd_filtrada == 0:
                print(f"      ⚠️ [Aviso] Arquivo lido, mas nenhuma linha classificada como Despesa de Eventos (Original: {qtd_original} linhas).")
                continue
                
            print(f"      ✅ Filtrado: {qtd_filtrada} registros de despesas (de {qtd_original} originais).")

            # --- TRATAMENTOS FINAIS ---
            if 'RazaoSocial' not in df_filtrado.columns:
                df_filtrado['RazaoSocial'] = 'NÃO INFORMADO'
                
            df_filtrado['Ano'] = ano
            df_filtrado['Trimestre'] = trim
            
            # Limpeza do Valor
            if 'Valor' in df_filtrado.columns:
                df_filtrado['Valor'] = df_filtrado['Valor'].apply(limpar_valor_monetario)
                # Inverter sinal se necessário (Despesas as vezes vêm negativas em demonstrativos, aqui queremos o valor absoluto ou positivo)
                # O teste pede "Valor numéricos positivos" na validação depois.
                df_filtrado['Valor'] = df_filtrado['Valor'].abs()
            else:
                # Se filtrou a linha mas não achou a coluna valor mapeada
                continue

            # Seleção final
            df_filtrado = df_filtrado.rename(columns={'Valor': 'ValorDespesas'})
            cols_finais = ['CNPJ', 'RazaoSocial', 'Trimestre', 'Ano', 'ValorDespesas']
            
            # Garante que colunas faltantes existam para não quebrar o append
            for c in cols_finais:
                if c not in df_filtrado.columns: df_filtrado[c] = None
                
            df_export = df_filtrado[cols_finais]
            
            # Salva incrementalmente
            df_export.to_csv(arquivo_saida, mode='a', index=False, header=primeira_vez, sep=';', encoding='utf-8')
            
            total_registros += len(df_export)
            primeira_vez = False
            
            del df, df_filtrado, df_export
            gc.collect()

        except Exception as e:
            print(f"      ❌ Erro ao processar arquivo: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n✅ CONSOLIDADO FINALIZADO: {total_registros} registros salvos em {arquivo_saida}")

def compactar_csv_final():
    print(">>> 3. Compactando arquivo consolidado...")
    
    # Definimos os caminhos usando os mesmos padrões do seu código
    pasta_data = "data"
    nome_csv = "consolidado_despesas.csv"
    nome_zip = "consolidado_despesas.zip"
    
    caminho_csv = os.path.join(pasta_data, nome_csv)
    caminho_zip = os.path.join(pasta_data, nome_zip)
    
    # Verificação de segurança: Só compactamos se o arquivo existir
    if not os.path.exists(caminho_csv):
        print(f"❌ Erro: O arquivo {nome_csv} não existe para ser compactado.")
        return

    try:
        # 'w' = write (cria/sobrescreve o zip)
        # zipfile.ZIP_DEFLATED = Algoritmo de compressão padrão (reduz tamanho)
        with zipfile.ZipFile(caminho_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            
            # O segredo está no 'arcname':
            # Ele diz: "Grave o arquivo 'caminho_csv', mas chame-o apenas de 'nome_csv' dentro do zip".
            # Isso evita que o zip contenha pastas indesejadas como "data/consolidado..."
            zf.write(caminho_csv, arcname=nome_csv)
            
        print(f"✅ Arquivo compactado com sucesso: {caminho_zip}")
        
    except Exception as e:
        print(f"❌ Erro ao compactar: {e}")
 
def validar_resultado():
    caminho_arquivo = os.path.join("data", "consolidado_despesas.csv")
    
    if not os.path.exists(caminho_arquivo):
        print("❌ ERRO: O arquivo 'consolidado_despesas.csv' não foi encontrado.")
        return

    print(">>> Carregando arquivo consolidado para validação...")
    try:
        df = pd.read_csv(caminho_arquivo, sep=';', encoding='utf-8')
    except Exception as e:
        print(f"❌ ERRO ao ler CSV: {e}")
        return

    # 1. Checagem de Volume
    qtd_linhas = len(df)
    print(f"\n📊 ESTATÍSTICAS GERAIS:")
    print(f"   - Total de Registros: {qtd_linhas}")
    print(f"   - Colunas Encontradas: {list(df.columns)}")
    
    if qtd_linhas == 0:
        print("❌ ALERTA: O arquivo está vazio! A filtragem foi agressiva demais ou os nomes das colunas não bateram.")
        return

    # 2. Checagem de Conteúdo (Valores)
    print("\n💰 ANÁLISE DE VALORES (ValorDespesas):")
    print(df['ValorDespesas'].describe().apply(lambda x: format(x, 'f')))
    
    # Verifica se tem valores zerados ou negativos (o código deveria ter tratado isso com .abs())
    negativos = df[df['ValorDespesas'] < 0]
    if not negativos.empty:
        print(f"   ⚠️ ALERTA: Encontrados {len(negativos)} registros com valor negativo!")
    else:
        print("   ✅ Nenhum valor negativo encontrado.")

    # 3. Checagem de Consistência (Trimestres)
    print("\n📅 DISTRIBUIÇÃO POR PERÍODO:")
    print(df.groupby(['Ano', 'Trimestre']).size())
    
    # 4. Amostra de Operadoras (Sanity Check)
    print("\n🏢 TOP 5 OPERADORAS (Por volume de registros):")
    print(df['RazaoSocial'].value_counts().head(5))

    print("\n✅ Validação concluída. Se os números acima fazem sentido (valores > 0, operadoras conhecidas), o processamento foi um sucesso.")


def raio_x_colunas():
    print(">>> 🔎 INSPECIONANDO COLUNAS ORIGINAIS...")
    
    # Pega o primeiro arquivo CSV que encontrar na pasta data
    arquivo_alvo = None
    for root, dirs, files in os.walk("data"):
        for f in files:
            if f.endswith(".csv") and "consolidado" not in f:
                arquivo_alvo = os.path.join(root, f)
                break
        if arquivo_alvo: break
    
    if not arquivo_alvo:
        print("❌ Nenhum arquivo bruto encontrado para inspeção.")
        return

    print(f"   Arquivo analisado: {os.path.basename(arquivo_alvo)}")
    try:
        # Lê apenas o cabeçalho
        df = pd.read_csv(arquivo_alvo, sep=';', encoding='latin1', nrows=5)
        if len(df.columns) <= 1: # Tenta outro separador se falhar
            df = pd.read_csv(arquivo_alvo, sep=',', encoding='utf-8', nrows=5)
            
        print("\n📋 LISTA DE COLUNAS NO ARQUIVO BRUTO:")
        for col in df.columns:
            print(f"   - {col}")
            
        print("\n👀 AMOSTRA DE DADOS (Primeiras 3 linhas):")
        print(df.head(3).to_string())
        
    except Exception as e:
        print(f"❌ Erro ao ler: {e}")


if __name__ == "__main__":
    baixar_dados()
    processar_incrementalmente()
    
    compactar_csv_final()
    
    validar_resultado()
    raio_x_colunas()