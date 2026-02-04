
USE teste_intuitive;

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
    @dummy, 
    @v_modalidade, 
    @dummy, 
    @dummy, 
    @dummy, 
    @dummy, 
    @dummy, 
    @v_uf,  
    @dummy, 
    @dummy, 
    @dummy, 
    @dummy, 
    @dummy, 
    @dummy, 
    @dummy, 
    @dummy, 
    @dummy  
)
SET 
    registro_ans = @v_registro,
    cnpj = NULLIF(@v_cnpj, ''),
    razao_social = @v_razao,
    modalidade = @v_modalidade,
    uf = @v_uf;


LOAD DATA LOCAL INFILE 'data/consolidado_despesas.csv'
INTO TABLE despesas
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ';' 
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
    @v_registro, 
    @dummy, 
    @dummy, 
    @v_trimestre, 
    @v_ano, 
    @v_valor
)
SET 
    registro_ans = @v_registro,
    ano = @v_ano,
    trimestre = @v_trimestre,
    valor = REPLACE(@v_valor, ',', '.'),
    
    data_evento = STR_TO_DATE(CONCAT(@v_ano, '-', (@v_trimestre * 3 - 2), '-01'), '%Y-%m-%d');


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
    @dummy 
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


LOAD DATA INFILE '.../data/operadoras_para_banco.csv'
INTO TABLE operadoras
FIELDS TERMINATED BY ';'
IGNORE 1 ROWS
(registro_ans, cnpj, razao_social, modalidade, uf);