from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

# --- Schemas Básicos (Representam os dados) ---

class OperadoraBase(BaseModel):
    registro_ans: str = Field(..., alias="RegistroANS")
    cnpj: str = Field(..., alias="CNPJ")
    razao_social: str = Field(..., alias="RazaoSocial")
    uf: Optional[str] = None
    modalidade: Optional[str] = None

    class Config:
        from_attributes = True
        class Config:populate_by_name = True 
        
class OperadoraDetalhe(OperadoraBase):
    pass

class DespesaBase(BaseModel):
    id: int
    ano: int
    trimestre: int
    data_evento: Optional[date] = None
    valor: float
    
    class Config:
        from_attributes = True

# --- Schemas de Resposta Envelopada 

class PaginationMeta(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int

class OperadoraResponse(BaseModel):
    data: List[OperadoraBase]
    meta: PaginationMeta

class TopOperadora(BaseModel):
    razao_social: str
    uf: str
    total_despesas: float
    
    class Config:
        from_attributes = True

class EstatisticasResponse(BaseModel):
    total_geral: float
    media_por_operadora: float
    top_5_operadoras: List[TopOperadora]    