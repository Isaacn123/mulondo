import html
import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def _is_configured() -> bool:
    settings = get_settings()
    return bool(settings.brevo_api_key and settings.brevo_sender_email and settings.admin_notification_email)


def _send_email(*, to_email: str, to_name: str, subject: str, html_content: str) -> bool:
    settings = get_settings()
    if not _is_configured():
        logger.warning("Brevo email skipped — set BREVO_API_KEY, BREVO_SENDER_EMAIL, ADMIN_NOTIFICATION_EMAIL")
        return False

    payload = {
        "sender": {"name": settings.brevo_sender_name, "email": settings.brevo_sender_email},
        "to": [{"email": to_email, "name": to_name or to_email}],
        "subject": subject,
        "htmlContent": html_content,
    }
    headers = {"api-key": settings.brevo_api_key, "Content-Type": "application/json"}

    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(BREVO_API_URL, json=payload, headers=headers)
            response.raise_for_status()
        return True
    except Exception:
        logger.exception("Failed to send Brevo email to %s", to_email)
        return False


def _row(label: str, value: str) -> str:
    if not value:
        return ""
    return f"<tr><td style='padding:6px 12px;color:#666;'>{html.escape(label)}</td><td style='padding:6px 12px;'>{html.escape(value)}</td></tr>"


def notify_admin_contact_submission(data: dict) -> bool:
    settings = get_settings()
    rows = "".join(
        [
            _row("Name", data.get("name", "")),
            _row("Email", data.get("email", "")),
            _row("Country", data.get("country", "")),
            _row("Investor type", data.get("investor_type", "")),
            _row("Capital range", data.get("capital_range", "")),
            _row("Message", data.get("message", "")),
        ]
    )
    html_content = (
        "<h2>New investment review request</h2>"
        "<p>A visitor submitted the contact form on the public website.</p>"
        f"<table style='border-collapse:collapse;'>{rows}</table>"
        "<p>View all submissions in the admin dashboard.</p>"
    )
    return _send_email(
        to_email=settings.admin_notification_email,
        to_name="Admin",
        subject=f"New contact request — {data.get('name', 'Website visitor')}",
        html_content=html_content,
    )


def notify_visitor_contact_received(name: str, email: str) -> bool:
    html_content = (
        f"<p>Hi {html.escape(name)},</p>"
        "<p>Thank you for your confidential investment review request. "
        "We have received your message and will respond within one business day.</p>"
        "<p>Mulondo Daniel<br>Smart Investing · Wealth · Education</p>"
    )
    return _send_email(
        to_email=email,
        to_name=name,
        subject="We received your investment review request",
        html_content=html_content,
    )


def notify_admin_membership_request(data: dict) -> bool:
    settings = get_settings()
    rows = "".join(
        [
            _row("Name", data.get("name", "")),
            _row("Email", data.get("email", "")),
            _row("Phone", data.get("phone", "")),
            _row("Country", data.get("country", "")),
            _row("Tier", data.get("tier", "")),
            _row("Message", data.get("message", "")),
        ]
    )
    html_content = (
        "<h2>New membership request</h2>"
        "<p>A visitor submitted a membership enrollment request on the public website.</p>"
        f"<table style='border-collapse:collapse;'>{rows}</table>"
        "<p>View all requests in the admin dashboard.</p>"
    )
    return _send_email(
        to_email=settings.admin_notification_email,
        to_name="Admin",
        subject=f"New membership request — {data.get('name', 'Website visitor')}",
        html_content=html_content,
    )


def notify_visitor_membership_received(name: str, email: str, tier: str = "") -> bool:
    tier_line = f" for the <strong>{html.escape(tier)}</strong> track" if tier else ""
    html_content = (
        f"<p>Hi {html.escape(name)},</p>"
        f"<p>Thank you for your interest in the AI Certification Membership program{tier_line}. "
        "We have received your request and will follow up with next steps shortly.</p>"
        "<p>Mulondo Daniel<br>Smart Investing · Wealth · Education</p>"
    )
    return _send_email(
        to_email=email,
        to_name=name,
        subject="We received your membership request",
        html_content=html_content,
    )


def notify_admin_investor_message(investor_name: str, investor_email: str, body: str) -> bool:
    html_content = (
        "<h2>New investor message</h2>"
        f"<p><strong>{html.escape(investor_name)}</strong> ({html.escape(investor_email)}) sent a message from the investor portal.</p>"
        f"<blockquote style='border-left:3px solid #d4af37;padding-left:12px;color:#333;'>{html.escape(body)}</blockquote>"
        "<p>Reply in the admin dashboard under Investors.</p>"
    )
    settings = get_settings()
    return _send_email(
        to_email=settings.admin_notification_email,
        to_name="Admin",
        subject=f"Investor message — {investor_name}",
        html_content=html_content,
    )


def notify_investor_new_message(investor_name: str, investor_email: str, body: str) -> bool:
    html_content = (
        f"<p>Hi {html.escape(investor_name)},</p>"
        "<p>You have a new message from the Mulondo Daniel team in your investor portal:</p>"
        f"<blockquote style='border-left:3px solid #d4af37;padding-left:12px;color:#333;'>{html.escape(body)}</blockquote>"
        "<p>Sign in to your portal to reply and view member materials.</p>"
        "<p>Mulondo Daniel<br>Smart Investing · Wealth · Education</p>"
    )
    return _send_email(
        to_email=investor_email,
        to_name=investor_name,
        subject="New message in your investor portal",
        html_content=html_content,
    )
