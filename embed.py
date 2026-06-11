import json
import chromadb
from sentence_transformers import SentenceTransformer

CHUNKS_FILE = "chunks.json"
DB_DIR = "chroma_db"
COLLECTION = "professor_reviews"
MODEL_NAME = "all-MiniLM-L6-v2"

print("Loading embedding model (first run downloads ~90MB)...")
model = SentenceTransformer(MODEL_NAME)

client = chromadb.PersistentClient(path=DB_DIR)
client.delete_collection(COLLECTION) if COLLECTION in [c.name for c in client.list_collections()] else None
collection = client.create_collection(COLLECTION)


def build():
    with open(CHUNKS_FILE, encoding="utf-8") as f:
        chunks = json.load(f)
    texts = [c["text"] for c in chunks]
    print(f"Embedding {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True).tolist()
    collection.add(
        ids=[c["id"] for c in chunks],
        documents=texts,
        embeddings=embeddings,
        metadatas=[c["metadata"] for c in chunks],
    )
    print(f"Stored {collection.count()} chunks in ChromaDB at {DB_DIR}/")


def search(query, k=5):
    q_emb = model.encode([query]).tolist()
    res = collection.query(query_embeddings=q_emb, n_results=k)
    print(f"\nQuery: {query}")
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        print(f"\n  (distance {dist:.3f}) [{meta['source']}]")
        print("  " + doc.replace("\n", "\n  "))


if __name__ == "__main__":
    build()
    print("\n" + "=" * 60)
    search("is Bierman a tough grader?")
    search("which professor is good for someone new to CS?")
