import sys
import chromadb
from sentence_transformers import SentenceTransformer

DB_DIR = "chroma_db"
COLLECTION = "professor_reviews"

model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path=DB_DIR)
collection = client.get_collection(COLLECTION)


def search(query, k=5):
    q_emb = model.encode([query]).tolist()
    res = collection.query(query_embeddings=q_emb, n_results=k)
    print(f"\nQuery: {query}")
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        print(f"\n  (distance {dist:.3f}) [{meta['source']}]")
        print("  " + doc.replace("\n", "\n  "))


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "is Bierman a tough grader?"
    search(q)
