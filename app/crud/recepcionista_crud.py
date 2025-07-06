# app/crud/recepcionista_crud.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Tuple
from app.crud.base_crud import CRUDBase
from app.models.recepcionista import Recepcionista
from app.schemas.recepcionista_schema import RecepcionistaCreate, RecepcionistaUpdate, RecepcionistaSearch


class CRUDRecepcionista(CRUDBase[Recepcionista, RecepcionistaCreate, RecepcionistaUpdate]):

    def get_by_dni(self, db: Session, *, dni: str) -> Optional[Recepcionista]:
        """Obtener recepcionista por DNI"""
        return db.query(Recepcionista).filter(Recepcionista.dni == dni).first()

    def get_by_email(self, db: Session, *, email: str) -> Optional[Recepcionista]:
        """Obtener recepcionista por email"""
        return db.query(Recepcionista).filter(Recepcionista.email == email).first()

    def search_recepcionistas(self, db: Session, *, search_params: RecepcionistaSearch) -> Tuple[
        List[Recepcionista], int]:
        """Buscar recepcionistas con filtros múltiples"""
        query = db.query(Recepcionista)

        # Aplicar filtros
        if search_params.nombre:
            nombre_filter = f"%{search_params.nombre}%"
            query = query.filter(
                or_(
                    Recepcionista.nombre.ilike(nombre_filter),
                    Recepcionista.apellido_paterno.ilike(nombre_filter),
                    Recepcionista.apellido_materno.ilike(nombre_filter)
                )
            )

        if search_params.dni:
            query = query.filter(Recepcionista.dni == search_params.dni)

        if search_params.estado:
            query = query.filter(Recepcionista.estado == search_params.estado)

        if search_params.turno:
            query = query.filter(Recepcionista.turno == search_params.turno)

        # Contar total
        total = query.count()

        # Aplicar paginación y ordenamiento
        recepcionistas = query.order_by(Recepcionista.fecha_ingreso.desc()) \
            .offset((search_params.page - 1) * search_params.per_page) \
            .limit(search_params.per_page).all()

        return recepcionistas, total

    def exists_by_dni(self, db: Session, *, dni: str, exclude_id: Optional[int] = None) -> bool:
        """Verificar si existe una recepcionista con ese DNI"""
        query = db.query(Recepcionista).filter(Recepcionista.dni == dni)
        if exclude_id:
            query = query.filter(Recepcionista.id_recepcionista != exclude_id)
        return query.first() is not None

    def exists_by_email(self, db: Session, *, email: str, exclude_id: Optional[int] = None) -> bool:
        """Verificar si existe una recepcionista con ese email"""
        query = db.query(Recepcionista).filter(Recepcionista.email == email)
        if exclude_id:
            query = query.filter(Recepcionista.id_recepcionista != exclude_id)
        return query.first() is not None

    def get_by_turno(self, db: Session, *, turno: str, estado: str = "Activo") -> List[Recepcionista]:
        """Obtener recepcionistas por turno y estado"""
        query = db.query(Recepcionista).filter(Recepcionista.turno == turno)
        if estado:
            query = query.filter(Recepcionista.estado == estado)
        return query.all()

    def cambiar_estado(self, db: Session, *, recepcionista_id: int, nuevo_estado: str) -> Optional[Recepcionista]:
        """Cambiar el estado de una recepcionista"""
        recepcionista_obj = db.query(Recepcionista).filter(Recepcionista.id_recepcionista == recepcionista_id).first()
        if recepcionista_obj:
            recepcionista_obj.estado = nuevo_estado
            db.commit()
            db.refresh(recepcionista_obj)
        return recepcionista_obj

    def get_estadisticas_por_turno(self, db: Session) -> List[dict]:
        """Obtener estadísticas de recepcionistas agrupadas por turno"""
        return db.query(
            Recepcionista.turno,
            db.func.count(Recepcionista.id_recepcionista).label('total'),
            db.func.sum(db.case([(Recepcionista.estado == 'Activo', 1)], else_=0)).label('activas'),
            db.func.sum(db.case([(Recepcionista.estado == 'Inactivo', 1)], else_=0)).label('inactivas')
        ).group_by(Recepcionista.turno).all()

    def soft_delete(self, db: Session, *, id: int) -> Optional[Recepcionista]:
        """Soft delete - cambiar estado a Inactivo"""
        recepcionista_obj = db.query(Recepcionista).filter(Recepcionista.id_recepcionista == id).first()
        if recepcionista_obj:
            recepcionista_obj.estado = "Inactivo"
            db.commit()
            db.refresh(recepcionista_obj)
        return recepcionista_obj


# Instancia única
recepcionista = CRUDRecepcionista(Recepcionista)