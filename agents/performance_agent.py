from crewai import Agent, LLM, Task
from agents.tools import fetch_pr_diff, fetch_pr_metadata
from config.settings import settings


def build_performance_agent() -> Agent:
    llm = LLM(model=f"anthropic/{settings.claude_model}", api_key=settings.anthropic_api_key)
    return Agent(
        role="Performance Reviewer",
        goal="Identify performance bottlenecks, inefficient algorithms, and resource waste in code changes",
        backstory=(
            "You are a performance engineering expert who identifies N+1 queries, "
            "missing indexes, O(n²) algorithms, memory leaks, unnecessary network calls, "
            "and blocking I/O in async code. You quantify impact and suggest concrete optimizations."
        ),
        tools=[fetch_pr_diff, fetch_pr_metadata],
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )


def build_performance_task(agent: Agent, repo: str, pr_number: int) -> Task:
    return Task(
        description=(
            f"Review PR #{pr_number} in {repo} for performance issues.\n"
            "Use fetch_pr_metadata then fetch_pr_diff to examine the changes.\n"
            "Check for: N+1 database queries, missing pagination, inefficient loops, "
            "large in-memory collections, missing caching opportunities, synchronous I/O "
            "in async contexts, and expensive operations inside hot paths."
        ),
        expected_output=(
            "A markdown performance report. Start with a 2-sentence summary.\n"
            "Then list each finding using EXACTLY this format:\n\n"
            "### Finding 1: <title>\n"
            "- **Impact:** High | Medium | Low\n"
            "- **File:** <relative/path/to/file.py>\n"
            "- **Line:** <line number>\n"
            "- **Description:** <what is slow and why>\n"
            "- **Suggestion:** <specific optimization>\n\n"
            "If a finding is not tied to a specific line, omit the File and Line fields.\n"
            "End the report with a single line: Performance verdict: pass | warn | block"
        ),
        agent=agent,
    )
