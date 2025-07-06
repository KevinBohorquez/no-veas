# app/schemas/recepcionista_schema.py
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import date
from .base_schema import BaseResponse, PaginationResponse, validate_dni, validate_telefono, validate_name

# ===== SCHEMAS DE INPUT (REQUEST) =====

class RecepcionistaCreate(BaseModel):
    """Schema para crear un recepcionista"""
    nombre: str
    apellido_paterno: str
    apellido_materno: str
    dni: str
    telefono: str
    email: EmailStr
    fecha_ingreso: Optional[date] = None
    turno: Optional[str] = None  # 'Mañana', 'Tarde', 'Noche'
    estado: Optional[str] = "Activo"
    contraseña: str
    genero: str  # 'F' o 'M'
    
    # Validators
    _validate_nombre = validator('nombre', allow_reuse=True)(validate_name)
    _validate_apellido_paterno = validator('apellido_paterno', allow_reuse=True)(validate_name)
    _validate_apellido_materno = validator('apellido_materno', allow_reuse=True)(validate_name)
    _validate_dni = validator('dni', allow_reuse=True)(validate_dni)
    _validate_telefono = validator('telefono', allow_reuse=True)(validate_telefono)
    
    @validator('turno')
    def validate_turno(cls, v):
        if v and v not in ['Mañana', 'Tarde', 'Noche']:
            raise ValueError('Turno debe ser Mañana, Tarde o Noche')
        return v
    
    @validator('estado')
    def validate_estado(cls, v):
        if v and v not in ['Activo', 'Inactivo']:
            raise ValueError('Estado debe ser Activo o Inactivo')
        return v
    
    @validator('genero')
    def validate_genero(cls, v):
        if v not in ['F', 'M']:
            raise ValueError('Género debe ser F o M')
        return v


class RecepcionistaUpdate(BaseModel):
    """Schema para actualizar un recepcionista"""
    nombre: Optional[str] = None
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    turno: Optional[str] = None
    estado: Optional[str] = None
    contraseña: Optional[str] = None
    
    # Validators similares a Create
    _validate_nombre = validator('nombre', allow_reuse=True)(validate_name)
    _validate_apellido_paterno = validator('apellido_paterno', allow_reuse=True)(validate_name)
    _validate_apellido_materno = validator('apellido_materno', allow_reuse=True)(validate_name)
    _validate_telefono = validator('telefono', allow_reuse=True)(validate_telefono)


class RecepcionistaLogin(BaseModel):
    """Schema para login de recepcionista"""
    email: EmailStr
    contraseña: str


# ===== SCHEMAS DE OUTPUT (RESPONSE) =====

class RecepcionistaResponse(BaseResponse):
    """Schema para devolver información de recepcionista"""
    id_recepcionista: int
    nombre: str
    apellido_paterno: str
    apellido_materno: str
    dni: str
    telefono: str
    email: str
    fecha_ingreso: Optional[date]
    turno: Optional[str]
    estado: Optional[str]
    genero: str
    # Nota: NO incluimos contraseña por seguridad


class RecepcionistaListResponse(PaginationResponse):
    """Schema para lista de recepcionistas"""
    recepcionistas: list[RecepcionistaResponse]


# ===== SCHEMAS DE BÚSQUEDA =====

class RecepcionistaSearch(BaseModel):
    """Schema para búsqueda de recepcionistas"""
    nombre: Optional[str] = None
    dni: Optional[str] = None
    estado: Optional[str] = None
    turno: Optional[str] = None
    page: int = 1
    per_page: int = 20