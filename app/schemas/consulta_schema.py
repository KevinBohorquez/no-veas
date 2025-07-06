# app/schemas/consulta_schema.py
from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from .base_schema import BaseResponse, PaginationResponse

# ===== SOLICITUD ATENCIÓN =====

class SolicitudAtencionCreate(BaseModel):
    """Schema para crear solicitud de atención"""
    id_mascota: int
    id_recepcionista: int
    tipo_solicitud: str  # 'Consulta urgente', 'Consulta normal', 'Servicio programado'
    fecha_hora_solicitud: Optional[datetime] = None
    
    @validator('tipo_solicitud')
    def validate_tipo_solicitud(cls, v):
        tipos_validos = ['Consulta urgente', 'Consulta normal', 'Servicio programado']
        if v not in tipos_validos:
            raise ValueError(f'Tipo debe ser uno de: {", ".join(tipos_validos)}')
        return v


class SolicitudAtencionResponse(BaseResponse):
    """Schema para respuesta de solicitud"""
    id_solicitud: int
    id_mascota: int
    id_recepcionista: int
    fecha_hora_solicitud: Optional[datetime]
    tipo_solicitud: str
    estado: str


# ===== TRIAJE =====

class TriajeCreate(BaseModel):
    """Schema para crear triaje"""
    id_solicitud: int
    id_veterinario: int
    peso_mascota: float
    latido_por_minuto: int
    frecuencia_respiratoria_rpm: int
    temperatura: float
    frecuencia_pulso: int
    clasificacion_urgencia: str
    talla: Optional[float] = None
    tiempo_capilar: Optional[str] = None
    color_mucosas: Optional[str] = None
    porce_deshidratacion: Optional[float] = None
    condicion_corporal: str = "Ideal"
    fecha_hora_triaje: Optional[datetime] = None
    
    @validator('peso_mascota')
    def validate_peso(cls, v):
        if v <= 0 or v > 100:
            raise ValueError('Peso debe estar entre 0 y 100 kg')
        return v
    
    @validator('latido_por_minuto')
    def validate_latido(cls, v):
        if v < 40 or v > 300:
            raise ValueError('Latidos por minuto debe estar entre 40 y 300')
        return v
    
    @validator('temperatura')
    def validate_temperatura(cls, v):
        if v < 35.0 or v > 42.0:
            raise ValueError('Temperatura debe estar entre 35.0 y 42.0°C')
        return v


class TriajeResponse(BaseResponse):
    """Schema para respuesta de triaje"""
    id_triaje: int
    id_solicitud: int
    id_veterinario: int
    fecha_hora_triaje: datetime
    peso_mascota: float
    latido_por_minuto: int
    frecuencia_respiratoria_rpm: int
    temperatura: float
    clasificacion_urgencia: str
    condicion_corporal: str


# ===== CONSULTA =====

class ConsultaCreate(BaseModel):
    """Schema para crear consulta"""
    id_triaje: int
    id_veterinario: int
    tipo_consulta: str
    motivo_consulta: Optional[str] = None
    sintomas_observados: Optional[str] = None
    diagnostico_preliminar: Optional[str] = None
    observaciones: Optional[str] = None
    condicion_general: str
    es_seguimiento: bool = False
    fecha_consulta: Optional[datetime] = None
    
    @validator('tipo_consulta')
    def validate_tipo_consulta(cls, v):
        if len(v.strip()) < 5:
            raise ValueError('Tipo de consulta debe tener al menos 5 caracteres')
        return v.strip()
    
    @validator('condicion_general')
    def validate_condicion_general(cls, v):
        condiciones = ['Excelente', 'Buena', 'Regular', 'Mala', 'Critica']
        if v not in condiciones:
            raise ValueError(f'Condición debe ser una de: {", ".join(condiciones)}')
        return v


class ConsultaResponse(BaseResponse):
    """Schema para respuesta de consulta"""
    id_consulta: int
    id_triaje: int
    id_veterinario: int
    tipo_consulta: str
    fecha_consulta: datetime
    motivo_consulta: Optional[str]
    condicion_general: str
    es_seguimiento: bool


# ===== DIAGNÓSTICO =====

class DiagnosticoCreate(BaseModel):
    """Schema para crear diagnóstico"""
    id_consulta: int
    id_patologia: int
    diagnostico: str
    tipo_diagnostico: str = "Presuntivo"
    estado_patologia: str = "Activa"
    fecha_diagnostico: Optional[datetime] = None
    
    @validator('diagnostico')
    def validate_diagnostico(cls, v):
        if len(v.strip()) < 5:
            raise ValueError('Diagnóstico debe tener al menos 5 caracteres')
        return v.strip()


class DiagnosticoResponse(BaseResponse):
    """Schema para respuesta de diagnóstico"""
    id_diagnostico: int
    id_consulta: int
    id_patologia: int
    tipo_diagnostico: str
    fecha_diagnostico: datetime
    estado_patologia: str
    diagnostico: str


# ===== TRATAMIENTO =====

class TratamientoCreate(BaseModel):
    """Schema para crear tratamiento"""
    id_consulta: int
    id_patologia: int
    tipo_tratamiento: str
    fecha_inicio: date
    eficacia_tratamiento: Optional[str] = None
    
    @validator('tipo_tratamiento')
    def validate_tipo_tratamiento(cls, v):
        tipos = ['Medicamentoso', 'Quirurgico', 'Terapeutico', 'Preventivo']
        if v not in tipos:
            raise ValueError(f'Tipo debe ser uno de: {", ".join(tipos)}')
        return v


class TratamientoResponse(BaseResponse):
    """Schema para respuesta de tratamiento"""
    id_tratamiento: int
    id_consulta: int
    id_patologia: int
    fecha_inicio: date
    eficacia_tratamiento: Optional[str]
    tipo_tratamiento: str


# ===== CITA =====

class CitaCreate(BaseModel):
    """Schema para crear cita"""
    id_mascota: int
    id_servicio: int
    fecha_hora_programada: datetime
    id_servicio_solicitado: Optional[int] = None
    requiere_ayuno: Optional[bool] = None
    observaciones: Optional[str] = None
    
    @validator('observaciones')
    def validate_observaciones(cls, v):
        if v and len(v.strip()) < 3:
            raise ValueError('Observaciones debe tener al menos 3 caracteres')
        return v.strip() if v else v


class CitaUpdate(BaseModel):
    """Schema para actualizar cita"""
    fecha_hora_programada: Optional[datetime] = None
    estado_cita: Optional[str] = None
    requiere_ayuno: Optional[bool] = None
    observaciones: Optional[str] = None
    
    @validator('estado_cita')
    def validate_estado_cita(cls, v):
        if v and v not in ['Programada', 'Cancelada', 'Atendida']:
            raise ValueError('Estado debe ser Programada, Cancelada o Atendida')
        return v


class CitaResponse(BaseResponse):
    """Schema para respuesta de cita"""
    id_cita: int
    id_mascota: int
    id_servicio: int
    id_servicio_solicitado: Optional[int]
    fecha_hora_programada: datetime
    estado_cita: str
    requiere_ayuno: Optional[bool]
    observaciones: Optional[str]


# ===== SERVICIO SOLICITADO =====

class ServicioSolicitadoCreate(BaseModel):
    """Schema para crear servicio solicitado"""
    id_consulta: int
    id_servicio: int
    prioridad: Optional[str] = "Normal"
    comentario_opcional: Optional[str] = None
    fecha_solicitado: Optional[datetime] = None
    
    @validator('prioridad')
    def validate_prioridad(cls, v):
        if v and v not in ['Urgente', 'Normal', 'Programable']:
            raise ValueError('Prioridad debe ser Urgente, Normal o Programable')
        return v


class ServicioSolicitadoResponse(BaseResponse):
    """Schema para respuesta de servicio solicitado"""
    id_servicio_solicitado: int
    id_consulta: int
    id_servicio: int
    fecha_solicitado: Optional[datetime]
    prioridad: Optional[str]
    estado_examen: str
    comentario_opcional: Optional[str]


# ===== RESULTADO SERVICIO =====

class ResultadoServicioCreate(BaseModel):
    """Schema para crear resultado de servicio"""
    id_cita: int
    id_veterinario: int
    resultado: str
    interpretacion: Optional[str] = None
    archivo_adjunto: Optional[str] = None
    fecha_realizacion: Optional[datetime] = None
    
    @validator('resultado')
    def validate_resultado(cls, v):
        if len(v.strip()) < 5:
            raise ValueError('Resultado debe tener al menos 5 caracteres')
        return v.strip()


class ResultadoServicioResponse(BaseResponse):
    """Schema para respuesta de resultado de servicio"""
    id_resultado: int
    id_cita: int
    id_veterinario: int
    resultado: str
    interpretacion: Optional[str]
    archivo_adjunto: Optional[str]
    fecha_realizacion: datetime


# ===== HISTORIAL CLÍNICO =====

class HistorialClinicoCreate(BaseModel):
    """Schema para crear historial clínico"""
    id_mascota: int
    tipo_evento: str
    descripcion_evento: str
    id_consulta: Optional[int] = None
    id_diagnostico: Optional[int] = None
    id_tratamiento: Optional[int] = None
    id_veterinario: Optional[int] = None
    edad_meses: Optional[int] = None
    peso_momento: Optional[float] = None
    observaciones: Optional[str] = None
    fecha_evento: Optional[datetime] = None
    
    @validator('tipo_evento')
    def validate_tipo_evento(cls, v):
        if len(v.strip()) < 4:
            raise ValueError('Tipo de evento debe tener al menos 4 caracteres')
        return v.strip()
    
    @validator('descripcion_evento')
    def validate_descripcion_evento(cls, v):
        if len(v.strip()) < 5:
            raise ValueError('Descripción debe tener al menos 5 caracteres')
        return v.strip()


class HistorialClinicoResponse(BaseResponse):
    """Schema para respuesta de historial clínico"""
    id_historial: int
    id_mascota: int
    fecha_evento: datetime
    tipo_evento: str
    descripcion_evento: str
    edad_meses: Optional[int]
    peso_momento: Optional[float]
    observaciones: Optional[str]


# ===== SCHEMAS DE BÚSQUEDA Y LISTADOS =====

class ConsultaSearch(BaseModel):
    """Schema para búsqueda de consultas"""
    id_mascota: Optional[int] = None
    id_veterinario: Optional[int] = None
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None
    condicion_general: Optional[str] = None
    es_seguimiento: Optional[bool] = None
    page: int = 1
    per_page: int = 20


class CitaSearch(BaseModel):
    """Schema para búsqueda de citas"""
    id_mascota: Optional[int] = None
    id_servicio: Optional[int] = None
    estado_cita: Optional[str] = None
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None
    page: int = 1
    per_page: int = 20


class HistorialSearch(BaseModel):
    """Schema para búsqueda de historial"""
    id_mascota: int
    tipo_evento: Optional[str] = None
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None
    page: int = 1
    per_page: int = 20