"""The constrained cloud OCR budget must not allow unbounded workers."""
import pytest
from pydantic import ValidationError
from app.config import Settings


def test_ocr_concurrency_is_bounded():
    for limit in (1, 2):
        assert Settings(ocr_max_workers=limit).ocr_max_workers == limit
    for limit in (0, -1, 3, 100):
        with pytest.raises(ValidationError):
            Settings(ocr_max_workers=limit)
