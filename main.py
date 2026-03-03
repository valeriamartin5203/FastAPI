from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()
    yield

app = FastAPI(
    title="API Proyecto Final con Redis",
    lifespan=lifespan
)

# =========================
# TEMPLATES Y STATIC
# =========================

templates = Jinja2Templates(directory="templates")

os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# =========================
# REDIS (UPSTASH)
# =========================

redis_client = redis.Redis(
    host="liked-stingray-38757.upstash.io",
    port=6379,
    username="default",
    password="AZdlAAIncDEwM2UxMGZhYjQxM2I0ZDUxYjYxZDgzMzgxMGY2ZWNlNHAxMzg3NTc",
    ssl=True,
    decode_responses=True
)

# =========================
# MODELOS
# =========================

class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    email: str
    password: str
    productos: List["Producto"] = Relationship(back_populates="usuario")

class Producto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    precio: float
    usuario_id: int = Field(foreign_key="usuario.id")
    imagen: Optional[str] = None
    usuario: Optional[Usuario] = Relationship(back_populates="productos")

# =========================
# SESSION
# =========================

def get_session():
    with Session(engine) as session:
        yield session

# =========================
# RUTAS HTML
# =========================

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/register")
def vista_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/login")
def vista_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/editar")
def editar(request: Request):
    return templates.TemplateResponse("editar.html", {"request": request})

# =========================
# REGISTER
# =========================

@app.post("/register")
def registrar_usuario(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    nuevo_usuario = Usuario(
        nombre=username,
        email=email,
        password=password
    )

    session.add(nuevo_usuario)
    session.commit()

    return RedirectResponse(url="/login", status_code=303)

# =========================
# LOGIN
# =========================

@app.post("/login")
def login_usuario(
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    usuario = session.exec(
        select(Usuario).where(Usuario.email == email)
    ).first()

    if not usuario or usuario.password != password:
        return {"error": "Credenciales incorrectas"}

    return RedirectResponse(url="/", status_code=303)

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
# RANKING CON CACHE
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
# SUBIR IMAGEN
# =========================

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