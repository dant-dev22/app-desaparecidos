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

Flujo habitual: código en disco → entorno virtual → **systemd** (autoarranque y `Restart=always`) → **Nginx** reverse proxy solo a `127.0.0.1` → **HTTPS** con Certbot → firewall **solo 80/443** (no expongas el puerto interno de Uvicorn).

Ajusta en todo el siguiente apartado estas variables según tu máquina y dominio (ejemplo: dominio **`estoyasalvo.com`**, ruta **`/srv/estoyasalvo/app-desaparecidos/backend`**, puerto interno **`8002`**, servicio **`estoyasalvo-api`**).

### 1. Subir el código (GitHub → VPS)

En GitHub: crea el repositorio, haz `git push` desde tu PC. En el VPS:

```bash
sudo apt update && sudo apt install -y python3 python3-venv python3-pip nginx git
sudo mkdir -p /srv/estoyasalvo && sudo chown $USER:$USER /srv/estoyasalvo
cd /srv/estoyasalvo
git clone <URL-de-tu-repositorio.git> app-desaparecidos
cd app-desaparecidos/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
deactivate
```

Prueba manual (luego Ctrl+C):

```bash
cd /srv/estoyasalvo/app-desaparecidos/backend
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8002
```

En otra sesión: `curl -sSf http://127.0.0.1:8002/docs > /dev/null && echo OK`. En producción no uses `--reload`.

### 2. DNS

En el panel de tu dominio (p. ej. `estoyasalvo.com`): registro **A** `@` → IP pública del VPS; opcional **A** o **CNAME** para `www`. Espera a que resuelva antes de Certbot.

### 3. Variables de entorno (opcional)

```bash
sudo install -m 640 /dev/stdin /etc/estoyasalvo-api.env <<'EOF'
REPD_HTTP_TIMEOUT=60
EOF
sudo chown root:root /etc/estoyasalvo-api.env
```

Si no usas archivo, quita la línea `EnvironmentFile` del servicio siguiente.

### 4. Servicio systemd

Archivo `/etc/systemd/system/estoyasalvo-api.service`:

```ini
[Unit]
Description=REPD Risk API (Uvicorn)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/srv/estoyasalvo/app-desaparecidos/backend
Environment=PATH=/srv/estoyasalvo/app-desaparecidos/backend/.venv/bin
EnvironmentFile=-/etc/estoyasalvo-api.env
ExecStart=/srv/estoyasalvo/app-desaparecidos/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8002
Restart=always
RestartSec=3
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

Carga y arranque:

```bash
sudo chown -R www-data:www-data /srv/estoyasalvo/app-desaparecidos/backend
sudo systemctl daemon-reload
sudo systemctl enable --now estoyasalvo-api
sudo systemctl status estoyasalvo-api
```

Si haces `git pull` con tu usuario y no quieres `chown` masivo, pon `User=tu_usuario` en el unit. Tras actualizar código: `sudo systemctl restart estoyasalvo-api`. Logs: `journalctl -u estoyasalvo-api -f`.

### 5. Nginx (sitio propio por dominio)

Archivo `/etc/nginx/sites-available/estoyasalvo.com`:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name estoyasalvo.com www.estoyasalvo.com;

    access_log /var/log/nginx/estoyasalvo_access.log;
    error_log  /var/log/nginx/estoyasalvo_error.log;

    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Con `server_name` dedicado y `location /`, no hace falta `--root-path` en Uvicorn: `https://estoyasalvo.com/docs`.

```bash
sudo ln -sf /etc/nginx/sites-available/estoyasalvo.com /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 6. HTTPS y firewall

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d estoyasalvo.com -d www.estoyasalvo.com
```

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

No abras en el firewall el puerto interno (**8002**): debe escuchar solo en **127.0.0.1**.

### Otra opción breve

Si la integras detrás del **`server`** de otro dominio ya existente como **subruta**, usa un `location /algo/` con `proxy_pass http://127.0.0.1:PUERTO/;` y en `ExecStart` añade `--root-path /algo` para que `/docs` sea coherente con la URL pública.
