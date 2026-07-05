import os
import time
from typing import List

import httpx

HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
HF_MODEL_URL = "https://router.huggingface.co/hf-inference/models/BAAI/bge-small-en-v1.5/pipeline/feature-extraction"
VECTOR_DIM = 384
BATCH_SIZE = 100
MAX_RETRIES = 3
RETRY_DELAY = 10  # seconds — model may need warm-up on first call


def embed_batch(texts: List[str]) -> List[List[float]]:
    """Embed all texts in batches of BATCH_SIZE. Returns one vector per text."""
    if not texts:
        return []

    all_vectors: List[List[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        vectors = _call_hf(batch)
        all_vectors.extend(vectors)

    return all_vectors


def _call_hf(texts: List[str]) -> List[List[float]]:
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {"inputs": texts, "options": {"wait_for_model": True}}

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"Calling HF API (attempt {attempt}/{MAX_RETRIES})...")
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(HF_API_URL, headers=headers, json=payload)

        if resp.status_code == 200:
            data = resp.json()
            # HF returns [[float,...], ...] for a list input
            # but may wrap in an extra list for some models — flatten if needed
            if data and isinstance(data[0], list) and isinstance(data[0][0], list):
                data = [item[0] for item in data]
            return data

        if resp.status_code == 503:
            # Model loading — wait and retry
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue

        resp.raise_for_status()

    raise RuntimeError(f"HF embedding failed after {MAX_RETRIES} attempts")


# Allow overriding the URL for local/mock testing
HF_API_URL = os.getenv("HF_API_URL", HF_MODEL_URL)
