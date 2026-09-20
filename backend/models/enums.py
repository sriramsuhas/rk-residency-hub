"""Enumerations shared across models, schemas, and services."""
import enum


class RoleName(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    RECEPTION = "RECEPTION"
    HOUSEKEEPING = "HOUSEKEEPING"
    OWNER = "OWNER"


class AvailabilityStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    BOOKED = "BOOKED"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"


class CleaningStatus(str, enum.Enum):
    CLEAN = "CLEAN"
    DIRTY = "DIRTY"
    IN_PROGRESS = "IN_PROGRESS"


class RoomMaintenanceFlag(str, enum.Enum):
    """Whether a room is currently flagged as under maintenance (Module 2's Room.maintenance_status)."""
    NONE = "NONE"
    UNDER_MAINTENANCE = "UNDER_MAINTENANCE"


class BookingStatus(str, enum.Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    CONFIRMED = "CONFIRMED"
    CHECKED_IN = "CHECKED_IN"
    CHECKED_OUT = "CHECKED_OUT"
    CANCELLED = "CANCELLED"


class PaymentMethod(str, enum.Enum):
    CASH = "CASH"
    UPI = "UPI"
    CARD = "CARD"


class PaymentStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    REFUNDED = "REFUNDED"


class MaintenanceCategory(str, enum.Enum):
    AC = "AC"
    WATER = "WATER"
    ELECTRICITY = "ELECTRICITY"
    WIFI = "WIFI"
    BATHROOM = "BATHROOM"
    FURNITURE = "FURNITURE"
    CLEANING = "CLEANING"
    OTHER = "OTHER"


class MaintenancePriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class MaintenanceRequestStatus(str, enum.Enum):
    """Lifecycle of a guest-raised maintenance request (Module 5)."""
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class NotificationType(str, enum.Enum):
    BOOKING = "BOOKING"
    PAYMENT = "PAYMENT"
    MAINTENANCE = "MAINTENANCE"
    SYSTEM = "SYSTEM"
