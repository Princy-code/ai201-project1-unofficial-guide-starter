import os
import chromadb
import gradio as gr
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


def ask(question):
    if not question.strip():
        return "Type a question above.", ""

    q_emb = model.encode([question]).tolist()
    res = collection.query(query_embeddings=q_emb, n_results=5)
    chunks = res["documents"][0]
    metas = res["metadatas"][0]

    context = "\n\n".join(f"[Review {i+1}]\n{c}" for i, c in enumerate(chunks))
    resp = groq.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context (student reviews):\n{context}\n\nQuestion: {question}"},
        ],
        temperature=0,
    )
    answer = resp.choices[0].message.content.strip()

    # Build the "retrieved from" panel: source + the actual review text used
    retrieved = ""
    for i, (c, m) in enumerate(zip(chunks, metas), 1):
        retrieved += f"[{i}] {m['source']}\n{c}\n\n"

    return answer, retrieved.strip()


with gr.Blocks(title="The Unofficial Guide") as demo:
    gr.Markdown("# The Unofficial Guide\nAsk about SFSU professors. Answers come "
                "only from real student reviews, with sources shown.")
    inp = gr.Textbox(label="Your question", placeholder="e.g. Is Bierman a tough grader?")
    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=6)
    sources = gr.Textbox(label="Retrieved from (the reviews used)", lines=12)
    btn.click(ask, inputs=inp, outputs=[answer, sources])
    inp.submit(ask, inputs=inp, outputs=[answer, sources])
    gr.Examples(
        ["Is Bierman a tough grader?",
         "Which professor is good for someone new to CS?",
         "Is Jose Ortiz-Costa an easy A?",
         "Does Duc Ta give extra credit?"],
        inputs=inp,
    )

if __name__ == "__main__":
    demo.launch()
