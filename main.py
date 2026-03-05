from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlmodel import SQLModel, Field, Session, create_engine, select, Relationship
from typing import Optional, List
from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware
import redis
import json
import os
from auth import get_password_hash, verify_password

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

# ✅ ACTIVAR SESIONES
app.add_middleware(SessionMiddleware, secret_key="clave_super_secreta")

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
    username: str = Field(unique=True, index=True)
    email: str
    password: str
    productos: List["Producto"] = Relationship(back_populates="owner")

class Producto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    precio: float
    descripcion: str
    imagen: Optional[str] = None
    owner_id: Optional[int] = Field(default=None, foreign_key="usuario.id")
    owner: Optional[Usuario] = Relationship(back_populates="productos")

# =========================
# SESSION DB
# =========================

def get_session():
    with Session(engine) as session:
        yield session

# =========================
# RUTAS HTML
# =========================

@app.get("/")
def index(request: Request, session: Session = Depends(get_session)):
    productos = session.exec(select(Producto)).all()
    user = request.session.get("user")

    return templates.TemplateResponse("index.html", {
        "request": request,
        "productos": productos,
        "user": user
    })

@app.get("/register")
def vista_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/login")
def vista_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@app.get("/editar")
def editar(request: Request):
    return templates.TemplateResponse("editar.html", {"request": request})

# =========================
# REGISTER (AUTO LOGIN)
# =========================

@app.post("/register")
def registrar_usuario(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    # Verificar si el usuario ya existe
    usuario_existente = session.exec(
        select(Usuario).where(Usuario.email == email)
    ).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    nuevo_usuario = Usuario(
        username=username,
        email=email,
        password=get_password_hash(password)
    )

    session.add(nuevo_usuario)
    session.commit()
    session.refresh(nuevo_usuario)

    # ✅ GUARDAR SESIÓN AUTOMÁTICA
    request.session.update({"user": {
        "id": nuevo_usuario.id,
        "username": nuevo_usuario.username
    }})

    return RedirectResponse(url="/", status_code=302)

# =========================
# LOGIN SEGURO
# =========================

@app.post("/login")
def login_usuario(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    usuario = session.exec(
        select(Usuario).where(Usuario.email == email)
    ).first()

    # LOGIN SEGURO (no revela si el usuario existe)
    if not usuario or not verify_password(password, usuario.password):
        raise HTTPException(
            status_code=401,
            detail="Credenciales inválidas"
        )

    request.session.update({"user": {
        "id": usuario.id,
        "username": usuario.username
    }})

    return RedirectResponse(url="/", status_code=302)

# =========================
# CREAR PRODUCTO DESDE HTML
# =========================

@app.post("/create")
def crear_producto(
    request: Request,
    nombre: str = Form(...),
    precio: float = Form(...),
    descripcion: str = Form(...),
    imagen: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    ruta = f"static/uploads/{imagen.filename}"

    with open(ruta, "wb") as buffer:
        buffer.write(imagen.file.read())

    nuevo_producto = Producto(
        nombre=nombre,
        precio=precio,
        descripcion=descripcion,
        imagen=ruta,
        owner_id=user["id"]
    )

    session.add(nuevo_producto)
    session.commit()

    redis_client.delete("ranking_productos")

    return RedirectResponse(url="/", status_code=303)

# =========================
# ELIMINAR PRODUCTO
# =========================

@app.post("/delete/{producto_id}")
def eliminar_producto(
    producto_id: int,
    request: Request,
    session: Session = Depends(get_session)
):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    producto = session.get(Producto, producto_id)

    if producto and producto.owner_id == user["id"]:
        session.delete(producto)
        session.commit()
        redis_client.delete("ranking_productos")

    return RedirectResponse(url="/", status_code=303)

# =========================
# API PRODUCTOS
# =========================

@app.get("/productos", response_model=List[Producto])
def listar_productos(session: Session = Depends(get_session)):
    return session.exec(select(Producto)).all()

@app.delete("/productos/{producto_id}")
def eliminar_producto_api(producto_id: int, session: Session = Depends(get_session)):
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