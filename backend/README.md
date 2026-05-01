# REPD Risk API (Jalisco)

Backend en **FastAPI** que consume la API pública del Registro Estatal de Personas Desaparecidas (REPD) de Jalisco, aplica filtros de negocio (edad ±3 años, sexo, exclusión de personas localizadas) y expone un indicador de casos similares y nivel de riesgo.

## Estructura del proyecto

El paquete Python se llama `app` y vive dentro de **`backend/`**. Los comandos (`uvicorn`, `pip`) deben ejecutarse **con carpeta activa `backend`**, donde está el directorio `app/`, para que funcionen imports como `app.main`.

```
app-desaparecidos/
  backend/
    requirements.txt
    README.md
    .env.example
    app/
      __init__.py
      main.py
      core/          → config, logging
      routes/        → routers (p. ej. risk)
      services/      → cliente HTTP REPD
      domain/        → filtros, scoring, zonas
      models/        → esquemas Pydantic
```

En `backend/` también pueden estar JSON de datos o muestras (municipios, CP, respuestas de prueba).

## Despliegue local

Requisitos: **Python 3.10+**.

```bash
cd backend
python -m venv .venv
```

En Linux/macOS: `source .venv/bin/activate`. En Windows PowerShell: `.\.venv\Scripts\Activate.ps1`.

```bash
pip install -U pip
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Desde la raíz del repo: `uvicorn app.main:app --reload --app-dir backend`.

Docs: `http://127.0.0.1:8000/docs`. Opcional: `export REPD_HTTP_TIMEOUT=60` (Linux/macOS) o `$env:REPD_HTTP_TIMEOUT="60"` antes de uvicorn en PowerShell.

Variables opcionales: `.env.example` (la app solo lee el entorno del proceso).

## VPS — actualizar el repo después de un cambio

Con la API en **`127.0.0.1`** y **`nohup`** (ej. puerto **48173** igual que tu `proxy_pass` en Nginx; cámbialo si usas otro). Por SSH:

```bash
pgrep -af "uvicorn app.main:app"   # anota el PID
kill <PID>

cd ~/app-desaparecidos/backend       # tu ruta real donde clonaste
git pull
source .venv/bin/activate
pip install -r requirements.txt    # omite esta línea si requirements no cambió

nohup uvicorn app.main:app --host 127.0.0.1 --port 48173 > ~/repd-api.log 2>&1 </dev/null &
echo $!
exit
```

Comprueba: `curl -sf http://127.0.0.1:48173/docs | head -n 1` o tu `https://tudominio.com/docs`.
