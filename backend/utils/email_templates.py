"""
Plain-text content for every transactional email RK Residency Hub sends.
Kept as simple (subject, body) tuple-returning functions - no template
engine, since the content is short and doesn't need one.
"""
from config.settings import settings


def welcome_email(full_name: str) -> tuple[str, str]:
    subject = "Welcome to RK Residency Hub"
    body = (
        f"Hi {full_name},\n\n"
        "Your RK Residency Hub account has been created. You can now browse "
        "rooms and book your stay any time.\n\n"
        "- RK Residency Hub"
    )
    return subject, body


def password_reset_email(full_name: str, reset_token: str) -> tuple[str, str]:
    reset_link = f"{settings.frontend_base_url}/reset-password?token={reset_token}"
    subject = "Reset your RK Residency Hub password"
    body = (
        f"Hi {full_name},\n\n"
        "We received a request to reset your password. Click the link below "
        "to choose a new one. This link expires in 1 hour.\n\n"
        f"{reset_link}\n\n"
        "If you didn't request this, you can safely ignore this email.\n\n"
        "- RK Residency Hub"
    )
    return subject, body


def booking_confirmation_email(
    full_name: str, room_number: str, check_in: str, check_out: str, total_amount: float
) -> tuple[str, str]:
    subject = "Your RK Residency Hub booking is confirmed"
    body = (
        f"Hi {full_name},\n\n"
        f"Your booking for Room {room_number} is confirmed.\n\n"
        f"Check-in: {check_in}\n"
        f"Check-out: {check_out}\n"
        f"Total paid: Rs. {total_amount:.2f}\n\n"
        "You can view your booking and download the invoice any time from "
        "My Bookings.\n\n"
        "- RK Residency Hub"
    )
    return subject, body


def booking_cancellation_email(full_name: str, room_number: str, check_in: str, check_out: str) -> tuple[str, str]:
    subject = "Your RK Residency Hub booking was cancelled"
    body = (
        f"Hi {full_name},\n\n"
        f"Your booking for Room {room_number} ({check_in} to {check_out}) has "
        "been cancelled.\n\n"
        "If you didn't request this, please contact the front desk.\n\n"
        "- RK Residency Hub"
    )
    return subject, body


def maintenance_created_email(full_name: str, category: str, room_number: str) -> tuple[str, str]:
    subject = "We received your maintenance request"
    body = (
        f"Hi {full_name},\n\n"
        f"We've received your {category} request for Room {room_number}. "
        "Our team will be in touch shortly.\n\n"
        "- RK Residency Hub"
    )
    return subject, body


def maintenance_assigned_email(full_name: str, category: str, room_number: str) -> tuple[str, str]:
    subject = "Your maintenance request is being handled"
    body = (
        f"Hi {full_name},\n\n"
        f"Your {category} request for Room {room_number} has been assigned "
        "to a staff member and will be worked on shortly.\n\n"
        "- RK Residency Hub"
    )
    return subject, body


def maintenance_completed_email(full_name: str, category: str, room_number: str) -> tuple[str, str]:
    subject = "Your maintenance request has been resolved"
    body = (
        f"Hi {full_name},\n\n"
        f"Your {category} request for Room {room_number} has been marked "
        "complete. Let us know if anything is still not right.\n\n"
        "- RK Residency Hub"
    )
    return subject, body
