from datetime import date, timedelta

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.extensions import db
from app.models import Pago, Usuario


portal_bp = Blueprint("portal", __name__)


PLANES = {
    "mensual": {"nombre": "Mensual", "precio": 80000, "dias": 30},
    "semestral": {"nombre": "Semestral", "precio": 420000, "dias": 180},
    "anual": {"nombre": "Anual", "precio": 780000, "dias": 365},
}


@portal_bp.get("/pago")
def pago():
    if not session.get("user_id"):
        flash("Inicia sesion para continuar con tu pago.", "error")
        return redirect(url_for("auth.login"))

    return render_template("portal/pago.html", planes=PLANES)


@portal_bp.post("/pago/confirmar")
def confirmar_pago():
    user_id = session.get("user_id")
    if not user_id:
        flash("Inicia sesion para continuar.", "error")
        return redirect(url_for("auth.login"))

    plan_key = request.form.get("plan", "mensual")
    plan = PLANES.get(plan_key, PLANES["mensual"])
    usuario = Usuario.query.get(user_id)
    if not usuario:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("auth.login"))

    usuario.status = "activo"
    usuario.activo = True
    db.session.add(
        Pago(
            estudiante_id=1,
            registrado_por=usuario.id,
            monto=plan["precio"],
            fecha_emision=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=plan["dias"]),
            estado="PAGADO",
        )
    )
    db.session.commit()

    flash(f"Pago {plan['nombre']} confirmado. Portal desbloqueado.", "success")
    return redirect(url_for("deportistas.deportistas_dashboard"))
