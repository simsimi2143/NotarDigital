import os
from flask import Flask
from config import Config
from .extensions import db, login_manager, migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER_ORIGINALS"], exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER_SIGNED"], exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER_COMPLAINTS"], exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER_COPIES"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    login_manager.login_view = "auth.login"

    from .routes.auth import auth_bp
    from .routes.public import public_bp
    from .routes.admin import admin_bp
    from .routes.documents import documents_bp
    from .routes.complaints import complaints_bp
    from .routes.sanctions import sanctions_bp
    from .routes.audits import audits_bp
    from .routes.backups import backups_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(complaints_bp)
    app.register_blueprint(sanctions_bp)
    app.register_blueprint(audits_bp)
    app.register_blueprint(backups_bp)

    return app