import json, os, re
DOCS_DIR = "documents"
OUT_FILE = "chunks.json"
def parse_doc(path):
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    parts = raw.split("---")
    professor = "Unknown"
    m = re.search(r"Professor:\s*(.+)", parts[0])
    if m:
        professor = m.group(1).strip()
    reviews = []
    for block in [p.strip() for p in parts[1:] if p.strip()]:
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        course = ""
        m = re.search(r"Review\s+\d+\s*-\s*(.+?)\s*\(", lines[0])
        if m:
            course = m.group(1).strip()
        quality = difficulty = ""
        if len(lines) > 1:
            mq = re.search(r"Quality:\s*([0-9.]+)", lines[1])
            md = re.search(r"Difficulty:\s*([0-9.]+)", lines[1])
            quality = mq.group(1) if mq else ""
            difficulty = md.group(1) if md else ""
        comment = ""
        for ln in lines:
            if ln.startswith("Comment:"):
                comment = ln[8:].strip()
                break
        if comment:
            reviews.append({"professor": professor, "course": course,
                            "quality": quality, "difficulty": difficulty, "comment": comment})
    return reviews
def main():
    chunks = []
    for fname in sorted(f for f in os.listdir(DOCS_DIR) if f.endswith(".txt")):
        reviews = parse_doc(os.path.join(DOCS_DIR, fname))
        for i, r in enumerate(reviews):
            label = f"Professor: {r['professor']} | Course: {r['course']} | Quality: {r['quality']} | Difficulty: {r['difficulty']}"
            chunks.append({"id": f"{fname[:-4]}_{i}", "text": f"{label}\n{r['comment']}",
                           "metadata": {"professor": r["professor"], "course": r["course"],
                                        "quality": r["quality"], "difficulty": r["difficulty"], "source": fname}})
        print(f"  {fname:28s} {len(reviews):3d} chunks")
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print(f"\nTotal: {len(chunks)} chunks written to {OUT_FILE}")
    for c in chunks[::max(1, len(chunks)//5)][:5]:
        print(f"\n[{c['id']}] (len={len(c['text'])})")
        print(c["text"])
if __name__ == "__main__":
    main()
