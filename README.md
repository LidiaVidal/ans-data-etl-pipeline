# Teste Técnico - Intuitive Care (Backend)

## Autor
**Nome:** Lídia Vidal

**Linguagem escolhida:** Python

## Sobre o Projeto
Este projeto realiza a extração, transformação e consolidação de dados financeiros da API de Dados Abertos da ANS, focado nas Despesas com Eventos/Sinistros das operadoras.

---

## 1. Instruções de Execução

### Pré-requisitos
*  Python 3.9+, bibliotecas específica

### Instalação
*  `pip install -r requirements.txt`

### Como Rodar
1. `source venv/bin/activate`

---

## 2. Decisões Técnicas e Trade-offs (Teste 1)

### 2.1 Processamento de Arquivos: Memória vs. Incremental 
**Abordagem Escolhida:** Processamento Incremental (File-by-File). Justificativa: Optei por processar os arquivos sequencialmente em vez de carregar todo o volume de dados (3 trimestres) na memória RAM de uma única vez.
**Justificativa:** Embora carregar tudo em memória (ex: concatenando DataFrames) pudesse ser ligeiramente mais rápido em máquinas potentes, a abordagem incremental é mais segura e escalável. Ela previne erros de MemoryError em ambientes com recursos limitados (como containers Docker ou máquinas CI/CD) e garante que o script funcione independente do aumento do volume de dados históricos da ANS.

### Tratamento de Inconsistências e Padronização
Durante a consolidação dos dados, foram implementadas as seguintes estratégias para garantir a integridade e uniformidade do *dataset*, conforme os desafios propostos:

* **Heterogeneidade de Formatos (CSV/TXT/XLSX):**
    Utilizei uma função de leitura robusta (`carregar_arquivo_robusto`) capaz de detectar e decodificar automaticamente diferentes *encodings* (`latin1` vs `utf-8`) e separadores (`;` vs `,`). Essa abordagem foi necessária pois a ANS não mantém um padrão estrito entre trimestres, e arquivos históricos frequentemente apresentam formatos legados.

* **Padronização de Colunas:**
    Desenvolvi um dicionário de mapeamento (`MAPA_COLUNAS`) que unifica nomenclaturas divergentes encontradas nos arquivos (ex: colunas como `'vl_saldo_final'` e `'valor_despesa'` são normalizadas para `'ValorDespesas'`). Isso soluciona o problema de esquemas de colunas variados sem a necessidade de intervenção manual.

* **Valores Numéricos e Negativos:**
    Identifiquei que as demonstrações contábeis frequentemente representam despesas com sinal negativo ou entre parênteses.
    * **Tratamento:** Apliquei limpeza via Regex para remover caracteres não numéricos e utilizei a função `.abs()` para obter o valor absoluto.
    * **Justificativa:** Para a análise de sinistralidade proposta, o foco é a magnitude da despesa (valor positivo). Essa normalização corrige inconsistências onde o mesmo tipo de evento contábil aparecia ora como positivo, ora como negativo nos dados brutos.

* **Resiliência a Estruturas de Diretórios:**
    Em substituição a caminhos estáticos, implementei uma varredura recursiva (`os.walk`) para localizar os arquivos de despesas. Essa decisão técnica endereça diretamente o alerta sobre trimestres que possuem múltiplas subpastas ou estruturas de diretório imprevisíveis após a descompactação
