#!/bin/bash

set -e

AWS_PROFILE=wambda
REGION=ap-northeast-1
STACK_NAME=stack-wambda-infra-cfn-execution-policies

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Deploying CloudFormation Execution Policies Stack ==="
echo "Stack: $STACK_NAME"
echo "Region: $REGION"
echo ""

aws cloudformation deploy \
  --profile "$AWS_PROFILE" \
  --region "$REGION" \
  --template-file "$SCRIPT_DIR/cfn-execution-policies.yaml" \
  --stack-name "$STACK_NAME" \
  --capabilities CAPABILITY_NAMED_IAM

echo ""
echo "✓ Done"
