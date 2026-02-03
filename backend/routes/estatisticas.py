from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from .. import models, schemas, database

router = APIRouter(
    prefix="/api/estatisticas",
    tags=["estatisticas"]
)


@router.get("/", response_model=schemas.EstatisticasResponse)
def get_estatisticas(db: Session = Depends(database.get_db)):
    # 1. Totais Gerais (Mantenha igual)
    total_geral = db.query(func.sum(models.DespesaAgregada.total_despesas)).scalar() or 0
    media_geral = db.query(func.avg(models.DespesaAgregada.total_despesas)).scalar() or 0

    # 2. Top 5 (Mantenha igual)
    top_5 = db.query(models.DespesaAgregada)\
        .order_by(desc(models.DespesaAgregada.total_despesas))\
        .limit(5)\
        .all()

    # 3. NOVO: Agrupamento por UF para o Gráfico
    # SQL equivalente: SELECT uf, SUM(total_despesas) as total FROM despesas_agregadas GROUP BY uf
    distribuicao_uf = db.query(
        models.DespesaAgregada.uf,
        func.sum(models.DespesaAgregada.total_despesas).label("total")
    ).group_by(models.DespesaAgregada.uf).all()

    dados_grafico = [
        {"uf": row.uf, "total": float(row.total or 0)} 
        for row in distribuicao_uf
    ]

    return {
        "total_geral": total_geral,
        "media_por_operadora": media_geral,
        "top_5_operadoras": top_5,
        "despesas_por_uf": dados_grafico,
        
    }