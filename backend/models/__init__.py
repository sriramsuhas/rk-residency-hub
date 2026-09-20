"""
Importing every model here ensures they're all registered on Base.metadata
before create_all() or any relationship string-lookup runs.
"""
from models.role import Role  # noqa: F401
from models.user import User  # noqa: F401
from models.token import RefreshToken, PasswordResetToken  # noqa: F401
from models.audit_log import AuditLog  # noqa: F401
from models.floor import Floor  # noqa: F401
from models.room_type import RoomType  # noqa: F401
from models.amenity import Amenity  # noqa: F401
from models.room import Room, room_amenities  # noqa: F401
from models.room_image import RoomImage  # noqa: F401
from models.booking import Booking  # noqa: F401
from models.payment import Payment  # noqa: F401
from models.invoice import Invoice  # noqa: F401
from models.maintenance_request import MaintenanceRequest  # noqa: F401
from models.review import Review  # noqa: F401
from models.notification import Notification  # noqa: F401
