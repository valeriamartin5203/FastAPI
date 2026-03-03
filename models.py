from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime

class Empleado(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    codigo: str

    ventas: List["Venta"] = Relationship(back_populates="empleado")


class Producto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    precio: float = Field(gt=0)
    existencia: float = Field(ge=0)
    tipo: str
    imagen: Optional[str] = None


class Venta(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    total: float
    fecha: datetime = Field(default_factory=datetime.utcnow)

    empleado_id: int = Field(foreign_key="empleado.id")
    empleado: Optional[Empleado] = Relationship(back_populates="ventas")