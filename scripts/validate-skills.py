#!/usr/bin/env python3
"""Validate every SKILL.md against the agent skill-loader contract.

Both Claude Code and Codex parse SKILL.md frontmatter as YAML and refuse to
load any skill whose frontmatter is missing, unparseable, or lacking a
non-empty `name` and `description`. The refusal is logged on the runner and is
invisible from inside the agent session, so a malformed skill silently
disappears from the library instead of failing loudly
(Alteriom/alteriom-dev-ops#2201).

This script is that missing loud failure. Exit 0 = every SKILL.md loads.

Why not "just run yaml.safe_load and fail on any error": the loaders are more
lenient than PyYAML about one construct, and matching PyYAML exactly would fail
skills that demonstrably load. Behaviour below was measured against the real
Codex loader (`codex debug prompt-input`, codex-cli 0.148.0), not assumed:

    accepted   description: Plain text. NOTE: with a colon-space in it
    accepted   description: >- (folded), 'single quoted', "double quoted"
    dropped    description: null            (and `description: # comment`)
    dropped    metadata: [unterminated      (structural YAML error)
    dropped    no description key at all

A plain scalar containing ": " is invalid per the YAML spec and PyYAML rejects
it, but the loaders accept it -- two skills in production rely on that today
(centris-extractor, prd-writer). So a strict parse failure is retried with
plain scalar values quoted; if it then parses, the file is one the loaders
accept. Only colon-bearing plain scalars are rewritten, and never one opening a
quote or a flow collection -- so a genuine structural error such as
`[unterminated` still fails, and a required field PyYAML typed as null or a
number keeps that type instead of being laundered into a passing string.

Deliberately NOT checked: `name` matching the directory name. The loaders key
skills off the directory, and many skills carry a human-readable `name`
("Next.js" in nextjs/) that loads fine.

Usage: scripts/validate-skills.py [root ...]   (default: repo root)
"""

import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    yaml = None

REQUIRED = ("name", "description")
SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__"}

# A top-level `key: value` line whose value is on the same line.
KEY_VALUE = re.compile(r"^([A-Za-z0-9_.-]+):[ \t]+(\S.*)$")

# Values opening a quote, flow collection, block scalar, anchor, alias or tag
# are real YAML syntax. Re-quoting those would paper over a structural error the
# loaders reject, so they are left exactly as written.
# "#" is in this list because a value starting with it is a YAML comment, so the
# field decodes to null. Its comment text can itself contain a colon
# (`description: # TODO: fill in`), which would otherwise satisfy the rewrite
# predicate below and launder a null field into a passing string.
YAML_INDICATORS = ("\"", "'", "[", "]", "{", "}", "|", ">", "&", "*", "!", "%", "@", "`", "#")

# A colon inside a plain scalar is the single construct the loaders tolerate and
# PyYAML does not, so it is the only thing the retry rewrites. Quoting any other
# value would destroy the type PyYAML correctly assigned it, and `description:
# null` would come back as the string "null" and wrongly pass.
COLON_IN_VALUE = re.compile(r":(\s|$)")


def _quote_colon_bearing_scalars(block):
    """Return the block with colon-bearing plain scalar values quoted."""
    out = []
    for line in block.splitlines():
        match = KEY_VALUE.match(line)
        value = match.group(2).rstrip() if match else ""
        if (
            match
            and not value.startswith(YAML_INDICATORS)
            and COLON_IN_VALUE.search(value)
        ):
            out.append(f"{match.group(1)}: {json.dumps(value)}")
        else:
            out.append(line)
    return "\n".join(out)


def parse_frontmatter(lines):
    """Return (mapping, error). Exactly one of the two is None."""
    if not lines or lines[0].strip() != "---":
        return None, "missing YAML frontmatter delimited by ---"

    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        return None, "unterminated YAML frontmatter (no closing ---)"

    block = "\n".join(lines[1:end])
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError as err:
        # Retry allowing the plain-scalar leniency the loaders have.
        try:
            data = yaml.safe_load(_quote_colon_bearing_scalars(block))
        except yaml.YAMLError as retry_err:
            # Report the retry's error, not the first one. The first error is
            # often the tolerated colon scalar, which points the reader at a
            # line that is actually fine; the retry's error is the one left.
            detail = " ".join(str(retry_err).split())
            return None, f"frontmatter is not valid YAML: {detail}"

    if data is None:
        return None, "frontmatter block is empty"
    if not isinstance(data, dict):
        return None, f"frontmatter must be a YAML mapping, got {type(data).__name__}"
    return data, None


def check(path):
    """Return a list of human-readable problems with one SKILL.md."""
    try:
        with open(path, encoding="utf-8") as handle:
            lines = handle.read().splitlines()
    except OSError as err:
        return [f"unreadable: {err}"]
    except UnicodeDecodeError as err:
        return [f"not valid UTF-8: {err}"]

    data, err = parse_frontmatter(lines)
    if err:
        return [err]

    problems = []
    for field in REQUIRED:
        if field not in data:
            problems.append(f"missing field `{field}`")
            continue
        value = data[field]
        if value is None:
            problems.append(f"field `{field}` is null")
        elif not isinstance(value, str):
            problems.append(
                f"field `{field}` must be a string, got {type(value).__name__}"
            )
        elif not value.strip():
            problems.append(f"field `{field}` is empty")
    return problems


def find_skill_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        if "SKILL.md" in filenames:
            yield os.path.join(dirpath, "SKILL.md")


def main(argv):
    # Fail closed. Without a YAML parser this could only do a weaker check, and
    # reporting "0 invalid" from a degraded run is the exact silent pass this
    # guard exists to prevent.
    if yaml is None:
        print(
            "ERROR: PyYAML is required to validate skill frontmatter "
            "(pip install pyyaml)",
            file=sys.stderr,
        )
        return 2

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
