import csv
from io import StringIO
from flask import Blueprint, render_template, request, make_response
from flask_login import login_required
from app.models import AuditLog, User
from app.decorators import roles_required

audits_bp = Blueprint("audits", __name__, url_prefix="/admin/audits")

@audits_bp.route("/")
@login_required
@roles_required("admin", "notario")
def list_audits():
    modulo = request.args.get("modulo", "").strip()
    accion = request.args.get("accion", "").strip()
    page = request.args.get("page", 1, type=int)

    query = AuditLog.query.order_by(AuditLog.fecha.desc())

    if modulo:
        query = query.filter(AuditLog.modulo.ilike(f"%{modulo}%"))
    if accion:
        query = query.filter(AuditLog.accion.ilike(f"%{accion}%"))

    pagination = query.paginate(page=page, per_page=15, error_out=False)
    logs = pagination.items

    users = {u.id: u for u in User.query.all()}

    return render_template(
        "audits/list.html",
        logs=logs,
        users=users,
        pagination=pagination,
        modulo=modulo,
        accion=accion
    )

@audits_bp.route("/export")
@login_required
@roles_required("admin", "notario")
def export_audits():
    logs = AuditLog.query.order_by(AuditLog.fecha.desc()).all()
    users = {u.id: u for u in User.query.all()}

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["Fecha", "Usuario", "Módulo", "Acción", "Detalle", "IP", "User Agent"])

    for log in logs:
        user_name = users[log.user_id].nombre if log.user_id in users else "Sistema/Desconocido"
        cw.writerow([log.fecha, user_name, log.modulo, log.accion, log.detalle, log.ip, log.user_agent])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=auditoria.csv"
    output.headers["Content-type"] = "text/csv; charset=utf-8"
    return output