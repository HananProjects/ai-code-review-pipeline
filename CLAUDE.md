# AI Code Review Pipeline — CLAUDE.md

## Mandatory Update Protocol

> **After every request, always:**
> 1. Update this `CLAUDE.md` with any new context, changes made, decisions taken, or current project state.
> 2. Update the Obsidian vault note at `B:\Obsidian Vault\Projects\AI Code Review Pipeline.md` to reflect the latest state.
> 3. Append an entry to `B:\Obsidian Vault\log.md`.

## Git Branch Workflow

> **Before doing any work on a request:**
> 1. Create a new branch from `main` named after the feature/fix (e.g. `feature/add-agent`, `fix/diff-parser`, `chore/update-deps`).
> 2. Do all work on that branch — never commit directly to `main`.
> 3. When the work is complete, summarize what the branch contains so it's ready to review and merge.
>
> Branch naming: `feature/<short-name>`, `fix/<short-name>`, or `chore/<short-name>`.

---

## Project Overview

**AI Code Review Pipeline** is an autonomous multi-agent system that reviews GitHub Pull Requests in real time — posting inline comments on specific lines of code, like CodeRabbit or Sourcery, but built from scratch.

- **Owner/developer:** Hanan (hananqazi21@gmail.com)
- **Location:** `B:\AI Code Review Pipeline\`
- **Repo:** `https://github.com/HananProjects/ai-code-review-pipeline`
- **Deployment:** GCP Cloud Run + Docker

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI Agents | CrewAI + Claude Sonnet 4.6 (Anthropic) |
| Webhook Server | FastAPI + Uvicorn |
| GitHub Integration | PyGithub + GitHub REST API v3 |
| Deployment | GCP Cloud Run + Docker |
| HTTP Client | httpx |
| Config | pydantic-settings (`.env`-based) |
| Language | Python 3.12 |

---

## Architecture

GitHub PR opened → FastAPI webhook (Cloud Run) → `202 Accepted` immediately → background task → Orchestrator runs 3 agents in parallel via `ThreadPoolExecutor`:

- **Security Agent** — OWASP Top 10: injection, hardcoded secrets, broken auth, path traversal, SSRF
- **Performance Agent** — N+1 queries, O(n²) algorithms, blocking I/O in async contexts, missing pagination
- **Style Agent** — bare excepts, unclear naming, duplicated logic, missing type hints, dead code

Findings are parsed for `File:` / `Line:` fields → validated against PR diff → posted as inline GitHub Review comments.

---

## Project Structure

```
B:\AI Code Review Pipeline\
├── agents/
│   ├── security_agent.py     ← OWASP / injection / secrets focus
│   ├── performance_agent.py  ← N+1 / algorithm / async I/O focus
│   ├── style_agent.py        ← naming / DRY / error handling focus
│   └── tools.py              ← fetch_pr_diff, fetch_pr_metadata
├── orchestrator/
│   ├── crew.py               ← ThreadPoolExecutor parallel runner
│   ├── parser.py             ← extract file:line findings from agent output
│   ├── diff_utils.py         ← parse PR diff for valid comment positions
│   └── github_review.py      ← post GitHub Review with inline comments
├── webhook/
│   └── handler.py            ← FastAPI, HMAC verification, background tasks
├── config/
│   └── settings.py           ← pydantic-settings, .env-based
├── scripts/
│   ├── dev.sh                ← start server + ngrok + register webhook
│   ├── setup_webhook.py      ← register/update/delete GitHub webhook
│   └── deploy_cloud_run.sh   ← build, push, deploy to GCP Cloud Run
├── tests/
│   └── test_orchestrator.py
├── Dockerfile
└── requirements.txt
```

---

## Environment Variables (`.env`)

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `GITHUB_TOKEN` | Fine-grained PAT — Pull requests: R/W + Webhooks: R/W |
| `GITHUB_WEBHOOK_SECRET` | Shared secret for HMAC webhook verification |
| `CLAUDE_MODEL` | Default: `claude-sonnet-4-6` |

---

## How to Run

### Local Dev
```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in keys
./scripts/dev.sh owner/your-repo   # starts server + ngrok + registers webhook
```

### Deploy to GCP Cloud Run
```bash
gcloud auth login
gcloud config set project your-project-id
gcloud run deploy ai-code-review \
    --source . \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars "ANTHROPIC_API_KEY=...,GITHUB_TOKEN=...,GITHUB_WEBHOOK_SECRET=..." \
    --timeout 300
python scripts/setup_webhook.py --repo owner/repo --url https://YOUR-SERVICE-URL/webhook
```

---

## Key Conventions

- Webhook always returns `202 Accepted` immediately — review runs in background thread
- HMAC-SHA256 signature verified on every incoming webhook payload
- Findings without a valid `file:line` fall back to the review summary body (never error out)
- Each agent verdict: `pass` / `warn` / `block` — one `block` escalates the whole review
- All three agents run concurrently — never sequentially

---

## Recent Changes

- 2026-06-17 — Fixed `github_review.py`: added fallback to include raw agent output when no structured `### Finding N:` blocks parse (was silently posting empty write-ups). Made `parser.py` regex more flexible (`(?:#{2,3}\s+|\*\*)?Finding\s+\d+`) to match varied LLM output formats.
- 2026-06-15 — Repo cloned to `B:\AI Code Review Pipeline\`; CLAUDE.md created; added to Obsidian vault

---

## Current State / Notes

<!-- Updated each session — current focus, open branches, blockers, next steps -->
