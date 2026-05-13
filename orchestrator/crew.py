from concurrent.futures import ThreadPoolExecutor, as_completed

from crewai import Crew, Process

from agents.security_agent import build_security_agent, build_security_task
from agents.performance_agent import build_performance_agent, build_performance_task
from agents.style_agent import build_style_agent, build_style_task


def _run_crew(agent_fn, task_fn, repo: str, pr_number: int) -> str:
    agent = agent_fn()
    task = task_fn(agent, repo, pr_number)
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)
    result = crew.kickoff()
    return str(result)


def run_parallel_review(repo: str, pr_number: int) -> dict[str, str]:
    """Returns {'security': ..., 'performance': ..., 'style': ...}."""
    specs = {
        "security": (build_security_agent, build_security_task),
        "performance": (build_performance_agent, build_performance_task),
        "style": (build_style_agent, build_style_task),
    }
    results = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {
            pool.submit(_run_crew, agent_fn, task_fn, repo, pr_number): name
            for name, (agent_fn, task_fn) in specs.items()
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception as exc:
                results[name] = f"_Agent failed: {exc}_\nOverall risk: warn"
    return results
