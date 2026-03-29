from flask import Blueprint, flash, render_template, request, current_app, send_from_directory
from app.forms import ComplaintForm
from app.extensions import db
from app.utils import save_file, generate_code, log_action, generate_folio
from app.services_email import send_email
from app.models import OfficeConfig, Service, Sanction, Document, Complaint, User

public_bp = Blueprint("public", __name__)

@public_bp.route("/")
def home():
    office = OfficeConfig.query.first()
    services = Service.query.filter_by(activo=True).all()
    sanctions = Sanction.query.filter_by(publica=True).all()
    return render_template("public/home.html", office=office, services=services, sanctions=sanctions)

@public_bp.route("/servicios")
def services():
    services = Service.query.filter_by(activo=True).all()
    return render_template("public/services.html", services=services)

@public_bp.route("/sanciones")
def public_sanctions():
    sanctions = Sanction.query.filter_by(publica=True).order_by(Sanction.fecha_sancion.desc()).all()
    users = {u.id: u for u in User.query.all()}
    return render_template("public/sanctions.html", sanctions=sanctions, users=users)

@public_bp.route("/reclamos", methods=["GET", "POST"])
def public_complaints():
    form = ComplaintForm()
    if form.validate_on_submit():
        try:
            filename = save_file(
                form.adjunto.data,
                current_app.config["UPLOAD_FOLDER_COMPLAINTS"],
                current_app.config["ALLOWED_EXTENSIONS"]
            ) if form.adjunto.data else None

            complaint = Complaint(
                folio=generate_folio("REC", Complaint),
                nombre_reclamante=form.nombre_reclamante.data,
                rut_reclamante=form.rut_reclamante.data,
                email=form.email.data,
                telefono=form.telefono.data,
                descripcion=form.descripcion.data,
                adjunto_path=filename
            )
            db.session.add(complaint)
            db.session.commit()

            if complaint.email:
                send_email(
                    complaint.email,
                    f"Confirmación de reclamo {complaint.folio}",
                    f"Su reclamo ha sido ingresado correctamente.\n\nFolio: {complaint.folio}\nEstado: {complaint.estado}"
                )

            return render_template("public/complaint_success.html", folio=complaint.folio)
        except ValueError as e:
            flash(str(e), "danger")

    return render_template("public/complaints.html", form=form)

@public_bp.route("/reclamos/seguimiento", methods=["GET", "POST"])
def complaint_tracking():
    folio = request.args.get("folio")
    complaint = None
    if folio:
        complaint = Complaint.query.filter_by(folio=folio).first()
    return render_template("public/complaint_tracking.html", complaint=complaint)

@public_bp.route("/verificar-documento", methods=["GET"])
def verify_document():
    code = request.args.get("code")
    document = None
    if code:
        document = Document.query.filter_by(verification_code=code).first()
    return render_template("public/verify_document.html", document=document)

@public_bp.route("/copias/<filename>")
def public_copy_download(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER_COPIES"], filename, as_attachment=True)