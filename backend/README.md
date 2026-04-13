# REPD Risk API (Jalisco)

Backend en FastAPI que consume la API pública del Registro Estatal de Personas Desaparecidas (REPD) de Jalisco, aplica filtros de negocio (edad ±3 años, sexo, exclusión de personas localizadas) y expone un indicador de casos similares y nivel de riesgo.

## Estructura del proyecto

El paquete Python se llama `app` y vive **dentro** de la carpeta `backend`. Uvicorn debe ejecutarse con el directorio de trabajo en `backend` para que `import app.main` funcione.

```
app-desaparecidos/
  backend/
    requirements.txt
    README.md
    app/
      __init__.py
      main.py
      core/
        __init__.py
        config.py
        logging.py
      routes/
        __init__.py
        risk.py
      services/
        __init__.py
        repd_client.py
      domain/
        __init__.py
        filters.py
        scoring.py
      models/
        __init__.py
        schemas.py
```

- `app/core`: configuración y logging
- `app/services`: cliente HTTP REPD
- `app/domain`: filtros y scoring
- `app/models`: esquemas Pydantic
- `app/routes`: endpoints

## Requisitos

- Python 3.10+

## Instalación

Desde la carpeta `backend`:

```bash
cd backend
pip install -r requirements.txt
```

## Ejecución

**Importante:** abre la terminal en la carpeta `backend` (la que contiene el directorio `app/`). Si corres `uvicorn` desde la raíz del repositorio, verás: `Could not import module "app.main"`.

```bash
cd backend
uvicorn app.main:app --reload
```

En PowerShell:

```powershell
Set-Location backend
uvicorn app.main:app --reload
```

Alternativa sin cambiar de carpeta (desde la raíz del repo):

```bash
uvicorn app.main:app --reload --app-dir backend
```

La documentación interactiva estará en `http://127.0.0.1:8000/docs`.

Si ves `Tiempo de espera agotado al consultar REPD`, la API tardó más que el timeout por petición. Por defecto son 30 segundos; puedes subirlo sin tocar código:

```powershell
$env:REPD_HTTP_TIMEOUT="60"
uvicorn app.main:app --reload
```

## Ejemplo

```bash
curl "http://127.0.0.1:8000/risk?municipio=guadalajara&edad=18&sexo=HOMBRE"
```
