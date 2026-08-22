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
    dropped    description: foo:          (colon with no space after it)
    accepted   an indented, nested `short-description: Text: details`
    accepted   the same scalar under a sequence marker, `- thing: Text: details`
    accepted   a quoted key, `"description": Text: details`
    accepted   a non-ASCII key, `méta: Text: details`
    accepted   a spaced key, `some key: Text: details`
    accepted   space before the separator, `description : Text: details`
    dropped    a repeated key, required or not (`metadata:` twice)
    dropped    a colon scalar inside a flow collection, `[thing: Text: details]`
    dropped    a plain scalar continued onto a more-indented line with a colon
    accepted   description: [DEPRECATED] Use when: x   (read as literal text)
    accepted   description: [thing: Text: details]      (likewise)
    accepted   description: &summary Text: details      (anchor NOT resolved)
    accepted   a plain key containing `#`, `foo#bar: Text: details`
    accepted   a quoted key containing one, `"some # key": Text: details`
    accepted   a root mapping indented as a whole
    accepted   a stray trailing quote on a required key, `description": ...`
    dropped    a stray leading quote on one, `"description: ...`
    dropped    a plain key containing a colon, `foo:bar:` / `http://x:`
    dropped    an indented root whose unread key carries a bad flow value
    dropped    description: "unterminated                (a quote really parses)
    accepted   metadata: / `  thing: [thing: Text: details]`  (nested, so fine)
    accepted   description: {thing: details}             (rendered verbatim)
    dropped    description: [alpha, beta]                (a flow SEQUENCE is not)
    dropped    metadata: [thing: Text: details]          (same value, unread key)
    dropped    metadata: &summary Text: details          (likewise)
    accepted   description: - item: detail   (read as the string "- item: detail")
    dropped    metadata: - item: detail     (same value, unread top-level key)
    dropped    metadata: ? item: detail  /  metadata: : item: detail
    dropped    metadata: -ish thing: detail  (a leading `-` is enough)
    dropped    metadata: ,item Text: detail  (flow-entry indicator, same rule)
    accepted   description: [DEPRECATED #1] Use when: x  (decodes to "[DEPRECATED")
    dropped    a nested quoted key with an escaped quote, `"some \" : key":`
    accepted   metadata: / `  thing: - item: detail`   (nested, so fine)
    accepted   description: ? item: detail   (likewise)
    dropped    a repeated `description:` key (PyYAML keeps the last; the
               loader rejects the file) -- but only for fields it knows;
               a repeated unknown key is accepted
    dropped    metadata: anything that is not a mapping
    accepted   any value shape at all under a genuinely unknown key
    dropped    `name`/`description` supplied only via `<<: *defaults`
    accepted   description: 123 # TODO: x  -- decodes to the number 123

Required fields must decode to a non-empty string, and that is the one place
this script is deliberately stricter than the loader. `description: 123` and
`description: {thing: details}` both load, rendered verbatim; `description:
[alpha, beta]` and `description: null` are dropped. Rather than encode that
split -- which is arbitrary, undocumented by the loader, and free to change
between builds -- all four are reported. A required field that is not a string
is an authoring mistake whichever way the loader happens to treat it. Every
other rule here fails only what the loader actually drops.

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

# A `key: value` line whose value is on the same line, at any indent. Nested
# values matter: the loaders accept an indented `short-description: Text: details`,
# so a top-level-only rewrite would leave the retry failing on a file that loads.
# The `-` alternative covers a mapping entry under a sequence marker
# (`  - thing: Text: details`), which the loaders also accept.
#
# The key is matched loosely -- quoted, non-ASCII, containing spaces, and with
# whitespace before the separator -- because `"description": Text: details`,
# `méta: Text: details`, `some key: Text: details` and `description : Text:
# details` all load, and a tight `[A-Za-z0-9_.-]+` pattern refused to rewrite
# any of them.
#
# A loose key pattern makes a continuation line of a multi-line plain scalar
# (`  that continues here: yes`) look exactly like a mapping entry. That is
# handled structurally instead, by indent: see the skip in
# `_quote_colon_bearing_scalars`. Excluding spaced keys to dodge it would trade
# one false positive for another.
KEY_VALUE = re.compile(
    r"^([ \t]*(?:-[ \t]+)*)"          # indent, and any sequence markers
    r"(\"[^\"]*\"|'[^']*'|[^\s:#][^:]*?)"  # key: quoted, or plain
    r"[ \t]*:[ \t]+(\S.*)$"          # optional space, separator, value
)

# `key: |` / `key: >` opens a block scalar; every more-indented line below it is
# literal text, not a mapping, and must never be rewritten.
BLOCK_SCALAR = re.compile(
    r"^([ \t]*(?:-[ \t]+)*)"
    r"(?:\"[^\"]*\"|'[^']*'|[^\s:#][^:#]*?)[ \t]*:[ \t]*[|>]"
)

# "#" only opens a comment when it follows whitespace -- `foo#bar` is one scalar.
INLINE_COMMENT = re.compile(r"(?:^|\s)#")

# Values opening a quote, flow collection, block scalar, anchor, alias or tag
# are real YAML syntax. Re-quoting those would paper over a structural error the
# loaders reject, so they are left exactly as written.
# "#" is in this list because a value starting with it is a YAML comment, so the
# field decodes to null. Its comment text can itself contain a colon
# (`description: # TODO: fill in`), which would otherwise satisfy the rewrite
# predicate below and launder a null field into a passing string.
# Excluded on every key. A quote opens a scalar the loader really does parse --
# `description: "unterminated` is dropped -- and `#` opens a comment, so the
# field decodes to null and is dropped too.
ALWAYS_EXCLUDED = ("\"", "'", "#")

# Value prefixes that make PyYAML refuse a line the loader still accepts. These
# are what the retry quotes; the loader treats them as ordinary text.
#
# This list used to be applied only to "unread" top-level keys, on the strength
# of `metadata: [thing: Text: details]` being dropped. That generalisation was
# wrong. `metadata` is not an unread key -- it is a typed schema field, and the
# loader drops the file when it is not a mapping, whatever the value looks like
# (`metadata: plainstring` is dropped too). A genuinely unknown key is ignored
# outright, and every one of these shapes loads under one:
#
#     zzunknown: [thing: Text: details]    ACCEPTED
#     zzunknown: - item: detail            ACCEPTED
#     zzunknown: ,item Text: detail        ACCEPTED
#     zzunknown: ax thing: detail          ACCEPTED
#
# So there is no key-dependent exclusion here any more. Typed fields are
# checked by type instead, which is what actually decides it -- see
# TYPED_FIELDS.
STRUCTURAL_INDICATORS = (
    "[", "]", "{", "}", "|", ">", "&", "*", "!", "%", "@", "`", "-", "?", ":", ",",
)

# Fields the loader deserializes into a specific shape. A wrong type here drops
# the whole file, and this is the real rule behind every `metadata:` case that
# looked like "unread keys reject indicators":
#
#     metadata: plainstring                DROPPED
#     metadata: [thing: Text: details]     DROPPED
#     metadata: - item: detail             DROPPED
#     metadata:\n  a: b                    ACCEPTED
#
# Deliberately short. Only fields measured against the loader belong here --
# guessing at the schema is how the previous rule went wrong.
TYPED_FIELDS = {"metadata": dict}

# Duplicate keys are rejected by the loader, but only for fields it knows. A
# repeated unknown key is ignored along with the key itself:
#
#     description: twice          DROPPED
#     metadata: twice (mappings)  DROPPED
#     zzunknown: twice            ACCEPTED
#
# The earlier blanket rule came from probing a duplicated `metadata:` whose
# value was also the wrong type -- a sufficient cause on its own, which masked
# the real scope.
KNOWN_FIELDS = frozenset(REQUIRED) | frozenset(TYPED_FIELDS)

# A colon inside a plain scalar is the single construct the loaders tolerate and
# PyYAML does not, so it is the only thing the retry rewrites. Quoting any other
# value would destroy the type PyYAML correctly assigned it, and `description:
# null` would come back as the string "null" and wrongly pass.
# Colon *followed by whitespace* -- that is the construct the loaders tolerate.
# A value merely ending in a colon (`description: foo:`) is not it: the loader
# drops that skill, so it must stay a parse failure rather than be quoted into a
# passing string.
COLON_IN_VALUE = re.compile(r":\s")


def _strip_inline_comment(value):
    """Return the value as the loader decodes it, without any trailing comment."""
    match = INLINE_COMMENT.search(value)
    return value[: match.start()].rstrip() if match else value


def _quote_colon_bearing_scalars(block):
    """Return the block with colon-bearing plain scalar values quoted."""
    out = []
    # Lines indented deeper than this belong to a scalar started above -- a
    # block scalar body, or the continuation of a multi-line plain scalar.
    # Either way they are content, not mapping entries, and rewriting one would
    # corrupt the value it is part of.
    skip_deeper_than = None

    for line in block.splitlines():
        if skip_deeper_than is not None:
            indent = len(line) - len(line.lstrip())
            if line.strip() and indent <= skip_deeper_than:
                skip_deeper_than = None
            else:
                out.append(line)
                continue

        opener = BLOCK_SCALAR.match(line)
        if opener:
            skip_deeper_than = len(opener.group(1))
            out.append(line)
            continue

        match = KEY_VALUE.match(line)
        if match:
            indent, key, raw = match.group(1), match.group(2), match.group(3).rstrip()
            # This key carries a value on its own line, so anything more
            # indented below is that value continuing.
            skip_deeper_than = len(indent)
            # Compare and quote the decoded value, not the raw line: an inline
            # comment is not part of the value, and treating it as part of one
            # would let `description: 123 # TODO: details` masquerade as a string.
            # `#` is only a comment after whitespace, so `foo#bar` is a real
            # key -- but `some key # note` is not one, it is a key plus a
            # comment, and rewriting the line would swallow the comment.
            # Inside quotes none of that applies: `"some # key"` is ordinary
            # key text, and the loader accepts it.
            quoted_key = key.startswith(('"', "'"))
            if not quoted_key and INLINE_COMMENT.search(key):
                out.append(line)
                continue

            value = _strip_inline_comment(raw)
            # A colon is the usual reason a line needs quoting, but not the
            # only one. On a required key an indicator-leading value is legal
            # text to the loader while PyYAML still refuses it, and stripping
            # an inline comment can leave the colon behind while leaving the
            # indicator:
            #
            #     description: [DEPRECATED #1] Use when: reviewing
            #
            # decodes to "[DEPRECATED" -- the loader strips the comment too,
            # and loads. Testing only for a colon left that line unrewritten
            # and failed a skill that loads.
            needs_rewrite = bool(COLON_IN_VALUE.search(value)) or value.startswith(
                STRUCTURAL_INDICATORS
            )
            if (
                not raw.startswith(ALWAYS_EXCLUDED)
                and value
                and needs_rewrite
            ):
                out.append(f"{indent}{key}: {json.dumps(value)}")
                continue

        out.append(line)
    return "\n".join(out)


def _literal_top_level_keys(text):
    """Keys written directly in the mapping, before merge-key expansion.

    `yaml.safe_load` hides two things the loader cares about. It resolves
    `<<: *defaults`, so a skill whose `name` exists only in an anchor looks
    complete when the loader will not advertise it; and it silently keeps the
    last of a repeated key, so a botched merge conflict that leaves two
    `description:` lines reads as valid when the loader rejects the file. The
    node tree still has both, so read the keys from there.
    """
    node = yaml.compose(text)
    if not isinstance(node, yaml.MappingNode):
        return []
    return [k.value for k, _ in node.value if isinstance(k, yaml.ScalarNode)]


def parse_frontmatter(lines):
    """Return (mapping, literal_keys, error). `error` is None on success."""
    if not lines or lines[0].strip() != "---":
        return None, [], "missing YAML frontmatter delimited by ---"

    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        return None, [], "unterminated YAML frontmatter (no closing ---)"

    text = block = "\n".join(lines[1:end])
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as err:
        # Retry allowing the plain-scalar leniency the loaders have.
        text = _quote_colon_bearing_scalars(block)
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as retry_err:
            # Report the retry's error, not the first one. The first error is
            # often the tolerated colon scalar, which points the reader at a
            # line that is actually fine; the retry's error is the one left.
            detail = " ".join(str(retry_err).split())
            return None, [], f"frontmatter is not valid YAML: {detail}"

    if data is None:
        return None, [], "frontmatter block is empty"
    if not isinstance(data, dict):
        return None, [], f"frontmatter must be a YAML mapping, got {type(data).__name__}"
    # Compose the same text that parsed, so the keys match the data.
    return data, _literal_top_level_keys(text), None


def check(path):
    """Return a list of human-readable problems with one SKILL.md."""
    try:
        with open(path, encoding="utf-8") as handle:
            lines = handle.read().splitlines()
    except OSError as err:
        return [f"unreadable: {err}"]
    except UnicodeDecodeError as err:
        return [f"not valid UTF-8: {err}"]

    data, literal_keys, err = parse_frontmatter(lines)
    if err:
        return [err]

    problems = []
    duplicates = sorted(
        {
            k
            for k in literal_keys
            if k in KNOWN_FIELDS and literal_keys.count(k) > 1
        }
    )
    if duplicates:
        listed = ", ".join(f"`{k}`" for k in duplicates)
        problems.append(
            f"duplicate key(s) {listed} — the loader rejects the file outright "
            f"rather than keeping the last value"
        )

    for field, expected in TYPED_FIELDS.items():
        if field in data and not isinstance(data[field], expected):
            got = type(data[field]).__name__
            problems.append(
                f"field `{field}` must be a {expected.__name__}, got {got} — "
                f"the loader drops the whole file on a wrong type here"
            )

    for field in REQUIRED:
        if field not in literal_keys:
            if field in data:
                # Present after PyYAML expanded `<<: *anchor`, absent as far as
                # the loader is concerned -- it does not merge, and drops the
                # skill. Say which of the two it is; "missing" alone would send
                # someone looking for a key they can plainly see.
                problems.append(
                    f"field `{field}` is only supplied through a YAML merge key, "
                    f"which the loader does not expand"
                )
            else:
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
