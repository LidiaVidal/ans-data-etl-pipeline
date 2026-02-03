
CREATE TABLE operadoras (
    registro_ans INT PRIMARY KEY, -- Mudamos de CNPJ para RegistroANS (presente em todos os CSVs)
    cnpj VARCHAR(20),             -- CNPJ vira um campo comum (pode vir do Relatorio_cadop.csv)
    razao_social VARCHAR(255),
    modalidade VARCHAR(100),
    uf CHAR(2),
    INDEX idx_uf (uf)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. Tabela de Despesas
CREATE TABLE despesas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    registro_ans INT,            -- Chave de ligação alterada para bater com o arquivo
    data_evento DATE,            
    ano INT,
    trimestre INT,
    valor DECIMAL(15, 2),
    
    -- Índices
    INDEX idx_registro_ans (registro_ans), -- Facilita o JOIN com operadoras
    INDEX idx_data_evento (data_evento)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 3. Tabela de Agregações
CREATE TABLE despesas_agregadas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    registro_ans INT,            -- Chave de ligação alterada
    razao_social VARCHAR(255),
    uf CHAR(2),
    total_despesas DECIMAL(15, 2),
    media_despesas DECIMAL(15, 2), 
    desvio_padrao DECIMAL(15, 2),  
    
    data_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_registro_ans_agg (registro_ans),
    INDEX idx_uf_total (uf, total_despesas)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;