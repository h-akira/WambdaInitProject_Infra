#!/usr/bin/env python3
import os
import json
import aws_cdk as cdk

from stacks import (
  CognitoStack,
  CSR001MainStack,
  SSR001MainStack,
  SSR001DynamoDBStack,
)

# Load configuration from config.json
with open("config.json", "r") as f:
  config = json.load(f)

# Get account from environment or config
account = config.get("account") or os.getenv("CDK_DEFAULT_ACCOUNT")
region = config["region"]
environment = config["environment"]

app = cdk.App()

# Stack 1: Cognito (Common Authentication)
cognito_stack = CognitoStack(
  app,
  "stack-wambda-common-infra-cognito",
  user_pool_name=config["cognito"]["user_pool_name"],
  client_name=config["cognito"]["client_name"],
  ssm_prefix=config["cognito"]["ssm_prefix"],
  environment=environment,
  env=cdk.Environment(account=account, region=region),
  description="Cognito User Pool and Client for WambdaInitProject",
)

# Stack 2: SSR001 DynamoDB Table
ssr001_dynamodb_stack = SSR001DynamoDBStack(
  app,
  "stack-wambda-ssr001-infra-dynamodb",
  table_name=config["ssr001"]["dynamodb"]["table_name"],
  environment=environment,
  env=cdk.Environment(account=account, region=region),
  description="DynamoDB table for WambdaInitProject SSR001",
)

# Stack 3: SSR001 Main (S3 + CloudFront)
# Deploy this after SAM stack (SSR001 backend) is deployed
ssr001_main_stack = SSR001MainStack(
  app,
  "stack-wambda-ssr001-infra-main",
  domain_name=config["ssr001"]["domain_name"],
  acm_certificate_arn=config["ssr001"]["acm_certificate_arn"],
  s3_bucket_name=config["ssr001"]["s3_bucket_name"],
  s3_origin_path=config["ssr001"]["s3_origin_path"],
  backend_stack_name=config["ssr001"]["backend_stack_name"],
  environment=environment,
  env=cdk.Environment(account=account, region=region),
  description="S3 + CloudFront for WambdaInitProject SSR001",
)

# Stack 4: CSR001 Main (S3 + CloudFront)
# Deploy this after SAM stack (CSR001 backend) is deployed
csr001_main_stack = CSR001MainStack(
  app,
  "stack-wambda-csr001-infra-main",
  domain_name=config["csr001"]["domain_name"],
  acm_certificate_arn=config["csr001"]["acm_certificate_arn"],
  s3_bucket_name=config["csr001"]["s3_bucket_name"],
  s3_origin_path=config["csr001"]["s3_origin_path"],
  backend_stack_name=config["csr001"]["backend_stack_name"],
  environment=environment,
  env=cdk.Environment(account=account, region=region),
  description="S3 + CloudFront for WambdaInitProject CSR001 (Vue.js SPA)",
)

app.synth()
