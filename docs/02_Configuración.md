# Configuración General

## Variables de entorno

Las variables que usamos para mandejar configuracion sensible (url, credenciales) estan guardadas en el archivo .env y se cargan mediante pydantic settings 

## Configuracion de dependencias

Este es mediante uv y lo definimos en el archivo pyproject.toml

se usa para poder mantener:
- versiones controladas 
- instalar dependencias de manera facil y consistentes entre diferentes entornos
- centraliza la configuracion del proyecto

## Ruff 
 Se usa como herramienta linting y formateo para tener consistencia y calidad en nuestro codigo.
 