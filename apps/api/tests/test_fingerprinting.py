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


# ── CLIP embedding ────────────────────────────────────────────────────────────

def test_compute_clip_embedding_returns_512_floats():
    from unittest.mock import MagicMock
    import torch
    from ml.fingerprinting.clip_embed import compute_clip_embedding

    mock_model = MagicMock()
    mock_processor = MagicMock()
    mock_processor.return_value = {"pixel_values": torch.zeros(1, 3, 224, 224)}
    mock_model.get_image_features.return_value = torch.randn(1, 512)

    img = _make_test_image()
    result = compute_clip_embedding(img, mock_model, mock_processor)

    assert isinstance(result, list)
    assert len(result) == 512
    assert all(isinstance(v, float) for v in result)


def test_compute_clip_embedding_calls_processor_with_image():
    from unittest.mock import MagicMock
    import torch
    from ml.fingerprinting.clip_embed import compute_clip_embedding

    mock_model = MagicMock()
    mock_processor = MagicMock()
    mock_processor.return_value = {"pixel_values": torch.zeros(1, 3, 224, 224)}
    mock_model.get_image_features.return_value = torch.randn(1, 512)

    img = _make_test_image()
    compute_clip_embedding(img, mock_model, mock_processor)

    mock_processor.assert_called_once_with(images=img, return_tensors="pt")
