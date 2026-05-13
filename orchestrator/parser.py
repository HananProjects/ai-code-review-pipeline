import re
from dataclasses import dataclass


@dataclass
class Finding:
    title: str
    body: str
    file: str | None
    line: int | None


def parse_findings(agent_output: str) -> list[Finding]:
    """Extract structured findings from an agent's markdown report."""
    findings = []
    blocks = re.split(r"\n###\s+Finding\s+\d+", agent_output, flags=re.IGNORECASE)
    for block in blocks[1:]:
        title_m = re.match(r"[:\s]*(.+?)(?:\n|$)", block)
        title = title_m.group(1).strip(" *:`") if title_m else "Finding"

        file_m = re.search(r"\*\*File:\*\*\s*`?([^\s`\n,]+)`?", block)
        line_m = re.search(r"\*\*Line:\*\*\s*(\d+)", block)

        file = file_m.group(1).strip() if file_m else None
        line = int(line_m.group(1)) if line_m else None

        findings.append(Finding(title=title, body=block.strip(), file=file, line=line))

    return findings


def extract_verdict(agent_output: str) -> str:
    last = agent_output.strip().splitlines()[-1].lower()
    if "block" in last:
        return "BLOCK"
    if "warn" in last:
        return "WARN"
    return "PASS"
