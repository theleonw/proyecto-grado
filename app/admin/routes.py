from flask import Blueprint, render_template

from app.admin.vistas import AdminReportesService
from app.auth.routes import role_required
from app.extensions import db
from app.models import Categoria, Estudiante, Pago, Usuario


admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/", methods=["GET"])
@role_required("ADMIN")
def admin_dashboard():
    total_usuarios = db.session.query(Usuario).count()
    total_estudiantes = db.session.query(Estudiante).count()
    total_categorias = db.session.query(Categoria).count()
    pagos_pendientes = db.session.query(Pago).filter(Pago.estado == "PENDIENTE").count()

    reportes = AdminReportesService(db.session)
    cuadro_honor = reportes.cuadro_de_honor(limite=5)
    morosos = reportes.detectar_mensualidades_vencidas()

    chart_data = {
        "labels": ["Usuarios", "Estudiantes", "Categorias", "Pendientes"],
        "values": [total_usuarios, total_estudiantes, total_categorias, pagos_pendientes],
        "morosos": len(morosos),
    }

    return render_template(
        "admin/dashboard.html",
        total_usuarios=total_usuarios,
        total_estudiantes=total_estudiantes,
        total_categorias=total_categorias,
        pagos_pendientes=pagos_pendientes,
        cuadro_honor=cuadro_honor,
        morosos=morosos,
        chart_data=chart_data,
    )
