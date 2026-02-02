"""Ponto de entrada da API)"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routes import operadoras, estatisticas



# Cria as tabelas no banco se elas não existirem
Base.metadata.create_all(bind=engine)

# --- AQUI ESTÁ A VARIÁVEL 'app' QUE O UVICORN PROCURA ---
app = FastAPI(
    title="Intuitive Care API - Teste Backend",
    description="API para consulta de operadoras e despesas da ANS",
    version="1.0.0"
)

# Configuração de CORS
origins = [
    "http://localhost:8080",
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Rotas Existentes ---
app.include_router(operadoras.router)

app.include_router(estatisticas.router)

@app.get("/")
def read_root():
    return {"message": "API Intuitive Care está rodando!"}