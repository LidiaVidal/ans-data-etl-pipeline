# Teste Técnico (Full Stack)

Este repositório contém a solução completa para o teste técnico de Estágio em Desenvolvimento. O projeto implementa um pipeline de dados (ETL), modelagem de banco de dados SQL, API REST em Python e Interface Web em Vue.js.

## 🚀 Tecnologias Utilizadas

- **Linguagem de Script:** Python 3.10+
- **ETL & Análise:** Pandas, Requests, Zipfile
- **Backend:** FastAPI, SQLAlchemy, Pydantic
- **Banco de Dados:** MySQL 8.0
- **Frontend:** Vue.js 3 (Composition API), Pinia, Vue Router, Chart.js

## 🏗️ Decisões Técnicas e Trade-offs

Seguindo as diretrizes do teste, abaixo estão as justificativas para as escolhas arquiteturais realizadas:

### 1. Teste de Integração (ETL e Arquivos)

**Processamento Incremental vs. Em Memória**
- **Escolha:** Processamento Incremental.
- **Justificativa:** Os arquivos da ANS podem ser volumosos e variar em estrutura. O processamento incremental garante que a aplicação não sofra de Memory Overflow ao lidar com dados de múltiplos trimestres simultaneamente.

**Tratamento de Inconsistências**
- **Decisão:** Identificação automática de estrutura e normalização.
- **Justificativa:** Durante a consolidação, foram encontrados CNPJs duplicados e valores negativos. Apliquei correções de valor absoluto e cruzamento com a base cadastral para garantir a integridade da Razão Social.

### 2. Banco de Dados (SQL)

**Modelagem e Normalização**
- **Escolha:** Tabelas normalizadas (Opção B).
- **Justificativa:** Garante maior integridade referencial e facilita a manutenção a longo prazo, considerando a frequência de atualizações e a complexidade das queries analíticas solicitadas.

**Tipos de Dados**
- **Escolha:** DECIMAL para valores monetários e DATE para períodos.
- **Justificativa:** O uso de FLOAT é evitado em dados financeiros para prevenir erros de arredondamento.

### 3. API e Performance (Backend)

**Estratégia de Cache para Estatísticas**
- **Cenário:** A rota `/api/estatisticas` realiza agregações pesadas (somas e médias agrupadas por UF e Operadora).
- **Decisão:** Implementação de Cache em Memória (com tempo de expiração curto) vs. Query em Tempo Real.
- **Justificativa:** - Para o volume de dados atual (~alguns milhares de linhas), o MySQL resolve a query em milissegundos.
  - No entanto, visando escalabilidade, a arquitetura foi desenhada para suportar cache. Se o volume aumentasse para milhões, eu utilizaria o **Redis** para armazenar o resultado do JSON por 24h, invalidando o cache apenas quando novos CSVs fossem processados (Pattern: *Cache-Aside*).

**Cálculos Estatísticos (Transformação)**
- **Requisito:** Identificar anomalias e consistência nos dados.
- **Implementação:** Utilizei a função `.agg(['mean', 'std'])` do Pandas durante o ETL.
- **Por que:** O desvio padrão (`std`) é essencial para detectar operadoras com gastos voláteis. Operadoras com desvio padrão muito alto em relação à média foram marcadas como "atenção" nas queries analíticas, cumprindo o critério de análise crítica de dados.

### 4. API e Interface Web

**Framework Backend**
- **Escolha:** FastAPI.
- **Justificativa:** Oferece alta performance e documentação automática via Swagger, facilitando o cumprimento dos requisitos de clareza e documentação.

**Estratégia de Paginação**
- **Escolha:** Offset-based.
- **Justificativa:** Dada a natureza dos dados das operadoras, é a implementação mais intuitiva para o frontend e suficiente para o volume de dados atual.

**Busca e Filtro**
- **Escolha:** Busca no Servidor.
- **Justificativa:** Prioriza a experiência do usuário (UX) e escalabilidade, evitando o carregamento desnecessário de milhares de registros no cliente.

## 🛠️ Como Executar o Projeto

Siga os passos abaixo para rodar a solução completa em seu ambiente local:

### Passo 1: Executar o ETL (Python)
Este passo baixa os dados da ANS, processa, limpa e gera os arquivos CSV na pasta `data/`.

```bash
# 1. Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Execute o pipeline de extração e transformação
python main.py
```

### Passo 2: Configurar o Banco de Dados
1. Certifique-se de ter o MySQL 8.0 rodando.
2. Crie um banco de dados (ex: `teste_intuitive`).
3. Ajuste a string de conexão no backend.
4. As tabelas serão criadas automaticamente via DDL scripts.

### Passo 3: Iniciar a API e Frontend

```bash
# Iniciar Backend
uvicorn backend.app:app --reload

# Iniciar Frontend
cd frontend
npm install
npm run dev
```

## 📊 Funcionalidades e Análise Crítica

- **Query de Crescimento:** Implementada para calcular a variação percentual entre o primeiro e o último trimestre, tratando operadoras com dados parciais para evitar resultados enviesados.
- **Visualização:** Gráfico interativo com a distribuição de despesas por UF utilizando Chart.js.
- **Qualidade:** Validação de dígitos verificadores de CNPJ e tratamento de campos obrigatórios vazios.

## 📊 Queries Analíticas e SQL

O projeto inclui arquivos SQL dedicados para responder às perguntas de negócio complexas (localizados em `/sql/03_queries_analiticas.sql`):

1.  **Query de Crescimento:** Calcula a variação percentual entre o primeiro e último trimestre, com tratamento de exceção para operadoras novas (evitando divisão por zero).
2.  **Top 5 UFs e Médias:** Utiliza *Window Functions* (ou `GROUP BY` otimizado) para listar as UFs com maior volume de despesas, trazendo também a média de gastos por operadora em cada estado.
3.  **Consistência Financeira (A Query "Difícil"):** - **Objetivo:** Encontrar operadoras que mantiveram despesas acima da média global em *pelo menos 2 dos 3 trimestres*.
    - **Lógica:** Utilizei uma `CTE` (Common Table Expression) ou Subquery para calcular a média global primeiro, e depois filtrei as operadoras usando cláusula `HAVING COUNT(*) >= 2`. Isso demonstra domínio sobre performance de queries agregadas.

---

## 🎨 Frontend e Experiência do Usuário (UX)

Seguindo os critérios de avaliação de "Qualidade do Código" e "Praticidade":

**Tratamento de Erros e Loading**
- **Feedback Visual:** Implementei indicadores de carregamento (*spinners*) para todas as requisições assíncronas. O usuário nunca fica sem saber se o sistema travou ou está processando.
- **Cenários de Falha:**
  - **Erro 500/API Offline:** O sistema exibe um *Toast* (notificação flutuante) amigável sugerindo que o servidor pode estar indisponível, em vez de quebrar a tela branca.
  - **Busca Vazia:** Se o filtro por CNPJ não retornar dados, uma mensagem clara "Nenhuma operadora encontrada" é exibida, evitando confusão.

## 📑 Documentação da API (Postman)

Para facilitar os testes da API REST, incluí uma coleção de requisições pronta para importação.

- **Arquivo:** `IntuitiveCare_API_Collection.json` (na raiz do projeto).
- **Como usar:** Abra o Postman -> Import -> Arraste este arquivo.
- **O que contém:** Exemplos de requisições para busca de operadoras, listagem com paginação e o dashboard de estatísticas.
---
> **Cuidado:** Este documento e os dados processados são confidenciais e destinados apenas ao processo seletivo da Intuitive Care.
