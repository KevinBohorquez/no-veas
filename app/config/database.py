# app/config/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# URL de conexión (usar sakila o railway según prefieras)
DATABASE_URL = os.getenv("DATABASE_URL")

# Crear engine
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Ver queries SQL en logs
    pool_pre_ping=True,  # Verificar conexión
    pool_recycle=300  # Reciclar conexiones cada 5 min
)

# Crear SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency para obtener sesión de DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()