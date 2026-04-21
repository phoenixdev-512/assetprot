import imagehash
from PIL import Image


def compute_phash(image: Image.Image) -> str:
    return str(imagehash.phash(image))


def compute_whash(image: Image.Image) -> str:
    return str(imagehash.whash(image))
