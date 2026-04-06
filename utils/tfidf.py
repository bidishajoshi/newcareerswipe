"""
TF-IDF based resume parsing and job matching utility.
Supports PDF, DOC, and DOCX formats.
"""
import os, re, math
from collections import Counter

# ── Optional parsers ─────────────────────────────────────────────────────────
try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    from docx import Document as DocxDocument
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False

# ── Stop words ───────────────────────────────────────────────────────────────
STOP_WORDS = {
    "a","an","the","and","or","but","in","on","at","to","for","of","with",
    "by","from","as","is","was","are","were","be","been","being","have",
    "has","had","do","does","did","will","would","could","should","may",
    "might","shall","can","need","dare","ought","used","that","this",
    "these","those","it","its","i","me","my","we","our","you","your",
    "he","she","they","them","their","his","her","not","no","nor",
    "so","yet","both","either","neither","each","few","more","most",
    "other","such","what","which","who","whom","how","when","where","why"
}

def clean_text(text: str) -> list[str]:
    """Lowercase, remove punctuation, tokenize, strip stop words."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\+\#]", " ", text)
    tokens = text.split()
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]

def parse_resume(filepath: str) -> str:
    """Extract raw text from PDF, DOCX, or DOC."""
    ext = filepath.rsplit(".", 1)[-1].lower()
    text = ""

    if ext == "pdf" and PDF_SUPPORT:
        try:
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception:
            text = ""

    elif ext == "docx" and DOCX_SUPPORT:
        try:
            doc = DocxDocument(filepath)
            text = "\n".join(p.text for p in doc.paragraphs)
        except Exception:
            text = ""

    elif ext == "doc":
        # fallback: try reading as text
        try:
            with open(filepath, "r", errors="ignore") as f:
                text = f.read()
        except Exception:
            text = ""

    return text

def compute_tfidf(documents: list[list[str]]) -> list[dict]:
    """
    Compute TF-IDF vectors for a list of tokenized documents.
    Returns list of dicts: {term: tfidf_score}
    """
    N = len(documents)
    # DF: how many documents contain each term
    df = Counter()
    for doc in documents:
        for term in set(doc):
            df[term] += 1

    tfidf_vectors = []
    for doc in documents:
        tf = Counter(doc)
        total = len(doc) if doc else 1
        vec = {}
        for term, count in tf.items():
            tf_score  = count / total
            idf_score = math.log((N + 1) / (df[term] + 1)) + 1  # smoothed
            vec[term] = tf_score * idf_score
        tfidf_vectors.append(vec)

    return tfidf_vectors

def cosine_similarity(vec_a: dict, vec_b: dict) -> float:
    """Cosine similarity between two TF-IDF vectors."""
    if not vec_a or not vec_b:
        return 0.0
    shared = set(vec_a.keys()) & set(vec_b.keys())
    dot    = sum(vec_a[t] * vec_b[t] for t in shared)
    mag_a  = math.sqrt(sum(v**2 for v in vec_a.values()))
    mag_b  = math.sqrt(sum(v**2 for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)

def match_resume_to_job(resume_text: str, job_text: str) -> int:
    """
    Returns a match score (0-100) between a resume and a job description
    using TF-IDF + Cosine Similarity.
    """
    tokens_resume = clean_text(resume_text)
    tokens_job    = clean_text(job_text)

    if not tokens_resume or not tokens_job:
        return 0

    vecs = compute_tfidf([tokens_resume, tokens_job])
    score = cosine_similarity(vecs[0], vecs[1])
    return round(score * 100)

def extract_keywords(text: str, top_n: int = 15) -> list[str]:
    """Extract top N keywords from text using TF-IDF on single document."""
    tokens = clean_text(text)
    if not tokens:
        return []
    vecs = compute_tfidf([tokens])
    sorted_terms = sorted(vecs[0].items(), key=lambda x: x[1], reverse=True)
    return [term for term, _ in sorted_terms[:top_n]]
