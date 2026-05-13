#!/usr/bin/env bash
# Deploy to GCP Cloud Run and register the GitHub webhook.
#
# Prerequisites:
#   gcloud auth login && gcloud auth configure-docker
#   gcloud projects create <PROJECT_ID> (or use existing)
#   Enable: Cloud Run, Cloud Build, Artifact Registry APIs
#
# Usage:
#   ./scripts/deploy_cloud_run.sh owner/repo

set -euo pipefail

REPO="${1:?Usage: ./scripts/deploy_cloud_run.sh owner/repo}"

PROJECT_ID="${GCP_PROJECT_ID:?Set GCP_PROJECT_ID in env}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="ai-code-review"
IMAGE="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "==> Building and pushing Docker image..."
docker build -t "$IMAGE" .
docker push "$IMAGE"

echo "==> Deploying to Cloud Run ($REGION)..."
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE" \
    --region "$REGION" \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars "$(grep -v '^#' .env | xargs | tr ' ' ',')" \
    --min-instances 0 \
    --max-instances 10 \
    --timeout 300 \
    --concurrency 10

SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --region "$REGION" \
    --format "value(status.url)")

echo "==> Service URL: $SERVICE_URL"

echo "==> Registering GitHub webhook..."
python scripts/setup_webhook.py --repo "$REPO" --url "$SERVICE_URL/webhook"

echo ""
echo "Deployed! Health check:"
curl -s "$SERVICE_URL/health"
echo ""
