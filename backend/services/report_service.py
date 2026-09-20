"""
Business logic for report generation: turns repository query results into
plain table rows, then hands off to the shared CSV/PDF builders. Each
generate_* method returns (bytes, media_type, filename) ready for a route
to stream back as a download.
"""
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from repositories.report_repository import ReportRepository
from utils.enum_utils import status_label
from utils.report_builder import build_csv, build_pdf

CSV_MEDIA_TYPE = "text/csv"
PDF_MEDIA_TYPE = "application/pdf"


class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ReportRepository(db)

    def _render(self, fmt, title, headers, rows, date_from, date_to, summary_line=None):
        if fmt == "pdf":
            content = build_pdf(title, headers, rows, date_from=date_from, date_to=date_to, summary_line=summary_line)
            return content, PDF_MEDIA_TYPE, "pdf"
        content = build_csv(headers, rows)
        return content, CSV_MEDIA_TYPE, "csv"

    def revenue_report(self, date_from: date, date_to: date, fmt: str):
        payments = self.repo.payments_in_range(date_from, date_to)
        headers = ["Date", "Booking ID", "Room", "Customer", "Method", "Amount", "Status"]
        rows = [
            [
                p.paid_at.strftime("%Y-%m-%d"),
                str(p.booking_id),
                p.booking.room.room_number,
                p.booking.customer.full_name,
                status_label(p.method),
                f"{float(p.amount):.2f}",
                status_label(p.status),
            ]
            for p in payments
        ]
        total = sum(float(p.amount) for p in payments if status_label(p.status) == "SUCCESS")
        summary = f"Total revenue: Rs. {total:.2f}"
        content, media_type, ext = self._render(fmt, "Revenue Report", headers, rows, date_from, date_to, summary)
        return content, media_type, f"revenue-report-{date_from}-to-{date_to}.{ext}"

    def booking_report(self, date_from: date, date_to: date, status_filter: str | None, fmt: str):
        bookings = self.repo.bookings_in_range(date_from, date_to, status_filter)
        headers = ["Booking ID", "Customer", "Room", "Check-in", "Check-out", "Status", "Total Amount"]
        rows = [
            [
                str(b.id),
                b.customer.full_name,
                b.room.room_number,
                b.check_in_date.isoformat(),
                b.check_out_date.isoformat(),
                status_label(b.status),
                f"{float(b.total_amount):.2f}",
            ]
            for b in bookings
        ]
        summary = f"Total bookings: {len(bookings)}"
        content, media_type, ext = self._render(fmt, "Booking Report", headers, rows, date_from, date_to, summary)
        return content, media_type, f"booking-report-{date_from}-to-{date_to}.{ext}"

    def maintenance_report(self, date_from: date, date_to: date, status_filter: str | None, fmt: str):
        requests_ = self.repo.maintenance_in_range(date_from, date_to, status_filter)
        headers = ["Request ID", "Room", "Category", "Priority", "Status", "Assigned To", "Created", "Completed"]
        rows = []
        for r in requests_:
            rows.append(
                [
                    str(r.id),
                    r.room.room_number,
                    status_label(r.category),
                    status_label(r.priority),
                    status_label(r.status),
                    r.assigned_staff.full_name if r.assigned_staff else "\u2014",
                    r.created_at.strftime("%Y-%m-%d"),
                    r.completed_at.strftime("%Y-%m-%d") if r.completed_at else "\u2014",
                ]
            )
        summary = f"Total requests: {len(requests_)}"
        content, media_type, ext = self._render(fmt, "Maintenance Report", headers, rows, date_from, date_to, summary)
        return content, media_type, f"maintenance-report-{date_from}-to-{date_to}.{ext}"

    def occupancy_report(self, date_from: date, date_to: date, fmt: str):
        daily = self.repo.occupancy_by_day(date_from, date_to)
        headers = ["Date", "Occupied Rooms", "Active Rooms", "Occupancy %"]
        rows = [
            [
                d.isoformat(),
                str(occupied),
                str(active),
                f"{round((occupied / active) * 100, 1) if active else 0}%",
            ]
            for d, occupied, active in daily
        ]
        avg_occupancy = (
            round(sum((o / a) * 100 for _, o, a in daily if a) / len(daily), 1) if daily else 0
        )
        summary = f"Average occupancy: {avg_occupancy}%"
        content, media_type, ext = self._render(fmt, "Occupancy Report", headers, rows, date_from, date_to, summary)
        return content, media_type, f"occupancy-report-{date_from}-to-{date_to}.{ext}"

    def customer_report(self, fmt: str):
        summary_rows = self.repo.customer_summary()
        headers = ["Customer ID", "Name", "Email", "Phone", "Registered", "Total Bookings", "Total Spent"]
        rows = [
            [
                str(c.id),
                c.full_name,
                c.email,
                c.phone or "\u2014",
                c.created_at.strftime("%Y-%m-%d"),
                str(bookings),
                f"{spent:.2f}",
            ]
            for c, bookings, spent in summary_rows
        ]
        summary = f"Total customers: {len(summary_rows)}"
        today = datetime.now(timezone.utc).date()
        content, media_type, ext = self._render(fmt, "Customer Report", headers, rows, None, None, summary)
        return content, media_type, f"customer-report-{today}.{ext}"
