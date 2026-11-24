---
name: ats-resume-checker
description: "Check a resume against a job description the way an applicant tracking system (ATS) and a recruiter would. Returns a match score from 0 to 100, the job keywords found and missing, each requirement with a quote from the resume as proof, ATS readability checks, recruiter red flags (date overlaps, gaps, typos) and the fixes that raise the score most. Use when someone asks to check, scan, score or review a resume or CV for ATS, asks for an ATS score or resume match score, asks why a resume gets no interviews, or wants to tailor a resume to a job posting. Triggers: ATS resume checker, resume checker, resume scanner, ATS score, CV checker, check my resume, is my resume ATS friendly, resume keywords, match resume to job description."
license: MIT
metadata:
  version: "1.1.1"
  homepage: "https://hiretop.com/ats-resume-checker"
---

# ATS resume checker

Compare one resume with one job posting and report how well they match, with evidence for every claim.

This is the method behind the free web checker at https://hiretop.com/ats-resume-checker. The model judges fit and extracts keywords. A script then verifies the parts a model can get wrong: whether a keyword is literally in the text, whether a quote exists in the resume, whether the dates add up, and the final score.

## What you need

1. **The resume as text.** If the user gives a PDF or DOCX, read it and work with the extracted text. An ATS also works with extracted text, so judge the text and say nothing about fonts, colours or columns you cannot see.
2. **The full job posting.** A job title alone is too little to check against. If the user gives under about 40 characters, or only a link you cannot open, ask them to paste the posting with its responsibilities and requirements.

If the resume text is nearly empty or garbled, stop and say so: the file is probably a scan or an image, and an ATS will not read it either.

Base every judgment on the two texts. Never invent a skill, employer, title, number or date that is not in the resume.

## Step 1. Draft the analysis

Work through these parts in order.

### Fit (0 to 100)

Weigh roughly:

- Required hard skills and keyword coverage, about 45%: how many of the job's must-have skills, tools and technologies appear in the resume.
- Title and role alignment, about 20%: does the most recent title match the target role and level.
- Experience and seniority, about 20%: years, scope and relevance against what the job asks.
- Responsibilities and domain, about 15%: overlap between past duties and the job's domain.

Be strict and use the full range. 90 to 100 is near perfect, 70 to 89 strong, 50 to 69 partial with several key requirements missing, 30 to 49 weak, 0 to 29 poor or the wrong field. Most real resumes land between 40 and 75. Penalise missing required skills heavily and missing nice-to-haves only slightly.

### Keywords (at most 20 in total)

Take the most important concrete keywords from the job posting only: hard skills, tools, technologies, frameworks, platforms, certifications, methodologies and the role title. Use the job's exact wording, most critical first. When the posting joins terms ("batch and streaming pipelines"), keep the phrase as written or take the single words that carry it ("streaming"); do not build a phrase the posting never uses.

Leave out academic degrees, years-of-experience phrases ("5+ years"), soft skills (communication, teamwork, leadership) and filler (responsibilities, stakeholders).

Split them into matched and missing. Treat well-known synonyms and acronyms as equal in either direction (Kubernetes and K8s, PostgreSQL and Postgres, CI/CD and continuous integration). The role title counts as matched only if the resume states that title, or an accepted synonym, for one of the candidate's own roles. "Senior Account Executive" against a job for "Account Director" is missing, and the gap belongs in a title fix.

### Requirements (5 to 10)

Break the posting into its most important requirements: skills, experience, scope, domain, languages, location. Write each as a short phrase in the job's wording and mark it Required or Nice to have. Duties listed under responsibilities count as Required unless the posting calls them optional. When one line of the posting names several skills and the resume has only some of them, keep it as one requirement and mark it Partial.

Give each a status:

- **Met**: the resume clearly shows it.
- **Partial**: the resume shows something related but weaker.
- **Missing**: nothing in the resume supports it.

For Met and Partial, give evidence: a verbatim quote of 5 to 25 words copied character for character from the resume. No paraphrase, no ellipsis, never a quote from the job posting. Missing has no evidence.

### ATS readability (exactly 3 checks)

Judge only whether the text is clean and parseable. Mark each check passed or failed honestly; many real resumes fail one.

1. **Clear section headings**: standard sections such as Experience, Education and Skills are present and labelled.
2. **Contact details present**: there is an email, and ideally a phone number and location.
3. **Quantified, keyword-rich content**: the text holds relevant skills and measurable results. It fails if either is true: fewer than two bullets carry a number or a measurable result, or the whole resume is under 150 words. Two strong bullets do not rescue a resume that short. The script reports the word count in step 2; correct this check if your estimate was wrong. When the check fails, say why in a recruiter flag.

Status follows the checks: 2 or 3 passed is Passed, exactly 1 is Needs work, 0 passed or garbled text is Failed.

### Recruiter flags (0 to 5 of your own)

Things a recruiter notices in a quick scan that could cost an interview: typos or inconsistent spelling, unclear or inflated titles, location or work authorisation against the job, missing contact details, vague bullets with no results, an overly long resume. Give each a severity (High, Medium, Low), a short title and one sentence that names the exact issue and quotes the typo or the vague phrase.

Leave dates to the script in step 2: overlaps, gaps, future dates and short tenures.

### Top fixes (at most 5)

The actions that would raise the score most, ordered High, then Medium, then Low. Give at most 5 in total: up to 3 High, up to 3 Medium, up to 2 Low. Skip a level when the resume has no gap of that kind.

- **High**: a missing required skill or keyword, or a major title or experience mismatch.
- **Medium**: align title wording, add quantified impact, add a missing section.
- **Low**: polish, such as spelling out an acronym.

Each fix names the actual gap. One fix may cover two or three missing keywords that belong together, such as an orchestrator and a modelling tool. Give a title of up to 8 words in the imperative, and one sentence on what to change and why. For High and Medium fixes that add or rewrite content, add one example bullet of up to 25 words that starts with an action verb and uses square-bracket placeholders for facts only the candidate knows ("[X]%", "[team size]"). Never fill in a real number, employer or outcome yourself.

A fix may ask the candidate to add a skill only if they have it. Say so when the skill is missing from the resume: "If you have used Airflow, name it."

## Step 2. Verify with the script

The script is `scripts/ats_check.py` in this skill's own folder, next to this file. That is not the user's working directory, so call it by its full path: the base directory shown when this skill loaded, or the folder you read this file from. If the resume or the job posting is not already a plain-text file, save its text to one. Write `draft.json` beside them, then run:

```bash
python3 <this skill's folder>/scripts/ats_check.py --resume resume.txt --job job.txt --draft draft.json
```

`draft.json` holds your fit score, your two keyword lists and every evidence quote, each copied exactly as it appears in your requirements table:

```json
{
  "fit": 62,
  "matched": ["Python", "SQL"],
  "missing": ["Airflow", "dbt"],
  "evidence": ["Built ETL pipelines in PySpark that load 3M+ records a day"]
}
```

Apply the output:

- **`matched` and `missing`** replace your lists. Keywords in `recovered` were in the resume after all, so delete any fix that tells the candidate to add one of them.
- **`keywordsNotInJob`** are keywords the posting does not contain, even as a synonym. Replace each with the posting's own wording, or drop it, then run the script again. A keyword may only come from the job.
- **`matchedBySynonym`** are keywords the resume has only under another spelling (the job says "Apache Spark", the resume says "PySpark"). Keep them matched and add a Low fix to write the job's exact term next to the existing one. If the five fixes are already taken by High and Medium gaps, skip that fix and mark the keyword in the Matched line instead: `Apache Spark (written as PySpark)`.
- **`matchedNotLiteral`** are keywords you matched on meaning that are in the resume neither as text nor as a known synonym. Keep them matched, and tell the candidate to write the exact term, because an ATS keyword filter would miss it.
- **`evidence`**: for every quote with `found: false`, drop the quote and set every requirement that used it to Missing. One quote may back two requirements when it proves both.
- **`dateFlags`** go into the recruiter flags with their `detail` as written, ahead of yours when the severity is equal. The report holds at most 6 flags in total: if there are more, drop your own lowest-severity flags first.
- **`score`**, **`coverage`** and **`fit`** are the three numbers in the report's first two lines, and **`matchedCount`** of **`keywordCount`** is the "6 of 9" beside the coverage.
- **`wordCount`** settles the 150-word rule of the third readability check.

Delete `draft.json` and any text files you created for the script once you have the output. Leave the user's own files alone.

If you cannot run scripts, do the same by hand:

1. Search the resume for each missing keyword and its common synonyms, and move any you find to matched.
2. Re-read each quote against the resume and drop any that is not there word for word.
3. Check each pair of job date ranges for overlaps and gaps.
4. Compute the score: `0.6 × (matched ÷ (matched + missing) × 100) + 0.4 × fit`, to one decimal. With no keywords, the score is the fit.

## Step 3. Report

Use this layout. Keep every line short.

```
## ATS match score: 64.8 / 100 (partial match)

Keyword coverage 66.7% (6 of 9) · Fit 62.0

### Keywords
Matched: Python, SQL, AWS, Apache Spark, Postgres, ETL
Missing: Airflow, dbt, Snowflake

### Requirements
| Requirement | Importance | Status | Evidence from the resume |
|---|---|---|---|

### ATS readability: Passed
- [x] Clear section headings
- [x] Contact details present
- [ ] Quantified, keyword-rich content

### Recruiter flags
- **Medium · Overlapping roles.** "Jun 2021 - Jun 2023" and "Mar 2023 - Present" overlap by 3 months.

### Top fixes
1. **High · Name Airflow if you have used it.** One sentence on what and why.
   Example: "Scheduled [N] daily pipelines in Airflow, cutting failed runs by [X]%."
```

Bands for the heading: 75 and above is a strong match, 50 to 74.9 a partial match, below 50 a weak match.

In the requirements table, leave the evidence cell of a Missing row as a dash.

End with one sentence that is specific to this resume, then one line offering to check again after edits. Add nothing else after the report.

## After the report

- When the candidate comes back with an edited resume, run the whole check again and compare the new score with the old one.
- If asked to rewrite the resume, reword and reorder what is there. Do not add skills, tools, titles or numbers the candidate has not confirmed.
- One resume is checked against one job. For several jobs, run the check once for each and report the scores side by side.
- If the candidate asks what the score means: it measures the match with this posting. It does not rate the candidate, and no checker can promise an interview.
