import re


def valid_lines(patch: str | None) -> set[int]:
    """Return the set of new-file line numbers that GitHub allows inline comments on."""
    if not patch:
        return set()
    result: set[int] = set()
    current = 0
    for raw in patch.split("\n"):
        m = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", raw)
        if m:
            current = int(m.group(1)) - 1
        elif raw.startswith("-"):
            continue
        elif raw.startswith("+") or raw.startswith(" "):
            current += 1
            result.add(current)
    return result


def build_line_index(pr_files) -> dict[str, set[int]]:
    """Map filename → set of commentable line numbers from the PR diff."""
    return {f.filename: valid_lines(f.patch) for f in pr_files}
