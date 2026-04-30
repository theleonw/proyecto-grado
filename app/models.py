from datetime import date, datetime

from app.extensions import db


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    status = db.Column(db.String(30), default="activo", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    acudiente = db.relationship("Acudiente", back_populates="usuario", uselist=False)
    pagos_registrados = db.relationship("Pago", back_populates="registrador")
    asistencias_registradas = db.relationship("Asistencia", back_populates="registrador")
    evaluaciones_realizadas = db.relationship("Evaluacion", back_populates="evaluador")


class Acudiente(db.Model):
    __tablename__ = "acudientes"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), unique=True, nullable=False)
    documento = db.Column(db.String(30), unique=True, nullable=False)
    parentesco_principal = db.Column(db.String(50), nullable=False)
    telefono_contacto = db.Column(db.String(30))

    usuario = db.relationship("Usuario", back_populates="acudiente")
    estudiantes = db.relationship("Estudiante", back_populates="acudiente")
    lista_espera_items = db.relationship("ListaEspera", back_populates="acudiente")


class Categoria(db.Model):
    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), unique=True, nullable=False)
    edad_min = db.Column(db.Integer, nullable=False)
    edad_max = db.Column(db.Integer, nullable=False)
    cupo_maximo = db.Column(db.Integer, nullable=False)

    estudiantes = db.relationship("Estudiante", back_populates="categoria")
    lista_espera_items = db.relationship("ListaEspera", back_populates="categoria")


class Estudiante(db.Model):
    __tablename__ = "estudiantes"

    id = db.Column(db.Integer, primary_key=True)
    acudiente_id = db.Column(db.Integer, db.ForeignKey("acudientes.id"), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=False)
    codigo = db.Column(db.String(30), unique=True, nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    estado = db.Column(db.String(20), default="PREINSCRITO", nullable=False)
    fecha_inscripcion = db.Column(db.Date, default=date.today, nullable=False)

    acudiente = db.relationship("Acudiente", back_populates="estudiantes")
    categoria = db.relationship("Categoria", back_populates="estudiantes")
    pagos = db.relationship("Pago", back_populates="estudiante")
    asistencias = db.relationship("Asistencia", back_populates="estudiante")
    metricas = db.relationship("Metrica", back_populates="estudiante")
    evaluaciones = db.relationship("Evaluacion", back_populates="estudiante")


class Pago(db.Model):
    __tablename__ = "pagos"

    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey("estudiantes.id"), nullable=False)
    registrado_por = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    fecha_emision = db.Column(db.Date, default=date.today, nullable=False)
    fecha_vencimiento = db.Column(db.Date, nullable=False)
    fecha_pago = db.Column(db.DateTime)
    estado = db.Column(db.String(20), default="PENDIENTE", nullable=False)

    estudiante = db.relationship("Estudiante", back_populates="pagos")
    registrador = db.relationship("Usuario", back_populates="pagos_registrados")


class Asistencia(db.Model):
    __tablename__ = "asistencias"

    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey("estudiantes.id"), nullable=False)
    registrado_por = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    fecha = db.Column(db.Date, default=date.today, nullable=False)
    asistio = db.Column(db.Boolean, nullable=False)
    observacion = db.Column(db.String(255))

    estudiante = db.relationship("Estudiante", back_populates="asistencias")
    registrador = db.relationship("Usuario", back_populates="asistencias_registradas")


class Metrica(db.Model):
    __tablename__ = "metricas"

    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey("estudiantes.id"), nullable=False)
    fecha_medicion = db.Column(db.Date, default=date.today, nullable=False)
    velocidad = db.Column(db.Numeric(5, 2))
    resistencia = db.Column(db.Numeric(5, 2))
    fuerza = db.Column(db.Numeric(5, 2))
    tecnica = db.Column(db.Numeric(5, 2))

    estudiante = db.relationship("Estudiante", back_populates="metricas")


class Evaluacion(db.Model):
    __tablename__ = "evaluaciones"

    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey("estudiantes.id"), nullable=False)
    evaluador_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    fecha = db.Column(db.Date, default=date.today, nullable=False)
    disciplina = db.Column(db.Numeric(4, 2), nullable=False)
    trabajo_equipo = db.Column(db.Numeric(4, 2), nullable=False)
    toma_decisiones = db.Column(db.Numeric(4, 2), nullable=False)
    condicion_fisica = db.Column(db.Numeric(4, 2), nullable=False)

    estudiante = db.relationship("Estudiante", back_populates="evaluaciones")
    evaluador = db.relationship("Usuario", back_populates="evaluaciones_realizadas")


class ListaEspera(db.Model):
    __tablename__ = "lista_espera"

    id = db.Column(db.Integer, primary_key=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=False)
    acudiente_id = db.Column(db.Integer, db.ForeignKey("acudientes.id"), nullable=False)
    nombres_estudiante = db.Column(db.String(100), nullable=False)
    apellidos_estudiante = db.Column(db.String(100), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    posicion = db.Column(db.Integer, nullable=False)
    estado = db.Column(db.String(20), default="EN_ESPERA", nullable=False)
    fecha_solicitud = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    categoria = db.relationship("Categoria", back_populates="lista_espera_items")
    acudiente = db.relationship("Acudiente", back_populates="lista_espera_items")
