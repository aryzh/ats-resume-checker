"""Run: python3 tests/test_ats_check.py"""
import importlib.util
import json
import pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "ats_check", ROOT / "skills/ats-resume-checker/scripts/ats_check.py"
)
ats = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ats)

resume = (ROOT / "tests/sample_resume.txt").read_text()
draft = json.loads((ROOT / "tests/sample_draft.json").read_text())
out = ats.check(resume, draft, today=datetime(2026, 11, 1, tzinfo=timezone.utc))

# Synonyms recover keywords the draft called missing.
assert out["recovered"] == ["Apache Spark", "Postgres", "Extract Transform Load"], out["recovered"]
assert out["missing"] == ["Airflow", "dbt", "Snowflake"]
# "Apache Spark" is there only as PySpark, "Postgres" only as PostgreSQL.
assert out["matchedBySynonym"] == ["Apache Spark", "Postgres", "Extract Transform Load"], out["matchedBySynonym"]
assert out["matchedNotLiteral"] == []
# 6 of 9 keywords, fit 62: 0.6 * 66.7 + 0.4 * 62 = 64.8
assert out["coverage"] == 66.7 and out["score"] == 64.8, (out["coverage"], out["score"])
assert (out["matchedCount"], out["keywordCount"]) == (6, 9)
assert out["wordCount"] == len(resume.split()) and 90 < out["wordCount"] < 130, out["wordCount"]
# A real quote passes, an invented one does not.
assert [e["found"] for e in out["evidence"]] == [True, False]
# Education dates are ignored; the two jobs overlap by 3 months.
assert [f["title"] for f in out["dateFlags"]] == ["Overlapping roles"], out["dateFlags"]
# No keywords: the score is the fit, clamped to 0..100.
assert ats.check(resume, {"fit": 140})["score"] == 100.0
# Word boundaries: "java" is not found inside "javascript".
assert not ats.present("Java", ats.normalize("JavaScript and TypeScript"))
assert ats.present("JS", ats.normalize("JavaScript and TypeScript"))
# With the posting, keywords that are not in it are reported; synonyms count.
job = "We need Python, SQL, Spark and Airflow on AWS. Postgres is a plus. ETL, dbt, Snowflake."
with_job = ats.check(resume, dict(draft, missing=draft["missing"] + ["Kubernetes"]), job_text=job)
assert with_job["keywordsNotInJob"] == ["Kubernetes"], with_job["keywordsNotInJob"]
assert "keywordsNotInJob" not in out
# "C" is not inside "C++" or "C#"; "Go" matches "Golang" through the synonym table.
langs = ats.normalize("Skills: C++, C#, .NET, Node.js, Golang, React")
assert [k for k in ["C++", "C#", ".NET", "Node.js", "Go", "C", "R"] if ats.present(k, langs)] == ["C++", "C#", ".NET", "Node.js", "Go"]
assert ats.present("C", ats.normalize("C, C++ and Python."))
# A repeated keyword counts once; one listed on both sides stays matched.
dup = ats.check("python sql", {"fit": 50, "matched": ["Python", "python"], "missing": ["SQL", "Python", "Go", 7, None]})
assert (dup["matched"], dup["missing"]) == (["Python", "SQL"], ["Go"]), dup
# A ligature from a PDF does not break a quote; a paraphrase still fails.
lig = "Built ef\ufb01cient pipelines for \ufb01nance reporting teams"
assert ats.check(lig, {"evidence": ["Built efficient pipelines for finance reporting teams"]})["evidence"][0]["found"]
assert not ats.check(lig, {"evidence": ["Created fast data flows for the accounting department"]})["evidence"][0]["found"]
# Bad input is reported, not a traceback.
for bad in ({"fit": "high"}, {"fit": None}, [1, 2]):
    try:
        ats.check("x", bad)
    except ValueError:
        pass
    else:
        raise AssertionError(bad)
# An education section under another name is not read as a job.
school = "EXPERIENCE\nRep, A 2018 - 2020\nSchooling\nBA, Example University, 2014 - 2019"
assert ats.date_flags(school, datetime(2026, 11, 1, tzinfo=timezone.utc)) == []
# No job: no score, but dates and word count still come back.
solo = ats.check(resume, {})
assert solo["score"] is None and solo["fit"] is None and solo["wordCount"] > 90 and solo["unreadable"] is None
assert out["unreadable"] is None
# A failed PDF export is named as unreadable.
assert ats.unreadable("J0RD4N L33\n%PDF-1.7 obj <<>> endobj\n(cid:12)(cid:44)(cid:9) (cid:3)")
assert "PDF" in ats.unreadable("%PDF-1.7 " + "word " * 40)
assert "glyph" in ats.unreadable("(cid:12) " * 30 + "name " * 40)
assert ats.unreadable("12 34 56 %% ## " * 20)
print("all tests passed")
