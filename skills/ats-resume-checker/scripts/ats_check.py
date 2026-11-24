#!/usr/bin/env python3
"""Deterministic half of the ATS resume check.

The model reads the resume and the job posting and drafts the analysis. This
script then checks the parts that should not depend on a model's judgment:

- keywords the draft calls missing but that are literally in the resume
  (directly or through a known synonym) are moved to matched;
- every evidence quote is looked up in the resume text;
- employment dates are checked for overlaps, gaps, future dates and
  backwards ranges;
- the final score is computed as 60% keyword coverage + 40% fit.

Usage:
    python3 ats_check.py --resume resume.txt --draft draft.json
    python3 ats_check.py --resume resume.txt < draft.json

draft.json:
    {"fit": 68,
     "matched": ["Python", "SQL"],
     "missing": ["Airflow", "dbt"],
     "evidence": ["Built ETL pipelines in PySpark for 3M+ records"]}

Python 3.8+, standard library only. Nothing is sent anywhere.
"""
import argparse
import difflib
import json
import re
import sys
from datetime import datetime, timezone

# Interchangeable spellings (lower-case, normalised). If the job uses one form
# and the resume another, the keyword still counts as present.
SYNONYM_GROUPS = [
    # --- General software / web / cloud ---
    ["javascript", "js"],
    ["typescript", "ts"],
    ["kubernetes", "k8s"],
    ["google cloud", "google cloud platform", "gcp"],
    ["amazon web services", "aws"],
    ["microsoft azure", "azure"],
    ["postgresql", "postgres"],
    ["rest api", "rest apis", "rest", "restful"],
    ["ci cd", "continuous integration", "continuous delivery"],
    ["github actions", "gha"],
    ["node.js", "nodejs", "node js", "node"],
    ["next.js", "nextjs", "next js"],

    # --- ML / AI / Data: core terms ---
    ["machine learning", "ml"],
    ["machine learning engineer", "ml engineer", "mle"],
    ["deep learning", "dl"],
    ["artificial intelligence", "ai"],
    ["generative ai", "genai", "gen ai"],
    ["large language model", "large language models", "llm", "llms"],
    ["natural language processing", "nlp"],
    ["retrieval augmented generation", "rag"],
    ["data science", "data scientist", "ds"],
    ["exploratory data analysis", "eda"],
    ["a b testing", "ab testing", "experimentation"],
    ["mlops", "ml ops"],
    ["feature store", "feature stores"],
    ["hyperparameter tuning", "hyperparameter optimization", "hyperparameter optimisation"],

    # --- ML: algorithms & model architectures ---
    ["convolutional neural network", "convolutional neural networks", "cnn", "convnet"],
    ["recurrent neural network", "recurrent neural networks", "rnn"],
    ["long short term memory", "lstm"],
    ["generative adversarial network", "generative adversarial networks", "gan", "gans"],
    ["graph neural network", "graph neural networks", "gnn"],
    ["support vector machine", "support vector machines", "svm"],
    ["k nearest neighbors", "k nearest neighbours", "knn"],
    ["principal component analysis", "pca"],
    ["gradient boosting", "gradient boosted trees", "gbm"],
    ["xgboost", "xgb"],
    ["lightgbm", "light gbm", "lgbm"],
    ["logistic regression", "logreg"],
    ["random forest", "random forests"],

    # --- NLP / vision tasks ---
    ["named entity recognition", "ner"],
    ["optical character recognition", "ocr"],

    # --- GenAI / LLM engineering ---
    ["fine tuning", "finetuning"],
    ["parameter efficient fine tuning", "peft"],
    ["low rank adaptation", "lora"],
    ["vector database", "vector databases", "vector store", "vector stores", "vector search"],

    # --- ML frameworks & libraries ---
    ["scikit learn", "sklearn"],
    ["hugging face", "huggingface", "hf", "transformers"],
    ["tensorflow", "tf"],
    ["pytorch", "torch"],
    ["opencv", "open cv"],

    # --- Cloud ML platforms ---
    ["amazon sagemaker", "aws sagemaker", "sagemaker"],
    ["vertex ai", "google vertex ai"],
    ["azure machine learning", "azure ml"],
    ["weights and biases", "weights biases", "wandb"],
    ["mlflow", "ml flow"],

    # --- Data engineering ---
    ["extract transform load", "etl"],
    ["extract load transform", "elt"],
    ["apache spark", "spark", "pyspark"],
    ["apache airflow", "airflow"],
    ["apache kafka", "kafka"],
    ["data build tool", "dbt"],
    ["bigquery", "bq", "google bigquery"],
    ["amazon redshift", "redshift"],

    # --- Statistics & BI ---
    ["statistical modeling", "statistical modelling", "statistical analysis", "statistics", "stats"],
    ["time series", "time series analysis", "timeseries", "time series forecasting"],
    ["power bi", "powerbi"],
]


def normalize(text):
    """Lower-case and collapse everything except letters, digits and + # . to spaces."""
    return re.sub(r"[^a-z0-9+#.]+", " ", text.lower()).strip()


def present(keyword, resume_norm):
    """True if the keyword or a known synonym occurs in the resume on word boundaries."""
    kw = normalize(keyword)
    if not kw:
        return False
    forms = {kw}
    for group in SYNONYM_GROUPS:
        if kw in group:
            forms.update(group)
    return any(
        re.search(rf"(?<![a-z0-9]){re.escape(form)}(?![a-z0-9])", resume_norm)
        for form in forms
    )


def literal(keyword, resume_norm):
    """True if the keyword itself, not a synonym, occurs in the resume."""
    kw = normalize(keyword)
    return bool(kw) and bool(re.search(rf"(?<![a-z0-9]){re.escape(kw)}(?![a-z0-9])", resume_norm))


def alnum_words(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def evidence_in_resume(evidence, resume_words):
    """A quote passes if it is in the resume, allowing a dropped word or a
    ligature but not a paraphrase: the longest exact run must cover 85% of it."""
    ev = alnum_words(evidence)
    if len(ev) < 8:
        return False
    if ev in resume_words:
        return True
    match = difflib.SequenceMatcher(None, ev, resume_words, autojunk=False).find_longest_match(
        0, len(ev), 0, len(resume_words)
    )
    return match.size >= 0.85 * len(ev)


# --- Dates ------------------------------------------------------------------
MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
MONTH_RE = (
    r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|"
    r"aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?"
)
DATE_RE = rf"(?:(?:{MONTH_RE})\.?\s*(?:19|20)\d{{2}}|\d{{1,2}}[/.](?:19|20)\d{{2}}|(?:19|20)\d{{2}})"
PRESENT_RE = r"till\s+now|till\s+date|to\s+date|present|current|now|today|ongoing"
RANGE_RE = re.compile(
    rf"({DATE_RE})\s*(?:-|\u2013|\u2014|to|until)\s*({DATE_RE}|{PRESENT_RE})", re.IGNORECASE
)
SECTION_RE = re.compile(
    r"\b(experience|employment|work history|education|languages?|skills|"
    r"certifications?|courses|projects|interests|references|awards|publications)\b",
    re.IGNORECASE,
)


def parse_month(token, is_end):
    """Return (month_index, precise) for a date token, or None for 'present'."""
    token = token.strip().lower()
    if re.fullmatch(PRESENT_RE, token):
        return None
    year = int(re.search(r"(19|20)\d{2}", token).group(0))
    numeric = re.match(r"(\d{1,2})[/.]", token)
    if numeric and 1 <= int(numeric.group(1)) <= 12:
        return year * 12 + int(numeric.group(1)) - 1, True
    named = re.match(r"[a-z]+", token)
    if named and named.group(0)[:3] in MONTHS:
        return year * 12 + MONTHS[named.group(0)[:3]] - 1, True
    # Year only: assume the whole year, so no overlap or gap is invented.
    return year * 12 + (11 if is_end else 0), False


def education_span(text):
    """Character span of the education section, whose dates are not jobs."""
    head = re.search(r"\bEDUCATION\b", text) or re.search(r"\bEducation\b", text)
    if not head:
        return None
    nxt = next(
        (m for m in SECTION_RE.finditer(text, head.end()) if m.group(1).lower() != "education"),
        None,
    )
    return head.start(), (nxt.start() if nxt else len(text))


def months(n):
    return f"{n} month{'s' if n != 1 else ''}"


def date_flags(resume_text, today):
    text = re.sub(r"\s+", " ", resume_text)
    now = today.year * 12 + today.month - 1
    edu = education_span(text)
    roles = []
    for m in RANGE_RE.finditer(text):
        if edu and edu[0] <= m.start() < edu[1]:
            continue
        start = parse_month(m.group(1), is_end=False)
        end = parse_month(m.group(2), is_end=True)
        if start is None:
            continue
        ongoing = end is None
        roles.append({
            "raw": m.group(0).strip(),
            "start": start[0],
            "end": now if ongoing else end[0],
            "precise": start[1] and (ongoing or end[1]),
            "ongoing": ongoing,
        })

    flags = []

    def flag(severity, title, detail):
        flags.append({"severity": severity, "title": title, "detail": detail})

    for r in roles:
        if not r["ongoing"] and r["end"] > now:
            flag("High", "Date in the future",
                 f'"{r["raw"]}" ends after today. Recruiters will read it as a typo.')
        if r["end"] < r["start"]:
            flag("High", "Date range runs backwards", f'"{r["raw"]}" ends before it starts.')

    ordered = sorted(roles, key=lambda r: r["start"])
    for i, a in enumerate(ordered):
        for b in ordered[i + 1:]:
            overlap = min(a["end"], b["end"]) - b["start"]
            threshold = 2 if (a["precise"] and b["precise"]) else 12
            if overlap > threshold:
                flag("Medium", "Overlapping roles",
                     f'"{a["raw"]}" and "{b["raw"]}" overlap by {months(overlap)}. '
                     "Fix the typo, or say the roles were concurrent.")

    latest_end = None
    for r in ordered:
        if latest_end is not None:
            gap = r["start"] - latest_end
            if gap > (6 if r["precise"] else 12):
                flag("Low", "Employment gap",
                     f'{months(gap)} with no role before "{r["raw"]}". A one-line explanation helps.')
        latest_end = r["end"] if latest_end is None else max(latest_end, r["end"])

    short = [r for r in roles if r["precise"] and not r["ongoing"]
             and r["end"] - r["start"] < 12 and r["end"] >= now - 60]
    if len(short) >= 2:
        flag("Medium", "Several short roles",
             f"{len(short)} roles under a year in the last 5 years. "
             "Recruiters read this as job-hopping unless it is explained.")
    return flags


# --- Check ------------------------------------------------------------------
MAX_KEYWORDS = 20


def check(resume_text, draft, today=None):
    resume_norm = normalize(resume_text)
    matched = [k for k in draft.get("matched", []) if str(k).strip()]
    missing = [k for k in draft.get("missing", []) if str(k).strip()]

    # A keyword the draft calls missing but that is in the text is matched.
    recovered = [k for k in missing if present(k, resume_norm)]
    have = {k.lower() for k in matched}
    matched += [k for k in recovered if k.lower() not in have]
    gone = {k.lower() for k in recovered}
    missing = [k for k in missing if k.lower() not in gone]

    # Keep at most 20 keywords, in the same matched-to-missing proportion.
    total = len(matched) + len(missing)
    if total > MAX_KEYWORDS:
        keep = round(MAX_KEYWORDS * len(matched) / total)
        keep = max(1, min(MAX_KEYWORDS - 1, keep)) if matched and missing else min(MAX_KEYWORDS, len(matched))
        matched, missing = matched[:keep], missing[: MAX_KEYWORDS - keep]

    fit = min(100.0, max(0.0, float(draft.get("fit", 0))))
    total = len(matched) + len(missing)
    coverage = round(100 * len(matched) / total, 1) if total else None
    score = round(0.6 * coverage + 0.4 * fit, 1) if total else round(fit, 1)

    resume_words = alnum_words(resume_text)
    return {
        "score": score,
        "fit": fit,
        "coverage": coverage,
        "matched": matched,
        "missing": missing,
        "recovered": recovered,
        # In the resume only under another spelling (job says "Apache Spark",
        # resume says "PySpark"). A strict keyword filter can miss these.
        "matchedBySynonym": [
            k for k in matched if present(k, resume_norm) and not literal(k, resume_norm)
        ],
        # Matched on meaning by the model, not found as text or as a known
        # synonym. A keyword filter in an ATS would miss these.
        "matchedNotLiteral": [k for k in matched if not present(k, resume_norm)],
        "evidence": [
            {"quote": q, "found": evidence_in_resume(q, resume_words)}
            for q in draft.get("evidence", [])
            if str(q).strip()
        ],
        "dateFlags": date_flags(resume_text, today or datetime.now(timezone.utc)),
    }


def main():
    parser = argparse.ArgumentParser(description="Verify a drafted ATS resume check.")
    parser.add_argument("--resume", required=True, help="plain-text resume file")
    parser.add_argument("--draft", help="JSON draft file (default: stdin)")
    args = parser.parse_args()
    with open(args.resume, encoding="utf-8") as fh:
        resume_text = fh.read()
    raw = open(args.draft, encoding="utf-8").read() if args.draft else sys.stdin.read()
    json.dump(check(resume_text, json.loads(raw)), sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
