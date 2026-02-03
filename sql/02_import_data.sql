-- Habilita o banco correto
USE teste_intuitive;

-- 1. IMPORTAR OPERADORAS (Relatorio_cadop.csv)
-- Mapeando exatamente as 20 colunas do arquivo
LOAD DATA LOCAL INFILE 'data/Relatorio_cadop.csv'
INTO TABLE operadoras
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ';' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
    @v_registro, 
    @v_cnpj, 
    @v_razao, 
    @dummy, -- Nome Fantasia
    @v_modalidade, 
    @dummy, -- Logradouro
    @dummy, -- Numero
    @dummy, -- Complemento
    @dummy, -- Bairro
    @dummy, -- Cidade
    @v_uf,  -- UF
    @dummy, -- CEP
    @dummy, -- DDD
    @dummy, -- Telefone
    @dummy, -- Fax
    @dummy, -- Endereco_eletronico
    @dummy, -- Representante
    @dummy, -- Cargo_Representante
    @dummy, -- Regiao_de_Comercializacao
    @dummy  -- Data_Registro_ANS
)
SET 
    registro_ans = @v_registro,
    cnpj = NULLIF(@v_cnpj, ''),
    razao_social = @v_razao,
    modalidade = @v_modalidade,
    uf = @v_uf;

-- 2. IMPORTAR DESPESAS (consolidado_despesas.csv)
LOAD DATA LOCAL INFILE 'data/consolidado_despesas.csv'
INTO TABLE despesas
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ';' 
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
    @v_registro, 
    @dummy, -- CNPJ vazio
    @dummy, -- RazaoSocial vazia
    @v_trimestre, 
    @v_ano, 
    @v_valor
)
SET 
    registro_ans = @v_registro,
    ano = @v_ano,
    trimestre = @v_trimestre,
    valor = REPLACE(@v_valor, ',', '.'),
    -- Lógica de Data: 1º dia do mês inicial do trimestre
    data_evento = STR_TO_DATE(CONCAT(@v_ano, '-', (@v_trimestre * 3 - 2), '-01'), '%Y-%m-%d');

-- 3. IMPORTAR AGREGADOS (despesas_agregadas.csv)
LOAD DATA LOCAL INFILE 'data/despesas_agregadas.csv'
INTO TABLE despesas_agregadas
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ';' 
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
    @v_razao,
    @v_uf,
    @v_registro,
    @v_total,
    @v_media,
    @v_desvio,
    @dummy -- QtdTrimestres
)
SET 
    registro_ans = @v_registro,
    razao_social = @v_razao,
    uf = @v_uf,
    total_despesas = @v_total,
    media_despesas = @v_media,
    desvio_padrao = @v_desvio;

    total_despesas = REPLACE(@v_total, ',', '.'),
    media_despesas = REPLACE(@v_media, ',', '.'),
    desvio_padrao  = REPLACE(@v_desvio, ',', '.');