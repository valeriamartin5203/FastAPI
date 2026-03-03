import shutil
import os
from fastapi import FastAPI, Depends, Form, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from database import create_db, get_session
from models import Usuario, Producto
from auth import get_password_hash, verify_password

app = FastAPI()

# Crear carpeta uploads si no existe
os.makedirs("static/uploads", exist_ok=True)

# Archivos estáticos y plantillas
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def on_startup():
    create_db()

# ---------------- HELPER ---------------- #

def get_current_user(request: Request, session: Session):
    username = request.cookies.get("user")
    if not username:
        return None
    return session.exec(
        select(Usuario).where(Usuario.username == username)
    ).first()

# ---------------- HOME ---------------- #

@app.get("/", response_class=HTMLResponse)
def home(request: Request, session: Session = Depends(get_session)):
    productos = session.exec(select(Producto)).all()
    user = get_current_user(request, session)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "productos": productos,
            "user": user
        }
    )

# ---------------- REGISTER ---------------- #

@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    # Verificar si ya existe
    existing_user = session.exec(
        select(Usuario).where(Usuario.username == username)
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    # Crear usuario
    user = Usuario(
        username=username,
        email=email,
        password=get_password_hash(password)
    )

    session.add(user)
    session.commit()

    return RedirectResponse("/login", status_code=303)

# ---------------- LOGIN ---------------- #

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    user = session.exec(
        select(Usuario).where(Usuario.username == username)
    ).first()

    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Credenciales incorrectas"
            }
        )

    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        key="user",
        value=user.username,
        httponly=True
    )
    return response

# ---------------- LOGOUT ---------------- #

@app.get("/logout")
def logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("user")
    return response

# ---------------- CREAR PRODUCTO ---------------- #

@app.post("/create")
def create_producto(
    request: Request,
    nombre: str = Form(...),
    descripcion: str = Form(...),
    precio: float = Form(...),
    imagen: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    user = get_current_user(request, session)

    if not user:
        return RedirectResponse("/login", status_code=303)

    file_path = f"static/uploads/{imagen.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(imagen.file, buffer)

    nuevo_producto = Producto(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        imagen=file_path,
        owner_id=user.id
    )

    session.add(nuevo_producto)
    session.commit()

    return RedirectResponse("/", status_code=303)

# ---------------- ELIMINAR PRODUCTO ---------------- #

@app.post("/delete/{id}")
def delete_producto(
    id: int,
    request: Request,
    session: Session = Depends(get_session)
):
    user = get_current_user(request, session)
    producto = session.get(Producto, id)

    if producto and user and producto.owner_id == user.id:
        session.delete(producto)
        session.commit()

    return RedirectResponse("/", status_code=303)