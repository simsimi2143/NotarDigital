from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Complaint
from app.forms import ComplaintResponseForm
from app.extensions import db
from app.utils import log_action

complaints_bp = Blueprint("complaints", __name__, url_prefix="/admin/complaints")

@complaints_bp.route("/")
@login_required
def list_complaints():
    complaints = Complaint.query.order_by(Complaint.fecha_creacion.desc()).all()
    return render_template("complaints/list.html", complaints=complaints)

@complaints_bp.route("/<int:id>", methods=["GET", "POST"])
@login_required
def complaint_detail(id):
    complaint = Complaint.query.get_or_404(id)
    form = ComplaintResponseForm(obj=complaint)
    if form.validate_on_submit():
        complaint.estado = form.estado.data
        complaint.respuesta = form.respuesta.data
        complaint.responded_by = current_user.id
        complaint.fecha_respuesta = datetime.utcnow()
        db.session.commit()
        log_action(current_user.id, "complaints", "update", f"Reclamo {complaint.folio}")
        flash("Reclamo actualizado", "success")
        return redirect(url_for("complaints.list_complaints"))
    return render_template("complaints/detail.html", complaint=complaint, form=form)