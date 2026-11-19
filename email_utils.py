"""
Email dispatching utilities for AI Doubt Solver.
Provides secure password reset delivery via SMTP, with console-print and
UI banner fallback in DEV_MODE.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Tuple


def is_dev_mode() -> bool:
    """Check if the application is running in development mode."""
    dev_str = os.getenv("DEV_MODE", "true").strip().lower()
    return dev_str in ("true", "1", "yes")


def send_password_reset_email(
    to_email: str,
    username: str,
    raw_token: str,
    valid_minutes: int = 20
) -> Tuple[bool, str, str]:
    """
    Send password reset email to user.
    Returns (success, status_message, reset_link).
    In DEV_MODE or if SMTP is not configured, prints the reset link to console.
    """
    base_url = os.getenv("APP_BASE_URL", "http://localhost:8501").rstrip("/")
    reset_link = f"{base_url}/?token={raw_token}&page=reset"

    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_from_name = os.getenv("SMTP_FROM_NAME", "AI Doubt Solver Support")

    dev_mode = is_dev_mode()

    # Console output for testing and development
    console_msg = (
        f"\n{'='*60}\n"
        f"[DEV MODE / CONSOLE] PASSWORD RESET REQUEST\n"
        f"Recipient: {to_email} ({username})\n"
        f"Token: {raw_token}\n"
        f"Reset Link: {reset_link}\n"
        f"Expires In: {valid_minutes} minutes\n"
        f"{'='*60}\n"
    )
    print(console_msg)

    # If SMTP is not configured, rely on console / dev mode fallback
    if not smtp_host or not smtp_user or not smtp_password:
        return True, "Reset link generated and printed to console (DEV MODE: SMTP not configured).", reset_link

    # Attempt to send real email via SMTP
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Reset Your AI Doubt Solver Password"
        msg["From"] = f"{smtp_from_name} <{smtp_user}>"
        msg["To"] = to_email

        text_content = (
            f"Hello {username},\n\n"
            f"We received a request to reset your password for AI Doubt Solver.\n"
            f"Click the link below (valid for {valid_minutes} minutes):\n\n"
            f"{reset_link}\n\n"
            f"Your reset code is: {raw_token}\n\n"
            f"If you did not request this, please ignore this email. Your account remains safe.\n\n"
            f"— The AI Doubt Solver Team"
        )

        html_content = f"""
        <html>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f7f9fc; padding: 25px; color: #333;">
            <div style="max-width: 540px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-top: 5px solid #4361ee;">
                <h2 style="color: #4361ee; margin-top: 0;">AI Doubt Solver</h2>
                <p>Hello <strong>{username}</strong>,</p>
                <p>We received a request to reset your password. Click the button below to set a new password:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" style="background-color: #4361ee; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px; display: inline-block;">Reset My Password</a>
                </div>
                <p style="font-size: 14px; color: #666;">Or copy and paste this link in your browser:</p>
                <p style="font-size: 13px; background: #eef2f7; padding: 10px; border-radius: 5px; word-break: break-all;"><a href="{reset_link}">{reset_link}</a></p>
                <p style="font-size: 13px; color: #555;">Alternatively, enter this Reset Code on the reset page: <code>{raw_token}</code></p>
                <p style="font-size: 13px; color: #e63946;"><strong>Note:</strong> This link will expire in {valid_minutes} minutes and can only be used once.</p>
                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 25px 0;" />
                <p style="font-size: 12px; color: #8d99ae;">If you did not request a password reset, you can safely ignore this email. Your account remains completely secure.</p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10.0)
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, [to_email], msg.as_string())
        server.quit()

        return True, "Password reset email sent successfully.", reset_link
    except Exception as e:
        print(f"[ERROR] Failed to send email via SMTP: {e}")
        # In dev mode, return the link anyway so testing is not blocked
        if dev_mode:
            return True, f"SMTP failed ({e}), but reset link is available in DEV MODE console.", reset_link
        return False, f"Failed to send email: {str(e)}", reset_link
