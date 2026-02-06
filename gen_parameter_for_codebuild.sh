#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REGION=$(jq -r '.region' "$SCRIPT_DIR/config.json")

echo "=== Creating SSM Parameters from config.json ==="

aws ssm put-parameter \
  --name /WambdaInit/Common/ACM/arn \
  --value "$(jq -r '.csr001.acm_certificate_arn' "$SCRIPT_DIR/config.json")" \
  --type String \
  --overwrite \
  --region "$REGION"

aws ssm put-parameter \
  --name /WambdaInit/CSR001/S3/contents/bucket_name \
  --value "$(jq -r '.csr001.s3_bucket_name' "$SCRIPT_DIR/config.json")" \
  --type String \
  --overwrite \
  --region "$REGION"

aws ssm put-parameter \
  --name /WambdaInit/SSR001/S3/contents/bucket_name \
  --value "$(jq -r '.ssr001.s3_bucket_name' "$SCRIPT_DIR/config.json")" \
  --type String \
  --overwrite \
  --region "$REGION"

aws ssm put-parameter \
  --name /WambdaInit/SSR001/DynamoDB/main/table_name \
  --value "$(jq -r '.ssr001.dynamodb.table_name' "$SCRIPT_DIR/config.json")" \
  --type String \
  --overwrite \
  --region "$REGION"

echo "✓ Done"
