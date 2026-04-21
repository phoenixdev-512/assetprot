import pytest
from PIL import Image


def _make_test_image(width: int = 64, height: int = 64) -> Image.Image:
    img = Image.new("RGB", (width, height), color=(128, 64, 32))
    return img


# ── perceptual hash ───────────────────────────────────────────────────────────

def test_compute_phash_returns_hex_string():
    from ml.fingerprinting.perceptual_hash import compute_phash
    img = _make_test_image()
    result = compute_phash(img)
    assert isinstance(result, str)
    assert len(result) == 16


def test_compute_whash_returns_hex_string():
    from ml.fingerprinting.perceptual_hash import compute_whash
    img = _make_test_image()
    result = compute_whash(img)
    assert isinstance(result, str)
    assert len(result) == 16


def test_identical_images_have_same_phash():
    from ml.fingerprinting.perceptual_hash import compute_phash
    img = _make_test_image()
    assert compute_phash(img) == compute_phash(img)


def test_different_images_have_different_phash():
    from ml.fingerprinting.perceptual_hash import compute_phash
    import numpy as np
    # Use images with different frequency content, not just different solid colors
    arr1 = np.zeros((64, 64, 3), dtype=np.uint8)
    arr1[::2, ::2] = 255  # checkerboard
    img1 = Image.fromarray(arr1)
    arr2 = np.zeros((64, 64, 3), dtype=np.uint8)
    arr2[:32, :] = 255  # top half white
    img2 = Image.fromarray(arr2)
    assert compute_phash(img1) != compute_phash(img2)
