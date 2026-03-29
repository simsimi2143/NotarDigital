import csv
from io import StringIO
from flask import Blueprint, render_template, request, make_response
from flask_login import login_required
from app.models import AuditLog

audits_bp = Blueprint("audits", __name__, url_prefix="/admin/audits")

@audits_bp.route("/")
@login_required
def list_audits():
    modulo = request.args.get("modulo", "").strip()
    accion = request.args.get("accion", "").strip()

    query = AuditLog.query.order_by(AuditLog.fecha.desc())

    if modulo:
        query = query.filter(AuditLog.modulo.ilike(f"%{modulo}%"))
    if accion:
        query = query.filter(AuditLog.accion.ilike(f"%{accion}%"))

    logs = query.all()
    return render_template("audits/list.html", logs=logs, modulo=modulo, accion=accion)

@audits_bp.route("/export")
@login_required
def export_audits():
    logs = AuditLog.query.order_by(AuditLog.fecha.desc()).all()

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["Fecha", "Módulo", "Acción", "Detalle", "IP", "User Agent"])

    for log in logs:
        cw.writerow([log.fecha, log.modulo, log.accion, log.detalle, log.ip, log.user_agent])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=auditoria.csv"
    output.headers["Content-type"] = "text/csv; charset=utf-8"
    return output