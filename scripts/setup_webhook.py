#!/usr/bin/env python3
"""
Register (or update) the GitHub webhook for this review pipeline.

Usage:
    python scripts/setup_webhook.py --repo owner/repo --url https://your-host/webhook
    python scripts/setup_webhook.py --repo owner/repo --url https://your-host/webhook --delete
"""
import argparse
import secrets
import sys

from github import Github, GithubException

EVENTS = ["pull_request"]
CONTENT_TYPE = "json"


def load_env() -> tuple[str, str]:
    """Read GITHUB_TOKEN and GITHUB_WEBHOOK_SECRET from .env without importing settings."""
    token, webhook_secret = "", ""
    try:
        with open(".env") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GITHUB_TOKEN="):
                    token = line.split("=", 1)[1].strip()
                elif line.startswith("GITHUB_WEBHOOK_SECRET="):
                    webhook_secret = line.split("=", 1)[1].strip()
    except FileNotFoundError:
        pass
    return token, webhook_secret


def find_existing(repo, url: str):
    for hook in repo.get_hooks():
        if hook.config.get("url") == url:
            return hook
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage GitHub webhook for AI code review")
    parser.add_argument("--repo", required=True, help="owner/repo (e.g. acme/my-service)")
    parser.add_argument("--url", required=True, help="Public HTTPS URL of /webhook endpoint")
    parser.add_argument("--delete", action="store_true", help="Remove the webhook instead of creating it")
    args = parser.parse_args()

    gh_token, webhook_secret = load_env()

    if not gh_token:
        print("ERROR: GITHUB_TOKEN not found in .env", file=sys.stderr)
        sys.exit(1)

    if not webhook_secret or webhook_secret in ("your-webhook-secret", ""):
        webhook_secret = secrets.token_hex(32)
        print(f"Generated new webhook secret: {webhook_secret}")
        print("Add this to your .env file as GITHUB_WEBHOOK_SECRET=<value>")

    gh = Github(gh_token)
    try:
        repo = gh.get_repo(args.repo)
    except GithubException as e:
        print(f"ERROR: cannot access {args.repo}: {e.data.get('message', e)}", file=sys.stderr)
        sys.exit(1)

    existing = find_existing(repo, args.url)

    if args.delete:
        if existing:
            existing.delete()
            print(f"Deleted webhook #{existing.id} from {args.repo}")
        else:
            print("No matching webhook found — nothing to delete")
        return

    config = {
        "url": args.url,
        "content_type": CONTENT_TYPE,
        "secret": webhook_secret,
        "insecure_ssl": "0",
    }

    if existing:
        existing.edit(name="web", config=config, events=EVENTS, active=True)
        print(f"Updated existing webhook #{existing.id} on {args.repo}")
        print(f"  URL:    {args.url}")
        print(f"  Events: {', '.join(EVENTS)}")
    else:
        hook = repo.create_hook(name="web", config=config, events=EVENTS, active=True)
        print(f"Created webhook #{hook.id} on {args.repo}")
        print(f"  URL:    {args.url}")
        print(f"  Events: {', '.join(EVENTS)}")

    print("\nDone. Open a test PR to verify delivery.")


if __name__ == "__main__":
    main()
