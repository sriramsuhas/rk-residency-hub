"""Tests for the shared, hardened upload utility."""
import io

import pytest
from fastapi import UploadFile

from utils.exceptions import ValidationAppError
from utils.uploads import save_uploaded_image


def _make_upload(filename: str, content_type: str, content: bytes) -> UploadFile:
    return UploadFile(filename=filename, file=io.BytesIO(content), headers={"content-type": content_type})


PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de"
    "0000000c4944415478da6360000002000155a5c9f10000000049454e44ae426082"
)


def test_saved_filename_never_uses_client_supplied_extension(tmp_path, monkeypatch):
    """
    A malicious filename should never influence what extension lands in the
    (publicly-served) uploads directory — the extension must come only from
    the validated Content-Type.
    """
    from config import settings as settings_module

    monkeypatch.setattr(settings_module.settings, "upload_dir", str(tmp_path))

    upload = _make_upload("shell.php", "image/jpeg", PNG_BYTES)
    url = save_uploaded_image(upload, "test_uploads")

    assert url.endswith(".jpg")
    assert ".php" not in url


def test_rejects_disallowed_content_type(tmp_path, monkeypatch):
    from config import settings as settings_module

    monkeypatch.setattr(settings_module.settings, "upload_dir", str(tmp_path))

    upload = _make_upload("payload.php", "application/x-php", b"<?php echo 'hi'; ?>")
    with pytest.raises(ValidationAppError):
        save_uploaded_image(upload, "test_uploads")


def test_rejects_oversized_file(tmp_path, monkeypatch):
    from config import settings as settings_module

    monkeypatch.setattr(settings_module.settings, "upload_dir", str(tmp_path))
    monkeypatch.setattr(settings_module.settings, "max_upload_size_mb", 0)  # anything is "too big"

    upload = _make_upload("photo.jpg", "image/jpeg", PNG_BYTES)
    with pytest.raises(ValidationAppError):
        save_uploaded_image(upload, "test_uploads")


def test_rejects_empty_file(tmp_path, monkeypatch):
    from config import settings as settings_module

    monkeypatch.setattr(settings_module.settings, "upload_dir", str(tmp_path))

    upload = _make_upload("empty.jpg", "image/jpeg", b"")
    with pytest.raises(ValidationAppError):
        save_uploaded_image(upload, "test_uploads")


def test_saved_filename_is_random_not_derived_from_input(tmp_path, monkeypatch):
    """Two uploads with the same filename must not collide or leak the original name."""
    from config import settings as settings_module

    monkeypatch.setattr(settings_module.settings, "upload_dir", str(tmp_path))

    upload1 = _make_upload("photo.jpg", "image/jpeg", PNG_BYTES)
    upload2 = _make_upload("photo.jpg", "image/jpeg", PNG_BYTES)
    url1 = save_uploaded_image(upload1, "test_uploads")
    url2 = save_uploaded_image(upload2, "test_uploads")

    assert url1 != url2
    assert "photo" not in url1
