from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from .database import Base

class Operadora(Base):
    __tablename__ = "operadoras"

    registro_ans = Column(Integer, primary_key=True, index=True)
    cnpj = Column(String(20), unique=True, index=True)
    razao_social = Column(String(255))
    modalidade = Column(String(100))
    uf = Column(String(2))

    despesas = relationship("Despesa", back_populates="operadora")

class Despesa(Base):
    __tablename__ = "despesas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    registro_ans = Column(Integer, ForeignKey("operadoras.registro_ans"))
    data_evento = Column(Date)
    ano = Column(Integer)
    trimestre = Column(Integer)
    valor = Column(Numeric(15, 2))

    operadora = relationship("Operadora", back_populates="despesas")

class DespesaAgregada(Base):
    __tablename__ = "despesas_agregadas"

    
    id = Column(Integer, primary_key=True, autoincrement=True)
    registro_ans = Column(Integer) 
    razao_social = Column(String(255))
    uf = Column(String(2))
    total_despesas = Column(Numeric(15, 2))
    media_despesas = Column(Numeric(15, 2))
    desvio_padrao = Column(Numeric(15, 2))
    data_processamento = Column(Date) 