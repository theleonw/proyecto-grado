import os
from urllib.parse import urlencode
from urllib.request import urlopen

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session, url_for

pagina_bp = Blueprint("pagina", __name__)


def _verify_recaptcha(token: str) -> bool:
    secret = os.getenv("RECAPTCHA_SECRET_KEY")
    if not secret:
        return True
    if not token:
        return False

    payload = urlencode({"secret": secret, "response": token}).encode("utf-8")
    try:
        with urlopen("https://www.google.com/recaptcha/api/siteverify", data=payload, timeout=8) as resp:
            body = resp.read().decode("utf-8")
            return '"success": true' in body or '"success":true' in body
    except Exception:
        return False


@pagina_bp.route("/", methods=["GET"])
def inicio():
    return render_template(
        "pagina/index.html",
        recaptcha_site_key=os.getenv("RECAPTCHA_SITE_KEY", ""),
    )


@pagina_bp.route("/contacto", methods=["POST"])
def contacto():
    token = request.form.get("recaptcha_token", "")
    if not _verify_recaptcha(token):
        flash("Validacion reCAPTCHA fallida. Intenta de nuevo.", "error")
        return redirect(url_for("pagina.inicio"))

    flash("Mensaje enviado correctamente. Te responderemos pronto.", "success")
    return redirect(url_for("pagina.inicio"))
