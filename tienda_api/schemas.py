from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ProductoCreate(BaseModel):
    nombre: str
    precio: float = Field(gt=0)
    existencia: float = Field(ge=0)
    tipo: str

class ProductoUpdate(BaseModel):
    nombre: Optional[str]
    precio: Optional[float]
    existencia: Optional[float]
    tipo: Optional[str]

class EmpleadoCreate(BaseModel):
    nombre: str
    codigo: str

class VentaCreate(BaseModel):
    total: float = Field(gt=0)
    empleado_id: int