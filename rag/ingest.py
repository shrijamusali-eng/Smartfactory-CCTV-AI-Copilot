import os
import shutil
import chromadb
from chromadb.config import Settings

CHROMA_PATH = "database/chroma"
os.makedirs(CHROMA_PATH, exist_ok=True)

def _init_client_and_collection():
    client = chromadb.PersistentClient(
        path=CHROMA_PATH,
        settings=Settings(anonymized_telemetry=False)
    )
    collection = client.get_or_create_collection(name="factory_incidents")
    return client, collection

try:
    client, collection = _init_client_and_collection()
except Exception as e:
    print(f"ChromaDB error detected ({e}), wiping storage and recreating...")
    try:
        if os.path.exists(CHROMA_PATH):
            shutil.rmtree(CHROMA_PATH)
        os.makedirs(CHROMA_PATH, exist_ok=True)
        client, collection = _init_client_and_collection()
    except Exception as e2:
        raise RuntimeError(
            f"ChromaDB failed to recover after wipe: {e2}"
        ) from e2

def add_incident(text, metadata):
    doc_id = f"{metadata['timestamp']}_{metadata['worker_id']}"
    collection.add(
        documents=[text],
        metadatas=[metadata],
        ids=[doc_id],
    )