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

## Despliegue en un VPS (producción continua)

Para que la API quede siempre disponible **después de reinicios del servidor** y se **levante sola** al arrancar, lo habitual en Linux es combinar:

1. Un **servicio systemd** (`Restart=always`, arranque en `multi-user.target`).
2. Opcionalmente **Nginx** delante como proxy inverso (TLS, dominio, mismo VPS que otras APIs).

No hace falta Docker para esto; basta con Python, un entorno virtual y systemd.

### 1. Preparar el servidor

```bash
sudo apt update && sudo apt install -y python3 python3-venv python3-pip nginx
# git si clonas el repo en el VPS
```

Clona o copia el proyecto y entra en `backend` (donde está el paquete `app/`).

```bash
cd /ruta/a/app-desaparecidos/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

Elige un **puerto interno** que no choque con tus otras APIs (por ejemplo `8001`, `8010`, etc.). El ejemplo usa `8001`.

### 2. Probar manualmente (sin systemd)

```bash
cd /ruta/a/app-desaparecidos/backend
source .venv/bin/activate
export REPD_HTTP_TIMEOUT=60   # opcional
uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Comprueba con `curl http://127.0.0.1:8001/docs` desde el VPS. No uses `--reload` en producción.

### 3. Variables de entorno (opcional)

Si quieres persistir `REPD_HTTP_TIMEOUT` u otras variables sin ponerlas en el unit de systemd:

```bash
sudo install -m 640 /dev/stdin /etc/repd-risk-api.env <<'EOF'
REPD_HTTP_TIMEOUT=60
EOF
sudo chown root:root /etc/repd-risk-api.env
```

(Si no usas archivo de entorno, omite `EnvironmentFile` en el servicio de abajo.)

### 4. Servicio systemd (inicio automático + reinicio si falla)

Crea `/etc/systemd/system/repd-risk-api.service`:

```ini
[Unit]
Description=REPD Risk API (FastAPI/Uvicorn)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/ruta/a/app-desaparecidos/backend
Environment=PATH=/ruta/a/app-desaparecidos/backend/.venv/bin
EnvironmentFile=-/etc/repd-risk-api.env
ExecStart=/ruta/a/app-desaparecidos/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001
Restart=always
RestartSec=3

# Límites razonables; ajusta según RAM del VPS
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

Ajusta **`User`/`Group`** (por ejemplo tu usuario deploy) si no quieres `www-data`, y **`WorkingDirectory`**, **`ExecStart`** y **`PATH`** a la ruta real del proyecto.

Los permisos del código y del venv deben permitir lectura/ejecución al usuario del servicio:

```bash
sudo chown -R www-data:www-data /ruta/a/app-desaparecidos/backend
# o deja el repo bajo tu usuario y usa User=tuusuario en el unit
sudo systemctl daemon-reload
sudo systemctl enable --now repd-risk-api
sudo systemctl status repd-risk-api
```

Tras cada **actualización del código**:

```bash
sudo systemctl restart repd-risk-api
```

Los logs:

```bash
journalctl -u repd-risk-api -f
```

Con esto la API **arranca sola tras un reboot** y systemd la **vuelve a levantar** si el proceso muere.

### 5. Nginx en el mismo VPS que otras APIs

Si ya tienes Nginx sirviendo otras aplicaciones **no necesitas pegar todo tu `nginx.conf` aquí** para integrar esta API: basta un `location` (o `server` dedicado por subdominio) que haga proxy a `http://127.0.0.1:8001` (o el puerto que hayas elegido).

Ejemplo mínimo de fragmento dentro de tu `server { ... }` existente:

```nginx
location /repd-risk/ {
    proxy_pass http://127.0.0.1:8001/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Si publicas bajo un **subpath** como el anterior, añade en `ExecStart` el argumento `--root-path /repd-risk` para que `/docs` y OpenAPI sigan alineados con la URL pública.

Si prefieres un **subdominio** (`repd.midominio.com`), crea otro bloque `server` con `server_name` y `proxy_pass` al mismo upstream; así no compites por rutas con las otras dos APIs.

**¿Hace falta que compartas tu Nginx completo?** Solo si quieres ayuda muy concreta (conflictos de `server_name`, rutas, HTTPS, certbot, o varias `location` que se pisan). Para documentar el despliegue del backend, no es obligatorio: con saber **puerto interno**, **dominio/subruta deseada** y si usas HTTPS basta para escribir el bloque correcto.

### 6. Firewall

Si expones puerto 80/443 con Nginx, abre solo esos puertos al mundo; mantén la API solo en `127.0.0.1` como arriba. No abras el puerto de Uvicorn (`8001`) a Internet salvo que tengas un motivo muy claro.

### 7. Carga y robustez intermedia

Para más tráfico, en lugar de un solo proceso Uvicorn se puede usar **Gunicorn** con workers Uvicorn; eso ya es opcional y cambia la línea `ExecStart`. En muchos VPS pequeños, un único proceso Uvicorn tras Nginx es suficiente para empezar.

### 8. Dominio propio e independiente (ejemplo: `estoyasalvo.com`)

Si quieres publicar esta API **bajo otro dominio** y mantenerla **fuera del `server { }` de otras apps** (Torneo Aztlán, etc.), el flujo es: DNS → código en el VPS → `systemd` → **archivo de sitio Nginx propio** → Certbot. No tienes que tocar la configuración de los otros proyectos más que tener Nginx cargando todos los sitios (`include /etc/nginx/sites-enabled/*` es lo habitual).

**Convenciones en este ejemplo**

- Carpeta del repo en el VPS: `/srv/estoyasalvo/app-desaparecidos/backend` (cámbiala si prefieres otra).
- Puerto interno (solo localhost): **`8002`** para no pisar tus otros servicios (`3000`, `5000`, etc.).
- Unidad systemd: **`estoyasalvo-api.service`** (nombre claro si administras varios backends).

---

#### Paso 1 — DNS en tu proveedor

En el panel del dominio `estoyasalvo.com`:

- Registro **A**: nombre `@` (raíz del dominio) → **IP pública de tu VPS**.
- Opcional: **A** para `www` → misma IP, o **CNAME** `www` → `estoyasalvo.com`.

Espera a que resuelvan (propagación suele ser minutos, a veces más). Comprueba desde tu PC: `ping estoyasalvo.com` (o herramienta online de DNS).

---

#### Paso 2 — Directorio en el VPS y código

Por SSH como usuario con `sudo`:

```bash
sudo mkdir -p /srv/estoyasalvo
sudo chown $USER:$USER /srv/estoyasalvo
cd /srv/estoyasalvo
```

Sube el código ( **`git clone`**, `rsync`, SCP, etc. ). Lo importante es que la carpeta que contiene el paquete Python `app/` quede así:

`/srv/estoyasalvo/app-desaparecidos/backend/app/...`

```bash
cd /srv/estoyasalvo/app-desaparecidos/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
deactivate
```

Prueba rápida:

```bash
cd /srv/estoyasalvo/app-desaparecidos/backend
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8002
```

En **otra** terminal SSH: `curl -sSf http://127.0.0.1:8002/docs >/dev/null && echo OK`. Luego Ctrl+C para parar uvicorn manual.

---

#### Paso 3 — Variables de entorno (opcional)

```bash
sudo install -m 640 /dev/stdin /etc/estoyasalvo-api.env <<'EOF'
REPD_HTTP_TIMEOUT=60
EOF
sudo chown root:root /etc/estoyasalvo-api.env
```

---

#### Paso 4 — Servicio systemd (arranque automático)

`/etc/systemd/system/estoyasalvo-api.service`:

```ini
[Unit]
Description=Estoy a salvo / REPD Risk API (Uvicorn)
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

Permisos y arranque:

```bash
sudo chown -R www-data:www-data /srv/estoyasalvo/app-desaparecidos/backend
sudo systemctl daemon-reload
sudo systemctl enable --now estoyasalvo-api
sudo systemctl status estoyasalvo-api
```

Si despliegas con `git pull` como usuario normal y no quieres que todo el árbol sea de `www-data`, usa **`User=`** ese usuario en el unit y omite el `chown` masivo.

Con **este** diseño (`server_name` propio apuntando a `/` en ese host), **no necesitas `--root-path`**: Swagger queda en `https://estoyasalvo.com/docs`.

Para actualizar código después de un `git pull`:

```bash
sudo systemctl restart estoyasalvo-api
```

---

#### Paso 5 — Sitio Nginx dedicado (archivo nuevo)

Archivo **`/etc/nginx/sites-available/estoyasalvo.com`**:

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

Activar y probar sintaxis:

```bash
sudo ln -sf /etc/nginx/sites-available/estoyasalvo.com /etc/nginx/sites-enabled/estoyasalvo.com
sudo nginx -t && sudo systemctl reload nginx
```

Comprueba en el VPS: `curl -H "Host: estoyasalvo.com" http://127.0.0.1/docs -I` — deberías ver respuesta desde tu app (via proxy). Cuando DNS ya apunte bien, también: `curl -I http://estoyasalvo.com`.

---

#### Paso 6 — HTTPS con Let’s Encrypt (Certbot)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d estoyasalvo.com -d www.estoyasalvo.com
```

Certbot suele crear el bloque `listen 443 ssl`, certificados bajo `/etc/letsencrypt/live/estoyasalvo.com/` y opcionalmente redirigir HTTP→HTTPS.

Renovaciones: `sudo certbot renew --dry-run` (el timer de systemd lo suele hacer solo).

Si quieres que **solo** sirva la variante canonical (todo a `https://estoyasalvo.com` sin `www`), puedes añadir después un `return 301` en el bloque HTTPS de `www` — eso ya es opcional de SEO/marketing.

---

#### Paso 7 — Firewall

Con **UFW** típico:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'   # 80 + 443
sudo ufw enable
sudo ufw status
```

No abras el **`8002`** (o el puerto que elijas para Uvicorn) hacia Internet: solo debe escuchar **`127.0.0.1`**.

---

#### Resumen de independencia respecto al resto del VPS

| Pieza              | Separación |
|--------------------|------------|
| Código             | Carpeta `/srv/estoyasalvo/…` solo de este proyecto |
| Proceso            | Servicio systemd `estoyasalvo-api` |
| Nginx              | Archivo **`sites-available/estoyasalvo.com`**, otro dominio (`server_name`) |
| Logs               | `estoyasalvo_*.log` y `journalctl -u estoyasalvo-api` |
| Certificados       | Let’s Encrypt asociados a `estoyasalvo.com` |

Tus otros `server { }` para `torneoaztlan.com` u otras APIs **no hace falta tocarlos** salvo conflicto muy raro (mismo `server_name` dos veces, etc.), que aquí no aplica porque el nombre de host es otro dominio.

---

#### Troubleshooting rápido

| Síntoma | Qué revisar |
|---------|--------------|
| 502 Bad Gateway | `sudo systemctl status estoyasalvo-api`; `journalctl -u estoyasalvo-api -n 50`; que el puerto en Nginx coincide con `--port` |
| Timeout al REPD | `REPD_HTTP_TIMEOUT` mayor en `/etc/estoyasalvo-api.env` + `restart` |
| Certbot falla | DNS del dominio aún no apunta a esta IP; firewall 80/443; `nginx -t` |
