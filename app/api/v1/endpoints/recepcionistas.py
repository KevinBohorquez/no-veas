# app/api/v1/endpoints/recepcionistas.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.config.database import get_db
from app.models.recepcionista import Recepcionista

router = APIRouter()


@router.get("/")
async def get_recepcionistas(
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1, description="Número de página"),
        per_page: int = Query(20, ge=1, le=100, description="Elementos por página"),
        turno: Optional[str] = Query(None, description="Filtrar por turno"),
        genero: Optional[str] = Query(None, description="Filtrar por género")
):
    """
    Obtener lista de recepcionistas con paginación
    """
    try:
        skip = (page - 1) * per_page

        query = db.query(Recepcionista)

        # Aplicar filtros opcionales
        if turno:
            query = query.filter(Recepcionista.turno == turno)
        if genero:
            query = query.filter(Recepcionista.genero == genero)

        total = query.count()
        recepcionistas = query.offset(skip).limit(per_page).all()

        return {
            "recepcionistas": recepcionistas,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener recepcionistas: {str(e)}"
        )


@router.get("/{recepcionista_id}")
async def get_recepcionista(
        recepcionista_id: int,
        db: Session = Depends(get_db)
):
    """
    Obtener una recepcionista específica por ID
    """
    try:
        recepcionista_obj = db.query(Recepcionista).filter(Recepcionista.id_recepcionista == recepcionista_id).first()

        if not recepcionista_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recepcionista no encontrada"
            )

        return recepcionista_obj

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener recepcionista: {str(e)}"
        )


@router.get("/dni/{dni}")
async def get_recepcionista_by_dni(
        dni: str,
        db: Session = Depends(get_db)
):
    """
    Obtener recepcionista por DNI
    """
    try:
        if len(dni) != 8 or not dni.isdigit():
            raise HTTPException(
                status_code=400,
                detail="DNI debe tener exactamente 8 dígitos"
            )

        recepcionista_obj = db.query(Recepcionista).filter(Recepcionista.dni == dni).first()

        if not recepcionista_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recepcionista no encontrada"
            )

        return recepcionista_obj

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al buscar recepcionista: {str(e)}"
        )


@router.get("/email/{email}")
async def get_recepcionista_by_email(
        email: str,
        db: Session = Depends(get_db)
):
    """
    Obtener recepcionista por email
    """
    try:
        recepcionista_obj = db.query(Recepcionista).filter(Recepcionista.email == email).first()

        if not recepcionista_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recepcionista no encontrada"
            )

        return recepcionista_obj

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al buscar recepcionista: {str(e)}"
        )


@router.get("/turno/{turno}")
async def get_recepcionistas_by_turno(
        turno: str,
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1, description="Número de página"),
        per_page: int = Query(20, ge=1, le=100, description="Elementos por página")
):
    """
    Obtener recepcionistas por turno
    """
    try:
        skip = (page - 1) * per_page

        query = db.query(Recepcionista).filter(Recepcionista.turno == turno)

        total = query.count()
        recepcionistas = query.offset(skip).limit(per_page).all()

        return {
            "turno": turno,
            "recepcionistas": recepcionistas,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener recepcionistas por turno: {str(e)}"
        )


@router.get("/debug/info")
async def debug_recepcionista_info(db: Session = Depends(get_db)):
    """
    Endpoint para depurar información de la tabla Recepcionista
    """
    try:
        # Obtener información de la tabla
        result = db.execute("DESCRIBE Recepcionista").fetchall()
        columns = [{"Field": row[0], "Type": row[1], "Null": row[2], "Key": row[3]} for row in result]

        # Contar registros
        total_count = db.query(Recepcionista).count()

        return {
            "table_info": {
                "name": "Recepcionista",
                "columns": columns,
                "total_records": total_count
            }
        }

    except Exception as e:
        return {
            "error": f"Error al obtener información: {str(e)}"
        }