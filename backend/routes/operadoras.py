from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import or_ # <--- IMPORTANTE: Importar o operador OR
from typing import List, Optional # <--- Importar Optional
import math
import re

# Importando nossos módulos locais
from .. import models, schemas, database

# Cria o "roteador" para agrupar as URLs deste arquivo
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
    search: Optional[str] = Query(None, description="Busca por Razão Social ou CNPJ"), # <--- NOVO PARÂMETRO
    db: Session = Depends(database.get_db)
):
    # 1. Base da Query
    query = db.query(models.Operadora)

    # 2. Aplicar Filtro de Busca (Se houver)
    if search:
        # Remove caracteres especiais caso seja uma busca por CNPJ
        termo_limpo = search.strip()
        search_cnpj = re.sub(r'\D', '', termo_limpo)
        
        # Filtra onde (CNPJ contém o termo) OU (Razão Social contém o termo)
        query = query.filter(
            or_(
                models.Operadora.razao_social.ilike(f"%{termo_limpo}%"), # ilike = case insensitive
                models.Operadora.cnpj.like(f"%{search_cnpj}%") if search_cnpj else False
            )
        )

    # 3. Contar total (já filtrado)
    total_registros = query.count()

    # 4. Paginação
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
    # 1. Limpeza
    cnpj_limpo = limpar_cnpj(cnpj)
    
    # 2. Validação de Formato (Opcional, mas boa prática de UX/Feedback)
    if len(cnpj_limpo) != 14:
        raise HTTPException(
            status_code=400, 
            detail="CNPJ inválido. O valor deve conter 14 dígitos numéricos."
        )

    # 3. Busca no Banco
    # Nota: Lembre-se de adicionar index=True ao campo CNPJ no models.py para performance
    operadora = db.query(models.Operadora).filter(models.Operadora.cnpj == cnpj_limpo).first()

    # 4. Tratamento de Erro (Conforme solicitado no PDF)
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

    # 1. Buscamos a operadora primeiro
    operadora = db.query(models.Operadora).filter(models.Operadora.cnpj == cnpj_limpo).first()

    if not operadora:
        raise HTTPException(
            status_code=404, 
            detail=f"Operadora com CNPJ {cnpj} não encontrada."
        )

    # 2. O SQLAlchemy faz a mágica aqui através do relationship
    # Ele busca na tabela de despesas onde registro_ans bate com o da operadora
    return operadora.despesas