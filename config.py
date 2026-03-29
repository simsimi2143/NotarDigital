import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "cambia-esto-por-una-clave-segura"
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "instance", "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER_ORIGINALS = os.path.join(BASE_DIR, "uploads", "originals")
    UPLOAD_FOLDER_SIGNED = os.path.join(BASE_DIR, "uploads", "signed")
    UPLOAD_FOLDER_COMPLAINTS = os.path.join(BASE_DIR, "uploads", "complaints")
    UPLOAD_FOLDER_COPIES = os.path.join(BASE_DIR, "uploads", "copies")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "doc", "docx"}

    # configuracion del apartado de correo
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "tu_correo@gmail.com"
    MAIL_PASSWORD = "tu_clave_app"
    MAIL_DEFAULT_SENDER = "tu_correo@gmail.com"