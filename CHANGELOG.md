# Changelog

## 1.2.0

Found by running the skill on a sales resume, an unreadable file and requests with no job posting.

- The report has an "Editing will not fix" line for blockers that rewording cannot change: location, years of experience, market segment, a required language. The closing sentence says whether the posting is a realistic target.
- A readability-only mode for "is my resume ATS friendly" with no job posting: checks, flags and fixes, no score.
- The script names an unreadable resume (`unreadable`) and returns no score when there is no job.
- Keywords: guidance on what counts, so the list is not padded with minor duties. A repeated keyword counts once.
- "C" is no longer found inside "C++" or "C#". "Go" matches "Golang".
- A PDF ligature no longer breaks an evidence quote.
- An education section called "Schooling" or "Academic background" is not read as a job.
- The skill states the 2-month overlap tolerance and that readability is not part of the score.
- Bad input gives a one-line error instead of a traceback.

## 1.1.1

- `ats_check.py` returns `wordCount`, which settles the 150-word rule of the readability check.
- The readability check fails if either condition is true, and a failed check is explained in a recruiter flag.
- When five fixes are already taken, a synonym-only match is marked in the Matched line instead of taking a fix.

## 1.1.0

- `ats_check.py --job job.txt` lists keywords that are not in the job posting (`keywordsNotInJob`), so a keyword the model reworded or invented is caught.
- The script returns `matchedCount` and `keywordCount` for the "6 of 9" line of the report.
- The skill says how to treat joined terms in a posting, that one fix may cover related keywords, and that temporary files are removed after the check.
- Tests run on every push with GitHub Actions.

## 1.0.1

- The skill calls the script by its full path. The first version used a path relative to the user's folder, where the script does not exist.
- `ats_check.py` lists keywords found in the resume only under another spelling (`matchedBySynonym`).
- Clarified the limits on flags and fixes, the importance of listed duties, compound requirements, the readability threshold and how the report ends.

## 1.0.0

- First release: the skill, the verification script with 66 synonym groups, and the plugin manifests.
