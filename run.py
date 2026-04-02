from app import create_app, db
import os
# Importamos la función desde tu archivo seed.py
from seed import seed_data 

app = create_app()

# Este bloque asegura la estructura y los datos dentro del volumen montado
with app.app_context():
    db.create_all()
    seed_data() # Ejecuta la lógica de creación del admin

if __name__ == "__main__":
    # Railway define el puerto dinámicamente; si no, usa el 8080 por defecto
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=True)