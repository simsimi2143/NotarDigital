import os
import uuid
import hashlib
from flask import request
from .extensions import db
from .models import AuditLog
from datetime import datetime
from app.models import Document, Complaint

def generate_folio(prefix, model):
    year = datetime.now().year
    count = model.query.count() + 1
    return f"{prefix}-{year}-{count:06d}"

def save_file(file, folder, allowed_extensions=None):
    if not file:
        return None

    if allowed_extensions and not allowed_file(file.filename, allowed_extensions):
        raise ValueError("Tipo de archivo no permitido")

    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(folder, filename)
    file.save(path)
    return filename

def sha256_file(path):
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def generate_code():
    return uuid.uuid4().hex[:12].upper()

def log_action(user_id, modulo, accion, detalle=""):
    log = AuditLog(
        user_id=user_id,
        modulo=modulo,
        accion=accion,
        detalle=detalle,
        ip=request.remote_addr,
        user_agent=request.headers.get("User-Agent")
    )
    db.session.add(log)
    db.session.commit()

def clean_rut(rut):
    return rut.replace(".", "").replace("-", "").upper().strip()

def validate_rut(rut):
    rut = clean_rut(rut)

    if len(rut) < 2:
        return False

    cuerpo = rut[:-1]
    dv = rut[-1]

    if not cuerpo.isdigit():
        return False

    suma = 0
    multiplo = 2

    for c in reversed(cuerpo):
        suma += int(c) * multiplo
        multiplo += 1
        if multiplo > 7:
            multiplo = 2

    resto = suma % 11
    dv_esperado = 11 - resto

    if dv_esperado == 11:
        dv_esperado = "0"
    elif dv_esperado == 10:
        dv_esperado = "K"
    else:
        dv_esperado = str(dv_esperado)

    return dv == dv_esperado

def allowed_file(filename, allowed_extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions