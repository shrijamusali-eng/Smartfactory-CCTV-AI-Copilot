import sys
import os

# Align your project folder structure paths
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from rag.ingest import collection

# 1. Print total count of auto-logged entries
print("--- ChromaDB Collection Count ---")
print(f"Total entries stored: {collection.count()}")

# 2. Peek at the first 3 actual logged violation sentences
print("\n--- Peeking at Top 3 Logged Sentences ---")
entries = collection.get(limit=3)
for i, doc in enumerate(entries.get('documents', [])):
    print(f"{i+1}. {doc}")