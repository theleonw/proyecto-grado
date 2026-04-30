from flask import Blueprint, render_template, session

from app.auth.routes import role_required
from app.extensions import db
from app.models import Pago


deportistas_bp = Blueprint("deportistas", __name__)


@deportistas_bp.route("/", methods=["GET"])
@role_required("USUARIO", "ADMIN", "ENTRENADOR")
def deportistas_dashboard():
    user_id = session.get("user_id")
    pagos_usuario = db.session.query(Pago).filter(Pago.registrado_por == user_id).all() if user_id else []

    estado_plan = "ACTIVO"
    if pagos_usuario and all(p.estado != "PAGADO" for p in pagos_usuario):
        estado_plan = "INACTIVO"

    progreso = [62, 67, 71, 76, 81, 84]
    atributos = {
        "Velocidad": 78,
        "Resistencia": 73,
        "Fuerza": 69,
        "Tecnica": 82,
    }

    tips_ia = []
    if atributos["Resistencia"] < 75:
        tips_ia.append("Haz 2 sesiones semanales de HIIT (15-20 min) para subir tu resistencia.")
    if atributos["Fuerza"] < 72:
        tips_ia.append("Incluye sentadillas, zancadas y planchas en bloques de 3x12 repeticiones.")
    if atributos["Tecnica"] >= 80:
        tips_ia.append("Tu tecnica es alta: practica pases a un toque para mejorar toma de decisiones.")

    return render_template(
        "usuario/dashboard.html",
        estado_plan=estado_plan,
        progreso=progreso,
        atributos=atributos,
        tips_ia=tips_ia,
        ranking_posicion=7,
        proximo_entrenamiento={
            "fecha": "Sabado 10:00 AM",
            "hora": "10:00 - 12:00",
            "sede": "Cancha Principal Forjadores",
        },
    )
