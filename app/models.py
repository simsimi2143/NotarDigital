from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from .extensions import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    rut = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(50), nullable=False, default="funcionario")
    cargo = db.Column(db.String(100))
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    eliminado = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class OfficeConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_notaria = db.Column(db.String(200), nullable=False)
    direccion = db.Column(db.String(255), nullable=False)
    comuna = db.Column(db.String(100), nullable=False)
    region = db.Column(db.String(100), nullable=False)
    correo_oficial = db.Column(db.String(150), nullable=False)
    telefono = db.Column(db.String(50))
    
    # Campos de horario (mantener compatibilidad)
    horario_apertura = db.Column(db.String(20))
    horario_cierre = db.Column(db.String(20))
    
    # Nuevos campos para horario flexible
    tipo_horario = db.Column(db.String(20), default='continuo')  # continuo, turnos, colacion
    
    # Horario continuo
    hora_apertura = db.Column(db.String(10))
    hora_cierre = db.Column(db.String(10))
    
    # Horario por turnos
    turno_manana_inicio = db.Column(db.String(10))
    turno_manana_fin = db.Column(db.String(10))
    turno_tarde_inicio = db.Column(db.String(10))
    turno_tarde_fin = db.Column(db.String(10))
    
    # Horario con colación
    colacion_apertura = db.Column(db.String(10))
    colacion_inicio = db.Column(db.String(10))
    colacion_fin = db.Column(db.String(10))
    colacion_cierre = db.Column(db.String(10))
    
    # Días de atención (almacenados como string separado por comas: "lunes,martes,miercoles...")
    dias_atencion = db.Column(db.String(100), default='lunes,martes,miercoles,jueves,viernes')
    
    # Opciones de sábado
    tipo_sabado = db.Column(db.String(20), default='medio')  # completo, medio, tarde
    sabado_inicio = db.Column(db.String(10))
    sabado_fin = db.Column(db.String(10))
    
    # Configuración adicional
    horas_minimas_atencion = db.Column(db.Integer, default=7)
    duracion_tramite = db.Column(db.Integer, default=30)  # minutos estimados por trámite

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text)
    tarifa = db.Column(db.Integer, nullable=False)
    activo = db.Column(db.Boolean, default=True)
    category_id = db.Column(db.Integer, db.ForeignKey('service_category.id'), nullable=True)

class ServiceCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    descripcion = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)
    orden = db.Column(db.Integer, default=0)  # para ordenar en la vista pública

    # Relación con servicios
    servicios = db.relationship('Service', backref='categoria', lazy=True)

    def __repr__(self):
        return f'<ServiceCategory {self.nombre}>'

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    folio = db.Column(db.String(50), unique=True, nullable=False)
    tipo_documento = db.Column(db.String(100), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    solicitante_nombre = db.Column(db.String(150))
    solicitante_rut = db.Column(db.String(20))
    contenido_resumen = db.Column(db.Text)
    estado = db.Column(db.String(50), default="borrador")

    original_file_path = db.Column(db.String(255))
    signed_file_path = db.Column(db.String(255))
    copy_file_path = db.Column(db.String(255))

    hash_signed_file = db.Column(db.String(255))
    provider_signature = db.Column(db.String(100))
    signed_at = db.Column(db.DateTime)

    verification_code = db.Column(db.String(100), unique=True)

    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    uploaded_signed_by = db.Column(db.Integer, db.ForeignKey("user.id"))

    eliminado = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    enviado_firma_externa = db.Column(db.Boolean, default=False)
    fecha_envio_firma = db.Column(db.DateTime)
    observacion_firma = db.Column(db.Text)

# models.py (fragmento)
class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    folio = db.Column(db.String(50), unique=True, nullable=False)
    nombre_reclamante = db.Column(db.String(150), nullable=False)
    rut_reclamante = db.Column(db.String(20))
    email = db.Column(db.String(120))
    telefono = db.Column(db.String(50))
    nombre_funcionario = db.Column(db.String(150))  # <--- NUEVO CAMPO
    descripcion = db.Column(db.Text, nullable=False)
    adjunto_path = db.Column(db.String(255))
    estado = db.Column(db.String(50), default="recibido")
    respuesta = db.Column(db.Text)
    responded_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_respuesta = db.Column(db.DateTime)

class Sanction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    motivo = db.Column(db.Text, nullable=False)
    resolucion = db.Column(db.Text)
    fecha_sancion = db.Column(db.Date, nullable=False)
    fecha_publicacion_inicio = db.Column(db.Date)
    fecha_publicacion_fin = db.Column(db.Date)
    publica = db.Column(db.Boolean, default=True)
    creada_por = db.Column(db.Integer, db.ForeignKey("user.id"))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    modulo = db.Column(db.String(100), nullable=False)
    accion = db.Column(db.String(100), nullable=False)
    detalle = db.Column(db.Text)
    ip = db.Column(db.String(100))
    user_agent = db.Column(db.String(255))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)