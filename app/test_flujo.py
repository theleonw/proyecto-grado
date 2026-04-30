import os
import sys
from datetime import date, timedelta

from werkzeug.security import generate_password_hash

# Permite ejecutar este archivo directamente: `python app/test_flujo.py`
# sin romper imports absolutos como `from app import create_app`.
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app
from app.extensions import db
from app.admin.vistas import AdminReportesService
from app.models import Acudiente, Categoria, Estudiante, Evaluacion, Usuario
from app.utils.algoritmos import ProcesadorFutbol


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "test-secret"


app = create_app(TestConfig)


with app.app_context():
    db.drop_all()
    db.create_all()

    print("1) Inscripcion de estudiante")
    admin = Usuario(
        nombres="Admin",
        apellidos="Sistema",
        email="admin@forjadores.com",
        password_hash=generate_password_hash("Admin123*"),
        activo=True,
    )
    entrenador = Usuario(
        nombres="Laura",
        apellidos="DT",
        email="entrenador@forjadores.com",
        password_hash=generate_password_hash("Coach123*"),
        activo=True,
    )
    acudiente_user = Usuario(
        nombres="Carlos",
        apellidos="Padre",
        email="acudiente@forjadores.com",
        password_hash=generate_password_hash("Padre123*"),
        activo=True,
    )
    db.session.add_all([admin, entrenador, acudiente_user])
    db.session.flush()

    acudiente = Acudiente(
        usuario_id=acudiente_user.id,
        documento="CC100200300",
        parentesco_principal="Padre",
        telefono_contacto="3001112233",
    )
    categoria = Categoria(nombre="Sub 12", edad_min=10, edad_max=12, cupo_maximo=1)
    db.session.add_all([acudiente, categoria])
    db.session.flush()

    estudiante_1 = Estudiante(
        acudiente_id=acudiente.id,
        categoria_id=categoria.id,
        codigo="FBC-001",
        nombres="Juan",
        apellidos="Perez",
        fecha_nacimiento=date(2015, 5, 10),
        estado="ACTIVO",
    )
    db.session.add(estudiante_1)
    db.session.commit()
    print("   Estudiante inscrito:", estudiante_1.codigo)

    print("2) Validacion de cupo")
    engine = ProcesadorFutbol(db.session)
    resultado_cupo = engine.gestionar_cola_espera(
        categoria.id,
        {
            "acudiente_id": acudiente.id,
            "nombres_estudiante": "Mateo",
            "apellidos_estudiante": "Lopez",
            "fecha_nacimiento": date(2015, 8, 25),
            "fecha_solicitud": date.today(),
        },
    )
    print("   Resultado cupo:", resultado_cupo)

    print("3) Asignacion de nota tecnica por entrenador")
    eval_1 = Evaluacion(
        estudiante_id=estudiante_1.id,
        evaluador_id=entrenador.id,
        fecha=date.today() - timedelta(days=1),
        disciplina=4.6,
        trabajo_equipo=4.8,
        toma_decisiones=4.5,
        condicion_fisica=4.7,
    )
    db.session.add(eval_1)
    db.session.commit()
    print("   Evaluacion registrada para:", estudiante_1.codigo)

    print("4) Verificacion de aparicion en ranking")
    reportes = AdminReportesService(db.session)
    ranking = reportes.cuadro_de_honor(categoria_id=categoria.id)
    print("   Ranking:", ranking)

    assert len(ranking) >= 1
    assert ranking[0]["codigo"] == "FBC-001"
    assert ranking[0]["promedio_rendimiento"] > 0
    print("Flujo integrado completado correctamente.")
