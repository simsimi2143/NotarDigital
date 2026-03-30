from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import Sanction, User
from app.forms import SanctionForm
from app.extensions import db
from app.utils import log_action
from app.decorators import roles_required

sanctions_bp = Blueprint("sanctions", __name__, url_prefix="/admin/sanctions")

@sanctions_bp.route("/")
@login_required
@roles_required("admin", "notario", "funcionario")   # ← Se agregó "funcionario"
def list_sanctions():
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    sanctions_query = Sanction.query.order_by(Sanction.fecha_sancion.desc())

    if q:
        sanctions_query = sanctions_query.join(User, Sanction.funcionario_id == User.id).filter(User.nombre.ilike(f"%{q}%"))

    pagination = sanctions_query.paginate(page=page, per_page=10, error_out=False)
    sanctions = pagination.items
    users = {u.id: u for u in User.query.all()}

    return render_template("sanctions/list.html", sanctions=sanctions, users=users, q=q, pagination=pagination)

@sanctions_bp.route("/new", methods=["GET", "POST"])
@login_required
@roles_required("admin", "notario")
def new_sanction():
    form = SanctionForm()
    funcionarios = User.query.filter_by(eliminado=False, activo=True).all()
    form.funcionario_id.choices = [(u.id, f"{u.nombre} - {u.cargo or u.rol}") for u in funcionarios]

    if form.validate_on_submit():
        sanction = Sanction(
            funcionario_id=form.funcionario_id.data,
            motivo=form.motivo.data,
            resolucion=form.resolucion.data,
            fecha_sancion=form.fecha_sancion.data,
            fecha_publicacion_inicio=form.fecha_publicacion_inicio.data,
            fecha_publicacion_fin=form.fecha_publicacion_fin.data,
            publica=form.publica.data,
            creada_por=current_user.id
        )
        db.session.add(sanction)
        db.session.commit()
        log_action(current_user.id, "sanctions", "create", f"Sanción creada para funcionario ID {sanction.funcionario_id}")
        flash("Sanción registrada correctamente", "success")
        return redirect(url_for("sanctions.list_sanctions"))

    # Se agrega sanction=None para que el template sepa que es una creación
    return render_template("sanctions/form.html", form=form, sanction=None)

@sanctions_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin", "notario")
def edit_sanction(id):
    sanction = Sanction.query.get_or_404(id)
    form = SanctionForm(obj=sanction)
    funcionarios = User.query.filter_by(eliminado=False, activo=True).all()
    form.funcionario_id.choices = [(u.id, f"{u.nombre} - {u.cargo or u.rol}") for u in funcionarios]

    if form.validate_on_submit():
        sanction.funcionario_id = form.funcionario_id.data
        sanction.motivo = form.motivo.data
        sanction.resolucion = form.resolucion.data
        sanction.fecha_sancion = form.fecha_sancion.data
        sanction.fecha_publicacion_inicio = form.fecha_publicacion_inicio.data
        sanction.fecha_publicacion_fin = form.fecha_publicacion_fin.data
        sanction.publica = form.publica.data

        db.session.commit()
        log_action(current_user.id, "sanctions", "update", f"Sanción {sanction.id} actualizada")
        flash("Sanción actualizada", "success")
        return redirect(url_for("sanctions.list_sanctions"))

    # Crucial: se pasa el objeto sanction para que el form sepa que es edición
    return render_template("sanctions/form.html", form=form, sanction=sanction)

@sanctions_bp.route("/<int:id>/toggle", methods=["POST"])
@login_required
@roles_required("admin", "notario")
def toggle_sanction(id):
    sanction = Sanction.query.get_or_404(id)
    sanction.publica = not sanction.publica
    db.session.commit()
    log_action(current_user.id, "sanctions", "toggle_publish", f"Sanción {sanction.id} publicación={sanction.publica}")
    flash("Estado de publicación actualizado", "success")
    return redirect(url_for("sanctions.list_sanctions"))