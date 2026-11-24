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
# A real quote passes, an invented one does not.
assert [e["found"] for e in out["evidence"]] == [True, False]
# Education dates are ignored; the two jobs overlap by 3 months.
assert [f["title"] for f in out["dateFlags"]] == ["Overlapping roles"], out["dateFlags"]
# No keywords: the score is the fit, clamped to 0..100.
assert ats.check(resume, {"fit": 140})["score"] == 100.0
# Word boundaries: "java" is not found inside "javascript".
assert not ats.present("Java", ats.normalize("JavaScript and TypeScript"))
assert ats.present("JS", ats.normalize("JavaScript and TypeScript"))
print("all tests passed")
