from datetime import date

from flask import Blueprint, jsonify, request

from app.auth.routes import admin_required
from app.extensions import db
from app.models import Pago


pagos_bp = Blueprint("pagos", __name__)


class PagoService:
    @admin_required
    def crear_pago(self):
        payload = request.get_json(silent=True) or {}
        required = ["estudiante_id", "registrado_por", "monto", "fecha_vencimiento"]
        faltantes = [f for f in required if not payload.get(f)]
        if faltantes:
            return jsonify({"error": "Datos incompletos", "faltantes": faltantes}), 400

        pago = Pago(
            estudiante_id=payload["estudiante_id"],
            registrado_por=payload["registrado_por"],
            monto=payload["monto"],
            fecha_emision=date.today(),
            fecha_vencimiento=date.fromisoformat(payload["fecha_vencimiento"]),
            estado=payload.get("estado", "PENDIENTE"),
        )
        db.session.add(pago)
        db.session.commit()
        return jsonify({"message": "Pago registrado", "pago_id": pago.id}), 201

    @admin_required
    def listar_pagos(self):
        pagos = Pago.query.order_by(Pago.id.desc()).limit(50).all()
        return jsonify(
            [
                {
                    "id": p.id,
                    "estudiante_id": p.estudiante_id,
                    "monto": float(p.monto),
                    "vencimiento": p.fecha_vencimiento.isoformat(),
                    "estado": p.estado,
                }
                for p in pagos
            ]
        ), 200


service = PagoService()


@pagos_bp.route("/", methods=["GET"])
def pagos_dashboard():
    return jsonify({"dashboard": "Pagos Dashboard"}), 200


@pagos_bp.route("/registrar", methods=["POST"])
def registrar_pago():
    return service.crear_pago()


@pagos_bp.route("/listado", methods=["GET"])
def listado_pagos():
    return service.listar_pagos()
