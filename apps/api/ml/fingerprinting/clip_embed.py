import torch
from PIL import Image


def compute_clip_embedding(image: Image.Image, model, processor) -> list[float]:
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        features = model.get_image_features(**inputs)
    return features[0].cpu().numpy().tolist()
