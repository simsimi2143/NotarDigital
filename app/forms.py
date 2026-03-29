from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, IntegerField, SelectField, FileField, BooleanField, DateField
from wtforms.validators import DataRequired, Email, Optional
from wtforms.validators import ValidationError
from app.utils import validate_rut

class LoginForm(FlaskForm):
    email = StringField("Correo", validators=[DataRequired(), Email()])
    password = PasswordField("Contraseña", validators=[DataRequired()])
    submit = SubmitField("Ingresar")

class ServiceForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired()])
    descripcion = TextAreaField("Descripción", validators=[Optional()])
    tarifa = IntegerField("Tarifa", validators=[DataRequired()])
    activo = BooleanField("Activo")
    submit = SubmitField("Guardar")

class DocumentForm(FlaskForm):
    tipo_documento = StringField("Tipo de documento", validators=[DataRequired()])
    titulo = StringField("Título", validators=[DataRequired()])
    solicitante_nombre = StringField("Solicitante", validators=[Optional()])
    solicitante_rut = StringField("RUT solicitante", validators=[Optional()])
    contenido_resumen = TextAreaField("Resumen", validators=[Optional()])
    original_file = FileField("Archivo original", validators=[Optional()])
    submit = SubmitField("Guardar")
    def validate_solicitante_rut(self, field):
        if field.data and not validate_rut(field.data):
            raise ValidationError("RUT del solicitante inválido")

class SignedUploadForm(FlaskForm):
    provider_signature = SelectField("Proveedor de firma", choices=[
        ("ecert", "ecert"),
        ("otro", "Otro")
    ])
    signed_file = FileField("Documento firmado", validators=[DataRequired()])
    submit = SubmitField("Subir firmado")

class ComplaintForm(FlaskForm):
    nombre_reclamante = StringField("Nombre", validators=[DataRequired()])
    rut_reclamante = StringField("RUT", validators=[Optional()])
    email = StringField("Correo", validators=[Optional(), Email()])
    telefono = StringField("Teléfono", validators=[Optional()])
    descripcion = TextAreaField("Descripción", validators=[DataRequired()])
    adjunto = FileField("Adjunto", validators=[Optional()])
    submit = SubmitField("Enviar reclamo")
    def validate_rut_reclamante(self, field):
        if field.data and not validate_rut(field.data):
            raise ValidationError("RUT inválido")

class ComplaintResponseForm(FlaskForm):
    estado = SelectField("Estado", choices=[
        ("recibido", "Recibido"),
        ("en_revision", "En revisión"),
        ("respondido", "Respondido"),
        ("cerrado", "Cerrado"),
        ("rechazado", "Rechazado"),
    ])
    respuesta = TextAreaField("Respuesta", validators=[Optional()])
    submit = SubmitField("Actualizar")

class SanctionForm(FlaskForm):
    funcionario_id = SelectField("Funcionario", coerce=int)
    motivo = TextAreaField("Motivo", validators=[DataRequired()])
    resolucion = TextAreaField("Resolución", validators=[Optional()])
    fecha_sancion = DateField("Fecha sanción", validators=[DataRequired()])
    fecha_publicacion_inicio = DateField("Inicio publicación", validators=[Optional()])
    fecha_publicacion_fin = DateField("Fin publicación", validators=[Optional()])
    publica = BooleanField("Publicar en portal")
    submit = SubmitField("Guardar sanción")

# ... (mantener lo anterior)

class UserForm(FlaskForm):
    nombre = StringField("Nombre Completo", validators=[DataRequired()])
    rut = StringField("RUT (ej: 12345678-9)", validators=[DataRequired()])
    email = StringField("Correo Electrónico", validators=[DataRequired(), Email()])
    password = PasswordField("Contraseña", validators=[DataRequired()])
    rol = SelectField("Rol", choices=[
        ("admin", "Administrador"),
        ("notario", "Notario"),
        ("funcionario", "Funcionario")
    ])
    cargo = StringField("Cargo")
    activo = BooleanField("Usuario Activo")
    submit = SubmitField("Guardar Usuario")
    def validate_rut(self, field):
        if not validate_rut(field.data):
            raise ValidationError("RUT inválido")

class OfficeConfigForm(FlaskForm):
    nombre_notaria = StringField("Nombre de la Notaría", validators=[DataRequired()])
    direccion = StringField("Dirección", validators=[DataRequired()])
    comuna = StringField("Comuna", validators=[DataRequired()])
    region = StringField("Región", validators=[DataRequired()])
    correo_oficial = StringField("Correo Oficial", validators=[DataRequired(), Email()])
    telefono = StringField("Teléfono")
    horario_apertura = StringField("Horario Apertura (ej: 09:00)", validators=[DataRequired()])
    horario_cierre = StringField("Horario Cierre (ej: 17:00)", validators=[DataRequired()])
    horas_minimas_atencion = IntegerField("Horas Mínimas de Atención", validators=[DataRequired()])
    submit = SubmitField("Actualizar Configuración")

class UserEditForm(FlaskForm):
    nombre = StringField("Nombre Completo", validators=[DataRequired()])
    rut = StringField("RUT (ej: 12345678-9)", validators=[DataRequired()])
    email = StringField("Correo Electrónico", validators=[DataRequired(), Email()])
    password = PasswordField("Nueva contraseña", validators=[Optional()])
    rol = SelectField("Rol", choices=[
        ("admin", "Administrador"),
        ("notario", "Notario"),
        ("funcionario", "Funcionario")
    ])
    cargo = StringField("Cargo")
    activo = BooleanField("Usuario Activo")
    submit = SubmitField("Actualizar Usuario")

    def validate_rut(self, field):
        if not validate_rut(field.data):
            raise ValidationError("RUT inválido")
        
class DocumentEditForm(FlaskForm):
    tipo_documento = StringField("Tipo de documento", validators=[DataRequired()])
    titulo = StringField("Título", validators=[DataRequired()])
    solicitante_nombre = StringField("Solicitante", validators=[Optional()])
    solicitante_rut = StringField("RUT solicitante", validators=[Optional()])
    contenido_resumen = TextAreaField("Resumen", validators=[Optional()])
    estado = SelectField("Estado", choices=[
        ("borrador", "Borrador"),
        ("en_revision", "En revisión"),
        ("pendiente_firma_externa", "Pendiente firma externa"),
        ("firmado", "Firmado"),
        ("publicado", "Publicado"),
        ("archivado", "Archivado"),
        ("anulado", "Anulado"),
    ])
    submit = SubmitField("Actualizar documento")

    def validate_solicitante_rut(self, field):
        if field.data and not validate_rut(field.data):
            raise ValidationError("RUT del solicitante inválido")        
        
class FirmaExternaForm(FlaskForm):
    observacion_firma = TextAreaField("Observación de envío", validators=[Optional()])
    submit = SubmitField("Marcar como enviado a firma externa")        