import os
from datetime import datetime
import shutil
from flask import Blueprint, render_template, redirect, url_for, flash, current_app, send_from_directory
from flask_login import login_required, current_user
from app.models import Document, OfficeConfig
from app.pdf_service import generate_copy_html
from app.extensions import db
from app.utils import save_file, generate_code, sha256_file, log_action, generate_folio
from app.decorators import roles_required
from flask import request
from app.forms import DocumentForm, SignedUploadForm, DocumentEditForm, FirmaExternaForm

documents_bp = Blueprint("documents", __name__, url_prefix="/documents")

@documents_bp.route("/")
@login_required
def list_documents():
    estado = request.args.get("estado", "").strip()
    folio = request.args.get("folio", "").strip()

    query = Document.query.filter_by(eliminado=False).order_by(Document.fecha_creacion.desc())

    if estado:
        query = query.filter_by(estado=estado)
    if folio:
        query = query.filter(Document.folio.ilike(f"%{folio}%"))

    docs = query.all()
    return render_template("documents/list.html", docs=docs, estado=estado, folio=folio)


@documents_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin", "notario", "funcionario")
def edit_document(id):
    doc = Document.query.get_or_404(id)

    if doc.estado == "firmado":
        flash("No se puede editar un documento ya firmado", "danger")
        return redirect(url_for("documents.document_detail", id=id))

    form = DocumentEditForm(obj=doc)

    if form.validate_on_submit():
        doc.tipo_documento = form.tipo_documento.data
        doc.titulo = form.titulo.data
        doc.solicitante_nombre = form.solicitante_nombre.data
        doc.solicitante_rut = form.solicitante_rut.data
        doc.contenido_resumen = form.contenido_resumen.data
        doc.estado = form.estado.data

        db.session.commit()
        log_action(current_user.id, "documents", "update", f"Documento {doc.folio} actualizado")
        flash("Documento actualizado", "success")
        return redirect(url_for("documents.document_detail", id=id))

    return render_template("documents/edit.html", form=form, doc=doc)

@documents_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
@roles_required("admin", "notario")
def delete_document(id):
    doc = Document.query.get_or_404(id)
    doc.eliminado = True
    db.session.commit()
    log_action(current_user.id, "documents", "delete_logic", f"Documento {doc.folio} eliminado lógicamente")
    flash("Documento ocultado correctamente", "success")
    return redirect(url_for("documents.list_documents"))

@documents_bp.route("/new", methods=["GET", "POST"])
@login_required
@roles_required("admin", "notario", "funcionario")
def new_document():
    form = DocumentForm()
    if form.validate_on_submit():
        filename = save_file(
            form.original_file.data,
            current_app.config["UPLOAD_FOLDER_ORIGINALS"],
            current_app.config["ALLOWED_EXTENSIONS"]
            ) if form.original_file.data else None
        doc = Document(
            folio=generate_folio("DOC", Document),
            tipo_documento=form.tipo_documento.data,
            titulo=form.titulo.data,
            solicitante_nombre=form.solicitante_nombre.data,
            solicitante_rut=form.solicitante_rut.data,
            contenido_resumen=form.contenido_resumen.data,
            original_file_path=filename,
            created_by=current_user.id,
            verification_code=generate_code(),
            estado="pendiente_firma_externa"
        )
        db.session.add(doc)
        db.session.commit()
        log_action(current_user.id, "documents", "create", f"Documento {doc.folio}")
        flash("Documento creado y marcado como pendiente de firma externa", "success")
        return redirect(url_for("documents.list_documents"))
    return render_template("documents/form.html", form=form)

@documents_bp.route("/<int:id>")
@login_required
def document_detail(id):
    doc = Document.query.get_or_404(id)
    form = SignedUploadForm()
    firma_form = FirmaExternaForm()
    return render_template("documents/detail.html", doc=doc, form=form, firma_form=firma_form)

@documents_bp.route("/<int:id>/download-original")
@login_required
def download_original(id):
    doc = Document.query.get_or_404(id)
    if not doc.original_file_path:
        flash("No hay archivo original", "warning")
        return redirect(url_for("documents.document_detail", id=id))
    log_action(current_user.id, "documents", "download_original", f"Documento {doc.folio}")
    return send_from_directory(current_app.config["UPLOAD_FOLDER_ORIGINALS"], doc.original_file_path, as_attachment=True)

@documents_bp.route("/<int:id>/download-signed")
@login_required
def download_signed(id):
    doc = Document.query.get_or_404(id)
    if not doc.signed_file_path:
        flash("No hay archivo firmado disponible", "warning")
        return redirect(url_for("documents.document_detail", id=id))

    log_action(current_user.id, "documents", "download_signed", f"Documento firmado {doc.folio}")
    return send_from_directory(current_app.config["UPLOAD_FOLDER_SIGNED"], doc.signed_file_path, as_attachment=True)

@documents_bp.route("/<int:id>/upload-signed", methods=["POST"])
@login_required
@roles_required("admin", "notario", "funcionario")
def upload_signed(id):
    doc = Document.query.get_or_404(id)
    form = SignedUploadForm()
    if form.validate_on_submit():
        try:
            filename = save_file(
                form.signed_file.data,
                current_app.config["UPLOAD_FOLDER_SIGNED"],
                {"pdf"}
            )
            full_path = os.path.join(current_app.config["UPLOAD_FOLDER_SIGNED"], filename)
            doc.signed_file_path = filename
            doc.provider_signature = form.provider_signature.data
            doc.hash_signed_file = sha256_file(full_path)
            doc.signed_at = datetime.utcnow()
            doc.uploaded_signed_by = current_user.id
            doc.estado = "firmado"
            db.session.commit()
            log_action(current_user.id, "documents", "upload_signed", f"Documento firmado {doc.folio}")
            flash("Documento firmado cargado correctamente", "success")
        except ValueError as e:
            flash(str(e), "danger")
    return redirect(url_for("documents.document_detail", id=id))

# ... (mantener imports y rutas anteriores)

@documents_bp.route("/<int:id>/emit-copy", methods=["POST"])
@login_required
@roles_required("admin", "notario")
def emit_copy(id):
    doc = Document.query.get_or_404(id)

    if doc.estado != "firmado":
        flash("Solo se pueden emitir copias de documentos ya firmados", "danger")
        return redirect(url_for("documents.document_detail", id=id))

    office = OfficeConfig.query.first()
    try:
        filename = generate_copy_html(doc, office)
        doc.copy_file_path = filename
        db.session.commit()
        log_action(current_user.id, "documents", "emitir_copia", f"Copia electrónica emitida para folio {doc.folio}")
        flash("Copia electrónica generada correctamente", "success")
    except Exception as e:
        flash(f"Error al generar copia: {str(e)}", "danger")

    return redirect(url_for("documents.document_detail", id=id))

@documents_bp.route("/<int:id>/mark-external-sign", methods=["POST"])
@login_required
@roles_required("admin", "notario", "funcionario")
def mark_external_sign(id):
    doc = Document.query.get_or_404(id)
    form = FirmaExternaForm()

    if form.validate_on_submit():
        doc.enviado_firma_externa = True
        doc.fecha_envio_firma = datetime.utcnow()
        doc.observacion_firma = form.observacion_firma.data
        doc.estado = "pendiente_firma_externa"
        db.session.commit()
        log_action(current_user.id, "documents", "mark_external_sign", f"Documento {doc.folio} enviado a firma externa")
        flash("Documento marcado como enviado a firma externa", "success")

    return redirect(url_for("documents.document_detail", id=id))