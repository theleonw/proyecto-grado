from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import func

from app.models import Estudiante, Pago
from app.utils.algoritmos import ProcesadorFutbol


@dataclass
class EstudianteRendimiento:
    id: int
    codigo: str
    nombre_completo: str
    promedio_rendimiento: float


class AdminReportesService:
    def __init__(self, db_session):
        self.db_session = db_session
        self.procesador = ProcesadorFutbol(db_session)

    def cuadro_de_honor(self, categoria_id: int | None = None, limite: int = 10) -> list[dict]:
        query = self.db_session.query(Estudiante)
        if categoria_id:
            query = query.filter(Estudiante.categoria_id == categoria_id)

        estudiantes = query.all()
        datos = []
        for est in estudiantes:
            datos.append(
                EstudianteRendimiento(
                    id=est.id,
                    codigo=est.codigo,
                    nombre_completo=f"{est.nombres} {est.apellidos}",
                    promedio_rendimiento=self.procesador.calcular_promedio_rendimiento(est),
                )
            )

        ranking = self.procesador.ordenamiento_burbuja(datos)
        return [
            {
                "posicion": idx + 1,
                "estudiante_id": item.id,
                "codigo": item.codigo,
                "nombre": item.nombre_completo,
                "promedio_rendimiento": item.promedio_rendimiento,
            }
            for idx, item in enumerate(ranking[:limite])
        ]

    def detectar_mensualidades_vencidas(self, dias_gracia: int = 30) -> list[dict]:
        hoy = date.today()

        subquery = (
            self.db_session.query(
                Pago.estudiante_id,
                func.max(Pago.fecha_vencimiento).label("ultima_fecha_vencimiento"),
            )
            .group_by(Pago.estudiante_id)
            .subquery()
        )

        filas = (
            self.db_session.query(Estudiante, subquery.c.ultima_fecha_vencimiento)
            .join(subquery, subquery.c.estudiante_id == Estudiante.id)
            .all()
        )

        vencidos = []
        for est, ultima_fecha in filas:
            if not ultima_fecha:
                continue
            if ultima_fecha + timedelta(days=dias_gracia) < hoy:
                dias_mora = (hoy - ultima_fecha).days
                vencidos.append(
                    {
                        "estudiante_id": est.id,
                        "codigo": est.codigo,
                        "nombre": f"{est.nombres} {est.apellidos}",
                        "ultima_fecha_vencimiento": ultima_fecha.isoformat(),
                        "dias_mora": dias_mora,
                    }
                )

        return vencidos
