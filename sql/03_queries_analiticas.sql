WITH limites_operadora AS (
    SELECT 
        d.registro_ans,
        o.razao_social,
        d.valor,
        d.data_evento,
        
        ROW_NUMBER() OVER (PARTITION BY d.registro_ans ORDER BY d.data_evento ASC) as rn_inicio,
        
        ROW_NUMBER() OVER (PARTITION BY d.registro_ans ORDER BY d.data_evento DESC) as rn_fim
    FROM despesas d
    JOIN operadoras o ON d.registro_ans = o.registro_ans
)
SELECT 
    inicio.registro_ans,
    inicio.razao_social,
    inicio.valor as valor_inicial,
    fim.valor as valor_final,
    ((fim.valor - inicio.valor) / inicio.valor) * 100 as crescimento_percentual
FROM limites_operadora inicio
JOIN limites_operadora fim ON inicio.registro_ans = fim.registro_ans
WHERE 
    inicio.rn_inicio = 1 
    AND fim.rn_fim = 1
    AND inicio.valor > 0 
ORDER BY crescimento_percentual DESC
LIMIT 5;

SELECT 
    o.uf,
    SUM(d.valor) as despesa_total,
    
    SUM(d.valor) / COUNT(DISTINCT d.registro_ans) as media_por_operadora
FROM despesas d
JOIN operadoras o ON d.registro_ans = o.registro_ans
GROUP BY o.uf
ORDER BY despesa_total DESC
LIMIT 5;

WITH media_geral AS (
    SELECT AVG(valor) as valor_medio_global FROM despesas
),
operadoras_acima AS (
    SELECT 
        d.registro_ans,
        COUNT(*) as qtd_trimestres_acima
    FROM despesas d
    JOIN media_geral mg ON d.valor > mg.valor_medio_global
    GROUP BY d.registro_ans
)
SELECT COUNT(*) as qtd_operadoras_alvo
FROM operadoras_acima
WHERE qtd_trimestres_acima >= 2;