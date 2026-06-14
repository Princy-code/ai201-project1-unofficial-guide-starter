# Planning — The Unofficial Guide

## Domain

Student opinions about what SFSU professors are actually like to take — teaching
style, grading toughness, workload, exam structure, and whether they're a good
fit for beginners. The source material is Rate My Professors reviews for 10
professors across Computer Science, Communication Studies, Economics, and
Mathematics.

This knowledge is hard to find through official channels because the university
publishes course catalogs and requirements, but not candid, first-hand accounts
of what a class is *like* — whether the exams track the lectures, whether the
professor grades late, whether attendance really matters. That signal lives
only in student-to-student reviews.

## Documents

10 documents, one per professor, cleaned from Rate My Professors:
- Timothy Sun (CSC 510) — 8 reviews
- Duc Ta (CSC 215/220/340) — 40 reviews
- Shahrukh Humayoun (CSC 642) — 11 reviews
- Jose Ortiz-Costa (CSC 510/648/675/230) — 35 reviews
- Anthony Souza (CSC 101/317/413/415) — 50 reviews
- Omar Kudsi (COMM 150/250/521) — 41 reviews
- Robert Bierman (CSC 415) — 55 reviews
- Venoo Kakar (ECON 102) — 42 reviews
- Vera Klimkovsky (MATH 124, stats/calc) — 35 reviews
- Mary Halloran (MATH 110/124/225, stats/calc) — 40 reviews

Total: 357 reviews. Raw pages were copied manually from RMP (its reviews are
JavaScript-rendered and block scrapers) and cleaned with `ingest.py`, which
strips navigation, ads, "Similar Professors," rating-distribution widgets, vote
counts, and footers — keeping each review's quality, difficulty, course, date,
grade, attendance, tags, and comment text.

## Chunking Strategy

**One review = one chunk. Minimal overlap.**

Each RMP review is a self-contained opinion, roughly 200–600 characters / 2–4
sentences (e.g. "Tough grader, grades late, but I learned a lot — go to office
hours."). That natural unit is exactly what a user query wants back, so the
chunk boundary follows the review boundary (the `---` separators in the cleaned
files).

- **Chunk size:** one review (no fixed character count — split on review
  boundaries, not arbitrary lengths).
- **Overlap:** little to none. Overlap exists to avoid splitting a single
  thought across two chunks, but each review is *already* a complete thought
  with a hard boundary, so there's nothing to bridge.

Why not the alternatives:
- *Too small* (one sentence): would separate "He's a tough grader" from "but I
  learned a lot," losing the nuance reviewers actually express.
- *Too large* (a whole professor as one chunk): a query about grading would pull
  back all ~50 of a professor's reviews, drowning the relevant opinion in noise.

[DECISION TO CONFIRM: should the embedded text be the comment alone, or comment
+ professor name + course + rating? Note your choice and one sentence on why —
think about how a query like "which CS prof is good for beginners?" needs the
professor's name/department present in the chunk to retrieve well.]

## Retrieval Approach

Embedding model: `all-MiniLM-L6-v2` via `sentence-transformers` (runs locally,
no API key, no rate limits). Vector store: ChromaDB (local).

[GUIDING QUESTIONS — answer briefly in your own words:
- How many chunks (top-k) should retrieval return to give the LLM enough
  context without diluting it? (Start k=4–5; you'll tune after seeing results.)
- Why does semantic search find relevant reviews even when the query doesn't use
  the same words as the review? (One sentence on embeddings/meaning vs keywords.)]

## Evaluation Plan

Five test questions, each with a specific answer checkable against the documents:

1. **Is Professor Bierman a tough grader?**
   Expected: Yes — reviews overwhelmingly describe him as a tough/harsh grader
   who grades assignments very late in the semester.
2. **Which professor is a good choice for someone new to CS?**
   Expected: Anthony Souza (and/or Duc Ta) — repeatedly praised for clear,
   beginner-friendly teaching and breaking concepts down.
3. **Does Duc Ta give extra credit or chances to boost your grade?**
   Expected: Yes — multiple reviews mention extra-credit opportunities and
   chances to raise your grade.
4. **Is Jose Ortiz-Costa an easy A?**
   Expected: No — reviews repeatedly say "not an easy A," challenging but
   rewarding if you put in the work.
5. **What is the workload like in Bierman's CSC 415?**
   Expected: Heavy — lots of homework plus a difficult group file-system
   project; reviews warn to take it with a light course load.

## Anticipated Challenges

- Contradictory reviews (e.g. Bierman has 5-star ratings on failing grades, and
  1-star ratings calling him the best) — how should the system handle a
  professor people disagree about?
- A query about a professor or topic not in the 10 documents — the system should
  say it doesn't have enough info, not invent an answer.
- Short reviews ("Easy A.", "save yourself") that carry little semantic signal.]

## AI Tool Plan

- Generating the chunking script from this spec
- Generating the embedding + ChromaDB loading + retrieval function
- Generating the Groq grounding prompt + Gradio interface

## Architecture

Document Ingestion (ingest.py) -> Chunking (one review = one chunk)
  -> Embedding (all-MiniLM-L6-v2) -> Vector Store (ChromaDB)
  -> Retrieval (top-k semantic search) -> Generation (Groq llama-3.3-70b)]