import email.message
import smtplib
import socket
import platform

def send_email(sender, receiver, body, pwd):
    """Sends automatic email notification to the developer when a user requests the service."""
    hostname = socket.gethostname()
    os_info = platform.system() + " " + platform.release()

    m = email.message.Message()
    m['From'] = sender
    m['To'] = receiver
    m['Subject'] = "Glimpse Through - User App Run Request"
    m.set_payload(body)

    smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
    smtp_server.ehlo()
    smtp_server.starttls()
    smtp_server.login(sender, pwd)
    smtp_server.sendmail(sender, receiver, m.as_string())
    smtp_server.quit()

def send_bug_report(sender, receiver, body, pwd):
    """Sends automatic email notification to the developer when a user encounters a bug."""
    try:
        m = email.message.Message()
        m['From'] = sender
        m['To'] = receiver
        m['Subject'] = "Glimpse Through - Error Bug Report"
        m.set_payload(body)

        smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_server.ehlo()
        smtp_server.starttls()
        smtp_server.login(sender, pwd)
        smtp_server.sendmail(sender, receiver, m.as_string())
        smtp_server.quit()
    except Exception as e:
        print(f"Error sending email: {e}")
