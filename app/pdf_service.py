import os
from datetime import datetime
from fpdf import FPDF
from flask import current_app

def generate_copy_file(document, office):
    """
    Genera un PDF con la copia electrónica del documento usando fpdf2.
    Retorna el nombre del archivo generado.
    """
    # Definir nombre de archivo
    filename = f"copia_{document.verification_code}.pdf"
    copies_folder = current_app.config.get("UPLOAD_FOLDER_COPIES")
    if not copies_folder:
        copies_folder = os.path.join(current_app.root_path, 'static', 'copies')
        os.makedirs(copies_folder, exist_ok=True)
    filepath = os.path.join(copies_folder, filename)

    # Crear objeto PDF
    pdf = FPDF()
    pdf.add_page()

    # Cargar fuente Unicode
    font_path = os.path.join(current_app.root_path, 'fonts', 'DejaVuSans.ttf')
    if os.path.exists(font_path):
        pdf.add_font('DejaVu', '', font_path, uni=True)
        pdf.set_font('DejaVu', size=12)
    else:
        # Fallback a Helvetica si no se encuentra la fuente
        pdf.set_font('Helvetica', size=12)

    # --- ENCABEZADO ---
    pdf.set_font('DejaVu' if os.path.exists(font_path) else 'Helvetica', 'B', 16)
    pdf.cell(0, 10, office.nombre_notaria if office else "Notaría Digital", ln=True, align='C')
    pdf.set_font('DejaVu' if os.path.exists(font_path) else 'Helvetica', size=10)
    if office:
        pdf.cell(0, 5, office.direccion or "", ln=True, align='C')
        pdf.cell(0, 5, f"{office.comuna or ''} - {office.region or ''}", ln=True, align='C')
        pdf.cell(0, 5, f"Correo: {office.correo_oficial or ''}", ln=True, align='C')
    pdf.ln(8)

    # Línea separadora
    pdf.set_draw_color(30, 58, 138)  # índigo
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

    # --- TÍTULO PRINCIPAL ---
    pdf.set_font('DejaVu' if os.path.exists(font_path) else 'Helvetica', 'B', 14)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 8, "Copia Electrónica de Documento Notarial", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)

    # --- CUADRO DE DATOS DEL DOCUMENTO ---
    pdf.set_font('DejaVu' if os.path.exists(font_path) else 'Helvetica', size=11)
    y_start = pdf.get_y()
    pdf.rect(10, y_start, 190, 70)  # caja
    x = 15
    y = y_start + 3
    pdf.set_y(y)
    pdf.set_x(x)
    pdf.set_font('DejaVu' if os.path.exists(font_path) else 'Helvetica', 'B', 10)

    # Definir función auxiliar para escribir línea
    def write_line(label, value):
        pdf.set_font('DejaVu' if os.path.exists(font_path) else 'Helvetica', 'B', 10)
        pdf.cell(35, 6, label, 0, 0)
        pdf.set_font('DejaVu' if os.path.exists(font_path) else 'Helvetica', '', 10)
        pdf.cell(0, 6, value, 0, 1)
        pdf.set_x(x)

    write_line("Folio:", document.folio)
    write_line("Título:", document.titulo)
    write_line("Tipo de documento:", document.tipo_documento)
    write_line("Solicitante:", document.solicitante_nombre or "No informado")
    write_line("RUT solicitante:", document.solicitante_rut or "No informado")
    write_line("Estado:", document.estado.replace('_', ' ').title())
    write_line("Proveedor firma:", document.provider_signature.upper() if document.provider_signature else "No informado")
    fecha_firma = document.signed_at.strftime("%d de %B de %Y a las %H:%M") if document.signed_at else "No disponible"
    write_line("Fecha de firma:", fecha_firma)

    pdf.set_y(y_start + 75)

    # --- CÓDIGO DE VERIFICACIÓN Y HASH ---
    pdf.set_font('DejaVu' if os.path.exists(font_path) else 'Helvetica', 'B', 10)
    pdf.cell(0, 6, "Código de verificación:", 0, 1)
    pdf.set_font('DejaVu' if os.path.exists(font_path) else 'Helvetica', '', 10)
    pdf.cell(0, 6, document.verification_code, 0, 1)
    pdf.ln(4)
    pdf.set_font('DejaVu' if os.path.exists(font_path) else 'Helvetica', 'B', 10)
    pdf.cell(0, 6, "Hash SHA-256 del documento firmado:", 0, 1)
    pdf.set_font('DejaVu' if os.path.exists(font_path) else 'Helvetica', '', 8)
    pdf.multi_cell(0, 5, document.hash_signed_file, 0, 1)

    # --- RESUMEN (opcional) ---
    if document.contenido_resumen:
        pdf.ln(4)
        pdf.set_font('DejaVu' if os.path.exists(font_path) else 'Helvetica', 'B', 10)
        pdf.cell(0, 6, "Resumen del contenido:", 0, 1)
        pdf.set_font('DejaVu' if os.path.exists(font_path) else 'Helvetica', '', 10)
        pdf.multi_cell(0, 5, document.contenido_resumen, 0, 1)

    # --- PIE DE PÁGINA ---
    pdf.set_y(-30)
    pdf.set_font('DejaVu' if os.path.exists(font_path) else 'Helvetica', 'I', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "Esta copia electrónica ha sido emitida por la Notaría Digital con validez legal conforme a la Ley N° 19.799.", 0, 1, 'C')
    pdf.cell(0, 5, f"Para verificar la integridad, ingrese al portal con el código: {document.verification_code}", 0, 1, 'C')
    fecha_actual = datetime.now().strftime("%d de %B de %Y a las %H:%M")
    pdf.cell(0, 5, f"Documento generado electrónicamente el {fecha_actual}.", 0, 1, 'C')

    # Guardar PDF
    pdf.output(filepath)
    return filename