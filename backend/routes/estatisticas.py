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
    """
    Retorna estatísticas agregadas.
    Estratégia: Consulta a tabela pré-processada 'despesas_agregadas' (Opção C do Trade-off).
    Isso garante performance O(1) ou O(N) baixo, sem recalcular milhões de linhas.
    """
    
    # 1. Calcular Totais Gerais (baseado na tabela agregada)
    # Somamos o total de todas as operadoras
    total_geral = db.query(func.sum(models.DespesaAgregada.total_despesas)).scalar() or 0
    
    # Média das despesas entre as operadoras
    media_geral = db.query(func.avg(models.DespesaAgregada.total_despesas)).scalar() or 0

    # 2. Buscar Top 5 Operadoras
    # Ordena pelo maior total e pega as 5 primeiras
    top_5 = db.query(models.DespesaAgregada)\
        .order_by(desc(models.DespesaAgregada.total_despesas))\
        .limit(5)\
        .all()

    return {
        "total_geral": total_geral,
        "media_por_operadora": media_geral,
        "top_5_operadoras": top_5
    }