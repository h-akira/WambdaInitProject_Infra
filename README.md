# WambdaInitProject Infrastructure CDK

AWS CDK (Python)によるWambdaInitProjectのインフラストラクチャ定義です。

## 構成

```
WambdaInitProject_Infra/
├── stacks/
│   ├── common/
│   │   └── cognito_stack.py          # Cognito User Pool & Client
│   ├── csr001/
│   │   └── main_stack.py             # S3 + CloudFront (Vue.js SPA)
│   └── ssr001/
│       ├── main_stack.py             # S3 + CloudFront (SSR)
│       └── dynamodb_stack.py         # DynamoDB Table
├── init/
│   └── cfn-execution-policies.yaml   # CDK Bootstrap用カスタムポリシー
├── app.py                            # CDKアプリケーションエントリーポイント
├── buildspec.yml                     # CodeBuild用ビルド仕様
├── config.json                       # 設定ファイル（環境変数、リソース名など）
├── config_sample.json                # 設定ファイルサンプル（CodeBuildで使用）
├── cdk.json                          # CDK設定
└── requirements.txt                  # Python依存関係
```

## セットアップ

### 前提条件

- Python 3.11以上
- Node.js（CDK CLI用）
- AWS CLI設定済み（`aws configure`または`~/.aws/credentials`）
- AWS_PROFILE=wambdaの設定

### 1. CDK CLIのインストール

```bash
npm install -g aws-cdk
cdk --version
```

### 2. Python仮想環境の作成と有効化

```bash
cd /Users/hakira/Programs/108_wambda-develop/WambdaInitProject_Infra
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 依存関係のインストール

```bash
cd /Users/hakira/Programs/108_wambda-develop/WambdaInitProject_Infra
pip install -r requirements.txt
```

### 4. CDK Bootstrap（初回のみ）

カスタムポリシーをデプロイしてからCDK Bootstrapを実行します。

```bash
cd /Users/hakira/Programs/108_wambda-develop/WambdaInitProject_Infra

# カスタムポリシーのデプロイ
AWS_PROFILE=wambda aws cloudformation deploy \
  --template-file init/cfn-execution-policies.yaml \
  --stack-name stack-wambda-infra-cfn-execution-policies \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ap-northeast-1

# ポリシーARNを動的に取得
COGNITO_DYNAMODB_ARN=$(AWS_PROFILE=wambda aws cloudformation describe-stacks \
  --stack-name stack-wambda-infra-cfn-execution-policies \
  --region ap-northeast-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`CognitoDynamoDBPolicyArn`].OutputValue' \
  --output text)

STORAGE_ARN=$(AWS_PROFILE=wambda aws cloudformation describe-stacks \
  --stack-name stack-wambda-infra-cfn-execution-policies \
  --region ap-northeast-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`StoragePolicyArn`].OutputValue' \
  --output text)

CONFIG_ARN=$(AWS_PROFILE=wambda aws cloudformation describe-stacks \
  --stack-name stack-wambda-infra-cfn-execution-policies \
  --region ap-northeast-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`ConfigPolicyArn`].OutputValue' \
  --output text)

IAM_ARN=$(AWS_PROFILE=wambda aws cloudformation describe-stacks \
  --stack-name stack-wambda-infra-cfn-execution-policies \
  --region ap-northeast-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`IAMPolicyArn`].OutputValue' \
  --output text)

# CDK Bootstrap実行
AWS_PROFILE=wambda cdk bootstrap \
  --cloudformation-execution-policies "${COGNITO_DYNAMODB_ARN},${STORAGE_ARN},${CONFIG_ARN},${IAM_ARN}" \
  --region ap-northeast-1
```

### 5. config.jsonの設定

`config_sample.json`をコピーして`config.json`を作成し、環境に合わせて値を設定してください。

```bash
cd /Users/hakira/Programs/108_wambda-develop/WambdaInitProject_Infra
cp config_sample.json config.json
# config.json を編集
```

## デプロイ

### 全スタックの確認

```bash
cd /Users/hakira/Programs/108_wambda-develop/WambdaInitProject_Infra
cdk ls
```

出力例:
```
stack-wambda-common-infra-cognito
stack-wambda-ssr001-infra-dynamodb
stack-wambda-ssr001-infra-main
stack-wambda-csr001-infra-main
```

### デプロイ順序

依存関係を考慮した推奨デプロイ順序：

```bash
cd /Users/hakira/Programs/108_wambda-develop/WambdaInitProject_Infra

# 1. Cognito（共通認証基盤）
AWS_PROFILE=wambda cdk deploy stack-wambda-common-infra-cognito

# 2. SSR001 DynamoDB
AWS_PROFILE=wambda cdk deploy stack-wambda-ssr001-infra-dynamodb

# 3. Backend（SAM）をデプロイ（CodeBuildまたは手動）
# SSR001: WambdaInitProject_SSR001 をデプロイ
# CSR001: WambdaInitProject_CSR001/Backend をデプロイ

# 4. SSR001 Main（SAMスタックからAPI Gateway URLを自動インポート）
AWS_PROFILE=wambda cdk deploy stack-wambda-ssr001-infra-main

# 5. CSR001 Main（SAMスタックからAPI Gateway URLを自動インポート）
AWS_PROFILE=wambda cdk deploy stack-wambda-csr001-infra-main

# 全スタック一括デプロイ
AWS_PROFILE=wambda cdk deploy --all
```

### スタックの削除

```bash
cd /Users/hakira/Programs/108_wambda-develop/WambdaInitProject_Infra

AWS_PROFILE=wambda cdk destroy stack-wambda-csr001-infra-main
AWS_PROFILE=wambda cdk destroy stack-wambda-ssr001-infra-main
AWS_PROFILE=wambda cdk destroy stack-wambda-ssr001-infra-dynamodb
AWS_PROFILE=wambda cdk destroy stack-wambda-common-infra-cognito
```

## CodeBuildによる自動デプロイ

`WambdaInitProject_CICD`リポジトリの`common/codebuild-infra.yaml`を使用してCodeBuildプロジェクトを作成してください。

### 必要な事前設定（Parameter Store）

```bash
cd /Users/hakira/Programs/108_wambda-develop

# ACM証明書ARN
AWS_PROFILE=wambda aws ssm put-parameter \
  --name "/WambdaInit/Common/ACM/arn" \
  --value "arn:aws:acm:us-east-1:XXXXXXXXXXXX:certificate/XXXXXXXX" \
  --type String \
  --region ap-northeast-1

# CSR001 S3バケット名
AWS_PROFILE=wambda aws ssm put-parameter \
  --name "/WambdaInit/CSR001/S3/contents/bucket_name" \
  --value "s3-wambda-csr001-contents-XXXXXXXXXXXX" \
  --type String \
  --region ap-northeast-1

# SSR001 S3バケット名
AWS_PROFILE=wambda aws ssm put-parameter \
  --name "/WambdaInit/SSR001/S3/contents/bucket_name" \
  --value "s3-wambda-ssr001-contents-XXXXXXXXXXXX" \
  --type String \
  --region ap-northeast-1

# SSR001 DynamoDBテーブル名
AWS_PROFILE=wambda aws ssm put-parameter \
  --name "/WambdaInit/SSR001/DynamoDB/main/table_name" \
  --value "wambda-table-ssr001" \
  --type String \
  --region ap-northeast-1
```

## 主な機能

### stack-wambda-common-infra-cognito
- Cognito User Pool作成
- Cognito User Pool Client作成（シークレット付き）
- SSM Parameter Storeへの認証情報保存
- パスワードポリシー設定（最小8文字、大文字/小文字/数字/記号必須）
- トークン有効期限設定（Access/ID: 5分、Refresh: 5日）

### stack-wambda-ssr001-infra-dynamodb
- DynamoDB Table作成
- パーティションキー: `pk`、ソートキー: `sk`
- オンデマンド課金モード
- ポイントインタイムリカバリ有効化
- 削除保護（RemovalPolicy.RETAIN）

### stack-wambda-ssr001-infra-main
- S3バケット作成（静的ファイル用）
- CloudFront Distribution作成
- Origin Access Control (OAC)設定
- カスタムドメイン設定（ACM証明書）
- API Gateway Origin（デフォルト: SSR、/static/*, /favicon.ico: S3）

### stack-wambda-csr001-infra-main
- S3バケット作成（フロントエンド静的ファイル用）
- CloudFront Distribution作成
- Origin Access Control (OAC)設定
- カスタムドメイン設定（ACM証明書）
- API Gateway Originの設定（/accounts/*, /api/*）
- SPAルーティング対応（404→200 /index.html）

## 有用なコマンド

* `cdk ls`          - スタック一覧表示
* `cdk synth`       - CloudFormationテンプレート生成
* `cdk deploy`      - スタックデプロイ
* `cdk diff`        - デプロイ済みスタックとの差分表示
* `cdk destroy`     - スタック削除

## 注意事項

1. **ACM証明書**: 事前にus-east-1リージョンで証明書を作成しておく必要があります。
2. **Route53**: DNSレコード設定は含まれていません。手動で設定してください。
3. **削除保護**: Cognito/DynamoDBはRemovalPolicy.RETAINに設定されています。
4. **API Gateway URL**: MainスタックはSAMスタックからAPI Gateway URLを自動的にインポートします。SAMテンプレートのOutputにExportが必要です。
