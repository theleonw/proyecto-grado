from datetime import date, timedelta

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from app.extensions import db
from app.models import Estudiante, Pago, Usuario


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

    return render_template(
        "portal/pago.html",
        planes=PLANES,
        stripe_public_key=current_app.config.get("STRIPE_PUBLISHABLE_KEY", ""),
    )


@portal_bp.post("/pago/checkout")
def crear_checkout():
    try:
        import stripe
    except ModuleNotFoundError:
        flash("Dependencia Stripe no instalada. Ejecuta: pip install -r requirements.txt", "error")
        return redirect(url_for("portal.pago"))

    user_id = session.get("user_id")
    if not user_id:
        flash("Inicia sesion para continuar.", "error")
        return redirect(url_for("auth.login"))

    plan_key = request.form.get("plan", "mensual")
    plan = PLANES.get(plan_key)
    if not plan:
        flash("Plan no valido.", "error")
        return redirect(url_for("portal.pago"))

    stripe_secret = current_app.config.get("STRIPE_SECRET_KEY", "")
    if not stripe_secret:
        flash("Stripe no esta configurado. Define STRIPE_SECRET_KEY en entorno.", "error")
        return redirect(url_for("portal.pago"))

    stripe.api_key = stripe_secret

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": "cop",
                    "product_data": {"name": f"Plan {plan['nombre']} Forjadores"},
                    "unit_amount": int(plan["precio"]),
                },
                "quantity": 1,
            }
        ],
        metadata={"user_id": str(user_id), "plan": plan_key},
        success_url=url_for("portal.pago_exitoso", _external=True) + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=url_for("portal.pago", _external=True),
    )

    return redirect(checkout_session.url, code=303)


@portal_bp.get("/pago/exito")
def pago_exitoso():
    try:
        import stripe
    except ModuleNotFoundError:
        flash("Dependencia Stripe no instalada. Ejecuta: pip install -r requirements.txt", "error")
        return redirect(url_for("portal.pago"))

    user_id = session.get("user_id")
    if not user_id:
        flash("Inicia sesion para finalizar la activacion.", "error")
        return redirect(url_for("auth.login"))

    session_id = request.args.get("session_id", "")
    if not session_id:
        flash("No se pudo validar el pago.", "error")
        return redirect(url_for("portal.pago"))

    stripe_secret = current_app.config.get("STRIPE_SECRET_KEY", "")
    stripe.api_key = stripe_secret
    checkout_session = stripe.checkout.Session.retrieve(session_id)
    if checkout_session.payment_status != "paid":
        flash("El pago aun no aparece como aprobado.", "error")
        return redirect(url_for("portal.pago"))

    plan_key = checkout_session.metadata.get("plan", "mensual")
    plan = PLANES.get(plan_key, PLANES["mensual"])
    usuario = Usuario.query.get(user_id)
    if not usuario:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("auth.login"))

    usuario.status = "activo"
    usuario.activo = True
    estudiante = Estudiante.query.first()
    if estudiante:
        db.session.add(
            Pago(
                estudiante_id=estudiante.id,
                registrado_por=usuario.id,
                monto=plan["precio"],
                fecha_emision=date.today(),
                fecha_vencimiento=date.today() + timedelta(days=plan["dias"]),
                estado="PAGADO",
            )
        )
    db.session.commit()

    flash(f"Pago {plan['nombre']} confirmado con Stripe. Portal desbloqueado.", "success")
    return redirect(url_for("deportistas.deportistas_dashboard"))


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
    estudiante = Estudiante.query.first()
    if estudiante:
        db.session.add(
            Pago(
                estudiante_id=estudiante.id,
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
