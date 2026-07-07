"""Email (SMTP) notification channel."""

import html
import logging
import smtplib
import ssl
from datetime import UTC, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy.orm import Session

from app.models import Event, Repo
from app.services.logs import add_log
from app.services.notifiers.base import BaseNotifier
from app.services.settings import get_setting, set_setting, validate_port

logger = logging.getLogger(__name__)


class EmailNotifier(BaseNotifier):
    """Send notifications via SMTP email."""

    @property
    def name(self) -> str:
        return "email"

    @property
    def display_name(self) -> str:
        return "Email (SMTP)"

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------

    def _config(self, db: Session) -> dict:
        return {
            "host": get_setting(db, "smtp_host", ""),
            "port": get_setting(db, "smtp_port", "587"),
            "username": get_setting(db, "smtp_username", ""),
            "password": get_setting(db, "smtp_password", ""),
            "use_tls": get_setting(db, "smtp_use_tls", "true").lower() == "true",
            "from_addr": get_setting(db, "smtp_from_addr", ""),
            "to_addr": get_setting(db, "smtp_to_addr", ""),
        }

    def is_configured(self, db: Session) -> bool:
        cfg = self._config(db)
        return bool(cfg["host"] and cfg["from_addr"] and cfg["to_addr"])

    def get_settings(self, db: Session) -> dict:
        return {
            "smtp_host": get_setting(db, "smtp_host", ""),
            "smtp_port": get_setting(db, "smtp_port", "587"),
            "smtp_username": get_setting(db, "smtp_username", ""),
            "smtp_password_set": bool(get_setting(db, "smtp_password", "")),
            "smtp_use_tls": get_setting(db, "smtp_use_tls", "true"),
            "smtp_from_addr": get_setting(db, "smtp_from_addr", ""),
            "smtp_to_addr": get_setting(db, "smtp_to_addr", ""),
            "email_configured": self.is_configured(db),
        }

    def save_settings(self, db: Session, data: dict[str, str]) -> None:
        set_setting(db, "smtp_host", data.get("smtp_host", ""))
        set_setting(db, "smtp_port", data.get("smtp_port", "587"))
        set_setting(db, "smtp_username", data.get("smtp_username", ""))
        pw = data.get("smtp_password", "")
        if pw:
            set_setting(db, "smtp_password", pw, secret=True)
        set_setting(db, "smtp_use_tls", data.get("smtp_use_tls", "true"))
        set_setting(db, "smtp_from_addr", data.get("smtp_from_addr", ""))
        set_setting(db, "smtp_to_addr", data.get("smtp_to_addr", ""))

    # ------------------------------------------------------------------
    # Sending
    # ------------------------------------------------------------------

    def send_test(self, db: Session) -> dict:
        cfg = self._config(db)
        if not cfg["host"] or not cfg["from_addr"] or not cfg["to_addr"]:
            return {"success": False, "message": "SMTP not fully configured"}

        subject = "GitHub Stars Release Watcher - Test Email"
        body_text = (
            "This is a test email from GitHub Stars Release Watcher.\n\n"
            "If you received this, email configuration is working correctly."
        )
        body_html = """<html><body>
        <h2>Test Email</h2>
        <p>This is a test email from <strong>GitHub Stars Release Watcher</strong>.</p>
        <p>If you received this, email configuration is working correctly.</p>
        </body></html>"""

        try:
            self._send(cfg, subject, body_text, body_html)
            return {"success": True, "message": f"Email sent to {cfg['to_addr']}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def send_weekly_summary(self, db: Session, events: list | None = None) -> dict:
        if not self.is_configured(db):
            msg = "Weekly summary skipped: email not configured"
            add_log("WARNING", msg, db=db)
            logger.warning(msg)
            return {"sent": False, "message": msg, "updates": 0}

        if events is None:
            week_ago = datetime.now(UTC) - timedelta(days=7)
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

        # Group by repo
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
            body_text = f"Weekly Summary - {total_updates} update{'s' if total_updates != 1 else ''}\n\n"
            for repo_name, group in sorted(repo_groups.items()):
                body_text += f"  {repo_name} ({group['html_url']})\n"
                for evt in group["updates"]:
                    body_text += f"    - {evt.title}\n"
                body_text += "\n"

            html_parts = [
                "<html><body>",
                "<h2>Weekly Summary</h2>",
                f"<p>{total_updates} update{'s' if total_updates != 1 else ''} this week</p>",
                "<hr>",
            ]
            for repo_name, group in sorted(repo_groups.items()):
                safe_url = html.escape(group["html_url"], quote=True)
                safe_name = html.escape(repo_name)
                html_parts.append(f'<h3><a href="{safe_url}">{safe_name}</a></h3>')
                html_parts.append("<ul>")
                for evt in group["updates"]:
                    html_parts.append(f"<li>{html.escape(evt.title)}</li>")
                html_parts.append("</ul>")
            html_parts.append("</body></html>")
            body_html = "\n".join(html_parts)

        try:
            cfg = self._config(db)
            self._send(cfg, subject, body_text, body_html)
            msg = f"Weekly summary sent: {total_updates} updates"
            add_log("INFO", msg, db=db)
            logger.info(msg)
            return {"sent": True, "message": msg, "updates": total_updates}
        except Exception as e:
            msg = f"Failed to send weekly summary: {e}"
            add_log("ERROR", msg, db=db)
            logger.exception("Failed to send weekly summary email")
            return {"sent": False, "message": msg, "updates": total_updates}

    # ------------------------------------------------------------------
    # Low-level SMTP send
    # ------------------------------------------------------------------

    @staticmethod
    def _send(cfg: dict, subject: str, body_text: str, body_html: str) -> str:
        host = cfg["host"]
        port = int(cfg["port"])
        username = cfg["username"]
        password = cfg["password"]
        use_tls = cfg["use_tls"]
        from_addr = cfg["from_addr"]
        to_addr = cfg["to_addr"]

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_addr

        msg.attach(MIMEText(body_text, "plain", "utf-8"))
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        context = ssl.create_default_context()
        if use_tls:
            with smtplib.SMTP(host, port) as server:
                server.starttls(context=context)
                if username and password:
                    server.login(username, password)
                server.send_message(msg)
        else:
            logger.warning("Sending email without TLS — password transmitted in plaintext")
            with smtplib.SMTP(host, port) as server:
                if username and password:
                    server.login(username, password)
                server.send_message(msg)

        return f"Email sent to {to_addr}"
