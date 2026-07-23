import chromadb

# PersistentClient ensures data writes directly to disk and survives app reboots
client = chromadb.PersistentClient(path="database/chroma")

# Create or fetch the specific collection for factory safety records
collection = client.get_or_create_collection("factory_incidents")

def add_incident(text, metadata):
    # Construct a unique primary key using timestamp and worker id to avoid duplicate rows
    doc_id = f"{metadata['timestamp']}_{metadata['worker_id']}"
    
    collection.add(
        documents=[text],
        metadatas=[metadata],
        ids=[doc_id]
    )