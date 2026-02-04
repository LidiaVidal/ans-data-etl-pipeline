from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import or_ 
from typing import List, Optional 
import math
import re


from .. import models, schemas, database


router = APIRouter(
    prefix="/api/operadoras",
    tags=["operadoras"]
)

def limpar_cnpj(cnpj: str) -> str:
    """Remove caracteres não numéricos do CNPJ."""
    return re.sub(r'\D', '', cnpj)


@router.get("/", response_model=schemas.OperadoraResponse)
def list_operadoras(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None, description="Busca por Razão Social ou CNPJ"),
    db: Session = Depends(database.get_db)
):
    
    query = db.query(models.Operadora)

    
    if search:
        
        termo_limpo = search.strip()
        search_cnpj = re.sub(r'\D', '', termo_limpo)
        
        
        query = query.filter(
            or_(
                models.Operadora.razao_social.like(f"%{termo_limpo}%"),
                models.Operadora.cnpj.like(f"%{search_cnpj}%") if search_cnpj else False
            )
        )

    
    total_registros = query.count()

    
    skip = (page - 1) * limit
    operadoras = query.offset(skip).limit(limit).all()
    
    total_pages = math.ceil(total_registros / limit) if limit > 0 else 1

    return {
        "data": operadoras,
        "meta": {
            "total": total_registros,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }
    }

@router.get("/{cnpj}", response_model=schemas.OperadoraDetalhe)
def get_operadora(
    cnpj: str = Path(..., title="CNPJ da Operadora", description="Aceita apenas números ou com formatação"),
    db: Session = Depends(database.get_db)
):
    """
    Busca os detalhes de uma operadora pelo CNPJ.
    Realiza sanitização do input antes da busca.
    """
    
    cnpj_limpo = limpar_cnpj(cnpj)
    
    if len(cnpj_limpo) != 14:
        raise HTTPException(
            status_code=400, 
            detail="CNPJ inválido. O valor deve conter 14 dígitos numéricos."
        )

    operadora = db.query(models.Operadora).filter(models.Operadora.cnpj == cnpj_limpo).first()

    if not operadora:
        raise HTTPException(
            status_code=404, 
            detail=f"Operadora com CNPJ {cnpj} não encontrada."
        )

    return operadora


@router.get("/{cnpj}/despesas", response_model=List[schemas.DespesaBase])
def get_operadora_despesas(
    cnpj: str = Path(..., title="CNPJ"),
    db: Session = Depends(database.get_db)
):
    """
    Retorna o histórico de despesas de uma operadora específica.
    """
    cnpj_limpo = limpar_cnpj(cnpj)

    operadora = db.query(models.Operadora).filter(models.Operadora.cnpj == cnpj_limpo).first()

    if not operadora:
        raise HTTPException(
            status_code=404, 
            detail=f"Operadora com CNPJ {cnpj} não encontrada."
        )

    return operadora.despesas