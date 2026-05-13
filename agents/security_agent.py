from crewai import Agent, LLM, Task
from agents.tools import fetch_pr_diff, fetch_pr_metadata
from config.settings import settings


def build_security_agent() -> Agent:
    llm = LLM(model=f"anthropic/{settings.claude_model}", api_key=settings.anthropic_api_key)
    return Agent(
        role="Security Reviewer",
        goal="Identify security vulnerabilities, misconfigurations, and risky patterns in code changes",
        backstory=(
            "You are a senior application security engineer specializing in OWASP Top 10, "
            "injection attacks, secrets exposure, authentication flaws, and insecure dependencies. "
            "You provide precise, actionable findings with severity ratings (critical/high/medium/low)."
        ),
        tools=[fetch_pr_diff, fetch_pr_metadata],
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )


def build_security_task(agent: Agent, repo: str, pr_number: int) -> Task:
    return Task(
        description=(
            f"Review PR #{pr_number} in {repo} for security issues.\n"
            "Use fetch_pr_metadata then fetch_pr_diff to get the full picture.\n"
            "Check for: injection (SQL/command/SSTI), hardcoded secrets or tokens, "
            "insecure deserialization, broken auth/authz, SSRF, path traversal, "
            "vulnerable dependency additions, and missing input validation."
        ),
        expected_output=(
            "A markdown security report. Start with a 2-sentence summary.\n"
            "Then list each finding using EXACTLY this format:\n\n"
            "### Finding 1: <title>\n"
            "- **Severity:** Critical | High | Medium | Low\n"
            "- **File:** <relative/path/to/file.py>\n"
            "- **Line:** <line number>\n"
            "- **Description:** <what is wrong and why it is dangerous>\n"
            "- **Remediation:** <specific fix>\n\n"
            "If a finding is not tied to a specific line, omit the File and Line fields.\n"
            "End the report with a single line: Overall risk: pass | warn | block"
        ),
        agent=agent,
    )
