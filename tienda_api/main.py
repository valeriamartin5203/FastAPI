from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select
from database import engine, create_db
from models import Producto, Empleado, Venta
from schemas import ProductoCreate, ProductoUpdate, EmpleadoCreate, VentaCreate
from typing import List
from cache import r
from fastapi.staticfiles import StaticFiles
import json
import os

app = FastAPI()

create_db()

# Carpeta para imágenes
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_session():
    with Session(engine) as session:
        yield session

# ------------------ CRUD PRODUCTOS ------------------

@app.post("/productos")
def crear_producto(data: ProductoCreate, session: Session = Depends(get_session)):
    producto = Producto.from_orm(data)
    session.add(producto)
    session.commit()
    session.refresh(producto)
    return producto


@app.get("/productos", response_model=List[Producto])
def listar_productos(session: Session = Depends(get_session)):
    return session.exec(select(Producto)).all()


@app.get("/productos/{id}")
def obtener_producto(id: int, session: Session = Depends(get_session)):
    producto = session.get(Producto, id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto


@app.put("/productos/{id}")
def actualizar_producto(id: int, data: ProductoUpdate, session: Session = Depends(get_session)):
    producto = session.get(Producto, id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    if data.nombre:
        producto.nombre = data.nombre
    if data.precio:
        producto.precio = data.precio
    if data.existencia:
        producto.existencia = data.existencia
    if data.tipo:
        producto.tipo = data.tipo

    session.commit()
    session.refresh(producto)
    return producto


@app.delete("/productos/{id}")
def eliminar_producto(id: int, session: Session = Depends(get_session)):
    producto = session.get(Producto, id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    session.delete(producto)
    session.commit()
    return {"mensaje": "Producto eliminado"}

# ------------------ SUBIR IMAGEN ------------------

@app.post("/productos/{id}/imagen")
def subir_imagen(id: int, file: UploadFile = File(...), session: Session = Depends(get_session)):
    producto = session.get(Producto, id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    filepath = f"static/{file.filename}"

    with open(filepath, "wb") as buffer:
        buffer.write(file.file.read())

    producto.imagen = filepath
    session.commit()

    return {"mensaje": "Imagen subida correctamente"}

# ------------------ CRUD EMPLEADOS ------------------

@app.post("/empleados")
def crear_empleado(data: EmpleadoCreate, session: Session = Depends(get_session)):
    empleado = Empleado.from_orm(data)
    session.add(empleado)
    session.commit()
    session.refresh(empleado)
    return empleado

# ------------------ CREAR VENTA ------------------

@app.post("/ventas")
def crear_venta(data: VentaCreate, session: Session = Depends(get_session)):
    empleado = session.get(Empleado, data.empleado_id)
    if not empleado:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")

    venta = Venta(total=data.total, empleado_id=data.empleado_id)
    session.add(venta)
    session.commit()
    session.refresh(venta)
    return venta

# ------------------ REDIS CACHE ------------------

@app.get("/estadisticas/productos-caros")
def productos_caros(session: Session = Depends(get_session)):

    cache = r.get("productos_caros")

    if cache:
        return json.loads(cache)

    productos = session.exec(
        select(Producto).where(Producto.precio > 50)
    ).all()

    data = [p.dict() for p in productos]

    r.setex("productos_caros", 60, json.dumps(data))

    return data