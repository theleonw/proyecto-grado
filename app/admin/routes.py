from werkzeug.security import generate_password_hash
from flask import Blueprint, flash, redirect, render_template, request, url_for

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

    usuarios = Usuario.query.order_by(Usuario.created_at.desc()).limit(12).all()

    return render_template(
        "admin/dashboard.html",
        total_usuarios=total_usuarios,
        total_estudiantes=total_estudiantes,
        total_categorias=total_categorias,
        pagos_pendientes=pagos_pendientes,
        cuadro_honor=cuadro_honor,
        morosos=morosos,
        chart_data=chart_data,
        usuarios=usuarios,
    )


@admin_bp.post("/usuarios/crear")
@role_required("ADMIN")
def crear_usuario_admin():
    email = (request.form.get("email") or "").strip().lower()
    if not email:
        flash("Email requerido", "error")
        return redirect(url_for("admin.admin_dashboard"))

    existe = Usuario.query.filter_by(email=email).first()
    if existe:
        flash("El usuario ya existe", "error")
        return redirect(url_for("admin.admin_dashboard"))

    rol = request.form.get("rol", "USUARIO")
    user = Usuario(
        nombres=request.form.get("nombres", "Nuevo"),
        apellidos=request.form.get("apellidos", "Usuario"),
        email=email,
        password_hash=generate_password_hash(request.form.get("password", "Temporal123*")),
        activo=rol in {"ADMIN", "ENTRENADOR"},
        status="activo" if rol in {"ADMIN", "ENTRENADOR"} else "pendiente_pago",
    )
    db.session.add(user)
    db.session.commit()
    flash("Usuario creado correctamente", "success")
    return redirect(url_for("admin.admin_dashboard"))
