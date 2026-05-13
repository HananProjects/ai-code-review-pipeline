"""
FastAPI webhook handler.

Deploy targets:
  GCP Cloud Run:  uvicorn webhook.handler:app --host 0.0.0.0 --port 8080
  AWS Lambda:     wrap `app` with Mangum (add mangum to requirements.txt)
"""
import hashlib
import hmac
import logging

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from github import Github

from config.settings import settings
from orchestrator.crew import run_parallel_review
from orchestrator.github_review import post_review

logger = logging.getLogger(__name__)
app = FastAPI(title="AI Code Review Webhook")


def _verify_signature(body: bytes, sig_header: str | None) -> None:
    if not sig_header or not sig_header.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Missing signature")
    expected = hmac.new(
        settings.github_webhook_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(f"sha256={expected}", sig_header):
        raise HTTPException(status_code=401, detail="Invalid signature")


def _run_review(repo_full_name: str, pr_number: int) -> None:
    """Runs in the background after GitHub receives our 202."""
    try:
        logger.info("Starting review for %s#%d", repo_full_name, pr_number)
        gh = Github(settings.github_token)
        repo = gh.get_repo(repo_full_name)
        pr = repo.get_pull(pr_number)
        commit_sha = pr.head.sha
        pr_files = list(pr.get_files())

        results = run_parallel_review(repo_full_name, pr_number)
        post_review(repo_full_name, pr_number, commit_sha, results, pr_files)
        logger.info("Review complete for %s#%d", repo_full_name, pr_number)
    except Exception:
        logger.exception("Review failed for %s#%d", repo_full_name, pr_number)


@app.post("/webhook", status_code=202)
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: str = Header(default=""),
    x_hub_signature_256: str = Header(default=""),
):
    body = await request.body()
    _verify_signature(body, x_hub_signature_256)

    if x_github_event != "pull_request":
        return {"status": "ignored", "event": x_github_event}

    payload = await request.json()
    action = payload.get("action", "")
    if action not in ("opened", "synchronize", "reopened"):
        return {"status": "ignored", "action": action}

    repo_full_name: str = payload["repository"]["full_name"]
    pr_number: int = payload["pull_request"]["number"]

    logger.info("Queued review for %s#%d (action=%s)", repo_full_name, pr_number, action)
    background_tasks.add_task(_run_review, repo_full_name, pr_number)
    return {"status": "accepted", "pr": pr_number}


@app.get("/health")
def health():
    return {"status": "ok"}
