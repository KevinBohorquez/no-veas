# app/api/v1/endpoints/veterinarios.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.config.database import get_db
# ✅ TEMPORAL: Usar el patrón que funciona en clientes
from app.crud import veterinario  # ← Si existe este import
from app.models.veterinario import Veterinario
from app.models.especialidad import Especialidad

# from app.schemas.veterinario_schema import (...)  # ← Comentado temporalmente

router = APIRouter()


@router.get("/")
async def get_veterinarios(
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1, description="Número de página"),
        per_page: int = Query(20, ge=1, le=100, description="Elementos por página"),
        especialidad: Optional[str] = Query(None, description="Filtrar por especialidad"),
        tipo_veterinario: Optional[str] = Query(None, description="Filtrar por tipo de veterinario"),
        disposicion: Optional[str] = Query(None, description="Filtrar por disposición"),
        turno: Optional[str] = Query(None, description="Filtrar por turno")
):
    """
    Obtener lista de veterinarios con paginación
    """
    try:
        skip = (page - 1) * per_page

        query = db.query(Veterinario)

        # Aplicar filtros opcionales
        if especialidad:
            query = query.join(Veterinario.especialidad).filter(Especialidad.nombre.ilike(f"%{especialidad}%"))
        if tipo_veterinario:
            query = query.filter(Veterinario.tipo_veterinario == tipo_veterinario)
        if disposicion:
            query = query.filter(Veterinario.disposicion == disposicion)
        if turno:
            query = query.filter(Veterinario.turno == turno)

        total = query.count()
        veterinarios = query.offset(skip).limit(per_page).all()

        return {
            "veterinarios": veterinarios,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener veterinarios: {str(e)}"
        )


@router.get("/{veterinario_id}")
async def get_veterinario(
        veterinario_id: int,
        db: Session = Depends(get_db)
):
    """
    Obtener un veterinario específico por ID
    """
    try:
        veterinario_obj = db.query(Veterinario).filter(Veterinario.id_veterinario == veterinario_id).first()

        if not veterinario_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Veterinario no encontrado"
            )

        return veterinario_obj

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener veterinario: {str(e)}"
        )


@router.get("/dni/{dni}")
async def get_veterinario_by_dni(
        dni: str,
        db: Session = Depends(get_db)
):
    """
    Obtener veterinario por DNI
    """
    try:
        if len(dni) != 8 or not dni.isdigit():
            raise HTTPException(
                status_code=400,
                detail="DNI debe tener exactamente 8 dígitos"
            )

        veterinario_obj = db.query(Veterinario).filter(Veterinario.dni == dni).first()

        if not veterinario_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Veterinario no encontrado"
            )

        return veterinario_obj

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al buscar veterinario: {str(e)}"
        )


@router.get("/email/{email}")
async def get_veterinario_by_email(
        email: str,
        db: Session = Depends(get_db)
):
    """
    Obtener veterinario por email
    """
    try:
        veterinario_obj = db.query(Veterinario).filter(Veterinario.email == email).first()

        if not veterinario_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Veterinario no encontrado"
            )

        return veterinario_obj

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al buscar veterinario: {str(e)}"
        )


@router.get("/codigo-cmvp/{codigo_cmvp}")
async def get_veterinario_by_codigo_cmvp(
        codigo_cmvp: str,
        db: Session = Depends(get_db)
):
    """
    Obtener veterinario por código CMVP
    """
    try:
        veterinario_obj = db.query(Veterinario).filter(Veterinario.codigo_CMVP == codigo_cmvp).first()

        if not veterinario_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Veterinario no encontrado"
            )

        return veterinario_obj

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al buscar veterinario: {str(e)}"
        )


@router.get("/disponibles")
async def get_veterinarios_disponibles(
        db: Session = Depends(get_db),
        turno: Optional[str] = Query(None, description="Filtrar por turno"),
        especialidad_id: Optional[int] = Query(None, description="Filtrar por ID de especialidad")
):
    """
    Obtener veterinarios disponibles (disposicion = 'Libre')
    """
    try:
        query = db.query(Veterinario).filter(Veterinario.disposicion == "Libre")

        if turno:
            query = query.filter(Veterinario.turno == turno)
        if especialidad_id:
            query = query.filter(Veterinario.id_especialidad == especialidad_id)

        veterinarios = query.all()

        return {
            "veterinarios_disponibles": veterinarios,
            "total": len(veterinarios),
            "filtros": {
                "turno": turno,
                "especialidad_id": especialidad_id
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener veterinarios disponibles: {str(e)}"
        )


@router.get("/especialidad/{especialidad_id}")
async def get_veterinarios_by_especialidad(
        especialidad_id: int,
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1, description="Número de página"),
        per_page: int = Query(20, ge=1, le=100, description="Elementos por página")
):
    """
    Obtener veterinarios por ID de especialidad
    """
    try:
        skip = (page - 1) * per_page

        # Verificar que la especialidad existe
        especialidad_obj = db.query(Especialidad).filter(Especialidad.id_especialidad == especialidad_id).first()
        if not especialidad_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Especialidad no encontrada"
            )

        query = db.query(Veterinario).filter(Veterinario.id_especialidad == especialidad_id)

        total = query.count()
        veterinarios = query.offset(skip).limit(per_page).all()

        return {
            "especialidad": {
                "id": especialidad_obj.id_especialidad,
                "nombre": especialidad_obj.nombre
            },
            "veterinarios": veterinarios,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener veterinarios por especialidad: {str(e)}"
        )