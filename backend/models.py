from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from .database import Base

class Operadora(Base):
    __tablename__ = "operadoras"

    # --- Colunas ---
    registro_ans = Column(Integer, primary_key=True, index=True)
    cnpj = Column(String(20), unique=True, index=True)
    razao_social = Column(String(255))
    modalidade = Column(String(100))
    uf = Column(String(2))

    # --- Relacionamento ---
    # back_populates="operadora" aponta para a variável 'operadora' na classe Despesa
    despesas = relationship("Despesa", back_populates="operadora")

class Despesa(Base):
    __tablename__ = "despesas"

    # --- Colunas ---
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # A Foreign Key deve apontar para nome_tabela.nome_coluna
    registro_ans = Column(Integer, ForeignKey("operadoras.registro_ans"))
    data_evento = Column(Date)
    ano = Column(Integer)
    trimestre = Column(Integer)
    valor = Column(Numeric(15, 2))

    # --- Relacionamento ---
    # back_populates="despesas" aponta para a variável 'despesas' na classe Operadora
    operadora = relationship("Operadora", back_populates="despesas")

class DespesaAgregada(Base):
    __tablename__ = "despesas_agregadas"

    # Conforme seu 01_schema_ddl.sql
    id = Column(Integer, primary_key=True, autoincrement=True)
    registro_ans = Column(Integer) # Não fizemos FK aqui para simplificar a importação, mas poderia ter
    razao_social = Column(String(255))
    uf = Column(String(2))
    total_despesas = Column(Numeric(15, 2))
    media_despesas = Column(Numeric(15, 2))
    desvio_padrao = Column(Numeric(15, 2))
    data_processamento = Column(Date) # ou Timestamp    
