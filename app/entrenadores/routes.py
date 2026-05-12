from datetime import date
import os

import requests
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.auth.routes import role_required
from app.extensions import db
from app.models import Estudiante, Evaluacion
from app.utils.algoritmos import ProcesadorFutbol


entrenadores_bp = Blueprint("entrenadores", __name__)


@entrenadores_bp.route("/", methods=["GET"])
@role_required("ENTRENADOR", "ADMIN")
def entrenadores_dashboard():
    engine = ProcesadorFutbol(db.session)
    estudiantes = Estudiante.query.all()

    class FilaRanking:
        def __init__(self, estudiante, promedio):
            self.estudiante = estudiante
            self.promedio_rendimiento = promedio

    filas = [FilaRanking(e, engine.calcular_promedio_rendimiento(e)) for e in estudiantes]
    ranking = engine.ordenamiento_burbuja(filas)

    ranking_view = [
        {
            "nombre": f"{item.estudiante.nombres} {item.estudiante.apellidos}",
            "codigo": item.estudiante.codigo,
            "promedio": item.promedio_rendimiento,
        }
        for item in ranking[:8]
    ]

    evaluaciones_hoy = (
        db.session.query(Evaluacion)
        .filter(Evaluacion.fecha == date.today())
        .count()
    )

    return render_template(
        "entrenador/dashboard.html",
        ranking=ranking_view,
        tendencia_equipo=[68, 70, 72, 75, 79, 81],
        evaluaciones_hoy=evaluaciones_hoy,
        total_estudiantes=len(estudiantes),
        estudiantes_activos=Estudiante.query.filter(Estudiante.estado.in_(["ACTIVO", "PREINSCRITO"])).all(),
    )


@entrenadores_bp.post("/evaluaciones/crear")
@role_required("ENTRENADOR", "ADMIN")
def crear_evaluacion():
    estudiante_id = int(request.form.get("estudiante_id"))
    evaluacion = Evaluacion(
        estudiante_id=estudiante_id,
        evaluador_id=session.get("user_id", 1),
        disciplina=float(request.form.get("disciplina", 3)),
        trabajo_equipo=float(request.form.get("trabajo_equipo", 3)),
        toma_decisiones=float(request.form.get("toma_decisiones", 3)),
        condicion_fisica=float(request.form.get("condicion_fisica", 3)),
    )
    db.session.add(evaluacion)
    db.session.commit()
    flash("Evaluacion registrada.", "success")
    return redirect(url_for("entrenadores.entrenadores_dashboard"))


@entrenadores_bp.post("/planes-ia")
@role_required("ENTRENADOR", "ADMIN")
def plan_ia():
    objetivo = (request.form.get("objetivo") or "Mejorar rendimiento general").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if not gemini_key:
        flash("Configura GEMINI_API_KEY para planes IA. Plan base: 3 sesiones tecnica + 2 fisico por semana.", "error")
        return redirect(url_for("entrenadores.entrenadores_dashboard"))

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
    payload = {
        "contents": [{"parts": [{"text": f"Crea un plan de entrenamiento semanal para futbol juvenil. Objetivo: {objetivo}"}]}]
    }
    plan_texto = "No se pudo generar plan IA"
    try:
        resp = requests.post(url, json=payload, timeout=20)
        if resp.ok:
            body = resp.json()
            plan_texto = body.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", plan_texto)
    except Exception:
        pass

    flash(f"Plan IA: {plan_texto[:320]}", "success")
    return redirect(url_for("entrenadores.entrenadores_dashboard"))
