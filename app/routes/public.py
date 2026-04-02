from flask import Blueprint, flash, redirect, render_template, request, current_app, send_from_directory, url_for
from flask_login import current_user
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
    # Obtenemos todos los servicios activos de una vez
    services_list = Service.query.filter_by(activo=True).all()
    return render_template("public/services.html", services=services_list)

@public_bp.route("/sanciones")
def public_sanctions():
    sanctions = Sanction.query.filter_by(publica=True).order_by(Sanction.fecha_sancion.desc()).all()
    users = {u.id: u for u in User.query.all()}
    return render_template("public/sanctions.html", sanctions=sanctions, users=users)

@public_bp.route("/reclamos", methods=["GET", "POST"])
def public_complaints():
    form = ComplaintForm()
    if form.validate_on_submit():
        folio = generate_folio('R', Complaint)   # CORREGIDO: con argumentos
        
        # Guardar archivo adjunto si existe
        adjunto_path = None
        if form.adjunto.data:
            adjunto_path = save_file(form.adjunto.data, folder='complaints')
        
        # Crear el reclamo
        complaint = Complaint(
            folio=folio,
            nombre_reclamante=form.nombre_reclamante.data,
            rut_reclamante=form.rut_reclamante.data,
            email=form.email.data,
            telefono=form.telefono.data,
            nombre_funcionario=form.nombre_funcionario.data,  # nuevo campo
            descripcion=form.descripcion.data,
            adjunto_path=adjunto_path
        )
        
        db.session.add(complaint)
        db.session.commit()
        
        # Registrar en auditoría (opcional)
        log_action(current_user.id if current_user.is_authenticated else None, 
                   "complaints", "create", f"Reclamo {folio}")
        
        flash("Su reclamo ha sido ingresado correctamente. Le responderemos a la brevedad.", "success")
        return render_template("public/complaint_success.html", folio=folio)
    
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

@public_bp.route('/descargar-firmado/<filename>')
def download_signed_document(filename):
    from flask import send_from_directory, current_app
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER_SIGNED'],
        filename,
        as_attachment=True
    )