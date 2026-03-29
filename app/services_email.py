import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = current_app.config["MAIL_DEFAULT_SENDER"]
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(current_app.config["MAIL_SERVER"], current_app.config["MAIL_PORT"])
        server.starttls()
        server.login(current_app.config["MAIL_USERNAME"], current_app.config["MAIL_PASSWORD"])
        server.sendmail(
            current_app.config["MAIL_DEFAULT_SENDER"],
            to_email,
            msg.as_string()
        )
        server.quit()
        return True
    except Exception as e:
        print("Error enviando correo:", e)
        return False