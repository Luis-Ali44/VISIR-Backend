    ## Arranque local

### Requisitos
- Python 3.12

- uv — instalar con:
```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
- Docker Desktop 


### Verificamos que esten instralados
- python --version
- uv --version
- docker --version

### Opcion A: Supabase

Llenas el .env segun el .env.example














### Pasos

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd Visir-Api

# 2. Copiar variables de entorno
cp .env.example .env
# Llenar las credenciales de Supabase en .env




# 3. Levantar el stack
make dev
```

El servidor queda disponible en:
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

### Migraciones

Aplicar los archivos de `migrations/` en orden desde el SQL Editor de Supabase:
### Si trabjas con supabase en lugar postgres local tienes que que comentar el servicio en `docker-compose`


### Solución a problemas comunes:
 Puerto 8000 ocupado: Lo mas seguro es cambiar de puerto por lo tanto tendrias que entrar a docker compose y cambiar el puerto de api por -"8001:8000" o por el puerto que no estes ocupando

 

