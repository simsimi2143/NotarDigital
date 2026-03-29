import os
import zipfile
from datetime import datetime
from flask import Blueprint, render_template, current_app, send_from_directory, flash, redirect, url_for
from flask_login import login_required, current_user
from app.decorators import roles_required
from app.utils import log_action

backups_bp = Blueprint("backups", __name__, url_prefix="/admin/backups")

@backups_bp.route("/")
@login_required
@roles_required("admin", "notario")
def list_backups():
    backup_dir = os.path.join(current_app.root_path, "..", "uploads", "backups")
    os.makedirs(backup_dir, exist_ok=True)
    files = sorted(os.listdir(backup_dir), reverse=True)
    return render_template("admin/backups.html", files=files)

@backups_bp.route("/create", methods=["POST"])
@login_required
@roles_required("admin", "notario")
def create_backup():
    base_dir = os.path.abspath(os.path.join(current_app.root_path, ".."))
    backup_dir = os.path.join(base_dir, "uploads", "backups")
    os.makedirs(backup_dir, exist_ok=True)

    db_path = os.path.join(base_dir, "instance", "app.db")
    uploads_path = os.path.join(base_dir, "uploads")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}.zip"
    backup_path = os.path.join(backup_dir, backup_name)

    try:
        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            if os.path.exists(db_path):
                zipf.write(db_path, arcname="instance/app.db")

            for root, dirs, files in os.walk(uploads_path):
                for file in files:
                    if file.endswith(".zip"):
                        continue
                    full_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_path, base_dir)
                    zipf.write(full_path, arcname=arcname)

        log_action(current_user.id, "backups", "create", f"Backup generado: {backup_name}")
        flash("Backup creado correctamente", "success")
    except Exception as e:
        flash(f"Error al crear backup: {str(e)}", "danger")

    return redirect(url_for("backups.list_backups"))

@backups_bp.route("/download/<filename>")
@login_required
@roles_required("admin", "notario")
def download_backup(filename):
    backup_dir = os.path.join(current_app.root_path, "..", "uploads", "backups")
    log_action(current_user.id, "backups", "download", f"Backup descargado: {filename}")
    return send_from_directory(backup_dir, filename, as_attachment=True)