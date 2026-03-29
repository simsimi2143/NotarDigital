from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from app.forms import LoginForm
from app.models import User
from app.utils import log_action

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data) and user.activo:
            login_user(user)
            log_action(user.id, "auth", "login", "Inicio de sesión")
            return redirect(url_for("admin.dashboard"))
        flash("Credenciales inválidas", "danger")
    return render_template("auth/login.html", form=form)

@auth_bp.route("/logout")
@login_required
def logout():
    log_action(getattr(__import__('flask_login').current_user, 'id', None), "auth", "logout", "Cierre de sesión")
    logout_user()
    return redirect(url_for("auth.login"))