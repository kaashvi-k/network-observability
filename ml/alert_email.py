import smtplib
from email.mime.text import MIMEText
import os


SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.environ.get("ALERT_EMAIL_ADDRESS")
SENDER_APP_PASSWORD = os.environ.get("ALERT_EMAIL_APP_PASSWORD")
RECIPIENT_EMAIL = os.environ.get("ALERT_EMAIL_ADDRESS")




def send_alert_email(severity, device_name, reason, telemetry_id):
    subject = f"[{severity}] Network Alert - {device_name}"
    body = (
        f"Severity: {severity}\n"
        f"Device: {device_name}\n"
        f"Telemetry ID: {telemetry_id}\n"
        f"Reason: {reason}\n"
    )

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
        print(f"Email sent for {device_name} ({severity})")
    except Exception as e:
        print(f"WARNING: failed to send email: {e}")


if __name__ == "__main__":

