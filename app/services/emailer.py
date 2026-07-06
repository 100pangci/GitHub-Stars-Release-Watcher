"""Email sending service using standard library."""

import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Repo, Version, Event
from app.services.logs import add_log
from app.services.settings import get_setting

logger = logging.getLogger(__name__)


def get_smtp_config(db: Session) -> dict:
    """Get SMTP configuration from settings."""
    return {
        "host": get_setting(db, "smtp_host", ""),
        "port": get_setting(db, "smtp_port", "587"),
        "username": get_setting(db, "smtp_username", ""),
        "password": get_setting(db, "smtp_password", ""),
        "use_tls": get_setting(db, "smtp_use_tls", "true").lower() == "true",
        "from_addr": get_setting(db, "smtp_from_addr", ""),
        "to_addr": get_setting(db, "smtp_to_addr", ""),
    }


def is_email_configured(db: Session) -> bool:
    """Check if email is configured."""
    config = get_smtp_config(db)
    return bool(config["host"] and config["from_addr"] and config["to_addr"])


def send_test_email(db: Session) -> str:
    """Send a test email. Returns success message or raises on error."""
    config = get_smtp_config(db)
    if not config["host"] or not config["from_addr"] or not config["to_addr"]:
        raise ValueError("SMTP not fully configured")

    subject = "GitHub Stars Release Watcher - Test Email"
    body_text = "This is a test email from GitHub Stars Release Watcher.\n\nIf you received this, email configuration is working correctly."
    body_html = """<html><body>
    <h2>Test Email</h2>
    <p>This is a test email from <strong>GitHub Stars Release Watcher</strong>.</p>
    <p>If you received this, email configuration is working correctly.</p>
    </body></html>"""

    return _send_email(config, subject, body_text, body_html)


def send_weekly_summary(db: Session) -> dict:
    """Send weekly summary email. Returns dict with status info."""
    if not is_email_configured(db):
        msg = "Weekly summary skipped: email not configured"
        add_log("WARNING", msg, db=db)
        logger.warning(msg)
        return {"sent": False, "message": msg}

    # Get events not yet included in weekly summary
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    events = (
        db.query(Event)
        .filter(
            Event.created_at >= week_ago,
            Event.included_in_weekly_summary == False,  # noqa: E712
        )
        .order_by(Event.created_at.desc())
        .all()
    )

    total_updates = len(events)

    # Mark events as included
    for evt in events:
        evt.included_in_weekly_summary = True
    db.commit()

    # Build email content
    repo_groups = {}
    for evt in events:
        repo = db.query(Repo).filter(Repo.id == evt.repo_id).first()
        if repo:
            repo_name = repo.full_name
            if repo_name not in repo_groups:
                repo_groups[repo_name] = {
                    "html_url": repo.html_url,
                    "updates": [],
                }
            repo_groups[repo_name]["updates"].append(evt)

    if total_updates == 0:
        # Optionally send "no updates" email
        send_no_updates = get_setting(db, "send_no_updates_email", "true").lower() == "true"
        if not send_no_updates:
            msg = "Weekly summary: no updates, skipped sending email"
            add_log("INFO", msg, db=db)
            return {"sent": False, "message": msg, "updates": 0}

        subject = "GitHub Stars Release Weekly Summary: No updates this week"
        body_text = "No new releases or tags were detected for your starred repositories this week."
        body_html = """<html><body>
        <h2>Weekly Summary</h2>
        <p>No new releases or tags were detected for your starred repositories this week.</p>
        </body></html>"""
    else:
        subject = f"GitHub Stars Release Weekly Summary: {total_updates} update{'s' if total_updates != 1 else ''}"

        # Build text body
        body_text = f"Weekly Summary - {total_updates} update{'s' if total_updates != 1 else ''}\n\n"
        for repo_name, group in sorted(repo_groups.items()):
            body_text += f"  {repo_name} ({group['html_url']})\n"
            for evt in group["updates"]:
                body_text += f"    - {evt.title}\n"
            body_text += "\n"

        # Build HTML body
        body_html_parts = [
            "<html><body>",
            f"<h2>Weekly Summary</h2>",
            f"<p>{total_updates} update{'s' if total_updates != 1 else ''} this week</p>",
            "<hr>",
        ]
        for repo_name, group in sorted(repo_groups.items()):
            body_html_parts.append(f'<h3><a href="{group["html_url"]}">{repo_name}</a></h3>')
            body_html_parts.append("<ul>")
            for evt in group["updates"]:
                body_html_parts.append(f"<li>{evt.title}</li>")
            body_html_parts.append("</ul>")
        body_html_parts.append("</body></html>")
        body_html = "\n".join(body_html_parts)

    try:
        config = get_smtp_config(db)
        result = _send_email(config, subject, body_text, body_html)
        msg = f"Weekly summary sent: {total_updates} updates"
        add_log("INFO", msg, db=db)
        logger.info(msg)
        return {"sent": True, "message": msg, "updates": total_updates}
    except Exception as e:
        msg = f"Failed to send weekly summary: {e}"
        add_log("ERROR", msg, db=db)
        logger.exception("Failed to send weekly summary email")
        return {"sent": False, "message": msg, "updates": total_updates}


def _send_email(config: dict, subject: str, body_text: str, body_html: str) -> str:
    """Send an email using SMTP. Returns success message."""
    host = config["host"]
    port = int(config["port"])
    username = config["username"]
    password = config["password"]
    use_tls = config["use_tls"]
    from_addr = config["from_addr"]
    to_addr = config["to_addr"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr

    part1 = MIMEText(body_text, "plain", "utf-8")
    part2 = MIMEText(body_html, "html", "utf-8")
    msg.attach(part1)
    msg.attach(part2)

    if use_tls:
        # Use STARTTLS
        context = ssl.create_default_context()
        with smtplib.SMTP(host, port) as server:
            server.starttls(context=context)
            if username and password:
                server.login(username, password)
            server.send_message(msg)
    else:
        # Use SSL/TLS directly or unencrypted
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context) as server:
            if username and password:
                server.login(username, password)
            server.send_message(msg)

    return f"Email sent to {to_addr}"