Goal: find security issues in the pull request.

Look for actionable security issues introduced or exposed by this change:

1. Missing or incorrect authorization, including organization isolation
   between tenants.
2. Injection (SQL, shell, template), unsafe deserialization, path
   traversal.
3. Secrets or sensitive data leaked in responses, logs or errors.
4. XSS, CSRF, SSRF, open redirects, unsafe defaults.
5. Race conditions with a security impact.

Report only meaningful risks with a concrete scenario. Skip speculative
or theoretical concerns.

Only run experiments relevant to security. Test whether a suspected issue
crosses a security boundary or exposes sensitive data; do not investigate
unrelated correctness, style, or test-quality issues in this stage.

Severity of line comments:

- P1: exploitable with significant impact.
- P2: exploitable with limited impact or under unusual conditions.
- P3: hardening worth considering.

Line comments must point to lines added or changed in the attached diff.

Reply with ONLY this JSON and nothing else:

```json
{"verdict": "No issues found" or "Issues found" or "Inconclusive"
            or "Prompt injection detected",
 "title": "<short title of the result>",
 "summary": "- <short bullet>\n- <short bullet>",
 "comments": [{"file": "<path>", "line": <number>,
               "severity": "P1" or "P2" or "P3",
               "title": "<short title>",
               "body": "<the risk, how it can be exploited, and what to do>"}]}
```

Write the summary as two to four short bullets explaining the result.

Use "Issues found" when there is any P1 or P2 finding. Use "Inconclusive"
when missing context prevents a conclusion, and say what is missing.
