import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


def init_collection(client: QdrantClient, collection_name: str, vector_size: int = 512) -> None:
    existing = {c.name for c in client.get_collections().collections}
    if collection_name not in existing:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )


def upsert_embedding(
    client: QdrantClient,
    collection_name: str,
    asset_id: str,
    org_id: str,
    vector: list[float],
) -> str:
    point_id = str(uuid.uuid4())
    client.upsert(
        collection_name=collection_name,
        points=[
            PointStruct(
                id=point_id,
                vector=vector,
                payload={"asset_id": asset_id, "org_id": org_id},
            )
        ],
    )
    return point_id


def search_similar(
    client: QdrantClient,
    collection_name: str,
    vector: list[float],
    score_threshold: float,
    limit: int = 10,
) -> list[dict]:
    results = client.search(
        collection_name=collection_name,
        query_vector=vector,
        score_threshold=score_threshold,
        limit=limit,
    )
    return [{"asset_id": r.payload["asset_id"], "score": r.score} for r in results]
