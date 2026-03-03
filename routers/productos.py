from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from database import get_session
from models import Producto, ProductoCreate
from redis_client import redis_client
import os
import json

router = APIRouter(prefix="/productos", tags=["Productos"])

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------------------
# CRUD
# -------------------

@router.post("/")
def crear_producto(producto: ProductoCreate, session: Session = Depends(get_session)):
    db_producto = Producto.model_validate(producto)
    session.add(db_producto)
    session.commit()
    session.refresh(db_producto)
    return db_producto

@router.get("/")
def listar_productos(session: Session = Depends(get_session)):
    productos = session.exec(select(Producto)).all()
    return productos

@router.get("/{producto_id}")
def obtener_producto(producto_id: int, session: Session = Depends(get_session)):
    producto = session.get(Producto, producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto

@router.put("/{producto_id}")
def actualizar_producto(producto_id: int, producto_data: ProductoCreate, session: Session = Depends(get_session)):
    producto = session.get(Producto, producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    for key, value in producto_data.dict().items():
        setattr(producto, key, value)

    session.commit()
    session.refresh(producto)
    return producto

@router.delete("/{producto_id}")
def eliminar_producto(producto_id: int, session: Session = Depends(get_session)):
    producto = session.get(Producto, producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    session.delete(producto)
    session.commit()
    return {"mensaje": "Producto eliminado"}

# -------------------
# REDIS CACHING
# -------------------

@router.get("/ranking/top")
def ranking_productos(session: Session = Depends(get_session)):
    cache = redis_client.get("ranking_productos")
    if cache:
        return json.loads(cache)

    productos = session.exec(select(Producto).order_by(Producto.stock.desc())).all()
    resultado = [producto.dict() for producto in productos]

    redis_client.set("ranking_productos", json.dumps(resultado), ex=60)
    return resultado

# -------------------
# SUBIDA DE IMAGEN
# -------------------

@router.post("/{producto_id}/imagen")
def subir_imagen(producto_id: int, file: UploadFile = File(...), session: Session = Depends(get_session)):
    producto = session.get(Producto, producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    file_path = f"{UPLOAD_FOLDER}/{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    producto.imagen = file_path
    session.commit()
    return {"mensaje": "Imagen subida correctamente"}