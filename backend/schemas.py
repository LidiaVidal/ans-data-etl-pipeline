from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class OperadoraBase(BaseModel):
    registro_ans: int = Field(..., alias="RegistroANS")
    cnpj: str = Field(..., alias="CNPJ")
    razao_social: str = Field(..., alias="RazaoSocial")
    uf: Optional[str] = Field(None, alias="UF") 
    modalidade: Optional[str] = Field(None, alias="Modalidade")

    class Config:
        from_attributes = True
        populate_by_name = True 
        
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


class DespesaUF(BaseModel):
    uf: str
    total: float
    
    class Config:
        from_attributes = True

class EstatisticasResponse(BaseModel):
    total_geral: float
    media_por_operadora: float
    top_5_operadoras: List[TopOperadora]
    despesas_por_uf: List[DespesaUF]  