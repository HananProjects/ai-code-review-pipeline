from crewai import Agent, LLM, Task
from agents.tools import fetch_pr_diff, fetch_pr_metadata
from config.settings import settings


def build_style_agent() -> Agent:
    llm = LLM(model=f"anthropic/{settings.claude_model}", api_key=settings.anthropic_api_key)
    return Agent(
        role="Code Style Reviewer",
        goal="Ensure code quality, readability, naming conventions, and maintainability",
        backstory=(
            "You are a senior engineer who enforces clean code principles: clear naming, "
            "single-responsibility functions, DRY, proper error handling, adequate test coverage, "
            "and idiomatic language patterns. You balance strictness with pragmatism."
        ),
        tools=[fetch_pr_diff, fetch_pr_metadata],
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )


def build_style_task(agent: Agent, repo: str, pr_number: int) -> Task:
    return Task(
        description=(
            f"Review PR #{pr_number} in {repo} for code style and quality.\n"
            "Use fetch_pr_metadata then fetch_pr_diff to examine the changes.\n"
            "Check for: unclear variable/function names, overly complex functions, "
            "duplicated logic, missing or misleading comments, improper error handling "
            "(bare excepts, swallowed exceptions), missing type hints, and dead code.\n"
            "Distinguish between blocking issues and nit-level suggestions."
        ),
        expected_output=(
            "A markdown style report. Start with a 2-sentence summary.\n"
            "Then list each finding using EXACTLY this format:\n\n"
            "### Finding 1: <title>\n"
            "- **Type:** block | nit\n"
            "- **File:** <relative/path/to/file.py>\n"
            "- **Line:** <line number>\n"
            "- **Description:** <what is wrong>\n"
            "- **Suggestion:** <specific improvement>\n\n"
            "If a finding is not tied to a specific line, omit the File and Line fields.\n"
            "End the report with a single line: Quality verdict: pass | warn | block"
        ),
        agent=agent,
    )
