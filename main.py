# main.py - Sistema Veterinaria API COMPLETO
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
import os
from datetime import datetime

from app.config.database import get_db
from app.models.clientes import Cliente

# ✅ IMPORTAR TODOS LOS ROUTERS (AUTENTICACIÓN + GESTIÓN)
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.clientes import router as clientes_router
from app.api.v1.endpoints.veterinarios import router as veterinarios_router
from app.api.v1.endpoints.recepcionistas import router as recepcionistas_router
from app.api.v1.endpoints.mascota import router as mascotas_router
from app.api.v1.endpoints.usuarios import router as usuarios_router
from app.api.v1.endpoints.administradores import router as administradores_router
from app.api.v1.endpoints.catalogos import router as catalogos_router
from app.api.v1.endpoints.consultas import router as consultas_router

app = FastAPI(
    title="🏥 Sistema Veterinaria API Completo",
    description="API integral para gestión de veterinaria con autenticación y todos los módulos",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
        "http://localhost:5173",
        "http://localhost:3000",
        "https://colitasfelices.netlify.app/"  # Frontend local       
                   ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ INCLUIR TODOS LOS ROUTERS DISPONIBLES
# Autenticación (prioritario)
app.include_router(auth_router, prefix="/api/v1/auth", tags=["🔐 autenticación"])

# Gestión de usuarios
app.include_router(clientes_router, prefix="/api/v1/clientes", tags=["👥 clientes"])
app.include_router(veterinarios_router, prefix="/api/v1/veterinarios", tags=["👨‍⚕️ veterinarios"])
app.include_router(recepcionistas_router, prefix="/api/v1/recepcionistas", tags=["👩‍💼 recepcionistas"])
app.include_router(usuarios_router, prefix="/api/v1/usuarios", tags=["👤 usuarios"])
app.include_router(administradores_router, prefix="/api/v1/administradores", tags=["👑 administradores"])

# Gestión de mascotas
app.include_router(mascotas_router, prefix="/api/v1/mascotas", tags=["🐕 mascotas"])

# Catálogos del sistema
app.include_router(catalogos_router, prefix="/api/v1/catalogos", tags=["📋 catálogos"])

# Procesos clínicos
app.include_router(consultas_router, prefix="/api/v1/consultas", tags=["🏥 consultas"])

# ===== ENDPOINTS PRINCIPALES =====

@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    available_modules = {
        "🔐 autenticación": "/api/v1/auth - Sistema de login/logout completo",
        "👥 clientes": "/api/v1/clientes - Gestión de clientes propietarios",
        "👨‍⚕️ veterinarios": "/api/v1/veterinarios - Gestión de veterinarios",
        "👩‍💼 recepcionistas": "/api/v1/recepcionistas - Gestión de recepcionistas",
        "👤 usuarios": "/api/v1/usuarios - Gestión de usuarios del sistema",
        "👑 administradores": "/api/v1/administradores - Gestión de administradores",
        "🐕 mascotas": "/api/v1/mascotas - Gestión de mascotas",
        "📋 catálogos": "/api/v1/catalogos - Razas, especialidades, servicios, patologías",
        "🏥 consultas": "/api/v1/consultas - Procesos clínicos completos"
    }

    return {
        "message": "🏥 Sistema Veterinaria API COMPLETO funcionando!",
        "version": "2.0.0",
        "status": "✅ Operativo",
        "timestamp": datetime.now().isoformat(),
        "available_modules": available_modules,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Endpoint de salud del sistema"""
    try:
        # Verificar conexión a la base de datos
        db.execute("SELECT 1")
        db_status = "✅ Conectada"
    except Exception as e:
        db_status = f"❌ Error: {str(e)}"
        
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": db_status,
        "version": "2.0.0"
    }


@app.get("/stats")
async def get_system_stats(db: Session = Depends(get_db)):
    """Estadísticas generales del sistema"""
    try:
        stats = {}
        
        # Contar registros principales
        try:
            stats["total_clientes"] = db.query(Cliente).count()
        except:
            stats["total_clientes"] = "No disponible"
            
        try:
            from app.models.veterinario import Veterinario
            stats["total_veterinarios"] = db.query(Veterinario).count()
        except:
            stats["total_veterinarios"] = "No disponible"
            
        try:
            from app.models.mascota import Mascota
            stats["total_mascotas"] = db.query(Mascota).count()
        except:
            stats["total_mascotas"] = "No disponible"

        return {
            "timestamp": datetime.now().isoformat(),
            "statistics": stats,
            "system_info": {
                "environment": os.getenv("ENVIRONMENT", "development"),
                "python_version": "3.x",
                "fastapi_version": "FastAPI"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )


# ===== MANEJO DE ERRORES GLOBALES =====

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request, exc):
    """Manejo global de errores de base de datos"""
    return {
        "error": "Error de base de datos",
        "detail": "Ocurrió un problema con la base de datos",
        "status_code": 500
    }


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Manejo de rutas no encontradas"""
    return {
        "error": "Endpoint no encontrado",
        "detail": f"La ruta {request.url.path} no existe",
        "available_endpoints": "/docs",
        "status_code": 404
    }


if __name__ == "__main__":
    import uvicorn
    
    # Configuración de servidor
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("ENVIRONMENT", "development") == "development"
    
    print(f"🚀 Iniciando servidor en http://{host}:{port}")
    print(f"📚 Documentación disponible en http://{host}:{port}/docs")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )