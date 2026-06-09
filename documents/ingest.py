"""
ingest.py  -- Milestone 3 (document ingestion + cleaning)

Reads raw Rate My Professors page dumps from  documents_raw/*.txt
and writes clean, structured per-professor files to  documents/*.txt

How to use:
  1. For each professor, open their RMP page, select-all the review area,
     copy, and paste into a file:  documents_raw/<anything>.txt
  2. Run:  python ingest.py
  3. Clean files appear in  documents/  -- read a couple to verify.

The cleaning strips RMP boilerplate (nav, ads, "Similar Professors",
rating-distribution widget, "Helpful / Thumbs up N" vote counts, footer)
and keeps only the signal: each review's quality, difficulty, course,
date, grade, attendance, would-take-again, the comment, and the tags.
"""

import os
import re

RAW_DIR = "documents_raw"
OUT_DIR = "documents"

# RMP's fixed tag vocabulary. We match tags against this exact set so that an
# all-CAPS *comment* (e.g. "JUST DO NOT TAKE HIM!!!") is never mistaken for a tag.
KNOWN_TAGS = {
    "TOUGH GRADER", "GET READY TO READ", "PARTICIPATION MATTERS",
    "LOTS OF HOMEWORK", "GRADED BY FEW THINGS", "ACCESSIBLE OUTSIDE CLASS",
    "AMAZING LECTURES", "CARING", "INSPIRATIONAL", "RESPECTED",
    "GIVES GOOD FEEDBACK", "CLEAR GRADING CRITERIA", "EXTRA CREDIT",
    "GROUP PROJECTS", "HILARIOUS", "TEST HEAVY", "BEWARE OF POP QUIZZES",
    "LECTURE HEAVY", "ONLINE SAVVY", "SKIP CLASS? YOU WON'T PASS.",
    "SO MANY PAPERS", "TESTS? NOT MANY", "WOULD TAKE AGAIN",
}

# Lines that are per-review metadata fields (key: value).
META_KEYS = ("For Credit", "Attendance", "Would Take Again",
             "Grade", "Textbook", "Online Class")


def parse_header(lines):
    """Pull professor name, department, and overall stats from the page top."""
    text = "\n".join(lines)
    name, dept = "Unknown", "Unknown"

    # "Jose Ortiz-Costa" sits on the line just before "Professor in the X department"
    for i, ln in enumerate(lines):
        m = re.match(r"Professor in the (.+?) department", ln.strip())
        if m:
            dept = m.group(1).strip()
            if i > 0:
                name = lines[i - 1].strip()
            break

    overall = ratings = wta = difficulty = None
    m = re.search(r"Overall Quality Based on (\d+) ratings", text)
    if m:
        ratings = m.group(1)
    # the overall quality number is the token right before "/ 5"
    m = re.search(r"([0-9.]+)\s*\n?\s*/\s*5\s*\nOverall Quality", text)
    if m:
        overall = m.group(1)
    m = re.search(r"(\d+)%\s*\nWould take again", text)
    if m:
        wta = m.group(1)
    m = re.search(r"([0-9.]+)\s*\nLevel of Difficulty", text)
    if m:
        difficulty = m.group(1)

    return {"name": name, "dept": dept, "overall": overall,
            "ratings": ratings, "wta": wta, "difficulty": difficulty}


def parse_reviews(lines):
    """Split the page on each 'QUALITY' marker and parse one review per block."""
    # indices of every standalone "QUALITY" line == start of a review
    starts = [i for i, ln in enumerate(lines) if ln.strip() == "QUALITY"]
    reviews = []

    for s in starts:
        block = lines[s:]
        # the block ends at the next "QUALITY" or at "Helpful"
        end = len(block)
        for j in range(1, len(block)):
            if block[j].strip() in ("QUALITY", "Load More Ratings"):
                end = j
                break
            if block[j].strip() == "Helpful":
                end = j
                break
        block = block[:end]

        try:
            quality = block[1].strip()       # line after QUALITY
            # find DIFFICULTY
            di = next(k for k, ln in enumerate(block) if ln.strip() == "DIFFICULTY")
            difficulty = block[di + 1].strip()
            course = re.sub(r"^(Computer Icon)", "", block[di + 2].strip()).strip()
            date = block[di + 3].strip()
        except (IndexError, StopIteration):
            continue

        meta, comment_lines, tags = {}, [], []
        for ln in block[di + 4:]:
            t = ln.strip()
            if not t:
                continue
            if t.startswith("Reviewed:"):          # moderation note, drop it
                continue
            key = t.split(":", 1)[0] if ":" in t else ""
            if key in META_KEYS:
                meta[key] = t.split(":", 1)[1].strip()
            elif t in KNOWN_TAGS:
                tags.append(t)
            else:
                comment_lines.append(t)

        reviews.append({
            "quality": quality, "difficulty": difficulty, "course": course,
            "date": date, "meta": meta,
            "comment": " ".join(comment_lines).strip(), "tags": tags,
        })
    return reviews


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "professor"


def write_clean(hdr, reviews, path):
    out = []
    out.append(f"Professor: {hdr['name']}")
    out.append(f"Department: {hdr['dept']}")
    out.append("School: San Francisco State University")
    out.append("Source: Rate My Professors (student reviews)")
    out.append("")
    stat = []
    if hdr["overall"]:
        stat.append(f"Overall Quality: {hdr['overall']} / 5")
    if hdr["ratings"]:
        stat.append(f"({hdr['ratings']} ratings)")
    if stat:
        out.append(" ".join(stat))
    if hdr["wta"]:
        out.append(f"Would Take Again: {hdr['wta']}%")
    if hdr["difficulty"]:
        out.append(f"Level of Difficulty: {hdr['difficulty']} / 5")
    out.append("")

    for n, r in enumerate(reviews, 1):
        out.append("-" * 3)
        out.append(f"Review {n} - {r['course']} ({r['date']})")
        bits = [f"Quality: {r['quality']}", f"Difficulty: {r['difficulty']}"]
        for k in ("Would Take Again", "Grade", "Attendance"):
            if r["meta"].get(k):
                bits.append(f"{k}: {r['meta'][k]}")
        out.append(" | ".join(bits))
        if r["tags"]:
            out.append("Tags: " + ", ".join(r["tags"]))
        if r["comment"]:
            out.append(f"Comment: {r['comment']}")
        out.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out).rstrip() + "\n")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    raw_files = sorted(f for f in os.listdir(RAW_DIR) if f.endswith(".txt"))
    if not raw_files:
        print(f"No .txt files found in {RAW_DIR}/ -- paste your RMP dumps there first.")
        return

    total_reviews = 0
    for fname in raw_files:
        with open(os.path.join(RAW_DIR, fname), encoding="utf-8") as f:
            lines = f.read().splitlines()
        hdr = parse_header(lines)
        reviews = parse_reviews(lines)
        out_path = os.path.join(OUT_DIR, slugify(hdr["name"]) + ".txt")
        write_clean(hdr, reviews, out_path)
        total_reviews += len(reviews)
        print(f"  {fname:35s} -> {os.path.basename(out_path):28s} "
              f"({len(reviews)} reviews)")

    print(f"\nDone. {len(raw_files)} professors, {total_reviews} reviews total, "
          f"written to {OUT_DIR}/")


if __name__ == "__main__":
    main()