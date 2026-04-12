#!/usr/bin/env bash
# Deploy the React frontend to S3 and invalidate CloudFront cache.
# Usage: ./deploy.sh <s3-bucket-name> <cloudfront-distribution-id> [api-url]
set -euo pipefail

BUCKET="${1:?Usage: $0 <bucket> <cf-distribution-id> [api-url]}"
CF_DIST_ID="${2:?Usage: $0 <bucket> <cf-distribution-id> [api-url]}"
API_URL="${3:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Building React app..."
if [ -n "$API_URL" ]; then
  REACT_APP_API_URL="$API_URL" npm run build --prefix "$SCRIPT_DIR"
else
  npm run build --prefix "$SCRIPT_DIR"
fi

echo "==> Syncing build/ to s3://${BUCKET}..."
aws s3 sync "$SCRIPT_DIR/build/" "s3://${BUCKET}/" \
  --delete \
  --cache-control "public,max-age=31536000,immutable" \
  --exclude "index.html"

# index.html must not be cached so browsers always get the latest shell
aws s3 cp "$SCRIPT_DIR/build/index.html" "s3://${BUCKET}/index.html" \
  --cache-control "no-cache,no-store,must-revalidate"

echo "==> Invalidating CloudFront cache (distribution: ${CF_DIST_ID})..."
aws cloudfront create-invalidation \
  --distribution-id "$CF_DIST_ID" \
  --paths "/*"

echo "==> Frontend deployed successfully."
