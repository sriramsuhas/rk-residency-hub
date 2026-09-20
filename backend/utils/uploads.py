"""
Shared image-upload handling for the upload sites in the app
(room images, maintenance photos). Profile pictures were removed — users
are shown a fixed, role-based avatar instead (see RoleAvatar.jsx on the
frontend), not an uploaded image.

Security notes:
- The file extension is derived from the validated Content-Type, never from
  the client-supplied filename. Trusting `file.filename`'s extension would
  let a malicious upload write an arbitrary extension (e.g. a script) into
  a publicly-served static directory, since Content-Type headers and
  filenames are both entirely client-controlled and easy to spoof together.
- The saved filename is a fresh random UUID — the original filename is
  never used for anything, closing off path traversal via crafted names
  (e.g. "../../etc/passwd") entirely, not just sanitizing it.
- Size is capped by reading the full upload into memory and checking length
  against the configured limit before writing anything to disk.
"""
import os
import uuid

from fastapi import UploadFile

from config.settings import settings
from utils.exceptions import ValidationAppError

# Maps validated Content-Type to the extension we'll actually write with —
# this is the allowlist; nothing outside these three types is ever accepted.
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def save_uploaded_image(file: UploadFile, subfolder: str) -> str:
    """
    Validates and saves an uploaded image. Returns the public URL path
    (e.g. "/uploads/room_images/<uuid>.jpg") to store on the owning record.
    """
    extension = ALLOWED_IMAGE_TYPES.get(file.content_type)
    if extension is None:
        raise ValidationAppError("Only JPEG, PNG, or WEBP images are allowed")

    contents = file.file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise ValidationAppError(f"File exceeds {settings.max_upload_size_mb}MB limit")
    if len(contents) == 0:
        raise ValidationAppError("Uploaded file is empty")

    safe_name = f"{uuid.uuid4().hex}{extension}"
    dest_dir = os.path.join(settings.upload_dir, subfolder)
    os.makedirs(dest_dir, exist_ok=True)
    with open(os.path.join(dest_dir, safe_name), "wb") as f:
        f.write(contents)

    return f"/uploads/{subfolder}/{safe_name}"
