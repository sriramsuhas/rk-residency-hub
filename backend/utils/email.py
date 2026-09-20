"""
Simple SMTP-based email sending.

If `settings.smtp_host` is blank (the default), emails are logged to the
console instead of actually being sent. This keeps local development and
the test suite working without a real mail server, while production
deployments just need to set SMTP_HOST (and the other SMTP_* variables) to
get real delivery — no code change required.

Kept deliberately simple: one function, plain SMTP + STARTTLS via the
standard library, no template engine, no queue, no background workers.
"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config.settings import settings

logger = logging.getLogger("rk_pms.email")


def send_email(to_email: str, subject: str, body: str) -> None:
    """
    Sends a plain-text email. Never raises - a failed or unconfigured send
    is logged and swallowed, since a transactional email failing (e.g. a
    "booking confirmed" notice) should never break the request that
    triggered it. Password reset works the same way - the reset token is
    only usable via the emailed link, so a failed send just means the
    person needs to retry "forgot password," not a security issue.
    """
    if not settings.smtp_host:
        logger.info(
            "SMTP not configured - logging email instead of sending.\nTo: %s\nSubject: %s\n\n%s",
            to_email,
            subject,
            body,
        )
        return

    message = MIMEMultipart()
    message["From"] = settings.email_from
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(settings.email_from, [to_email], message.as_string())
        logger.info("Email sent to %s: %s", to_email, subject)
    except Exception:
        logger.exception("Failed to send email to %s (subject: %s)", to_email, subject)
