import requests
import os
import zipfile
import gc
import re
import pandas as pd
from bs4 import BeautifulSoup
import shutil


MAPA_COLUNAS = {
    'CNPJ': ['nr_cnpj', 'cnp', 'cnpj', 'cnpj_operadora'],
    'RegistroANS': ['reg_ans', 'cd_operadora', 'registro_ans', 'codigo_ans'],
    'RazaoSocial': ['nm_raz_soc', 'nm_razao_social', 'razao_social', 'operadora', 'nome_fantasia'],
    'Valor': ['vl_saldo_final', 'valor', 'vl_despesa', 'valor_despesa', 'vl_evento'],
    'Conta': ['cd_conta_contabil', 'cd_conta', 'nr_conta', 'codigo_conta_contabil'],
    'Descricao': ['ds_conta', 'nm_conta_contabil', 'descricao', 'ds_conta_contabil']
}

# --- Acessa a api ---
def baixar_dados():
    print(">>> 1. Iniciando processo de download...")
    url_base = "https://dadosabertos.ans.gov.br/FTP/PDA/"
    url_categoria = url_base + "demonstracoes_contabeis/"

    try:
        print(f"   Acessando {url_categoria}...")
        resposta_categoria = requests.get(url_categoria)
        soup_categoria = BeautifulSoup(resposta_categoria.text, 'html.parser')
        lista_de_anos = [link.get('href').strip('/') for link in soup_categoria.find_all('a') 
                         if link.get('href') and link.get('href').strip('/').isdigit() and len(link.get('href').strip('/')) == 4]
    except Exception as e:
        print(f"❌ Erro ao acessar site da ANS: {e}")
        return

#Encontra os arquivos
    arquivos_encontrados = []
    for ano in lista_de_anos:
        url_ano = url_categoria + ano + "/"
        try: 
            soup_ano = BeautifulSoup(requests.get(url_ano).text, 'html.parser')
            for link in soup_ano.find_all('a'):
                nome = link.get('href')
                if not nome or not nome.lower().endswith('.zip'): continue
                
                trim = 0
                n_low = nome.lower()
                if '1t' in n_low or '1_trimestre' in n_low: trim = 1
                elif '2t' in n_low or '2_trimestre' in n_low: trim = 2
                elif '3t' in n_low or '3_trimestre' in n_low: trim = 3
                elif '4t' in n_low or '4_trimestre' in n_low: trim = 4
                
                if trim > 0:
                    arquivos_encontrados.append({
                        "ano": int(ano), "trimestre": trim, 
                        "url": url_ano + nome, "nome": nome
                    })
        except: pass

    arquivos_encontrados.sort(key=lambda x: (x['ano'], x['trimestre']), reverse=True)
    ultimos_3 = arquivos_encontrados[:3]
    
    if not ultimos_3:
        print("❌ Nenhum arquivo encontrado.")
        return
#baixa os arquivos
    pasta_root = os.path.join(os.getcwd(), "data")
    if not os.path.exists(pasta_root): os.makedirs(pasta_root)

    for item in ultimos_3:
        pasta_destino = os.path.join(pasta_root, f"{item['ano']}_{item['trimestre']}")
        
        precisa_baixar = True
        if os.path.exists(pasta_destino):
            arquivos_na_pasta = os.listdir(pasta_destino)
            if arquivos_na_pasta:
                print(f"   Pasta {item['ano']}_{item['trimestre']} já existe e contém arquivos. Pulando.")
                precisa_baixar = False
            else:
                shutil.rmtree(pasta_destino)
        
        if precisa_baixar:
            if not os.path.exists(pasta_destino): os.makedirs(pasta_destino)
            print(f"   Baixando {item['ano']} T{item['trimestre']} ({item['nome']})...")
            try:
                r = requests.get(item['url'], stream=True)
                caminho_zip = os.path.join(pasta_root, "temp.zip")
                with open(caminho_zip, 'wb') as f: 
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                with zipfile.ZipFile(caminho_zip, 'r') as z: z.extractall(pasta_destino)
                os.remove(caminho_zip)
            except Exception as e:
                print(f"   ❌ Falha ao baixar {item['url']}: {e}")


#Limpa os valores
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

def normalizar_colunas(df):
    cols_novas = {}
    for col_atual in df.columns:
        col_lower = col_atual.lower().strip()
        for col_padrao, possiveis in MAPA_COLUNAS.items():
            if col_lower in possiveis or col_atual in possiveis:
                cols_novas[col_atual] = col_padrao
                break
    
    df = df.rename(columns=cols_novas)

    cols_presentes = [c for c in df.columns if c in MAPA_COLUNAS.keys()]
    return df[cols_presentes]


def carregar_arquivo_robusto(caminho):
    if caminho.endswith('.xlsx'): return pd.read_excel(caminho)

    try: return pd.read_csv(caminho, sep=';', encoding='utf-8', on_bad_lines='skip', low_memory=False)
    except:
        try: return pd.read_csv(caminho, sep=';', encoding='latin1', on_bad_lines='skip', low_memory=False)
        except: return pd.read_csv(caminho, sep=',', encoding='utf-8', on_bad_lines='skip', low_memory=False)

def identificar_arquivos_nas_pastas(pasta_raiz):
    arquivos = []
    if not os.path.exists(pasta_raiz): return []

    for root, dirs, files in os.walk(pasta_raiz):
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
        
        if ano == 0: continue

        for file in files:
            if file.lower().endswith(('.csv', '.txt', '.xlsx')):
                termos_chave = ['evento', 'sinistro', 'despesa', 'demonstracao', 'contabeis', '1t', '2t', '3t', '4t']
                if any(x in file.lower() for x in termos_chave):
                    arquivos.append((os.path.join(root, file), ano, trim))
    return arquivos

def processar_incrementalmente():
    print(">>> 2. Iniciando processamento incremental com FILTRAGEM CONTÁBIL...")
    arquivo_saida = os.path.join("data", "consolidado_despesas.csv")
    
    if os.path.exists(arquivo_saida): os.remove(arquivo_saida)
    
    arquivos = identificar_arquivos_nas_pastas("data")
    if not arquivos:
        print("\n❌ ERRO FATAL: Nenhum arquivo válido encontrado.")
        return

    arquivos.sort(key=lambda x: (x[1], x[2]))
    primeira_vez = True
    total_registros = 0
    
    print(f"\n   Processando {len(arquivos)} arquivos encontrados...")

    for caminho, ano, trim in arquivos:
        print(f"   -> Lendo: {os.path.basename(caminho)}...")
        try:
            df = carregar_arquivo_robusto(caminho)
            df = normalizar_colunas(df)
            
            if 'Conta' not in df.columns:
                print(f"      ⚠️ [Ignorado] Sem coluna 'Conta'. Colunas atuais: {list(df.columns)}")
                continue

          
            col_conta_limpa = df['Conta'].astype(str).str.replace(r'[^0-9]', '', regex=True)
            mascara_despesa = col_conta_limpa.str.startswith('41', na=False)
            df_filtrado = df[mascara_despesa].copy()
            
            qtd_filtrada = len(df_filtrado)
            if qtd_filtrada == 0:
                print("      ⚠️ [Aviso] Nenhuma linha de despesa encontrada.")
                continue
                
            print(f"      ✅ Filtrado: {qtd_filtrada} registros.")

            if 'Valor' not in df_filtrado.columns:
                print(f"      ❌ ERRO CRÍTICO: Coluna 'Valor' não encontrada após mapeamento. Pulando arquivo.")
                continue

     
            df_filtrado['ValorDespesas'] = df_filtrado['Valor'].apply(limpar_valor_monetario).abs()
            df_filtrado['Ano'] = ano
            df_filtrado['Trimestre'] = trim
       
            cols_finais = ['RegistroANS', 'CNPJ', 'RazaoSocial', 'Trimestre', 'Ano', 'ValorDespesas']
            
            for c in cols_finais:
                if c not in df_filtrado.columns: 
                    df_filtrado[c] = None 
                
            df_export = df_filtrado[cols_finais]
            
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
    pasta_data = "data"
    nome_csv = "consolidado_despesas.csv"
    nome_zip = "consolidado_despesas.zip"
    caminho_csv = os.path.join(pasta_data, nome_csv)
    caminho_zip = os.path.join(pasta_data, nome_zip)
    
    if not os.path.exists(caminho_csv):
        print(f"❌ Erro: O arquivo {nome_csv} não existe.")
        return

    try:
        with zipfile.ZipFile(caminho_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(caminho_csv, arcname=nome_csv)
        print(f"✅ Arquivo compactado com sucesso: {caminho_zip}")
    except Exception as e:
        print(f"❌ Erro ao compactar: {e}")
 
def validar_resultado():
    caminho_arquivo = os.path.join("data", "consolidado_despesas.csv")
    if not os.path.exists(caminho_arquivo): return

    print(">>> Validando arquivo gerado...")
    try:
        df = pd.read_csv(caminho_arquivo, sep=';', encoding='utf-8', nrows=5)
        print(f"   Colunas finais: {list(df.columns)}")
        print(df.to_string())
    except Exception as e:
        print(f"❌ Erro ao ler CSV: {e}")

def raio_x_colunas():
    pass

if __name__ == "__main__":
    baixar_dados()
    processar_incrementalmente()
    compactar_csv_final()
    validar_resultado()