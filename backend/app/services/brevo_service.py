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


def notify_admin_investor_message(investor_name: str, investor_email: str, body: str, *, portal_label: str = "investor portal") -> bool:
    html_content = (
        f"<h2>New message from {html.escape(portal_label)}</h2>"
        f"<p><strong>{html.escape(investor_name)}</strong> ({html.escape(investor_email)}) sent a message.</p>"
        f"<blockquote style='border-left:3px solid #d4af37;padding-left:12px;color:#333;'>{html.escape(body)}</blockquote>"
        "<p>Reply in the admin dashboard under Investors.</p>"
    )
    settings = get_settings()
    return _send_email(
        to_email=settings.admin_notification_email,
        to_name="Admin",
        subject=f"Portal message — {investor_name}",
        html_content=html_content,
    )


def notify_investor_new_message(investor_name: str, investor_email: str, body: str, *, portal_label: str = "investor dashboard") -> bool:
    html_content = (
        f"<p>Hi {html.escape(investor_name)},</p>"
        f"<p>You have a new message from the Mulondo Daniel team in your {html.escape(portal_label)}:</p>"
        f"<blockquote style='border-left:3px solid #d4af37;padding-left:12px;color:#333;'>{html.escape(body)}</blockquote>"
        "<p>Sign in to your portal to reply.</p>"
        "<p>Mulondo Daniel<br>Smart Investing · Wealth · Education</p>"
    )
    return _send_email(
        to_email=investor_email,
        to_name=investor_name,
        subject=f"New message in your {portal_label}",
        html_content=html_content,
    )


def notify_investor_registration_welcome(investor_name: str, investor_email: str, login_url: str) -> bool:
    html_content = (
        f"<p>Hi {html.escape(investor_name)},</p>"
        "<p>Welcome to the Mulondo Daniel investor dashboard. Your account is ready.</p>"
        "<p>Sign in to access member materials, portfolio updates, and direct messaging with our team.</p>"
        f"<p><a href=\"{html.escape(login_url)}\">Sign in to your investor dashboard</a></p>"
        "<p>Mulondo Daniel<br>Smart Investing · Wealth · Education</p>"
    )
    return _send_email(
        to_email=investor_email,
        to_name=investor_name,
        subject="Welcome to the Mulondo Daniel investor dashboard",
        html_content=html_content,
    )


def notify_mentee_registration_welcome(mentee_name: str, mentee_email: str, login_url: str) -> bool:
    html_content = (
        f"<p>Hi {html.escape(mentee_name)},</p>"
        "<p>Welcome to AISkills — Build AI-Powered Trading Skills Mentorship.</p>"
        "<p>Sign in to access the structured training plan and message your mentor.</p>"
        f"<p><a href=\"{html.escape(login_url)}\">Sign in to AISkills</a></p>"
        "<p>Mulondo Daniel<br>Smart Investing · Wealth · Education</p>"
    )
    return _send_email(
        to_email=mentee_email,
        to_name=mentee_name,
        subject="Welcome to AISkills — Build AI-Powered Trading Skills Mentorship",
        html_content=html_content,
    )


def notify_admin_new_investor_registration(investor_name: str, investor_email: str) -> bool:
    settings = get_settings()
    rows = "".join(
        [
            _row("Name", investor_name),
            _row("Email", investor_email),
            _row("Portal", "Investor dashboard"),
        ]
    )
    html_content = (
        "<h2>New investor registration</h2>"
        "<p>A new investor account was created on the public website.</p>"
        f"<table style='border-collapse:collapse;'>{rows}</table>"
        "<p>Review the account in the admin dashboard under Investors.</p>"
    )
    return _send_email(
        to_email=settings.admin_notification_email,
        to_name="Admin",
        subject=f"New investor registered — {investor_name}",
        html_content=html_content,
    )


def notify_admin_new_mentee_registration(mentee_name: str, mentee_email: str) -> bool:
    settings = get_settings()
    rows = "".join(
        [
            _row("Name", mentee_name),
            _row("Email", mentee_email),
            _row("Portal", "AISkills"),
        ]
    )
    html_content = (
        "<h2>New AISkills registration</h2>"
        "<p>A new mentee registered for AISkills — Build AI-Powered Trading Skills Mentorship.</p>"
        f"<table style='border-collapse:collapse;'>{rows}</table>"
        "<p>Review the account in the admin dashboard under Investors.</p>"
    )
    return _send_email(
        to_email=settings.admin_notification_email,
        to_name="Admin",
        subject=f"New AISkills mentee — {mentee_name}",
        html_content=html_content,
    )


def notify_admin_consultation_request(data: dict) -> bool:
    settings = get_settings()
    rows = "".join(
        [
            _row("Name", data.get("name", "")),
            _row("Email", data.get("email", "")),
            _row("Phone", data.get("phone", "")),
            _row("Event", data.get("event_name", "")),
            _row("Scheduled", data.get("scheduled_at", "")),
            _row("Source", data.get("source", "")),
            _row("Notes", data.get("message", "")),
        ]
    )
    html_content = (
        "<h2>New consultation request</h2>"
        "<p>A visitor requested or booked a consultation on the public website.</p>"
        f"<table style='border-collapse:collapse;'>{rows}</table>"
        "<p>View all consultation requests in the admin dashboard.</p>"
    )
    return _send_email(
        to_email=settings.admin_notification_email,
        to_name="Admin",
        subject=f"New consultation — {data.get('name', 'Website visitor')}",
        html_content=html_content,
    )


def notify_visitor_consultation_received(
    name: str,
    email: str,
    event_name: str = "",
    scheduled_at=None,
) -> bool:
    when_line = ""
    if scheduled_at is not None:
        try:
            when_line = f" for <strong>{scheduled_at.strftime('%d %b %Y at %H:%M UTC')}</strong>"
        except Exception:
            when_line = ""
    event_line = f" ({html.escape(event_name)})" if event_name else ""
    html_content = (
        f"<p>Hi {html.escape(name)},</p>"
        f"<p>Thank you — we received your consultation request{event_line}{when_line}.</p>"
        "<p>Our team will confirm details or follow up within one business day.</p>"
        "<p>Mulondo Daniel<br>Smart Investing · Wealth · Education</p>"
    )
    return _send_email(
        to_email=email,
        to_name=name,
        subject="We received your consultation request",
        html_content=html_content,
    )
