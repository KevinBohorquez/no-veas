# app/api/v1/endpoints/consultas.py - VERSIÓN CORREGIDA
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from app.config.database import get_db
from app.crud.consulta_crud import (
    consulta, diagnostico, tratamiento, historial_clinico,
    triaje, solicitud_atencion
)
from app.crud.veterinario_crud import veterinario
from app.models.consulta import Consulta
from app.models.triaje import Triaje
from app.models.solicitud_atencion import SolicitudAtencion
from app.schemas.consulta_schema import (
    ConsultaCreate, ConsultaResponse, ConsultaSearch,
    DiagnosticoCreate, DiagnosticoResponse,
    TratamientoCreate, TratamientoResponse,
    HistorialClinicoCreate, HistorialClinicoResponse, SolicitudAtencionResponse, SolicitudAtencionCreate, CitaResponse,
    CitaCreate
)
from app.schemas.base_schema import MessageResponse

router = APIRouter()


# ===== RUTAS ESPECÍFICAS PRIMERO (ANTES DE LAS RUTAS CON PARÁMETROS) =====

@router.post("/solicitudes/", response_model=SolicitudAtencionResponse, status_code=status.HTTP_201_CREATED)
async def create_solicitud_atencion(
        solicitud_data: SolicitudAtencionCreate,
        db: Session = Depends(get_db)
):
    """
    Crear una nueva solicitud de atención
    """
    try:
        # Verificar que la mascota existe
        from app.crud import mascota
        mascota_obj = mascota.get(db, solicitud_data.id_mascota)
        if not mascota_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mascota no encontrada"
            )

        # Verificar que la recepcionista existe
        from app.crud import recepcionista
        recep_obj = recepcionista.get(db, solicitud_data.id_recepcionista)
        if not recep_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recepcionista no encontrada"
            )

        # Agregar timestamp actual si no se proporciona
        solicitud_dict = solicitud_data.dict()
        solicitud_dict['fecha_hora_solicitud'] = solicitud_dict.get('fecha_hora_solicitud', datetime.now())
        solicitud_dict['estado'] = 'Pendiente'  # Estado inicial

        # Crear la solicitud
        nueva_solicitud = solicitud_atencion.create(db, obj_in=solicitud_dict)

        return nueva_solicitud

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear solicitud: {str(e)}"
        )


@router.get("/solicitudes/", response_model=List[SolicitudAtencionResponse])
async def get_solicitudes_atencion(
        db: Session = Depends(get_db),
        estado: Optional[str] = Query(None, description="Filtrar por estado"),
        tipo_solicitud: Optional[str] = Query(None, description="Filtrar por tipo"),
        mascota_id: Optional[int] = Query(None, description="Filtrar por mascota"),
        limit: int = Query(50, ge=1, le=100, description="Límite de resultados")
):
    """
    Obtener lista de solicitudes de atención con filtros
    """
    try:
        if estado:
            solicitudes = solicitud_atencion.get_by_estado(db, estado=estado)
        elif tipo_solicitud:
            solicitudes = solicitud_atencion.get_by_tipo(db, tipo_solicitud=tipo_solicitud)
        elif mascota_id:
            solicitudes = solicitud_atencion.get_by_mascota(db, mascota_id=mascota_id)
        else:
            solicitudes = solicitud_atencion.get_multi(db, limit=limit)

        return solicitudes[:limit]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener solicitudes: {str(e)}"
        )


@router.get("/solicitudes/{solicitud_id}", response_model=SolicitudAtencionResponse)
async def get_solicitud_atencion(
        solicitud_id: int,
        db: Session = Depends(get_db)
):
    """
    Obtener una solicitud específica por ID
    """
    try:
        solicitud = solicitud_atencion.get(db, solicitud_id)
        if not solicitud:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud no encontrada"
            )
        return solicitud

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener solicitud: {str(e)}"
        )


# OPCIONAL: Endpoint para actualizar estado de solicitud
@router.patch("/solicitudes/{solicitud_id}/estado")
async def actualizar_estado_solicitud(
        solicitud_id: int,
        nuevo_estado: str = Query(..., description="Nuevo estado de la solicitud"),
        db: Session = Depends(get_db)
):
    """
    Actualizar el estado de una solicitud
    """
    try:
        # Validar que el estado es válido
        estados_validos = ['Pendiente', 'En triaje', 'En atencion', 'Completada', 'Cancelada']
        if nuevo_estado not in estados_validos:
            raise HTTPException(
                status_code=400,
                detail=f"Estado inválido. Debe ser uno de: {', '.join(estados_validos)}"
            )

        solicitud_actualizada = solicitud_atencion.cambiar_estado(
            db,
            solicitud_id=solicitud_id,
            nuevo_estado=nuevo_estado
        )

        if not solicitud_actualizada:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud no encontrada"
            )

        return {
            "message": "Estado actualizado exitosamente",
            "solicitud": solicitud_actualizada
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar estado: {str(e)}"
        )


@router.get("/search")
async def search_consultas_endpoint(
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1, description="Número de página"),
        per_page: int = Query(20, ge=1, le=100, description="Elementos por página"),
        id_veterinario: Optional[int] = Query(None, description="Filtrar por veterinario"),
        fecha_desde: Optional[date] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
        fecha_hasta: Optional[date] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
        condicion_general: Optional[str] = Query(None, description="Filtrar por condición"),
        es_seguimiento: Optional[bool] = Query(None, description="Filtrar seguimientos")
):
    """
    Buscar consultas con filtros avanzados
    """
    try:
        search_params = ConsultaSearch(
            id_veterinario=id_veterinario,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            condicion_general=condicion_general,
            es_seguimiento=es_seguimiento,
            page=page,
            per_page=per_page
        )

        consultas_result, total = consulta.search_consultas(db, search_params=search_params)

        return {
            "consultas": consultas_result,
            "total": total,
            "page": search_params.page,
            "per_page": search_params.per_page,
            "total_pages": (total + search_params.per_page - 1) // search_params.per_page
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en búsqueda de consultas: {str(e)}"
        )


@router.get("/estadisticas/resumen")
async def get_estadisticas_consultas(
        db: Session = Depends(get_db),
        fecha_desde: Optional[date] = Query(None, description="Fecha desde"),
        fecha_hasta: Optional[date] = Query(None, description="Fecha hasta")
):
    """
    Obtener estadísticas de consultas
    """
    try:
        # Estadísticas por condición general
        stats_condicion = consulta.get_estadisticas_por_condicion(db)

        # Consultas de seguimiento
        seguimientos = consulta.get_seguimientos(db)

        # Si hay rango de fechas, filtrar consultas por fecha
        if fecha_desde and fecha_hasta:
            search_params = ConsultaSearch(
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                page=1,
                per_page=1000  # Para obtener todas y contar
            )
            consultas_periodo, total_periodo = consulta.search_consultas(db, search_params=search_params)
        else:
            total_periodo = db.query(Consulta).count()

        # Diagnósticos más frecuentes
        diagnosticos_frecuentes = diagnostico.get_mas_frecuentes(db, limit=5)

        return {
            "periodo": {
                "fecha_desde": fecha_desde,
                "fecha_hasta": fecha_hasta,
                "total_consultas": total_periodo
            },
            "estadisticas_condicion": stats_condicion,
            "total_seguimientos": len(seguimientos),
            "diagnosticos_frecuentes": diagnosticos_frecuentes
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )


@router.get("/hoy/agenda")
async def get_consultas_hoy(
        db: Session = Depends(get_db)
):
    """
    Obtener consultas del día actual
    """
    try:
        hoy = date.today()
        consultas_hoy = consulta.get_por_fecha(db, fecha=hoy)

        # Organizar por veterinario
        consultas_por_veterinario = {}
        for c in consultas_hoy:
            vet_id = c.id_veterinario
            if vet_id not in consultas_por_veterinario:
                vet_obj = veterinario.get(db, vet_id)
                consultas_por_veterinario[vet_id] = {
                    "veterinario": f"{vet_obj.nombre} {vet_obj.apellido_paterno}" if vet_obj else "Desconocido",
                    "consultas": []
                }
            consultas_por_veterinario[vet_id]["consultas"].append(c)

        return {
            "fecha": hoy,
            "total_consultas": len(consultas_hoy),
            "consultas_por_veterinario": list(consultas_por_veterinario.values()),
            "consultas_detalle": consultas_hoy
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener consultas de hoy: {str(e)}"
        )


@router.get("/veterinario/{veterinario_id}")
async def get_consultas_by_veterinario(
        veterinario_id: int,
        db: Session = Depends(get_db),
        fecha_desde: Optional[date] = Query(None, description="Fecha desde"),
        fecha_hasta: Optional[date] = Query(None, description="Fecha hasta"),
        limit: int = Query(50, ge=1, le=100, description="Límite de resultados")
):
    """
    Obtener consultas realizadas por un veterinario
    """
    try:
        # Verificar que el veterinario existe
        veterinario_obj = veterinario.get(db, veterinario_id)
        if not veterinario_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Veterinario no encontrado"
            )

        consultas_list = consulta.get_by_veterinario(
            db,
            veterinario_id=veterinario_id,
            fecha_inicio=fecha_desde,
            fecha_fin=fecha_hasta
        )

        # Limitar resultados
        consultas_list = consultas_list[:limit]

        return {
            "veterinario": {
                "id_veterinario": veterinario_obj.id_veterinario,
                "nombre": f"{veterinario_obj.nombre} {veterinario_obj.apellido_paterno}"
            },
            "consultas": consultas_list,
            "total": len(consultas_list),
            "filtros": {
                "fecha_desde": fecha_desde,
                "fecha_hasta": fecha_hasta
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener consultas del veterinario: {str(e)}"
        )


# ===== RUTAS GENERALES (DESPUÉS DE LAS ESPECÍFICAS) =====

@router.post("/", response_model=ConsultaResponse, status_code=status.HTTP_201_CREATED)
async def create_consulta(
        consulta_data: ConsultaCreate,
        db: Session = Depends(get_db)
):
    """
    Crear una nueva consulta médica
    """
    try:
        # Verificar que el triaje existe
        triaje_obj = triaje.get(db, consulta_data.id_triaje)
        if not triaje_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Triaje no encontrado"
            )

        # Verificar que el veterinario existe y está disponible
        veterinario_obj = veterinario.get(db, consulta_data.id_veterinario)
        if not veterinario_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Veterinario no encontrado"
            )

        # Verificar que no existe ya una consulta para este triaje
        consulta_existente = consulta.get_by_triaje(db, triaje_id=consulta_data.id_triaje)
        if consulta_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una consulta para este triaje"
            )

        # Agregar timestamp actual si no se proporciona
        consulta_dict = consulta_data.dict()
        consulta_dict['fecha_consulta'] = consulta_dict.get('fecha_consulta', datetime.now())

        # Crear la consulta
        nueva_consulta = consulta.create(db, obj_in=consulta_dict)

        # Cambiar disposición del veterinario a ocupado
        veterinario.cambiar_disposicion(
            db,
            veterinario_id=consulta_data.id_veterinario,
            nueva_disposicion="Ocupado"
        )

        # Cambiar estado de la solicitud de atención a "En atencion"
        solicitud_obj = solicitud_atencion.get(db, triaje_obj.id_solicitud)
        if solicitud_obj:
            solicitud_atencion.cambiar_estado(
                db,
                solicitud_id=triaje_obj.id_solicitud,
                nuevo_estado="En atencion"
            )

        # Agregar evento al historial clínico
        if solicitud_obj:
            historial_clinico.add_evento_consulta(
                db,
                mascota_id=solicitud_obj.id_mascota,
                consulta_id=nueva_consulta.id_consulta,
                veterinario_id=consulta_data.id_veterinario,
                descripcion=f"Consulta: {consulta_data.tipo_consulta}. Motivo: {consulta_data.motivo_consulta or 'No especificado'}",
                peso_actual=float(triaje_obj.peso_mascota) if triaje_obj.peso_mascota else None
            )

        return nueva_consulta

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear consulta: {str(e)}"
        )


@router.get("/")
async def get_consultas(
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1, description="Número de página"),
        per_page: int = Query(20, ge=1, le=100, description="Elementos por página"),
        id_veterinario: Optional[int] = Query(None, description="Filtrar por veterinario"),
        fecha_desde: Optional[date] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
        fecha_hasta: Optional[date] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
        condicion_general: Optional[str] = Query(None, description="Filtrar por condición"),
        es_seguimiento: Optional[bool] = Query(None, description="Filtrar seguimientos")
):
    """
    Obtener lista de consultas con paginación y filtros
    """
    try:
        search_params = ConsultaSearch(
            id_veterinario=id_veterinario,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            condicion_general=condicion_general,
            es_seguimiento=es_seguimiento,
            page=page,
            per_page=per_page
        )

        consultas_result, total = consulta.search_consultas(db, search_params=search_params)

        return {
            "consultas": consultas_result,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener consultas: {str(e)}"
        )


# ===== RUTAS CON PARÁMETROS AL FINAL =====

@router.get("/{consulta_id}", response_model=ConsultaResponse)
async def get_consulta(
        consulta_id: int,
        db: Session = Depends(get_db)
):
    """
    Obtener una consulta específica por ID
    """
    try:
        consulta_obj = consulta.get(db, consulta_id)
        if not consulta_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consulta no encontrada"
            )
        return consulta_obj

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener consulta: {str(e)}"
        )


@router.get("/{consulta_id}/completa")
async def get_consulta_completa(
        consulta_id: int,
        db: Session = Depends(get_db)
):
    """
    Obtener consulta con toda la información relacionada (triaje, diagnósticos, tratamientos)
    """
    try:
        consulta_obj = consulta.get(db, consulta_id)
        if not consulta_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consulta no encontrada"
            )

        # Obtener triaje relacionado
        triaje_obj = triaje.get(db, consulta_obj.id_triaje)

        # Obtener solicitud de atención
        solicitud_obj = None
        if triaje_obj:
            solicitud_obj = solicitud_atencion.get(db, triaje_obj.id_solicitud)

        # Obtener diagnósticos de la consulta
        diagnosticos_list = diagnostico.get_by_consulta(db, consulta_id=consulta_id)

        # Obtener tratamientos de la consulta
        tratamientos_list = tratamiento.get_by_consulta(db, consulta_id=consulta_id)

        # Obtener veterinario
        veterinario_obj = veterinario.get(db, consulta_obj.id_veterinario)

        # Obtener historial relacionado
        historial_list = historial_clinico.get_by_consulta(db, consulta_id=consulta_id)

        return {
            "consulta": consulta_obj,
            "triaje": {
                "id_triaje": triaje_obj.id_triaje if triaje_obj else None,
                "clasificacion_urgencia": triaje_obj.clasificacion_urgencia if triaje_obj else None,
                "peso_mascota": float(triaje_obj.peso_mascota) if triaje_obj and triaje_obj.peso_mascota else None,
                "temperatura": float(triaje_obj.temperatura) if triaje_obj and triaje_obj.temperatura else None,
                "condicion_corporal": triaje_obj.condicion_corporal if triaje_obj else None
            },
            "solicitud": {
                "id_solicitud": solicitud_obj.id_solicitud if solicitud_obj else None,
                "id_mascota": solicitud_obj.id_mascota if solicitud_obj else None,
                "tipo_solicitud": solicitud_obj.tipo_solicitud if solicitud_obj else None,
                "estado": solicitud_obj.estado if solicitud_obj else None
            },
            "veterinario": {
                "id_veterinario": veterinario_obj.id_veterinario if veterinario_obj else None,
                "nombre_completo": f"{veterinario_obj.nombre} {veterinario_obj.apellido_paterno}" if veterinario_obj else None,
                "especialidad_id": veterinario_obj.id_especialidad if veterinario_obj else None
            },
            "diagnosticos": diagnosticos_list,
            "tratamientos": tratamientos_list,
            "eventos_historial": historial_list
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener consulta completa: {str(e)}"
        )


@router.post("/{consulta_id}/diagnosticos", response_model=DiagnosticoResponse, status_code=status.HTTP_201_CREATED)
async def create_diagnostico(
        consulta_id: int,
        diagnostico_data: DiagnosticoCreate,
        db: Session = Depends(get_db)
):
    """
    Crear un diagnóstico para una consulta
    """
    try:
        # Verificar que la consulta existe
        consulta_obj = consulta.get(db, consulta_id)
        if not consulta_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consulta no encontrada"
            )

        # Verificar que la patología existe
        from app.crud.catalogo_crud import patologia
        patologia_obj = patologia.get(db, diagnostico_data.id_patologia)
        if not patologia_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patología no encontrada"
            )

        # Actualizar el id_consulta con el de la URL
        diagnostico_data.id_consulta = consulta_id

        # Agregar timestamp actual
        diagnostico_dict = diagnostico_data.dict()
        diagnostico_dict['fecha_diagnostico'] = diagnostico_dict.get('fecha_diagnostico', datetime.now())

        # Crear el diagnóstico
        nuevo_diagnostico = diagnostico.create(db, obj_in=diagnostico_dict)

        # Agregar evento al historial clínico
        # Obtener ID de mascota
        triaje_obj = triaje.get(db, consulta_obj.id_triaje)
        if triaje_obj:
            solicitud_obj = solicitud_atencion.get(db, triaje_obj.id_solicitud)
            if solicitud_obj:
                historial_clinico.add_evento_diagnostico(
                    db,
                    mascota_id=solicitud_obj.id_mascota,
                    diagnostico_id=nuevo_diagnostico.id_diagnostico,
                    veterinario_id=consulta_obj.id_veterinario,
                    descripcion=f"Diagnóstico {diagnostico_data.tipo_diagnostico}: {diagnostico_data.diagnostico}"
                )

        return nuevo_diagnostico

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear diagnóstico: {str(e)}"
        )


@router.post("/{consulta_id}/tratamientos", response_model=TratamientoResponse, status_code=status.HTTP_201_CREATED)
async def create_tratamiento(
        consulta_id: int,
        tratamiento_data: TratamientoCreate,
        db: Session = Depends(get_db)
):
    """
    Crear un tratamiento para una consulta
    """
    try:
        # Verificar que la consulta existe
        consulta_obj = consulta.get(db, consulta_id)
        if not consulta_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consulta no encontrada"
            )

        # Actualizar el id_consulta con el de la URL
        tratamiento_data.id_consulta = consulta_id

        # Crear el tratamiento
        nuevo_tratamiento = tratamiento.create(db, obj_in=tratamiento_data)

        # Agregar evento al historial clínico
        triaje_obj = triaje.get(db, consulta_obj.id_triaje)
        if triaje_obj:
            solicitud_obj = solicitud_atencion.get(db, triaje_obj.id_solicitud)
            if solicitud_obj:
                historial_clinico.add_evento_tratamiento(
                    db,
                    mascota_id=solicitud_obj.id_mascota,
                    tratamiento_id=nuevo_tratamiento.id_tratamiento,
                    veterinario_id=consulta_obj.id_veterinario,
                    descripcion=f"Tratamiento {tratamiento_data.tipo_tratamiento} iniciado para patología"
                )

        return nuevo_tratamiento

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear tratamiento: {str(e)}"
        )


@router.get("/{consulta_id}/diagnosticos")
async def get_diagnosticos_consulta(
        consulta_id: int,
        db: Session = Depends(get_db)
):
    """
    Obtener todos los diagnósticos de una consulta
    """
    try:
        # Verificar que la consulta existe
        consulta_obj = consulta.get(db, consulta_id)
        if not consulta_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consulta no encontrada"
            )

        diagnosticos_list = diagnostico.get_by_consulta(db, consulta_id=consulta_id)

        return {
            "consulta_id": consulta_id,
            "diagnosticos": diagnosticos_list,
            "total": len(diagnosticos_list)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener diagnósticos: {str(e)}"
        )


@router.get("/{consulta_id}/tratamientos")
async def get_tratamientos_consulta(
        consulta_id: int,
        db: Session = Depends(get_db)
):
    """
    Obtener todos los tratamientos de una consulta
    """
    try:
        # Verificar que la consulta existe
        consulta_obj = consulta.get(db, consulta_id)
        if not consulta_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consulta no encontrada"
            )

        tratamientos_list = tratamiento.get_by_consulta(db, consulta_id=consulta_id)

        return {
            "consulta_id": consulta_id,
            "tratamientos": tratamientos_list,
            "total": len(tratamientos_list)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener tratamientos: {str(e)}"
        )


@router.patch("/{consulta_id}/finalizar", response_model=MessageResponse)
async def finalizar_consulta(
        consulta_id: int,
        db: Session = Depends(get_db)
):
    """
    Finalizar una consulta médica
    """
    try:
        # Verificar que la consulta existe
        consulta_obj = consulta.get(db, consulta_id)
        if not consulta_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consulta no encontrada"
            )

        # Liberar al veterinario
        veterinario.cambiar_disposicion(
            db,
            veterinario_id=consulta_obj.id_veterinario,
            nueva_disposicion="Libre"
        )

        # Cambiar estado de la solicitud a "Completada"
        triaje_obj = triaje.get(db, consulta_obj.id_triaje)
        if triaje_obj:
            solicitud_atencion.cambiar_estado(
                db,
                solicitud_id=triaje_obj.id_solicitud,
                nuevo_estado="Completada"
            )

        return {
            "message": "Consulta finalizada exitosamente",
            "success": True,
            "consulta_id": consulta_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al finalizar consulta: {str(e)}"
        )

from app.crud.consulta_crud import CRUDCita
# ==============================
# 1. Crear cita
# ==============================
@router.post("/cita", response_model=CitaResponse, status_code=status.HTTP_201_CREATED)
async def create_cita(
        cita_data: CitaCreate,
        db: Session = Depends(get_db)
):
    """
    Crear una nueva cita programada
    """
    try:
        # Verificar que la mascota existe
        from app.crud import mascota
        mascota_obj = mascota.get(db, cita_data.id_mascota)
        if not mascota_obj:
            raise HTTPException(
                status_code=400,
                detail="Mascota no encontrada"
            )

        # Verificar que el servicio existe
        from app.crud.consulta_crud import servicio_solicitado
        from app.crud.consulta_crud import cita
        servicio_obj = servicio_solicitado.get(db, cita_data.id_servicio_solicitado)
        if not servicio_obj:
            raise HTTPException(
                status_code=400,
                detail="Servicio solicitado no encontrado"
            )

        # Crear la cita
        cita_dict = cita_data.dict()
        cita_dict['estado_cita'] = 'Programada'  # Estado inicial
        from app.crud.consulta_crud import CRUDCita
        nueva_cita = CRUDCita.create(db, obj_in=cita_dict)

        return nueva_cita

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear cita: {str(e)}"
        )


# ==============================
# 2. Obtener lista de citas
# ==============================
@router.get("/cita", response_model=List[CitaResponse])
async def get_citas(
        db: Session = Depends(get_db),
        estado: Optional[str] = Query(None, description="Filtrar por estado de la cita"),
        mascota_id: Optional[int] = Query(None, description="Filtrar por mascota"),
        limit: int = Query(50, ge=1, le=100, description="Límite de resultados")
):
    """
    Obtener lista de citas programadas
    """
    try:
        if estado:
            citas = CRUDCita.get_by_estado(db, estado=estado)
        elif mascota_id:
            citas = db.query(CRUDCita.Cita).filter(CRUDCita.Cita.id_mascota == mascota_id).limit(limit).all()
        else:
            citas = CRUDCita.get_multi(db, limit=limit)

        return citas[:limit]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener citas: {str(e)}"
        )


# ==============================
# 3. Obtener cita por ID
# ==============================
@router.get("/cita/{cita_id}", response_model=CitaResponse)
async def get_cita(
        cita_id: int,
        db: Session = Depends(get_db)
):
    """
    Obtener una cita específica por ID
    """
    try:
        cita = CRUDCita.get(db, cita_id)
        if not cita:
            raise HTTPException(
                status_code=404,
                detail="Cita no encontrada"
            )
        return cita

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener cita: {str(e)}"
        )