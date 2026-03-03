from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models import Categoria, CategoriaCreate

router = APIRouter(prefix="/categorias", tags=["Categorias"])

@router.post("/")
def crear_categoria(categoria: CategoriaCreate, session: Session = Depends(get_session)):
    db_categoria = Categoria.model_validate(categoria)
    session.add(db_categoria)
    session.commit()
    session.refresh(db_categoria)
    return db_categoria

@router.get("/")
def listar_categorias(session: Session = Depends(get_session)):
    categorias = session.exec(select(Categoria)).all()
    return categorias

@router.get("/{categoria_id}")
def obtener_categoria(categoria_id: int, session: Session = Depends(get_session)):
    categoria = session.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return categoria

@router.delete("/{categoria_id}")
def eliminar_categoria(categoria_id: int, session: Session = Depends(get_session)):
    categoria = session.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    session.delete(categoria)
    session.commit()
    return {"mensaje": "Categoría eliminada"}