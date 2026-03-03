from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List


# ---------------- USUARIO ---------------- #

class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str
    password: str

    productos: List["Producto"] = Relationship(back_populates="owner")


# ---------------- PRODUCTO ---------------- #

class Producto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    descripcion: str
    precio: float
    imagen: Optional[str] = None

    owner_id: Optional[int] = Field(default=None, foreign_key="usuario.id")
    owner: Optional[Usuario] = Relationship(back_populates="productos")