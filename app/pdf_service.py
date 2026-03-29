import os
from flask import render_template, current_app

def generate_copy_html(document, office):
    html = render_template("documents/copy_template.html", document=document, office=office)
    filename = f"copia_{document.verification_code}.html"
    output_path = os.path.join(current_app.config["UPLOAD_FOLDER_COPIES"], filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return filename