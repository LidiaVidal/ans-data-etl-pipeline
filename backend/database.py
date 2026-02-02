"""Conexão com o banco criada no Teste 3)"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ------------------------------------------------------------------
# CONFIGURAÇÃO DE CONEXÃO
# ------------------------------------------------------------------
# Substitua abaixo pelo seu usuário, senha, host e nome do banco.
# Exemplo Postgres: "postgresql://usuario:senha@localhost/nome_do_banco"
# Exemplo MySQL: "mysql+mysqlconnector://usuario:senha@localhost/nome_do_banco"
SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://lidia:8070@localhost/teste_intuitive?charset=utf8mb4"

# Cria o motor de conexão.
# Se for SQLite (apenas teste), precisaria de connect_args={"check_same_thread": False}
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Cria a fábrica de sessões. Cada requisição terá sua própria sessão.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os seus Models (tabelas) herdarem
Base = declarative_base()

# Função auxiliar para injetar dependência nas rotas (Dependency Injection)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()