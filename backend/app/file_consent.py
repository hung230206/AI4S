"""Per-upload processing acknowledgement, separate from optional external AI."""
from fastapi import Header
from .security import ApiError

FILE_NOTICE_VERSION = "files-2026-10-19-v1"


def require_file_consent(purpose):
    def check(x_processing_consent: str | None = Header(default=None)):
        expected = f"{purpose}:{FILE_NOTICE_VERSION}"
        if x_processing_consent != expected:
            raise ApiError("FILE_CONSENT_REQUIRED", "Cần chọn Đồng ý trong thông báo xử lý tệp trước khi tải lên.", 403)
        return expected
    return check
