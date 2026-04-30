from collections import deque
from datetime import date

from app.models import Categoria, Estudiante, Evaluacion, ListaEspera


class ProcesadorFutbol:
    def __init__(self, db_session):
        self.db_session = db_session

    def calcular_promedio_rendimiento(self, estudiante: Estudiante) -> float:
        evaluaciones = (
            self.db_session.query(Evaluacion)
            .filter(Evaluacion.estudiante_id == estudiante.id)
            .all()
        )
        if not evaluaciones:
            return 0.0

        total = 0.0
        for e in evaluaciones:
            total += float((e.disciplina + e.trabajo_equipo + e.toma_decisiones + e.condicion_fisica) / 4)
        return round(total / len(evaluaciones), 2)

    def ordenamiento_burbuja(self, lista_estudiantes: list[object]) -> list[object]:
        """
        Ordena objetos en memoria (sin SQL ORDER BY) por atributo promedio_rendimiento.
        """
        n = len(lista_estudiantes)
        for i in range(n):
            for j in range(0, n - i - 1):
                if lista_estudiantes[j].promedio_rendimiento < lista_estudiantes[j + 1].promedio_rendimiento:
                    lista_estudiantes[j], lista_estudiantes[j + 1] = lista_estudiantes[j + 1], lista_estudiantes[j]
        return lista_estudiantes

    def gestionar_cola_espera(self, id_categoria: int, datos_estudiante: dict) -> dict:
        """
        Verifica cupo de categoria; si esta llena registra en lista_espera.
        """
        categoria = self.db_session.get(Categoria, id_categoria)
        if not categoria:
            raise ValueError("Categoria no encontrada")

        ocupados = (
            self.db_session.query(Estudiante)
            .filter(
                Estudiante.categoria_id == id_categoria,
                Estudiante.estado.in_(["PREINSCRITO", "ACTIVO"]),
            )
            .count()
        )

        if ocupados < categoria.cupo_maximo:
            return {
                "estado": "CUPO_DISPONIBLE",
                "mensaje": "Puede continuar con la inscripcion.",
            }

        cola_actual = (
            self.db_session.query(ListaEspera)
            .filter(
                ListaEspera.categoria_id == id_categoria,
                ListaEspera.estado == "EN_ESPERA",
            )
            .order_by(ListaEspera.posicion.asc())
            .all()
        )
        cola = deque(cola_actual)
        posicion = cola[-1].posicion + 1 if cola else 1

        item = ListaEspera(
            categoria_id=id_categoria,
            acudiente_id=datos_estudiante["acudiente_id"],
            nombres_estudiante=datos_estudiante["nombres_estudiante"],
            apellidos_estudiante=datos_estudiante["apellidos_estudiante"],
            fecha_nacimiento=datos_estudiante["fecha_nacimiento"],
            posicion=posicion,
            estado="EN_ESPERA",
            fecha_solicitud=datos_estudiante.get("fecha_solicitud", date.today()),
        )
        self.db_session.add(item)
        self.db_session.commit()

        return {
            "estado": "EN_ESPERA",
            "mensaje": "Categoria llena, agregado a lista de espera.",
            "posicion": posicion,
        }
