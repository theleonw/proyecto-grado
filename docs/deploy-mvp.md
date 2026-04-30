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

## 3. Deploy en Render (rapido)
1. Sube repo a GitHub.
2. En Render: **New Web Service** -> conecta repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn "app:create_app()"`
5. Agrega variables de entorno del paso 2.

## 4. Probar pago Stripe (modo test)
- Inicia sesion con usuario normal.
- Entra a `/portal/pago`.
- Elige plan y paga.
- Usa tarjeta de prueba Stripe: `4242 4242 4242 4242`, fecha futura, CVC cualquiera.
- Al volver a `/portal/pago/exito`, el sistema activa `usuario.activo=True` y `status='activo'`.

## 5. Verificar resultado
- Reingresa a la plataforma con el mismo usuario.
- Debes ver dashboard y progreso desbloqueado.
