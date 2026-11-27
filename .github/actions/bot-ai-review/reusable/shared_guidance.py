"""Extracts the shared OpenWISP AI guidance used by every review.

Usage: shared_guidance.py <agents-md> <guidance-output> <notes-output>

- Copies the SECTIONS of the shared AGENTS.md from openwisp-opencode-configs,
  each with its subsections.
- Writes a note for every section that cannot be found, and when the file
  could not be downloaded, so the review continues without it.
"""

import os
import sys

SECTIONS = ("Writing Style", "Repository Instructions", "Credential Safety", "Reviews")
INTRO = (
    "Follow these rules from the shared OpenWISP AI configuration. The"
    " instructions above still decide how pull request content and repository"
    " AGENTS.md files are used.\n"
)


def extract(text, title):
    lines = [line.rstrip() for line in text.splitlines()]
    heading = f"## {title}"
    if heading not in lines:
        return None
    section = [heading]
    start = lines.index(heading) + 1
    for line in lines[start:]:
        if line.startswith(("# ", "## ")):
            break
        section.append(line)
    return "\n".join(section).strip()


def build(text):
    if text is None:
        return "", ["- Note: the shared AI guidance could not be downloaded."]
    found = []
    notes = []
    for title in SECTIONS:
        section = extract(text, title)
        if section is None:
            notes.append(f'- Note: shared AI guidance section "{title}" was not found.')
        else:
            found.append(section)
    guidance = "\n\n".join([INTRO, *found]) + "\n" if found else ""
    return guidance, notes


def main():
    source, guidance_path, notes_path = sys.argv[1:4]
    text = None
    if os.path.isfile(source):
        with open(source, encoding="utf-8", errors="replace") as f:
            text = f.read()
    guidance, notes = build(text)
    with open(guidance_path, "w", encoding="utf-8") as f:
        f.write(guidance)
    with open(notes_path, "w", encoding="utf-8") as f:
        f.write("".join(f"{note}\n" for note in notes))


if __name__ == "__main__":
    main()
