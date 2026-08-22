#!/usr/bin/env python3
"""Validate every SKILL.md against the agent skill-loader contract.

Both Claude Code and Codex refuse to load a skill whose SKILL.md lacks a
`---`-delimited YAML frontmatter block carrying a non-empty `name` and
`description`. The refusal is logged on the runner and is invisible from
inside the agent session, so a malformed skill silently disappears from the
library instead of failing loudly (Alteriom/alteriom-dev-ops#2201).

This script is that missing loud failure. Exit 0 = every SKILL.md loads.

Deliberately NOT checked: `name` matching the directory name. The loaders key
skills off the directory, and many skills here carry a human-readable `name`
("Next.js" in nextjs/) that loads fine.

Usage: scripts/validate-skills.py [root ...]   (default: repo root)
"""

import os
import sys

REQUIRED = ("name", "description")
SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__"}


def frontmatter_keys(lines):
    """Return (keys, error). keys maps top-level frontmatter key -> value."""
    if not lines or lines[0].strip() != "---":
        return None, "missing YAML frontmatter delimited by ---"

    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        return None, "unterminated YAML frontmatter (no closing ---)"

    keys = {}
    for line in lines[1:end]:
        # Only top-level scalars; indented lines and list items belong to a
        # parent key, and a bare `#` line is a comment.
        if not line.strip() or line.startswith((" ", "\t", "-", "#")):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        keys[key.strip()] = value.strip()
    return keys, None


def check(path):
    """Return a list of human-readable problems with one SKILL.md."""
    try:
        with open(path, encoding="utf-8") as handle:
            lines = handle.read().splitlines()
    except OSError as err:
        return [f"unreadable: {err}"]
    except UnicodeDecodeError as err:
        return [f"not valid UTF-8: {err}"]

    keys, err = frontmatter_keys(lines)
    if err:
        return [err]

    problems = []
    for field in REQUIRED:
        if field not in keys:
            problems.append(f"missing field `{field}`")
        elif not keys[field].strip().strip("\"'"):
            problems.append(f"empty field `{field}`")
    return problems


def find_skill_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        if "SKILL.md" in filenames:
            yield os.path.join(dirpath, "SKILL.md")


def main(argv):
    roots = argv[1:] or [os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]

    found = []
    for root in roots:
        found.extend(find_skill_files(root))
    found.sort()

    if not found:
        print(f"ERROR: no SKILL.md found under {', '.join(roots)}", file=sys.stderr)
        return 2

    failures = [(path, problems) for path in found if (problems := check(path))]

    for path, problems in failures:
        rel = os.path.relpath(path)
        for problem in problems:
            print(f"::error file={rel}::{problem}")
            print(f"FAIL {rel}: {problem}", file=sys.stderr)

    print(f"scanned {len(found)} SKILL.md file(s); {len(failures)} invalid")
    if failures:
        print(
            "A skill that fails here is dropped by the loader at session start "
            "without any error the agent can see.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
