import requests
import os
import zipfile
from bs4 import BeautifulSoup

url_base = "https://dadosabertos.ans.gov.br/FTP/PDA/"
url_categoria = url_base + "demonstracoes_contabeis/"

resposta_categoria = requests.get(url_categoria)
soup_categoria = BeautifulSoup(resposta_categoria.text, 'html.parser')

lista_de_anos = []

for link in soup_categoria.find_all('a'):
    diretorio = link.get('href')
    
    if diretorio is not None:
        texto = diretorio.strip('/')
        if texto.isdigit() and len(texto) == 4:
            lista_de_anos.append(texto)

arquivos_encontrados = []

for ano in lista_de_anos:

    # Aqui é montado a URL específica daquele ano (ex: .../2023/)
    url_ano = url_categoria + ano + "/"
    
    try: 
    
        resposta_ano = requests.get(url_ano)
        soup_ano = BeautifulSoup(resposta_ano.text, 'html.parser')
        
        links_trimestres = soup_ano.find_all('a')
    
        for link_t in links_trimestres:

            nome_arquivo = link_t.get('href')

            if not nome_arquivo or not nome_arquivo.lower().endswith('.zip'):
                continue
                
            nome_lower = nome_arquivo.lower()
            trimestre_detectado = 0
            
            # Lógica de Resiliência para detectar o número do trimestre
            if '1t' in nome_lower or '1_trimestre' in nome_lower or '1-trimestre' in nome_lower:
                trimestre_detectado = 1
            elif '2t' in nome_lower or '2_trimestre' in nome_lower or '2-trimestre' in nome_lower:
                trimestre_detectado = 2
            elif '3t' in nome_lower or '3_trimestre' in nome_lower or '3-trimestre' in nome_lower:
                trimestre_detectado = 3
            elif '4t' in nome_lower or '4_trimestre' in nome_lower or '4-trimestre' in nome_lower:
                trimestre_detectado = 4
                
            if trimestre_detectado > 0:
                arquivos_encontrados.append({
                    "ano": int(ano),
                    "trimestre": trimestre_detectado,
                    "nome_arquivo": nome_arquivo,
                    "url_completa": url_ano + nome_arquivo
                })
    except Exception as e:
        print(f"Erro ao acessar ano {ano}: {e}")


arquivos_encontrados.sort(key=lambda x: (x['ano'], x['trimestre']), reverse=True)

ultimos_3 = arquivos_encontrados[:3]

print("-" * 50)
print("✅ RESULTADO FINAL: Os 3 últimos trimestres disponíveis são:")
for arquivo in ultimos_3:
    print(f"{arquivo['ano']} - {arquivo['trimestre']}º Trimestre: {arquivo['nome_arquivo']}")
    print(f"URL: {arquivo['url_completa']}")
    print("-" * 20)

pasta_download = "data"

if not os.path.exists(pasta_download):
    os.makedirs(pasta_download)

print(f"Iniciando download de {len(ultimos_3)} arquivos...")

for item in ultimos_3: 
    ano = item['ano']
    trimestre = item['trimestre']
    url = item['url_completa']

    nome_arquivo_local = os.path.join(pasta_download, f"{ano}_{trimestre}.zip")

    print(f"Baixando {ano} - {trimestre}º Trimestre...")

    try:

        resposta = requests.get(url, stream=True)    
        resposta.raise_for_status()

        with open(nome_arquivo_local, 'wb') as arquivo_zip:
            for pedaco in resposta.iter_content(chunk_size=8192):
                arquivo_zip.write(pedaco)
        
        print("Download concluído. Extraindo...")

        # 4. A Extração
        # Cria uma subpasta para não misturar arquivos
        pasta_destino_final = os.path.join(pasta_download, f"{ano}_{trimestre}")
        
        with zipfile.ZipFile(nome_arquivo_local, 'r') as zip_ref:
            zip_ref.extractall(pasta_destino_final)
            
        print(f"Arquivos extraídos em: {pasta_destino_final}")
        print("-" * 30)

    except Exception as e:
        print(f"Erro ao processar {url}: {e}")

        