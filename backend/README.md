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
```

Arranque con recarga útil para desarrollo:

```bash
cd backend
uvicorn app.main:app --reload
```

Desde la raíz del repo (sin cambiar de carpeta):

```bash
uvicorn app.main:app --reload --app-dir backend
```

Documentación interactiva: `http://127.0.0.1:8000/docs`.

Opcional — subir tiempo máximo por petición al REPD (por defecto 30 s):

```bash
export REPD_HTTP_TIMEOUT=60   # Linux/macOS
```

```powershell
$env:REPD_HTTP_TIMEOUT="60"; uvicorn app.main:app --reload
```

Variables opcionales se documentan en `.env.example` (la app lee solo el entorno del proceso, no un archivo `.env` automático).

## Despliegue en un VPS

Flujo: clonar → Uvicorn en un **puerto poco habitual** y **solo en `127.0.0.1`** → **Nginx** expone puertos 80/443 al mundo y envía todo a ese puerto → puedes usar **HTTPS** con Certbot. Sigues usando **`nohup`** (o `tmux`) para que Uvicorn no muera al cerrar SSH; solo hace falta **un archivo** de sitio Nginx nuevo bajo `/etc/nginx/sites-available/`.

Si **`48173`** está ocupado, elige otro (`ss -tlnp`). Sustituye **`estoyasalvo.com`** (y opcional **`www.estoyasalvo.com`**) por tu dominio con DNS tipo **A** apuntando a la IP del VPS.

### 1. Clonar y dependencias

```bash
sudo apt update && sudo apt install -y python3 python3-venv python3-pip git nginx
cd ~
git clone <URL-del-repositorio.git> app-desaparecidos
cd app-desaparecidos/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip && pip install -r requirements.txt
```

### 2. Arrancar Uvicorn solo en localhost (detrás de Nginx)

Así nadie llega directo al puerto `48173` desde fuera del VPS — solo **Nginx** entra desde Internet.

```bash
cd ~/app-desaparecidos/backend
source .venv/bin/activate
export REPD_HTTP_TIMEOUT=60   # opcional
uvicorn app.main:app --host 127.0.0.1 --port 48173
```

En **otra** terminal SSH:

```bash
curl -sf "http://127.0.0.1:48173/docs" | head -n 1
```

Para cuando termines de probar en primer plano: **Ctrl+C**.

### 3. Nginx: proxy reverso en 80 / tu dominio

Crea **`/etc/nginx/sites-available/repd-api`** (nombre libre):

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name estoyasalvo.com www.estoyasalvo.com;

    access_log /var/log/nginx/repd_api_access.log;
    error_log  /var/log/nginx/repd_api_error.log;

    location / {
        proxy_pass http://127.0.0.1:48173;
        proxy_http_version 1.1;

        proxy_set_header Host               $host;
        proxy_set_header X-Real-IP          $remote_addr;
        proxy_set_header X-Forwarded-For    $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto  $scheme;
    }
}
```

Activa el sitio y recarga:

```bash
sudo ln -sf /etc/nginx/sites-available/repd-api /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

Lee la API públicamente ya por **HTTP**, por ejemplo `http://estoyasalvo.com/docs` (o `curl http://localhost/docs -H "Host: estoyasalvo.com"` desde el VPS).

Si usas **ufw**:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'   # 80 y 443
sudo ufw enable
```

**No** abras el **`48173`** al exterior: debe quedar cerrado porque Uvicorn no escucha en `0.0.0.0`.

### 4. HTTPS con Certbot

Cuando DNS resuelva bien hacia esta máquina:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d estoyasalvo.com -d www.estoyasalvo.com
```

Certbot ajusta tu bloque y activa HTTPS. Prueba después `https://estoyasalvo.com/docs`.

### 5. Que Uvicorn siga al cerrar SSH

Igual que antes, pero **siempre `--host 127.0.0.1`** (Nginx es la única puerta desde fuera):

```bash
cd ~/app-desaparecidos/backend
source .venv/bin/activate
nohup uvicorn app.main:app --host 127.0.0.1 --port 48173 > ~/repd-api.log 2>&1 &
echo $!
```

Logs: `tail -f ~/repd-api.log`. Parar: `kill <PID>`. Alternativa: **`tmux`** con el mismo comando `uvicorn` dentro (`tmux attach` para revisar).

### 6. Actualizar después de `git pull`

```bash
kill <PID>
cd ~/app-desaparecidos/backend && git pull
source .venv/bin/activate && pip install -r requirements.txt
nohup uvicorn app.main:app --host 127.0.0.1 --port 48173 > ~/repd-api.log 2>&1 &
```

Tras reiniciar el VPS hace falta volver a lanzar ese `uvicorn` (o pasar después a **systemd** para arranque automático).

### Prueba rápida sin Nginx (opcional)

Si solo quieres ver que responde por IP antes de crear el sitio, puedes lanzar **`--host 0.0.0.0 --port 48173`** temporalmente abriendo ese puerto en el firewall (`sudo ufw allow 48173/tcp`). En producción con dominio usa el esquema de arriba: **127.0.0.1 + Nginx**.
