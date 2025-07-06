# app/api/v1/endpoints/mascotas.py (CORREGIDO)
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.config.database import get_db
from app.crud import mascota, cliente
from app.models.mascota import Mascota
from app.models.cliente_mascota import ClienteMascota
from app.schemas import (
    MascotaCreate, MascotaUpdate, MascotaResponse, MascotaSearch
)
from app.api.deps import get_mascota_or_404

router = APIRouter()


@router.post("/", response_model=MascotaResponse, status_code=status.HTTP_201_CREATED)
async def create_mascota(
        mascota_data: MascotaCreate,
        cliente_id: int = Query(..., description="ID del cliente propietario"),
        db: Session = Depends(get_db)
):
    """
    Crear una nueva mascota y asociarla a un cliente
    """
    # Verificar que el cliente existe
    cliente_obj = cliente.get(db, cliente_id)
    if not cliente_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cliente no existe"
        )

    # Verificar que la raza existe
    try:
        raza_exists = db.execute(
            "SELECT COUNT(*) as count FROM Raza WHERE id_raza = :id_raza",
            {"id_raza": mascota_data.id_raza}
        ).fetchone()

        if not raza_exists or raza_exists.count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Raza no existe"
            )
    except Exception:
        # Si no existe tabla Raza, continuar
        pass

    # Crear la mascota
    nueva_mascota = mascota.create(db, obj_in=mascota_data)

    # Crear la relación cliente-mascota
    relacion = ClienteMascota(
        id_cliente=cliente_id,
        id_mascota=nueva_mascota.id_mascota
    )
    db.add(relacion)
    db.commit()

    return nueva_mascota


@router.get("/")
async def get_mascotas(
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1, description="Número de página"),
        per_page: int = Query(20, ge=1, le=100, description="Elementos por página"),
        sexo: Optional[str] = Query(None, description="Filtrar por sexo"),
        id_raza: Optional[int] = Query(None, description="Filtrar por raza")
):
    """
    Obtener lista de mascotas con paginación
    """
    skip = (page - 1) * per_page

    query = db.query(Mascota)

    if sexo:
        query = query.filter(Mascota.sexo == sexo)

    if id_raza:
        query = query.filter(Mascota.id_raza == id_raza)

    total = query.count()
    mascotas = query.offset(skip).limit(per_page).all()

    # Convertir a diccionarios con información adicional
    result = []
    for mascota in mascotas:
        # Buscar cliente asociado
        cliente_info = None
        cliente_mascota = db.query(ClienteMascota).filter(
            ClienteMascota.id_mascota == mascota.id_mascota
        ).first()

        if cliente_mascota:
            from app.models.clientes import Cliente
            cliente = db.query(Cliente).filter(
                Cliente.id_cliente == cliente_mascota.id_cliente
            ).first()
            if cliente:
                cliente_info = {
                    "id_cliente": cliente.id_cliente,
                    "nombre": f"{cliente.nombre} {cliente.apellido_paterno}"
                }

        result.append({
            "id_mascota": mascota.id_mascota,
            "nombre": mascota.nombre,
            "sexo": mascota.sexo,
            "color": mascota.color,
            "edad_anios": mascota.edad_anios,
            "edad_meses": mascota.edad_meses,
            "esterilizado": mascota.esterilizado,
            "imagen": mascota.imagen,
            "id_raza": mascota.id_raza,
            "cliente": cliente_info
        })

    return {
        "mascotas": result,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }


@router.get("/{mascota_id}", response_model=MascotaResponse)
async def get_mascota(
        mascota_obj: Mascota = Depends(get_mascota_or_404)
):
    """
    Obtener una mascota específica por ID
    """
    return mascota_obj


@router.get("/{mascota_id}/details")
async def get_mascota_with_details(
        mascota_id: int,
        db: Session = Depends(get_db)
):
    """
    Obtener mascota con detalles del cliente y raza
    """
    mascota_obj = mascota.get(db, mascota_id)
    if not mascota_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mascota no encontrada"
        )

    # Buscar cliente asociado
    cliente_info = None
    cliente_mascota = db.query(ClienteMascota).filter(
        ClienteMascota.id_mascota == mascota_id
    ).first()

    if cliente_mascota:
        from app.models.clientes import Cliente
        cliente = db.query(Cliente).filter(
            Cliente.id_cliente == cliente_mascota.id_cliente
        ).first()
        if cliente:
            cliente_info = {
                "id_cliente": cliente.id_cliente,
                "nombre": cliente.nombre,
                "apellidos": f"{cliente.apellido_paterno} {cliente.apellido_materno}",
                "telefono": cliente.telefono,
                "email": cliente.email
            }

    # Buscar información de raza
    raza_info = None
    try:
        raza_result = db.execute(
            "SELECT nombre_raza, especie FROM Raza WHERE id_raza = :id_raza",
            {"id_raza": mascota_obj.id_raza}
        ).fetchone()
        if raza_result:
            raza_info = {
                "nombre_raza": raza_result.nombre_raza,
                "especie": raza_result.especie
            }
    except Exception:
        pass

    return {
        "id_mascota": mascota_obj.id_mascota,
        "nombre": mascota_obj.nombre,
        "sexo": mascota_obj.sexo,
        "color": mascota_obj.color,
        "edad_anios": mascota_obj.edad_anios,
        "edad_meses": mascota_obj.edad_meses,
        "esterilizado": mascota_obj.esterilizado,
        "imagen": mascota_obj.imagen,
        "id_raza": mascota_obj.id_raza,
        "cliente": cliente_info,
        "raza": raza_info
    }


@router.put("/{mascota_id}", response_model=MascotaResponse)
async def update_mascota(
        mascota_id: int,
        mascota_data: MascotaUpdate,
        db: Session = Depends(get_db)
):
    """
    Actualizar una mascota
    """
    mascota_obj = mascota.get(db, mascota_id)
    if not mascota_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mascota no encontrada"
        )

    # Validar raza si se está actualizando
    update_data = mascota_data.dict(exclude_unset=True)
    if "id_raza" in update_data:
        try:
            raza_exists = db.execute(
                "SELECT COUNT(*) as count FROM Raza WHERE id_raza = :id_raza",
                {"id_raza": update_data["id_raza"]}
            ).fetchone()

            if not raza_exists or raza_exists.count == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Raza no existe"
                )
        except Exception:
            pass

    return mascota.update(db, db_obj=mascota_obj, obj_in=mascota_data)


@router.delete("/{mascota_id}")
async def delete_mascota(
        mascota_id: int,
        db: Session = Depends(get_db)
):
    """
    Eliminar una mascota
    """
    mascota_obj = mascota.get(db, mascota_id)
    if not mascota_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mascota no encontrada"
        )

    mascota.remove(db, id=mascota_id)
    return {"message": "Mascota eliminada correctamente", "success": True}


@router.post("/search")
async def search_mascotas(
        search_params: MascotaSearch,
        db: Session = Depends(get_db)
):
    """
    Buscar mascotas con filtros avanzados
    """
    mascotas_result, total = mascota.search_mascotas(db, search_params=search_params)

    return {
        "mascotas": mascotas_result,
        "total": total,
        "page": search_params.page,
        "per_page": search_params.per_page,
        "total_pages": (total + search_params.per_page - 1) // search_params.per_page
    }


@router.get("/cliente/{cliente_id}/list")
async def get_mascotas_by_cliente(
        cliente_id: int,
        db: Session = Depends(get_db)
):
    """
    Obtener todas las mascotas de un cliente específico
    """
    # Verificar que el cliente existe
    cliente_obj = cliente.get(db, cliente_id)
    if not cliente_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )

    mascotas = mascota.get_mascotas_by_cliente(db, cliente_id=cliente_id)

    return {
        "cliente_id": cliente_id,
        "cliente_nombre": f"{cliente_obj.nombre} {cliente_obj.apellido_paterno}",
        "mascotas": mascotas,
        "total": len(mascotas)
    }


@router.get("/stats/por-sexo")
async def get_estadisticas_por_sexo(
        db: Session = Depends(get_db)
):
    """
    Obtener estadísticas de mascotas por sexo
    """
    stats = mascota.count_mascotas_by_sexo(db)
    return {
        "estadisticas_por_sexo": stats,
        "total": stats["machos"] + stats["hembras"]
    }


@router.get("/no-esterilizadas/list")
async def get_mascotas_no_esterilizadas(
        db: Session = Depends(get_db)
):
    """
    Obtener mascotas no esterilizadas
    """
    mascotas = mascota.get_mascotas_no_esterilizadas(db)
    return {
        "mascotas_no_esterilizadas": mascotas,
        "total": len(mascotas)
    }