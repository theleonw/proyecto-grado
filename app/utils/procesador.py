from collections import deque

from app.models import Categoria, Estudiante, Evaluacion, ListaEspera


class SportsEngine:
    def __init__(self, db_session):
        self.db_session = db_session

    def bubble_sort_students(self, categoria_id: int) -> list[dict]:
        students = self.db_session.query(Estudiante).filter_by(categoria_id=categoria_id).all()
        ranking = []

        for student in students:
            evals = self.db_session.query(Evaluacion).filter_by(estudiante_id=student.id).all()
            if evals:
                avg = sum(
                    float((e.disciplina + e.trabajo_equipo + e.toma_decisiones + e.condicion_fisica) / 4)
                    for e in evals
                ) / len(evals)
            else:
                avg = 0.0

            ranking.append(
                {
                    "id": student.id,
                    "codigo": student.codigo,
                    "nombre": f"{student.nombres} {student.apellidos}",
                    "promedio": round(avg, 2),
                }
            )

        n = len(ranking)
        for i in range(n):
            for j in range(0, n - i - 1):
                if ranking[j]["promedio"] < ranking[j + 1]["promedio"]:
                    ranking[j], ranking[j + 1] = ranking[j + 1], ranking[j]

        return ranking

    def manage_queue(self, payload: dict) -> dict:
        categoria_id = payload["categoria_id"]
        categoria = self.db_session.get(Categoria, categoria_id)
        if not categoria:
            raise ValueError("Categoria no encontrada")

        current_students = (
            self.db_session.query(Estudiante)
            .filter(
                Estudiante.categoria_id == categoria_id,
                Estudiante.estado.in_(["PREINSCRITO", "ACTIVO"]),
            )
            .count()
        )

        if current_students < categoria.cupo_maximo:
            return {"status": "SPOT_AVAILABLE", "message": "Hay cupo disponible."}

        existing = (
            self.db_session.query(ListaEspera)
            .filter_by(categoria_id=categoria_id, estado="EN_ESPERA")
            .order_by(ListaEspera.posicion.asc())
            .all()
        )
        queue = deque(existing)
        next_position = queue[-1].posicion + 1 if queue else 1

        wait_item = ListaEspera(
            categoria_id=categoria_id,
            acudiente_id=payload["acudiente_id"],
            nombres_estudiante=payload["nombres_estudiante"],
            apellidos_estudiante=payload["apellidos_estudiante"],
            fecha_nacimiento=payload["fecha_nacimiento"],
            posicion=next_position,
            estado="EN_ESPERA",
        )
        self.db_session.add(wait_item)
        self.db_session.commit()

        return {
            "status": "WAITLISTED",
            "message": "Categoria llena, agregado a lista de espera.",
            "position": next_position,
        }
