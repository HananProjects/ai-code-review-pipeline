from crewai.tools import tool
from github import Github
from config.settings import settings

_gh = Github(settings.github_token)


@tool("fetch_pr_diff")
def fetch_pr_diff(repo_full_name: str, pr_number: int) -> str:
    """Fetch the unified diff for a GitHub pull request."""
    repo = _gh.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)
    files = pr.get_files()
    parts = []
    for f in files:
        parts.append(f"### {f.filename} ({f.status}, +{f.additions}/-{f.deletions})")
        if f.patch:
            parts.append(f"```diff\n{f.patch}\n```")
    return "\n".join(parts)


@tool("fetch_pr_metadata")
def fetch_pr_metadata(repo_full_name: str, pr_number: int) -> str:
    """Fetch title, description, and file list for a GitHub pull request."""
    repo = _gh.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)
    files = [f.filename for f in pr.get_files()]
    return (
        f"Title: {pr.title}\n"
        f"Author: {pr.user.login}\n"
        f"Base: {pr.base.ref} ← Head: {pr.head.ref}\n"
        f"Description:\n{pr.body or '(none)'}\n"
        f"Changed files ({len(files)}):\n" + "\n".join(f"  - {f}" for f in files)
    )
