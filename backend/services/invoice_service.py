"""
Business logic for invoices: generating the invoice record and rendering a
PDF for it. Called by PaymentService right after a mock payment succeeds.
"""
import os
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from config.settings import settings
from models.booking import Booking
from models.invoice import Invoice
from models.payment import Payment
from repositories.payment_repository import InvoiceRepository
from utils.exceptions import NotFoundError

TAX_RATE = 0.12  # mock 12% GST


class InvoiceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = InvoiceRepository(db)

    def _next_invoice_number(self) -> str:
        year = datetime.now(timezone.utc).year
        sequence = self.repo.count_all() + 1
        return f"INV-{year}-{sequence:06d}"

    def generate_invoice(self, booking: Booking, payment: Payment) -> Invoice:
        subtotal = float(booking.total_amount)
        tax_amount = round(subtotal * TAX_RATE, 2)
        total_amount = round(subtotal + tax_amount, 2)

        invoice = Invoice(
            booking_id=booking.id,
            payment_id=payment.id,
            invoice_number=self._next_invoice_number(),
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
        )
        invoice = self.repo.create(invoice)

        pdf_path = self._render_pdf(invoice, booking, payment)
        invoice.pdf_path = pdf_path
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def _render_pdf(self, invoice: Invoice, booking: Booking, payment: Payment) -> str:
        dest_dir = os.path.join(settings.upload_dir, "invoices")
        os.makedirs(dest_dir, exist_ok=True)
        filename = f"{invoice.invoice_number}.pdf"
        filepath = os.path.join(dest_dir, filename)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "InvoiceTitle", parent=styles["Title"], fontSize=20, textColor=colors.HexColor("#34432F")
        )
        label_style = ParagraphStyle(
            "Label", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#77816F")
        )

        doc = SimpleDocTemplate(
            filepath, pagesize=A4, topMargin=24 * mm, bottomMargin=24 * mm, leftMargin=20 * mm, rightMargin=20 * mm
        )
        story = []

        story.append(Paragraph("RK Residency Hub", title_style))
        story.append(Paragraph("Property Management System — Invoice", label_style))
        story.append(Spacer(1, 16))

        header_table = Table(
            [
                ["Invoice Number", invoice.invoice_number],
                ["Issued", invoice.issued_at.strftime("%d %b %Y")],
                ["Billed To", booking.customer.full_name],
                ["Email", booking.customer.email],
            ],
            colWidths=[110, 350],
        )
        header_table.setStyle(
            TableStyle(
                [
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#77816F")),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(header_table)
        story.append(Spacer(1, 20))

        nights = (booking.check_out_date - booking.check_in_date).days
        line_items = [
            ["Description", "Nights", "Rate/night", "Amount"],
            [
                f"Room {booking.room.room_number} ({booking.check_in_date} to {booking.check_out_date})",
                str(nights),
                f"Rs. {float(booking.room.price_per_night):.2f}",
                f"Rs. {invoice.subtotal:.2f}",
            ],
            ["", "", "Subtotal", f"Rs. {invoice.subtotal:.2f}"],
            ["", "", "Tax (12%)", f"Rs. {invoice.tax_amount:.2f}"],
            ["", "", "Total", f"Rs. {invoice.total_amount:.2f}"],
        ]
        items_table = Table(line_items, colWidths=[260, 50, 90, 90])
        items_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1ECE1")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#CFC6B4")),
                    ("LINEABOVE", (0, -1), (-1, -1), 0.75, colors.HexColor("#34432F")),
                    ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(items_table)
        story.append(Spacer(1, 24))

        payment_method_label = getattr(payment.method, "value", payment.method)
        payment_note = Paragraph(
            f"Paid via {payment_method_label} — reference {payment.transaction_reference}", label_style
        )
        story.append(payment_note)

        doc.build(story)
        return f"/uploads/invoices/{filename}"

    def get_by_booking(self, booking_id: int) -> Invoice:
        invoice = self.repo.get_by_booking_id(booking_id)
        if invoice is None:
            raise NotFoundError("No invoice has been generated for this booking yet")
        return invoice
