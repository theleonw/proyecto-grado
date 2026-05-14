from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.auth.routes import role_required
from app.extensions import db
from app.models import Asistencia, Estudiante, Evaluacion, Metrica, Pago
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
            "id": item.estudiante.id,
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
    asistieron_hoy = (
        db.session.query(Asistencia)
        .filter(Asistencia.fecha == date.today(), Asistencia.asistio.is_(True))
        .count()
    )

    return render_template(
        "entrenador/dashboard.html",
        ranking=ranking_view,
        tendencia_equipo=[68, 70, 72, 75, 79, 81],
        evaluaciones_hoy=evaluaciones_hoy,
        asistieron_hoy=asistieron_hoy,
        estudiantes_hoy=ranking_view[:5],
        total_estudiantes=len(estudiantes),
    )


@entrenadores_bp.post("/actualizar")
@role_required("ENTRENADOR", "ADMIN")
def actualizar_rendimiento_asistencia():
    estudiante_id = request.form.get("estudiante_id", type=int)
    asistio = request.form.get("asistio") == "1"

    estudiante = Estudiante.query.get(estudiante_id)
    if not estudiante:
        flash("Estudiante no encontrado", "error")
        return redirect(url_for("entrenadores.entrenadores_dashboard"))

    ultimo_pago = (
        Pago.query.filter_by(estudiante_id=estudiante_id, estado="PAGADO")
        .order_by(Pago.fecha_vencimiento.desc())
        .first()
    )
    if not ultimo_pago or ultimo_pago.fecha_vencimiento < date.today():
        flash("Solo usuarios pagos pueden registrar rendimiento/asistencia.", "error")
        return redirect(url_for("entrenadores.entrenadores_dashboard"))

    metric = Metrica(
        estudiante_id=estudiante_id,
        velocidad=request.form.get("velocidad", type=float),
        resistencia=request.form.get("resistencia", type=float),
        fuerza=request.form.get("fuerza", type=float),
        tecnica=request.form.get("tecnica", type=float),
    )
    asistencia = Asistencia(
        estudiante_id=estudiante_id,
        registrado_por=session.get("user_id"),
        asistio=asistio,
        observacion=request.form.get("observacion", ""),
    )
    db.session.add(metric)
    db.session.add(asistencia)
    db.session.commit()
    flash("Rendimiento y asistencia actualizados.", "success")
    return redirect(url_for("entrenadores.entrenadores_dashboard"))
