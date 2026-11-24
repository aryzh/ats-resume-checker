# ATS Resume Checker: open-source Claude skill

[![test](https://github.com/aryzh/ats-resume-checker/actions/workflows/test.yml/badge.svg)](https://github.com/aryzh/ats-resume-checker/actions/workflows/test.yml)
[![licence: MIT](https://img.shields.io/badge/licence-MIT-blue.svg)](LICENSE)

Check a resume against a job description and get an ATS match score, the missing keywords and the fixes that raise the score. It runs inside Claude as a skill, and the same check is free in the browser.

**Try it without installing anything: [hiretop.com/ats-resume-checker](https://hiretop.com/ats-resume-checker?utm_source=github&utm_medium=readme&utm_campaign=ats-skill)** (free, no sign-up, PDF or DOCX, 5 checks a day).

This repository holds the method behind that web checker: the scoring rubric, the keyword rules, the synonym table and the script that verifies the result.

## What an ATS resume check gives you

An applicant tracking system (ATS) stores the text of your resume and lets recruiters search and filter it by keywords from the job posting. A resume that lacks those words, or whose text comes out scrambled, is hard to find. This skill compares one resume with one job posting and reports:

| Part of the report | What it tells you |
|---|---|
| ATS match score, 0 to 100 | How closely the resume matches this job |
| Matched and missing keywords | Which of the job's skills, tools and titles are in the resume, and which are absent |
| Requirements table | Each requirement of the job marked Met, Partial or Missing, with a quote from your resume as proof |
| ATS readability | Whether the text has clear section headings, contact details and measurable results |
| Recruiter red flags | Overlapping dates, employment gaps, future dates, typos, vague bullets |
| Top fixes | Up to five changes, most important first, each with an example bullet to adapt |

## Example report

A fictional data engineer's resume ([`sample_resume.txt`](tests/sample_resume.txt)) checked against a Senior Data Engineer posting ([`sample_job_senior.txt`](tests/sample_job_senior.txt)), shortened here.

```
## ATS match score: 39.4 / 100 (weak match)

Keyword coverage 35.7% (5 of 14) · Fit 45.0

### Keywords
Matched: Python, SQL, Apache Spark, AWS, batch pipelines
Missing: Senior Data Engineer, Apache Airflow, dbt, Snowflake, Kafka, CI/CD, ...

### Requirements
| Requirement                        | Importance | Status  | Evidence from the resume                          |
|------------------------------------|------------|---------|---------------------------------------------------|
| 5+ years in data engineering       | Required   | Partial | "Data engineer with 4 years of experience ..."    |
| Strong Python and SQL              | Required   | Met     | "Maintained Python jobs that ingest CSV feeds..." |
| Set up CI/CD for data pipelines    | Required   | Missing | -                                                 |

### ATS readability: Passed
- [x] Clear section headings
- [x] Contact details present
- [ ] Quantified, keyword-rich content

### Recruiter flags
- Medium · Overlapping roles. "Jun 2021 - Jun 2023" and "Mar 2023 - Present"
  overlap by 3 months. Fix the typo, or say the roles were concurrent.

### Top fixes
1. High · Name Airflow and dbt if you have used them.
   Example: "Orchestrated [N] daily pipelines in Apache Airflow and modelled [N] tables in dbt."
5. Low · Write "Apache Spark" next to PySpark.
```

The date overlap and the "Apache Spark" note come from the script, which checks both on every run.

## Install the skill

### Claude Code

```bash
/plugin marketplace add aryzh/ats-resume-checker
```

```bash
/plugin install ats-resume-checker@ats-resume-checker
```

### Claude desktop and claude.ai

Download this repository as a ZIP, then upload the `skills/ats-resume-checker` folder as a skill in Settings, under Capabilities.

### By hand

Copy `skills/ats-resume-checker` into `~/.claude/skills/`.

## Use it

Give Claude a resume and a full job posting, then ask in your own words:

- "Check my resume against this job description."
- "What is my ATS score for this role?"
- "Which keywords from the job posting are missing in my CV?"
- "Is my resume ATS friendly?"
- "Tailor my resume to this job, but don't invent anything."

Paste the whole posting, with its responsibilities and requirements. A job title alone is too short to check against.

## How the ATS score is calculated

```
score = 0.6 × keyword coverage + 0.4 × fit
```

- **Keyword coverage** is the share of the job's top keywords (at most 20) found in the resume. Synonyms count: "K8s" matches "Kubernetes", "Postgres" matches "PostgreSQL". The table has 66 groups and lives in [`ats_check.py`](skills/ats-resume-checker/scripts/ats_check.py).
- **Fit** is the model's judgment of required skills (about 45%), title and level (20%), experience and seniority (20%), responsibilities and domain (15%).

Most real resumes score between 40 and 75. A score of 75 or more is a strong match, 50 to 74.9 a partial match, below 50 a weak one.

### What the script verifies

A language model can call a keyword missing when it is in the text, or quote a line the resume never contained. [`ats_check.py`](skills/ats-resume-checker/scripts/ats_check.py) checks the draft before you see it:

- A keyword marked missing that is in the resume, directly or as a synonym, moves to matched.
- Every evidence quote is searched for in the resume. A quote that is not there is dropped, and the requirement becomes Missing.
- A keyword in the resume only under another spelling ("PySpark" for "Apache Spark") is reported, so you can write the job's exact term.
- A keyword that is not in the job posting at all is reported, so the model cannot pad the list with its own wording.
- Job dates are parsed for overlaps, gaps, future dates and ranges that run backwards.
- The final score is computed from the corrected keyword lists.

The script uses the Python standard library and sends nothing anywhere. You can run it yourself:

```bash
python3 skills/ats-resume-checker/scripts/ats_check.py --resume tests/sample_resume.txt --job tests/sample_job.txt --draft tests/sample_draft.json
```

## ATS resume checkers by role

The [web version](https://hiretop.com/ats-resume-checker?utm_source=github&utm_medium=readme&utm_campaign=ats-skill) has pages for single professions, such as DevOps engineer, product manager and account executive, each with the keywords recruiters search for in that role.

## FAQ

### What is an ATS resume checker?

A tool that reads your resume the way an applicant tracking system does, as plain text, and compares it with a job description. It shows which of the job's keywords the resume contains and where the text would be hard for a recruiter to find or read.

### Is this ATS resume checker free?

Yes. The skill is open source under the MIT licence, and the [web checker](https://hiretop.com/ats-resume-checker?utm_source=github&utm_medium=readme&utm_campaign=ats-skill) gives 5 free checks a day without an account. Inside Claude the check uses your own Claude plan.

### What is a good ATS score?

With this rubric, 75 or more means the resume covers most of what the job asks. Most resumes we see land between 40 and 75. The score is specific to one job posting: the same resume can score 74 for one role and 49 for another.

### Does it work with a CV, a PDF or a DOCX?

Yes. "CV" and "resume" are treated the same. Claude reads PDF and DOCX files, and the web checker accepts both up to 2 MB. Resumes and job postings should be in English.

### Will a high score get me an interview?

No checker can promise that. The score shows how well the text matches one posting. A recruiter still decides, and employers configure their ATS in different ways.

### Is my resume stored?

The skill runs inside your own Claude session, so your resume goes where your Claude conversations go, and the script runs on your machine. The web checker reads the file in your browser and sends the extracted text for scoring. It keeps the resume in Hiretop's candidate database unless you tick "Don't save my resume" before checking.

### Can it rewrite my resume?

It can reword and reorder what is already there. The skill is told never to add a skill, employer, title or number you have not confirmed, and example bullets use placeholders such as "[X]%" for facts only you know.

## Related

- [ats-resume-text](https://github.com/aryzh/ats-resume-text): a command-line tool that prints the plain text an ATS extracts from a PDF resume and flags layouts that scramble it.
- [Hiretop](https://hiretop.com/?utm_source=github&utm_medium=readme&utm_campaign=ats-skill): the tech recruiters who built this checker.

## Contributing

Synonym groups are the easiest place to help. If the checker called a keyword missing when your resume had it under another spelling, [open a synonym issue](https://github.com/aryzh/ats-resume-checker/issues/new?template=synonym.yml) with both spellings, or add a group to `SYNONYM_GROUPS` in `ats_check.py`.

```bash
python3 tests/test_ats_check.py
```

Changes are listed in the [changelog](CHANGELOG.md).

## Licence

MIT. See [LICENSE](LICENSE).
