# Estoy a salvo / REPD Jalisco — API de riesgo

Monorepositorio centrado en el backend **FastAPI** que consulta el REPD Jalisco público.

- **Backend:** carpeta [`backend`](backend/) (`app/`, instalación y despliegue en [`backend/README.md`](backend/README.md)).

### GitHub → VPS

1. Crea el repositorio en GitHub (vacío o con README según prefieras).
2. Desde esta carpeta (`app-desaparecidos`): `git add .`, commit, `git remote add origin …`, `git push -u origin main` (o `master`).
3. En el VPS: `git clone <url-del-repo.git>` en la ruta deseada (p. ej. `/srv/estoyasalvo/app-desaparecidos`).
4. `cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` y continúa con **systemd** y **Nginx** en [`backend/README.md`](backend/README.md).

No subas `.env` con secretos: usa el ejemplo [`backend/.env.example`](backend/.env.example) y variables en el servidor (archivo systemd o `/etc/*.env`).
