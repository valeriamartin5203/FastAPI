# 🛍️ Proyecto Final – Tienda Web con FastAPI y Redis

Aplicación web desarrollada con **FastAPI**, **SQLModel**, **SQLite** y **Redis** que permite a los usuarios registrarse, iniciar sesión y gestionar productos con imágenes.

---

# 📌 Descripción del Dominio del Proyecto

Este proyecto representa el dominio de una **tienda en línea** donde:

- Existen **Usuarios**
- Cada usuario puede crear múltiples **Productos**
- Cada producto pertenece a un solo usuario
- Los productos pueden visualizarse públicamente
- Solo el dueño del producto puede eliminarlo

## 🔎 Entidades principales

### 👤 Usuario
- id
- nombre
- email
- password
- relación 1:N con productos

### 🛍️ Producto
- id
- nombre
- precio
- descripción
- imagen
- usuario_id (clave foránea)

Relación:
Un Usuario → puede tener muchos Productos.

---

# 🚀 Tecnologías Utilizadas

- FastAPI
- SQLModel
- SQLite
- Redis
- Jinja2
- Uvicorn

---

# ⚙️ Instalación del Proyecto

## 1️⃣ Clonar o descargar el proyecto

```bash
git clone <url-del-repositorio>
cd proyecto


---

## Crear entorno virtual


