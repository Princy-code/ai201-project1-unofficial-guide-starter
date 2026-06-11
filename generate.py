import sys
import os
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

DB_DIR = "chroma_db"
COLLECTION = "professor_reviews"
LLM_MODEL = "llama-3.3-70b-versatile"

model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path=DB_DIR)
collection = client.get_collection(COLLECTION)
groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = (
    "You answer questions about SFSU professors using ONLY the student reviews "
    "provided in the context. Do not use any outside knowledge. If the reviews "
    "do not contain enough information to answer, say exactly: 'I don't have "
    "enough information on that.' When you answer, base every claim on the "
    "reviews and mention the professor by name. Be concise."
)


def retrieve(query, k=5):
    q_emb = model.encode([query]).tolist()
    res = collection.query(query_embeddings=q_emb, n_results=k)
    chunks = res["documents"][0]
    sources = sorted(set(m["source"] for m in res["metadatas"][0]))
    return chunks, sources


def answer(query, k=5):
    chunks, sources = retrieve(query, k)
    context = "\n\n".join(f"[Review {i+1}]\n{c}" for i, c in enumerate(chunks))
    user_msg = f"Context (student reviews):\n{context}\n\nQuestion: {query}"

    resp = groq.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0,
    )
    reply = resp.choices[0].message.content.strip()

    print(f"\nQuestion: {query}\n")
    print(f"Answer: {reply}\n")
    print(f"Sources: {', '.join(sources)}")


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "is Bierman a tough grader?"
    answer(q)
