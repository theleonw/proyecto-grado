from datetime import date

from flask import Blueprint, render_template

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
        evaluaciones_hoy=evaluaciones_hoy,
        total_estudiantes=len(estudiantes),
    )
