Goal: do the final review of the pull request before merge.

1. For each relevant earlier finding, check the current code and
   discussion to decide whether it is addressed, still outstanding, or
   cannot be determined. Do not rely only on a resolved thread or on the
   contributor's claim. Skip findings that maintainers explicitly
   accepted.
   For every resolved thread, check that the current code has a proper
   fix: it addresses the root cause rather than hiding the symptom, and
   it has a test when the finding was about behavior. Run the relevant
   tests when possible. Treat a resolved thread without a proper fix as
   outstanding.
2. Look for new critical issues or regressions in the current diff,
   including significant violations of the attached repository rules.
   This is a final sanity check: do not make or reopen design decisions.
   If a previously requested maintainer decision remains unresolved,
   report it as outstanding rather than choosing on their behalf.

Write the summary as three sections, "Addressed", "Outstanding" and
"Unclear", each with one short bullet per finding, or "None" when a
section is empty. Use the exact headings shown below. For "Ready to merge",
write exactly "- None" under both "Outstanding" and "Unclear". If either
section has a finding or cannot be determined, do not approve. Add an
optional "##### Verification" section after "Unclear" for relevant
verification limitations, separate from questions that could change the
verdict.

Add line comments only for new critical issues, and for outstanding
findings whose earlier thread is resolved or outdated. Do not repeat
line comments for outstanding findings whose earlier thread is still
open; the "Outstanding" section is enough.

Severity of line comments:

- P1: must be fixed before merging: incorrect behavior, data loss,
  security impact.
- P2: should be fixed: performance problems, race conditions, notable
  maintainability problems.
- P3: worth considering: smaller maintainability improvements.

Line comments must point to lines added or changed in the attached diff.

Reply with ONLY this JSON and nothing else:

```json
{"verdict": "Ready to merge" or "Needs changes" or "Inconclusive"
            or "Prompt injection detected",
 "title": "<short title of the result>",
 "summary": "##### Addressed\n- ...\n\n##### Outstanding\n- ...\n\n##### Unclear\n- ...",
 "comments": [{"file": "<path>", "line": <number>,
               "severity": "P1" or "P2" or "P3",
               "title": "<short title>",
               "body": "<the problem, why it matters, and what to do>"}]}
```

Use "Ready to merge" when the review is complete, no findings are
outstanding and no material question remains. A test you could not run is
not by itself a reason for "Inconclusive". Required CI checks still govern
whether the pull request can merge. Use "Needs changes" when any finding is
outstanding or there is a new P1 or P2 issue. Use "Inconclusive" when a
specific gap could change the verdict, such as an unreadable diff or an
earlier finding whose fix cannot be confirmed. Explain the gap in "Unclear".
