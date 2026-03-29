from app import create_app
from app.extensions import db
from app.models import User, OfficeConfig

app = create_app()

with app.app_context():
    if not User.query.filter_by(email="admin@notaria.cl").first():
        user = User(
            nombre="Administrador",
            rut="11111111-1",
            email="admin@notaria.cl",
            rol="admin",
            cargo="Administrador"
        )
        user.set_password("123456")
        db.session.add(user)

    if not OfficeConfig.query.first():
        office = OfficeConfig(
            nombre_notaria="Notaría Demo Araucanía",
            direccion="Calle Principal 123",
            comuna="Temuco",
            region="La Araucanía",
            correo_oficial="contacto@notaria.cl",
            telefono="+56 9 1234 5678",
            horario_apertura="09:00",
            horario_cierre="17:00",
            horas_minimas_atencion=7
        )
        db.session.add(office)

    db.session.commit()
    print("Datos iniciales creados")