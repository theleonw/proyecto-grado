# Deploy MVP (Render) + Stripe Sandbox

## 1. Preparar proyecto
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Variables de entorno
Configura en tu hosting:
- `SECRET_KEY`
- `DATABASE_URL` (si no usas SQLite)
- `STRIPE_SECRET_KEY` (test key: `sk_test_...`)
- `STRIPE_PUBLISHABLE_KEY` (test key: `pk_test_...`)
- `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET` (o aliases `GOOGLE_OAUTH_CLIENT_ID` / `GOOGLE_OAUTH_CLIENT_SECRET`)
- `GOOGLE_REDIRECT_URI` (opcional, recomendado en producción)

## 3. Deploy en Render (rapido)
1. Sube repo a GitHub.
2. En Render: **New Web Service** -> conecta repo.
3. Build command: `pip install -r requirements.txt && pip install gunicorn==23.0.0`
4. Start command: `gunicorn "app:create_app()"` (no `app:app`, este proyecto usa factory)
5. Agrega variables de entorno del paso 2.
6. Si ya tenias un deploy previo, borra el Start Command viejo `gunicorn app:app` y redeploya.

## 4. Probar pago Stripe (modo test)
- Opcion A: Inicia sesion con usuario normal.
- Opcion B: Registra un usuario nuevo en `/auth/registro` (se guarda en DB y redirige a pago).
- Entra a `/portal/pago`.
- Elige plan y paga.
- Usa tarjeta de prueba Stripe: `4242 4242 4242 4242`, fecha futura, CVC cualquiera.
- Al volver a `/portal/pago/exito`, el sistema activa `usuario.activo=True` y `status='activo'`.

## 5. Verificar resultado
- Reingresa a la plataforma con el mismo usuario.
- Debes ver dashboard y progreso desbloqueado.

## 6. Usuario demo para pruebas
- Admin: `admin@forjadores.com` / `Admin123*`
- Entrenador: `entrenador@forjadores.com` / `Coach123*`
- Usuario: `usuario@forjadores.com` / `User123*`
- Usuario Google test: `google.test@forjadores.com` / `Google123*`

Puedes cambiar estos valores con variables `DEFAULT_*` en `.env`.
