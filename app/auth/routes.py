import os
from functools import wraps

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import Usuario

try:
    from authlib.integrations.flask_client import OAuth
except Exception:
    OAuth = None


auth_bp = Blueprint("auth", __name__)


def _inferir_rol(email: str) -> str:
    email = (email or "").lower()
    if email == "admin@forjadores.com" or email.startswith("admin"):
        return "ADMIN"
    if "entrenador" in email or email.startswith("coach"):
        return "ENTRENADOR"
    return "USUARIO"


def _redirect_por_rol(rol: str):
    if rol == "ADMIN":
        return redirect(url_for("admin.admin_dashboard"))
    if rol == "ENTRENADOR":
        return redirect(url_for("entrenadores.entrenadores_dashboard"))
    return redirect(url_for("deportistas.deportistas_dashboard"))


def role_required(*roles_permitidos):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if not session.get("user_id"):
                flash("Debes iniciar sesion para continuar.", "error")
                return redirect(url_for("auth.login"))
            rol = session.get("rol", "")
            if rol not in roles_permitidos:
                flash("No tienes permisos para acceder a este modulo.", "error")
                return redirect(url_for("pagina.inicio"))
            return view_func(*args, **kwargs)

        return wrapper

    return decorator


def payment_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            flash("Debes iniciar sesion para continuar.", "error")
            return redirect(url_for("auth.login"))

        usuario = Usuario.query.get(user_id)
        if not usuario or not usuario.activo:
            flash("Tu cuenta no esta activa.", "error")
            return redirect(url_for("auth.login"))

        if usuario.status == "pendiente_pago":
            flash("Completa tu pago para desbloquear el portal.", "error")
            return redirect(url_for("portal.pago"))

        return view_func(*args, **kwargs)

    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Autenticacion requerida"}), 401
        usuario = Usuario.query.get(user_id)
        if not usuario or not usuario.activo:
            return jsonify({"error": "Usuario no valido"}), 403
        rol = session.get("rol") or _inferir_rol(usuario.email)
        if rol != "ADMIN":
            return jsonify({"error": "Solo administracion puede gestionar pagos"}), 403
        return view_func(*args, **kwargs)

    return wrapper


def _debe_tener_plan_inactivo(rol: str) -> bool:
    return rol not in {"ADMIN", "ENTRENADOR"}


def _oauth_client():
    if OAuth is None:
        return None, None

    oauth = current_app.extensions.get("google_oauth")
    if oauth is None:
        oauth = OAuth(current_app)
        current_app.extensions["google_oauth"] = oauth

    client_id = current_app.config.get("GOOGLE_CLIENT_ID")
    client_secret = current_app.config.get("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        return oauth, None

    google = oauth.create_client("google")
    if google is None:
        oauth.register(
            name="google",
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_id=client_id,
            client_secret=client_secret,
            client_kwargs={"scope": "openid email profile"},
        )
        google = oauth.create_client("google")

    return oauth, google


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        show_blocked = request.args.get("blocked") == "1"
        return render_template("auth/login.html", show_blocked_modal=show_blocked)

    payload = request.get_json(silent=True)
    if payload is None:
        payload = request.form.to_dict()

    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not email or not password:
        if request.is_json:
            return jsonify({"error": "Email y password son obligatorios"}), 400
        flash("Email y contrasena son obligatorios", "error")
        return redirect(url_for("auth.login"))

    try:
        usuario = Usuario.query.filter_by(email=email).first()
    except SQLAlchemyError:
        if request.is_json:
            return jsonify({"error": "No hay conexion con base de datos"}), 503
        flash("No hay conexion con la base de datos. Verifica configuracion local.", "error")
        return redirect(url_for("auth.login"))

    if not usuario or not check_password_hash(usuario.password_hash, password):
        if request.is_json:
            return jsonify({"error": "Credenciales invalidas"}), 401
        flash("Credenciales invalidas", "error")
        return redirect(url_for("auth.login"))

    rol = _inferir_rol(usuario.email)

    if _debe_tener_plan_inactivo(rol) and (not usuario.activo or usuario.status != "activo"):
        flash("Tu plan esta inactivo. Completa el pago para entrar al portal.", "error")
        return redirect(url_for("portal.pago"))

    session["user_id"] = usuario.id
    session["email"] = usuario.email
    session["nombre"] = f"{usuario.nombres} {usuario.apellidos}"
    session["rol"] = rol

    if request.is_json:
        return jsonify({"message": "Login exitoso", "rol": rol}), 200
    flash("Bienvenido al sistema", "success")
    return _redirect_por_rol(rol)


@auth_bp.get("/google")
def google_login():
    _, google = _oauth_client()
    if google is None:
        flash("Google OAuth no configurado. Define GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET.", "error")
        return redirect(url_for("auth.login"))
    redirect_uri = current_app.config.get("GOOGLE_REDIRECT_URI") or url_for("auth.google_callback", _external=True)
    return google.authorize_redirect(redirect_uri)


@auth_bp.get("/google/callback")
def google_callback():
    _, google = _oauth_client()
    if google is None:
        flash("Google OAuth no disponible.", "error")
        return redirect(url_for("auth.login"))

    try:
        token = google.authorize_access_token()
    except Exception:
        flash("No se pudo completar autenticacion con Google. Revisa credenciales y redirect URI.", "error")
        return redirect(url_for("auth.login"))
    userinfo = token.get("userinfo")
    if not userinfo:
        userinfo = google.userinfo()

    email = (userinfo.get("email") or "").lower().strip()
    if not email:
        flash("No se obtuvo email desde Google.", "error")
        return redirect(url_for("auth.login"))

    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario:
        rol_nuevo = _inferir_rol(email)
        usuario = Usuario(
            nombres=userinfo.get("given_name") or "Usuario",
            apellidos=userinfo.get("family_name") or "Google",
            email=email,
            password_hash=generate_password_hash(os.urandom(24).hex()),
            activo=not _debe_tener_plan_inactivo(rol_nuevo),
            status="pendiente_pago" if _debe_tener_plan_inactivo(rol_nuevo) else "activo",
        )
        from app.extensions import db
        db.session.add(usuario)
        db.session.commit()

    rol = _inferir_rol(usuario.email)

    if _debe_tener_plan_inactivo(rol) and (not usuario.activo or usuario.status != "activo"):
        flash("Tu plan esta inactivo. Completa el pago para entrar al portal.", "error")
        return redirect(url_for("portal.pago"))

    session["user_id"] = usuario.id
    session["email"] = usuario.email
    session["nombre"] = f"{usuario.nombres} {usuario.apellidos}"
    session["rol"] = rol
    flash("Acceso con Google exitoso.", "success")
    return _redirect_por_rol(rol)


@auth_bp.route("/logout", methods=["GET"])
def logout():
    session.clear()
    flash("Sesion cerrada correctamente", "success")
    return redirect(url_for("pagina.inicio"))
