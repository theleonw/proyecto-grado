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

    return render_template(
        "usuario/dashboard.html",
        estado_plan=estado_plan,
        ranking_posicion=7,
        proximo_entrenamiento={
            "fecha": "Sabado 10:00 AM",
            "hora": "10:00 - 12:00",
            "sede": "Cancha Principal Forjadores",
        },
    )
