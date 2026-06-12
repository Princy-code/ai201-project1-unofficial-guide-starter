# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

Student opinions about what SFSU professors are actually like to take — covering teaching style, grading toughness, workload, exam structure, extra-credit policies, and whether a professor is a good fit for beginners. The source material is Rate My Professors reviews for 10 professors across Computer Science, Communication Studies, Economics, and Mathematics.

This knowledge is hard to find through official channels because the university publishes course catalogs and grade distributions, but not candid, first-hand accounts of what a class is *like* day-to-day — whether the exams track the lectures, whether the professor grades assignments late, whether office hours are actually useful. That signal lives only in student-to-student reviews, which are JavaScript-rendered on RMP and not indexed in a way that lets you compare professors across departments.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Timothy Sun (CSC 510) | Rate My Professors — student reviews (manually copied) | documents/timothy_sun.txt |
| 2 | Duc Ta (CSC 215/220/340) | Rate My Professors — student reviews (manually copied) | documents/duc_ta.txt |
| 3 | Shahrukh Humayoun (CSC 642) | Rate My Professors — student reviews (manually copied) | documents/shahrukh_humayoun.txt |
| 4 | Jose Ortiz-Costa (CSC 510/648/675/230) | Rate My Professors — student reviews (manually copied) | documents/jose_ortiz_costa.txt |
| 5 | Anthony Souza (CSC 101/317/413/415) | Rate My Professors — student reviews (manually copied) | documents/anthony_souza.txt |
| 6 | Omar Kudsi (COMM 150/250/521) | Rate My Professors — student reviews (manually copied) | documents/omar_kudsi.txt |
| 7 | Robert Bierman (CSC 415) | Rate My Professors — student reviews (manually copied) | documents/robert_bierman.txt |
| 8 | Venoo Kakar (ECON 102) | Rate My Professors — student reviews (manually copied) | documents/venoo_kakar.txt |
| 9 | Vera Klimkovsky (MATH 124, stats/calc) | Rate My Professors — student reviews (manually copied) | documents/vera_klimkovsky.txt |
| 10 | Mary Halloran (MATH 110/124/225, stats/calc) | Rate My Professors — student reviews (manually copied) | documents/mary_halloran.txt |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** One review = one chunk. No fixed character count — the boundary follows the `---` separators written by `ingest.py` into the cleaned files. Reviews average roughly 200–600 characters (2–4 sentences). Each chunk's embedded text includes a label line (`Professor: X | Course: Y | Quality: Z | Difficulty: W`) prepended to the comment, so cross-professor queries have the professor name and course present in every chunk.

**Overlap:** None. Overlap is designed to avoid splitting a single coherent thought across two chunks, but each RMP review is already a self-contained opinion with a hard boundary — there is no thought to bridge. Adding artificial overlap would only duplicate text across adjacent chunks without adding signal.

**Why these choices fit your documents:** RMP reviews are naturally atomic: one student, one opinion, one chunk. Splitting them smaller (by sentence) would separate "tough grader" from "but I learned a lot," losing the nuance. Merging them larger (all reviews for one professor as one chunk) would force the LLM to work with 50 reviews at once, burying the specific opinion a query is looking for. The review-boundary split is the natural unit that matches how users ask questions.

**Preprocessing:** `ingest.py` strips RMP boilerplate — navigation bars, ads, the "Similar Professors" section, rating-distribution widgets, vote counts ("Helpful / Thumbs up N"), and footers — keeping only each review's quality score, difficulty score, course, date, grade, attendance flag, would-take-again, tags, and comment text. Tags are matched against a known vocabulary (e.g., `TOUGH GRADER`, `EXTRA CREDIT`) so that all-caps comment text is never misclassified as a tag.

**Final chunk count:** 357 chunks across 10 professor files.

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers` (runs locally, no API key required). Chosen because it is fast, small (~90 MB), runs offline with no rate limits or cost, and produces strong semantic embeddings for short English text — which matches the review-length chunks in this corpus.

**Production tradeoff reflection:** For a real deployment, I would weigh the following tradeoffs. A larger hosted model like OpenAI's `text-embedding-3-large` or Cohere's `embed-english-v3.0` offers meaningfully higher accuracy on domain-specific retrieval at the cost of API latency and per-token pricing; for a high-traffic system that cost would add up fast. `all-MiniLM-L6-v2` has a 256-token context window, which is fine for short reviews but would truncate longer documents — a model like `text-embedding-3-small` (8k context) would be safer for a broader document corpus. Multilingual support is not needed here since all reviews are in English, but if SFSU's student body submitted reviews in other languages, a multilingual model like `paraphrase-multilingual-MiniLM-L12-v2` or Cohere's multilingual embeddings would be necessary. Latency matters for the Gradio UI: a local model answers a query in milliseconds, while an API call adds ~200–500 ms of network overhead per query, which is noticeable for an interactive tool.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

> "You answer questions about SFSU professors using ONLY the student reviews provided in the context. Do not use any outside knowledge. If the reviews do not contain enough information to answer, say exactly: 'I don't have enough information on that.' When you answer, base every claim on the reviews and mention the professor by name. Be concise."

The phrase "ONLY the student reviews provided in the context" is the primary constraint. The exact fallback phrase ("I don't have enough information on that.") is specified verbatim so the model does not hedge with a plausible-but-invented answer — if that string appears, it signals a clean retrieval miss rather than a hallucinated response. `temperature=0` is set on the Groq call to make generation deterministic and prevent the model from drifting toward creative paraphrasing.

The context is formatted as numbered review blocks (`[Review 1]\n...\n[Review 2]\n...`) so the model can refer back to specific reviews when constructing its answer, making claims traceable.

**How source attribution is surfaced in the response:** After generation, `generate.py` collects the `source` metadata field from all retrieved chunks (the original `.txt` filename) and prints `Sources: robert_bierman.txt` below the answer. In the Gradio UI (`app.py`), the full text of every retrieved review is shown in a "Retrieved from" panel alongside the answer, so the user can read the exact review the model drew from.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Is Professor Bierman a tough grader? | Yes — overwhelmingly described as tough/harsh; grades late | "Yes, according to the reviews, Professor Robert Bierman is a tough grader, as stated in Review 1, Review 3, and also implied in Review 2 and Review 5." Sources: robert_bierman.txt | Relevant | Accurate |
| 2 | Which professor is a good choice for someone new to CS? | Anthony Souza (and/or Duc Ta) — repeatedly praised for clear, beginner-friendly teaching | "Professor Anthony Souza is a good choice…his CSC317 has a difficulty of 1.0…praised as an excellent teacher." Sources: anthony_souza.txt, duc_ta.txt, robert_bierman.txt | Partially relevant | Accurate |
| 3 | Does Duc Ta give extra credit or chances to boost your grade? | Yes — multiple reviews mention extra-credit opportunities | "I don't have enough information on that." Sources: duc_ta.txt | Partially relevant | Inaccurate |
| 4 | Is Jose Ortiz-Costa an easy A? | No — repeatedly described as challenging, not an easy A | "No… Review 3 states 'this professor is not for students looking for an easy A' and Review 5 mentions 'you will have to work very hard.'" Sources: jose_ortiz_costa.txt | Relevant | Accurate |
| 5 | What is the workload like in Bierman's CSC 415? | Heavy — lots of homework plus a difficult group file-system project | "Heavy workload. Review 3 states the class 'WILL take up a majority of your time'… homework assignments are 'brutal'…recommends taking it with a light class load." Sources: robert_bierman.txt | Relevant | Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:** "Does Duc Ta give extra credit or chances to boost your grade?"

**What the system returned:** "I don't have enough information on that." — even though the source retrieved was duc_ta.txt, which contains reviews that mention extra credit.

**Root cause (tied to a specific pipeline stage):** The failure is in the **retrieval stage**. Duc Ta has 40 reviews, but the system only retrieves k=5 chunks per query. The embedding model represents each review holistically — a review that says "He's a great teacher, very caring, gives extra credit too" embeds as *primarily* a positive-sentiment teaching review; the extra-credit mention is one clause among several and does not dominate the chunk's semantic position in vector space. When the query "Does Duc Ta give extra credit or chances to boost your grade?" is embedded, the top-5 nearest neighbors are the 5 most semantically similar reviews — which turn out to be reviews about Duc Ta's general helpfulness and grading style, not the specific reviews where students mentioned extra credit in passing. The extra-credit reviews were ranked outside the top-5 and were never passed to the LLM, leaving it with no evidence to answer.

**What you would change to fix it:** Increase k from 5 to 10–12 for this corpus size (40 reviews per professor means k=5 sees only 12% of the available evidence). Alternatively, add a hybrid retrieval step: run BM25 keyword search in parallel with semantic search and merge the results. A BM25 pass on "extra credit" would have retrieved those reviews directly regardless of their semantic distance score, giving the LLM the evidence it needed.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:** The evaluation plan in `planning.md` — five questions with specific expected answers — forced a concrete decision about chunk content before writing a line of embedding code. When I asked myself "will the query 'which professor is good for beginners?' retrieve the right reviews?", I realized that embedding the comment text alone would fail: a review saying "He explains things really clearly" carries no professor name or course, so retrieval could return that chunk without the LLM knowing *who* the student was praising. The spec made me see this gap early, which drove the decision to prepend the `Professor: X | Course: Y | Quality: Z | Difficulty: W` label to every chunk's embedded text.

**One way your implementation diverged from the spec, and why:** The spec explicitly deferred the decision on whether to embed comment-only vs. comment+metadata as a "[DECISION TO CONFIRM]" note. The implementation resolved that by always including the full label line in the chunk text — a departure from the spec's "one review = one chunk" description, which implied the comment was the primary content. This also changed the chunk's character count: what the spec described as "200–600 characters" became more like 300–750 characters once the label line was added. The divergence was deliberate: the label line is short, doesn't dilute the semantic signal of the comment, and is essential for cross-professor queries to work correctly.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:* The full `ingest.py` requirements from `planning.md` — strip RMP boilerplate, keep quality/difficulty/course/date/grade/attendance/tags/comment per review, write structured `---`-delimited output — plus a sample of raw RMP page text showing how the page was laid out.
- *What it produced:* A `parse_reviews()` function that split on `QUALITY` markers and extracted fields. The initial version treated any all-caps line as a tag, which caused long all-caps student comments (e.g. "JUST DO NOT TAKE HIM!!!") to be silently dropped instead of kept as the comment.
- *What I changed or overrode:* Added the `KNOWN_TAGS` set (matching RMP's fixed tag vocabulary exactly) so the parser distinguishes tags from all-caps comments by set membership rather than just case. This preserved comments that students wrote in all caps and prevented data loss.

**Instance 2**

- *What I gave the AI:* The `generate.py` design from `planning.md` — retrieve top-k chunks from ChromaDB, pass them as context to Groq llama-3.3-70b-versatile, return a grounded answer with source attribution — plus the five evaluation questions as a test suite.
- *What it produced:* A working `answer()` function with a system prompt that said "answer only using the provided reviews." The initial system prompt did not specify what to say when evidence was missing, so the model occasionally produced hedged guesses ("It's possible that…") rather than a clean non-answer.
- *What I changed or overrode:* Tightened the grounding instruction to include the exact fallback phrase ("I don't have enough information on that.") and added `temperature=0` to make outputs deterministic. This made the failure mode explicit and testable: if that exact string appears in the output, retrieval missed — and the failure case in Question 3 confirmed this behavior directly.
