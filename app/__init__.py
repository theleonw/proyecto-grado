import os
from datetime import datetime

from flask import Flask
from sqlalchemy import inspect, text
from werkzeug.security import generate_password_hash

from app.extensions import db


def _es_rol_con_plan_activo(email: str) -> bool:
    email_norm = (email or "").strip().lower()
    return email_norm == "admin@forjadores.com" or "entrenador" in email_norm or email_norm.startswith("coach")


def _load_dotenv(project_root: str) -> None:
    env_path = os.path.join(project_root, ".env")
    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            clean_key = key.strip().lstrip("\ufeff")
            os.environ.setdefault(clean_key, value.strip().strip('"').strip("'"))


def _bootstrap_data() -> None:
    db.create_all()
    inspector = inspect(db.engine)
    if "usuarios" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("usuarios")}
        if "status" not in columns:
            db.session.execute(text("ALTER TABLE usuarios ADD COLUMN status VARCHAR(30) NOT NULL DEFAULT 'activo'"))
            db.session.commit()

    from app.models import Usuario

    usuarios_demo = [
        ("Admin", "Sistema", os.getenv("DEFAULT_ADMIN_EMAIL", "admin@forjadores.com"), os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin123*")),
        ("Laura", "Entrenadora", "entrenador@forjadores.com", "Coach123*"),
        ("Carlos", "Jugador", "usuario@forjadores.com", "User123*"),
    ]

    for nombres, apellidos, email, password in usuarios_demo:
        email_norm = email.strip().lower()
        existe = Usuario.query.filter_by(email=email_norm).first()
        if not existe:
            db.session.add(
                Usuario(
                    nombres=nombres,
                    apellidos=apellidos,
                    email=email_norm,
                    password_hash=generate_password_hash(password),
                    activo=_es_rol_con_plan_activo(email_norm),
                    status="activo" if _es_rol_con_plan_activo(email_norm) else "pendiente_pago",
                )
            )

    db.session.commit()


def create_app(config_object: str | None = None) -> Flask:
    app = Flask(__name__)

    project_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    _load_dotenv(project_root)

    sqlite_path = os.path.join(project_root, "forjadores.db")
    sqlite_url = f"sqlite:///{os.path.abspath(sqlite_path)}"

    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "forjadores-secret-key"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", sqlite_url),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        GOOGLE_CLIENT_ID=os.getenv("GOOGLE_CLIENT_ID", ""),
        GOOGLE_CLIENT_SECRET=os.getenv("GOOGLE_CLIENT_SECRET", ""),
        RECAPTCHA_SITE_KEY=os.getenv("RECAPTCHA_SITE_KEY", ""),
        RECAPTCHA_SECRET_KEY=os.getenv("RECAPTCHA_SECRET_KEY", ""),
        STRIPE_SECRET_KEY=os.getenv("STRIPE_SECRET_KEY", ""),
        STRIPE_PUBLISHABLE_KEY=os.getenv("STRIPE_PUBLISHABLE_KEY", ""),
    )

    if config_object:
        app.config.from_object(config_object)

    db.init_app(app)

    from app.pagina.routes import pagina_bp
    from app.auth.routes import auth_bp
    from app.admin.routes import admin_bp
    from app.deportistas.routes import deportistas_bp
    from app.entrenadores.routes import entrenadores_bp
    from app.pagos.routes import pagos_bp
    from app.portal.routes import portal_bp

    app.register_blueprint(pagina_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(deportistas_bp, url_prefix="/deportistas")
    app.register_blueprint(entrenadores_bp, url_prefix="/entrenadores")
    app.register_blueprint(pagos_bp, url_prefix="/pagos")
    app.register_blueprint(portal_bp, url_prefix="/portal")

    with app.app_context():
        _bootstrap_data()

    @app.get("/health")
    def healthcheck():
        return {
            "service": "forjadores-del-futuro",
            "status": "ok",
            "time": datetime.utcnow().isoformat() + "Z",
            "database": app.config["SQLALCHEMY_DATABASE_URI"],
            "google_configured": bool(app.config.get("GOOGLE_CLIENT_ID") and app.config.get("GOOGLE_CLIENT_SECRET")),
        }, 200

    return app
