from fastapi import FastAPI
from qdrant_client import QdrantClient

from core.config import settings
from ml.qdrant_store import init_collection


def load_models(app: FastAPI) -> None:
    from transformers import CLIPModel, CLIPProcessor

    app.state.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    app.state.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    app.state.clip_model.eval()

    qdrant = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    init_collection(qdrant, settings.qdrant_collection, vector_size=512)
    app.state.qdrant = qdrant
