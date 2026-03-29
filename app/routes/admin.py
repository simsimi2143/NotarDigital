from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.decorators import roles_required
from app.models import Service, User, OfficeConfig, Document, Complaint, Sanction
from app.forms import ServiceForm, UserForm, UserEditForm, OfficeConfigForm
from app.extensions import db
from app.utils import log_action, generate_code, sha256_file
import os
import shutil
from sqlalchemy import func

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/")
@login_required
@roles_required("admin", "notario")
def dashboard():
    stats = {
        "total_docs": Document.query.count(),
        "docs_firmados": Document.query.filter_by(estado="firmado").count(),
        "reclamos_pendientes": Complaint.query.filter_by(estado="recibido").count(),
        "usuarios_activos": User.query.filter_by(activo=True).count(),
        "sanciones_vigentes": Sanction.query.filter_by(publica=True).count()
    }

    docs_by_status = db.session.query(Document.estado, func.count(Document.id)).group_by(Document.estado).all()
    complaints_by_status = db.session.query(Complaint.estado, func.count(Complaint.id)).group_by(Complaint.estado).all()

    docs_labels = [item[0] for item in docs_by_status]
    docs_values = [item[1] for item in docs_by_status]

    complaints_labels = [item[0] for item in complaints_by_status]
    complaints_values = [item[1] for item in complaints_by_status]

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        docs_labels=docs_labels,
        docs_values=docs_values,
        complaints_labels=complaints_labels,
        complaints_values=complaints_values
    )

# --- GESTIÓN DE USUARIOS ---

@admin_bp.route("/users")
@login_required
@roles_required("admin")
def list_users():
    users = User.query.all()
    return render_template("admin/users.html", users=users)

@admin_bp.route("/users/new", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def new_user():
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            nombre=form.nombre.data,
            rut=form.rut.data,
            email=form.email.data,
            rol=form.rol.data,
            cargo=form.cargo.data,
            activo=form.activo.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        log_action(current_user.id, "usuarios", "crear", f"Usuario {user.nombre} creado")
        flash("Usuario creado con éxito", "success")
        return redirect(url_for("admin.list_users"))
    return render_template("admin/user_form.html", form=form)

@admin_bp.route("/users/<int:id>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def delete_user(id):
    user = User.query.get_or_404(id)
    if current_user.id == user.id:
        flash("No puedes eliminar tu propio usuario", "danger")
        return redirect(url_for("admin.list_users"))
    db.session.delete(user)
    db.session.commit()
    log_action(current_user.id, "usuarios", "eliminar", f"Usuario {user.nombre} eliminado")
    flash("Usuario eliminado", "success")
    return redirect(url_for("admin.list_users"))

# --- CONFIGURACIÓN DE LA NOTARÍA ---

@admin_bp.route("/config", methods=["GET", "POST"])
@login_required
@roles_required("admin", "notario")
def office_config():
    office = OfficeConfig.query.first()
    if not office:
        office = OfficeConfig(nombre_notaria="Nueva Notaría") # Default
    
    form = OfficeConfigForm(obj=office)
    
    if form.validate_on_submit():
        office.nombre_notaria = form.nombre_notaria.data
        office.direccion = form.direccion.data
        office.comuna = form.comuna.data
        office.region = form.region.data
        office.correo_oficial = form.correo_oficial.data
        office.telefono = form.telefono.data
        office.horario_apertura = form.horario_apertura.data
        office.horario_cierre = form.horario_cierre.data
        office.horas_minimas_atencion = form.horas_minimas_atencion.data
        
        db.session.commit()
        log_action(current_user.id, "config", "actualizar", "Configuración de notaría actualizada")
        flash("Configuración actualizada", "success")
        return redirect(url_for("admin.office_config"))
    
    return render_template("admin/office_config.html", form=form, office=office)

# --- GESTIÓN DE SERVICIOS (Mantenido de Parte 1) ---

@admin_bp.route("/services")
@login_required
def services():
    items = Service.query.all()
    return render_template("admin/services.html", items=items)

@admin_bp.route("/services/new", methods=["GET", "POST"])
@login_required
@roles_required("admin", "notario")
def new_service():
    form = ServiceForm()
    if form.validate_on_submit():
        service = Service(nombre=form.nombre.data, descripcion=form.descripcion.data, tarifa=form.tarifa.data, activo=form.activo.data)
        db.session.add(service)
        db.session.commit()
        flash("Servicio creado", "success")
        return redirect(url_for("admin.services"))
    return render_template("admin/service_form.html", form=form)

@admin_bp.route("/users/<int:id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def edit_user(id):
    user = User.query.get_or_404(id)
    form = UserEditForm(obj=user)

    if form.validate_on_submit():
        user.nombre = form.nombre.data
        user.rut = form.rut.data
        user.email = form.email.data
        user.rol = form.rol.data
        user.cargo = form.cargo.data
        user.activo = form.activo.data

        if form.password.data:
            user.set_password(form.password.data)

        db.session.commit()
        log_action(current_user.id, "usuarios", "update", f"Usuario {user.nombre} actualizado")
        flash("Usuario actualizado correctamente", "success")
        return redirect(url_for("admin.list_users"))

    return render_template("admin/user_form.html", form=form)

@admin_bp.route("/users/<int:id>/toggle-active", methods=["POST"])
@login_required
@roles_required("admin")
def toggle_user_active(id):
    user = User.query.get_or_404(id)

    if current_user.id == user.id:
        flash("No puedes desactivar tu propio usuario", "danger")
        return redirect(url_for("admin.list_users"))

    user.activo = not user.activo
    db.session.commit()
    log_action(current_user.id, "usuarios", "toggle_active", f"Usuario {user.nombre} activo={user.activo}")
    flash("Estado del usuario actualizado", "success")
    return redirect(url_for("admin.list_users"))