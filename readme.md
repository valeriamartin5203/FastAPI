# 🛒 Marketplace CUAK - API FastAPI con Redis

Una plataforma de marketplace completamente funcional construida con **FastAPI**, **SQLModel** y **Redis** para gestionar productos, usuarios y caché de rendimiento.

---

## 📋 Descripción del Proyecto

**Marketplace CUAK** es una aplicación web que permite a los usuarios:

- ✅ Registrarse e iniciar sesión con contraseñas encriptadas (Argon2)
- ✅ Crear, visualizar y eliminar productos
- ✅ Subir imágenes de productos
- ✅ Ver un ranking de productos en caché con Redis
- ✅ Gestionar sesiones de usuario persistentes
- ✅ API REST completa para operaciones CRUD

### Tecnologías Utilizadas

| Tecnología | Versión | Propósito |
|------------|---------|----------|
| FastAPI | ^0.104 | Framework web asincrónico |
| SQLModel | ^0.0.14 | ORM con tipado de Python |
| SQLite | - | Base de datos |
| Redis | - | Caché distribuido (Upstash) |
| Passlib + Argon2 | - | Encriptación de contraseñas |
| Jinja2 | - | Templates HTML |
| Bootstrap 5 | - | Estilos CSS |

---

## 🚀 Instalación

### 1. Clonar o descargar el proyecto

```bash
cd "c:\Users\afton\OneDrive\Escritorio\programacion para internet\FastAPI"
```

### 2. Crear y activar el entorno virtual

```bash
# Crear entorno virtual
python -m venv .venv

# Activar (Windows)
.venv\Scripts\Activate

# Activar (Linux/Mac)
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

Si no tienes `requirements.txt`, instala manualmente:

```bash
pip install fastapi uvicorn sqlmodel redis passlib argon2-cffi python-multipart jinja2 starlette
```

### 4. Configurar Redis (Upstash)

Este proyecto utiliza **Redis en la nube** mediante [Upstash](https://upstash.com/).

#### Opción A: Usar Redis local (para desarrollo)

```bash
# Instalar Redis (Windows usando WSL o Docker)
docker run -d -p 6379:6379 redis:latest

# O en Linux/Mac
brew install redis
redis-server
```

#### Opción B: Usar Upstash (ya configurado en el proyecto)

Las credenciales de Upstash ya están configuradas en `main.py`:

```python
redis_client = redis.Redis(
    host="liked-stingray-38757.upstash.io",
    port=6379,
    username="default",
    password="AZdlAAIncDEwM2UxMGZhYjQxM2I0ZDUxYjYxZDgzMzgxMGY2ZWNlNHAxMzg3NTc",
    ssl=True,
    decode_responses=True
)
```

---

## ⚙️ Levantar la Aplicación

### Iniciar el servidor FastAPI

```bash
uvicorn main:app --reload
```

**Salida esperada:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [PID] using WatchFiles
```

### Acceder a la aplicación

- 🌐 **Interfaz web**: http://localhost:8000/
- 📚 **Documentación Swagger**: http://localhost:8000/docs
- 🔧 **Documentación ReDoc**: http://localhost:8000/redoc

---

## 📖 Ejemplos de Uso

### 1️⃣ Registro de Usuario

#### Con Curl:
```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=juan&email=juan@example.com&password=micontraseña123"
```

#### Con Postman:
1. Método: `POST`
2. URL: `http://localhost:8000/register`
3. Body → form-data:
   - `username`: juan
   - `email`: juan@example.com
   - `password`: micontraseña123

### 2️⃣ Iniciar Sesión

#### Con Curl:
```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=juan@example.com&password=micontraseña123" \
  -v
```

#### Con Postman:
1. Método: `POST`
2. URL: `http://localhost:8000/login`
3. Body → form-data:
   - `email`: juan@example.com
   - `password`: micontraseña123

### 3️⃣ Crear Producto

#### Con Curl (multipart/form-data):
```bash
curl -X POST "http://localhost:8000/create" \
  -H "Cookie: session=<tu_cookie_de_sesion>" \
  -F "nombre=Laptop" \
  -F "precio=999.99" \
  -F "descripcion=Laptop gaming de alta gama" \
  -F "imagen=@C:\ruta\a\imagen.jpg"
```

#### Con Postman:
1. Método: `POST`
2. URL: `http://localhost:8000/create`
3. Body → form-data:
   - `nombre`: Laptop
   - `precio`: 999.99
   - `descripcion`: Laptop gaming de alta gama
   - `imagen`: (seleccionar archivo)
4. Headers → Cookie: `session=<tu_cookie_de_sesion>`

### 4️⃣ Listar Productos (API)

#### Con Curl:
```bash
curl -X GET "http://localhost:8000/productos" \
  -H "accept: application/json"
```

#### Respuesta:
```json
[
  {
    "id": 1,
    "nombre": "Laptop",
    "precio": 999.99,
    "descripcion": "Laptop gaming de alta gama",
    "imagen": "static/uploads/imagen.jpg",
    "owner_id": 1
  }
]
```

### 5️⃣ Ranking de Productos con Caché Redis

#### Con Curl:
```bash
curl -X GET "http://localhost:8000/productos/ranking" \
  -H "accept: application/json"
```

#### Respuesta (primera vez - desde BD):
```json
{
  "source": "cache",
  "data": [
    {
      "id": 1,
      "nombre": "Laptop",
      "precio": 999.99,
      "descripcion": "Laptop gaming",
      "imagen": "static/uploads/imagen.jpg",
      "owner_id": 1
    }
  ]
}
```

### 6️⃣ Eliminar Producto

#### Con Curl:
```bash
curl -X POST "http://localhost:8000/delete/1" \
  -H "Cookie: session=<tu_cookie_de_sesion>"
```

#### Con Postman (API):
```bash
curl -X DELETE "http://localhost:8000/productos/1"
```

### 7️⃣ Cerrar Sesión

#### Con Curl:
```bash
curl -X GET "http://localhost:8000/logout" \
  -H "Cookie: session=<tu_cookie_de_sesion>"
```

---

## 📁 Estructura del Proyecto

```
FastAPI/
├── main.py                 # Aplicación principal
├── models.py              # Modelos SQLModel (Usuario, Producto)
├── auth.py                # Funciones de autenticación (hash, verify)
├── database.py            # Configuración de BD y sesiones
├── redis_client.py        # Cliente Redis
├── requirements.txt       # Dependencias del proyecto
├── database.db            # Base de datos SQLite
├── static/
│   └── uploads/           # Carpeta para imágenes cargadas
├── templates/
│   ├── base.html         # Template base (navbar, styles)
│   ├── index.html        # Página principal
│   ├── login.html        # Formulario de login
│   ├── register.html     # Formulario de registro
│   └── editar.html       # Página de edición
└── routers/
    ├── categorias.py     # Rutas para categorías (futuro)
    └── productos.py      # Rutas para productos (API)
```

---

## 🔐 Seguridad

- ✅ **Contraseñas encriptadas** con Argon2-CFFI
- ✅ **Sesiones de usuario** con Starlette SessionMiddleware
- ✅ **CSRF protection** disponible
- ⚠️ **Nota**: La clave secreta de sesiones (`clave_super_secreta`) debe cambiarse en producción

### Cambiar clave secreta:

```python
# En main.py, línea 33
app.add_middleware(SessionMiddleware, secret_key="TU_NUEVA_CLAVE_SUPER_SEGURA_AQUí")
```

---

## 🧪 Pruebas Rápidas

### Test 1: Registro y login completo

```bash
# 1. Registrar usuario
curl -X POST "http://localhost:8000/register" \
  -d "username=test&email=test@test.com&password=test123" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -c cookies.txt

# 2. Listar productos (sin autenticación)
curl -X GET "http://localhost:8000/productos"

# 3. Ranking desde caché
curl -X GET "http://localhost:8000/productos/ranking"
```

---

## 🐛 Solución de Problemas

| Problema | Solución |
|----------|----------|
| `ModuleNotFoundError: No module named 'redis'` | `pip install redis` |
| `ModuleNotFoundError: No module named 'sqlmodel'` | `pip install sqlmodel` |
| `No such column: producto.descripcion` | Elimina `database.db` y reinicia el servidor |
| `argon2: no backends available` | `pip install argon2-cffi` |
| `Connection refused (Redis)` | Verifica que Redis esté corriendo o usa Upstash |

---

## 📊 Endpoints Disponibles

### Páginas HTML (Renderizado)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Página principal |
| GET | `/register` | Formulario de registro |
| GET | `/login` | Formulario de login |
| GET | `/logout` | Cerrar sesión |
| POST | `/register` | Registrar usuario |
| POST | `/login` | Iniciar sesión |
| POST | `/create` | Crear producto |
| POST | `/delete/{id}` | Eliminar producto |

### API REST (JSON)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/productos` | Listar todos los productos |
| GET | `/productos/{id}` | Obtener producto por ID |
| DELETE | `/productos/{id}` | Eliminar producto (API) |
| GET | `/productos/ranking` | Ranking con caché Redis |

---

## 📝 Notas de Desarrollo

- El proyecto usa **SQLite** por defecto (fácil para desarrollo)
- Para producción, considera cambiar a **PostgreSQL**
- Redis en **Upstash** está configurado pero es opcional
- Las imágenes se guardan en `static/uploads/`

---

## 👨‍💻 Autor

Proyecto desarrollado como proyecto final de programación para Internet con FastAPI.

---

## 📧 Soporte

Para reportar bugs o sugerencias, contacta al equipo de desarrollo.

---

## Pagina web

https://fastapi-6fr5.onrender.com/

### Imagenes

<p align="center">
    <img width="1914" height="941" alt="1" src="https://github.com/user-attachments/assets/08a7c13c-bc15-4d0b-aeab-bf6140d2d726" />
</p>


<p align="center">
    <img width="1919" height="945" alt="2" src="https://github.com/user-attachments/assets/fc682547-900e-4ea3-a14f-9c00b9d9d7bc" />
</p>

<p align="center">
    <img width="1919" height="949" alt="3" src="https://github.com/user-attachments/assets/9b2a2709-5410-43d9-8e7d-c0cc99e6cc5d" />
</p>


---

**Última actualización**: 3 de marzo de 2026
