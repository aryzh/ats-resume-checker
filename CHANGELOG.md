# Changelog

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
