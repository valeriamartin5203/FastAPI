from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel, Field, Session, create_engine, select, Relationship
from typing import Optional, List
from contextlib import asynccontextmanager
import redis
import json
import os

# =========================
# BASE DE DATOS
# =========================

sqlite_file_name = "database.db"
engine = create_engine(f"sqlite:///{sqlite_file_name}", echo=False)

def create_db():
    SQLModel.metadata.create_all(engine)

# =========================
# LIFESPAN (FORMA MODERNA)
# =========================

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()
    yield

app = FastAPI(
    title="API Proyecto Final con Redis",
    lifespan=lifespan
)

# =========================
# REDIS (UPSTASH)
# =========================

redis_client = redis.Redis(
    host="liked-stingray-38757.upstash.io",  # TU HOST
    port=6379,
    username="default",
    password="AZdlAAIncDEwM2UxMGZhYjQxM2I0ZDUxYjYxZDgzMzgxMGY2ZWNlNHAxMzg3NTc",
    ssl=True,
    decode_responses=True
)

# =========================
# MODELOS
# =========================

class Producto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(min_length=3, max_length=50)
    precio: float = Field(gt=0)
    usuario_id: int = Field(foreign_key="usuario.id")
    imagen: Optional[str] = None

class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=5, max_length=100)
    productos: List[Producto] = Relationship(back_populates="usuario")

Producto.usuario = Relationship(back_populates="productos")

# =========================
# DEPENDENCIA SESSION
# =========================

def get_session():
    with Session(engine) as session:
        yield session

# =========================
# CRUD USUARIOS
# =========================

@app.post("/usuarios", response_model=Usuario)
def crear_usuario(usuario: Usuario, session: Session = Depends(get_session)):
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario

@app.get("/usuarios", response_model=List[Usuario])
def listar_usuarios(session: Session = Depends(get_session)):
    return session.exec(select(Usuario)).all()

@app.get("/usuarios/{usuario_id}", response_model=Usuario)
def detalle_usuario(usuario_id: int, session: Session = Depends(get_session)):
    usuario = session.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

@app.patch("/usuarios/{usuario_id}", response_model=Usuario)
def actualizar_usuario(usuario_id: int, datos: Usuario, session: Session = Depends(get_session)):
    usuario = session.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    usuario.nombre = datos.nombre
    usuario.email = datos.email

    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario

@app.delete("/usuarios/{usuario_id}")
def eliminar_usuario(usuario_id: int, session: Session = Depends(get_session)):
    usuario = session.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    session.delete(usuario)
    session.commit()
    return {"mensaje": "Usuario eliminado"}

# =========================
# CRUD PRODUCTOS
# =========================

@app.post("/productos", response_model=Producto)
def crear_producto(producto: Producto, session: Session = Depends(get_session)):
    session.add(producto)
    session.commit()
    session.refresh(producto)

    redis_client.delete("ranking_productos")

    return producto

@app.get("/productos", response_model=List[Producto])
def listar_productos(session: Session = Depends(get_session)):
    return session.exec(select(Producto)).all()

@app.get("/productos/{producto_id}", response_model=Producto)
def detalle_producto(producto_id: int, session: Session = Depends(get_session)):
    producto = session.get(Producto, producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto

@app.patch("/productos/{producto_id}", response_model=Producto)
def actualizar_producto(producto_id: int, datos: Producto, session: Session = Depends(get_session)):
    producto = session.get(Producto, producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    producto.nombre = datos.nombre
    producto.precio = datos.precio

    session.add(producto)
    session.commit()
    session.refresh(producto)

    redis_client.delete("ranking_productos")

    return producto

@app.delete("/productos/{producto_id}")
def eliminar_producto(producto_id: int, session: Session = Depends(get_session)):
    producto = session.get(Producto, producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    session.delete(producto)
    session.commit()

    redis_client.delete("ranking_productos")

    return {"mensaje": "Producto eliminado"}

# =========================
# ENDPOINT PESADO CON CACHE
# =========================

@app.get("/productos/ranking")
def ranking_productos(session: Session = Depends(get_session)):

    cache = redis_client.get("ranking_productos")

    if cache:
        return {"source": "cache", "data": json.loads(cache)}

    productos = session.exec(
        select(Producto).order_by(Producto.precio.desc())
    ).all()

    redis_client.setex(
        "ranking_productos",
        60,
        json.dumps([p.model_dump() for p in productos])
    )

    return {"source": "database", "data": productos}

# =========================
# SUBIDA DE IMÁGENES
# =========================

os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/productos/{producto_id}/imagen")
def subir_imagen(producto_id: int, file: UploadFile = File(...), session: Session = Depends(get_session)):
    producto = session.get(Producto, producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    ruta = f"static/uploads/{file.filename}"

    with open(ruta, "wb") as buffer:
        buffer.write(file.file.read())

    producto.imagen = ruta
    session.add(producto)
    session.commit()

    return {"mensaje": "Imagen subida correctamente"}