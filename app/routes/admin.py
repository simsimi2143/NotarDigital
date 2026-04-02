from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.decorators import roles_required
from app.models import Service, User, OfficeConfig, Document, Complaint, Sanction, ServiceCategory
from app.forms import ServiceForm, UserForm, UserEditForm, OfficeConfigForm, CategoryForm
from app.extensions import db
from app.utils import log_action, generate_code, sha256_file
import os
import shutil
from sqlalchemy import func
from app.models import AuditLog

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/")
@login_required
def dashboard():
    stats = {
        "total_docs": Document.query.count(),
        "docs_firmados": Document.query.filter_by(estado="firmado").count(),
        "reclamos_pendientes": Complaint.query.filter_by(estado="recibido").count(),
        "usuarios_activos": User.query.filter_by(activo=True).filter(User.rol != 'admin').count(),
        "sanciones_vigentes": Sanction.query.filter_by(publica=True).count()
    }

    docs_by_status = db.session.query(Document.estado, func.count(Document.id)).group_by(Document.estado).all()
    complaints_by_status = db.session.query(Complaint.estado, func.count(Complaint.id)).group_by(Complaint.estado).all()

    docs_labels = [item[0] for item in docs_by_status]
    docs_values = [item[1] for item in docs_by_status]

    complaints_labels = [item[0] for item in complaints_by_status]
    complaints_values = [item[1] for item in complaints_by_status]

    recent_logs = AuditLog.query.order_by(AuditLog.fecha.desc()).limit(8).all() if current_user.rol in ['admin', 'notario'] else []
    users = {u.id: u for u in User.query.all()} if current_user.rol in ['admin', 'notario'] else {}

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        docs_labels=docs_labels,
        docs_values=docs_values,
        complaints_labels=complaints_labels,
        complaints_values=complaints_values,
        recent_logs=recent_logs,
        users=users
    )

# --- GESTIÓN DE USUARIOS ---

@admin_bp.route("/users")
@login_required
@roles_required("admin")
def list_users():
    page = request.args.get("page", 1, type=int)
    pagination = User.query.filter_by(eliminado=False).order_by(User.fecha_creacion.desc()).paginate(page=page, per_page=10, error_out=False)
    users = pagination.items
    return render_template("admin/users.html", users=users, pagination=pagination)

@admin_bp.route("/users/new", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def new_user():
    form = UserForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("Error: El correo electrónico ya está registrado.", "danger")
            return render_template("admin/user_form.html", form=form)
        
        existing_rut = User.query.filter_by(rut=form.rut.data).first()
        if existing_rut:
            flash("Error: El RUT ya está registrado.", "danger")
            return render_template("admin/user_form.html", form=form)
        
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

    return render_template("admin/user_form.html", form=form, user=user)

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

# --- CONFIGURACIÓN DE LA NOTARÍA ---

@admin_bp.route("/config", methods=["GET", "POST"])
@login_required
@roles_required("admin", "notario")
def office_config():
    office = OfficeConfig.query.first()
    if not office:
        office = OfficeConfig(nombre_notaria="Nueva Notaría")
        db.session.add(office)
        db.session.commit()
    
    form = OfficeConfigForm(obj=office)
    
    if form.validate_on_submit():
        office.nombre_notaria = form.nombre_notaria.data
        office.direccion = form.direccion.data
        office.comuna = form.comuna.data
        office.region = form.region.data
        office.correo_oficial = form.correo_oficial.data
        office.telefono = form.telefono.data
        office.horas_minimas_atencion = form.horas_minimas_atencion.data
        
        office.tipo_horario = request.form.get('tipo_horario', 'continuo')
        
        office.hora_apertura = request.form.get('hora_apertura')
        office.hora_cierre = request.form.get('hora_cierre')
        
        office.turno_manana_inicio = request.form.get('turno_manana_inicio')
        office.turno_manana_fin = request.form.get('turno_manana_fin')
        office.turno_tarde_inicio = request.form.get('turno_tarde_inicio')
        office.turno_tarde_fin = request.form.get('turno_tarde_fin')
        
        office.colacion_apertura = request.form.get('colacion_apertura')
        office.colacion_inicio = request.form.get('colacion_inicio')
        office.colacion_fin = request.form.get('colacion_fin')
        office.colacion_cierre = request.form.get('colacion_cierre')
        
        dias = request.form.getlist('dias_atencion')
        office.dias_atencion = ','.join(dias) if dias else 'lunes,martes,miercoles,jueves,viernes'
        
        office.tipo_sabado = request.form.get('tipo_sabado', 'medio')
        office.sabado_inicio = request.form.get('sabado_inicio')
        office.sabado_fin = request.form.get('sabado_fin')
        
        office.duracion_tramite = request.form.get('duracion_tramite', 30, type=int)
        
        office.horario_apertura = request.form.get('hora_apertura') or request.form.get('horario_apertura')
        office.horario_cierre = request.form.get('hora_cierre') or request.form.get('horario_cierre')
        
        db.session.commit()
        log_action(current_user.id, "config", "actualizar", "Configuración de notaría actualizada")
        flash("Configuración actualizada correctamente", "success")
        return redirect(url_for("admin.office_config"))
    
    return render_template("admin/office_config.html", form=form, office=office)

# --- GESTIÓN DE CATEGORÍAS ---

@admin_bp.route("/categories")
@login_required
@roles_required("admin", "notario")
def list_categories():
    categories = ServiceCategory.query.order_by(ServiceCategory.orden).all()
    return render_template("admin/categories.html", categories=categories)

@admin_bp.route("/categories/new", methods=["GET", "POST"])
@login_required
@roles_required("admin", "notario")
def new_category():
    form = CategoryForm()
    if form.validate_on_submit():
        category = ServiceCategory(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            activo=form.activo.data,
            orden=form.orden.data or 0
        )
        db.session.add(category)
        db.session.commit()
        log_action(current_user.id, "categorias", "crear", f"Categoría {category.nombre} creada")
        flash("Categoría creada con éxito", "success")
        return redirect(url_for("admin.list_categories"))
    return render_template("admin/category_form.html", form=form)

@admin_bp.route("/categories/<int:id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin", "notario")
def edit_category(id):
    category = ServiceCategory.query.get_or_404(id)
    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        category.nombre = form.nombre.data
        category.descripcion = form.descripcion.data
        category.activo = form.activo.data
        category.orden = form.orden.data or 0
        db.session.commit()
        log_action(current_user.id, "categorias", "editar", f"Categoría {category.nombre} actualizada")
        flash("Categoría actualizada", "success")
        return redirect(url_for("admin.list_categories"))
    return render_template("admin/category_form.html", form=form, category=category)

@admin_bp.route("/categories/<int:id>/toggle-active", methods=["POST"])
@login_required
@roles_required("admin", "notario")
def toggle_category_active(id):
    category = ServiceCategory.query.get_or_404(id)
    category.activo = not category.activo
    db.session.commit()
    log_action(current_user.id, "categorias", "toggle_active", f"Categoría {category.nombre} activo={category.activo}")
    flash("Estado de categoría actualizado", "success")
    return redirect(url_for("admin.list_categories"))

# --- GESTIÓN DE SERVICIOS ---

@admin_bp.route("/services")
@login_required
def services():
    items = Service.query.all()
    categories = {c.id: c.nombre for c in ServiceCategory.query.all()}
    return render_template("admin/services.html", items=items, categories=categories)

@admin_bp.route("/services/new", methods=["GET", "POST"])
@login_required
@roles_required("admin", "notario")
def new_service():
    form = ServiceForm()
    # Actualizar choices dinámicamente
    from app.models import ServiceCategory
    form.category_id.choices = [(0, '-- Sin categoría --')] + [(c.id, c.nombre) for c in ServiceCategory.query.filter_by(activo=True).order_by(ServiceCategory.orden).all()]
    if form.validate_on_submit():
        service = Service(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            tarifa=form.tarifa.data,
            activo=form.activo.data,
            category_id=form.category_id.data if form.category_id.data != 0 else None
        )
        db.session.add(service)
        db.session.commit()
        log_action(current_user.id, "servicios", "crear", f"Servicio {service.nombre} creado")
        flash("Servicio creado", "success")
        return redirect(url_for("admin.services"))
    return render_template("admin/service_form.html", form=form)

@admin_bp.route("/services/<int:id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin", "notario")
def edit_service(id):
    service = Service.query.get_or_404(id)
    form = ServiceForm(obj=service)
    from app.models import ServiceCategory
    form.category_id.choices = [(0, '-- Sin categoría --')] + [(c.id, c.nombre) for c in ServiceCategory.query.filter_by(activo=True).order_by(ServiceCategory.orden).all()]
    if request.method == 'GET':
        form.category_id.data = service.category_id if service.category_id else 0
    if form.validate_on_submit():
        service.nombre = form.nombre.data
        service.descripcion = form.descripcion.data
        service.tarifa = form.tarifa.data
        service.activo = form.activo.data
        service.category_id = form.category_id.data if form.category_id.data != 0 else None
        db.session.commit()
        log_action(current_user.id, "servicios", "editar", f"Servicio {service.nombre} actualizado")
        flash("Servicio actualizado", "success")
        return redirect(url_for("admin.services"))
    return render_template("admin/service_form.html", form=form, service=service)