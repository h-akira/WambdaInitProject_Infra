from aws_cdk import (
  Stack,
  aws_dynamodb as dynamodb,
  RemovalPolicy,
  Tags,
)
from constructs import Construct


class SSR001DynamoDBStack(Stack):
  """
  DynamoDB Table for WambdaInitProject SSR001 Backend
  """

  def __init__(
    self,
    scope: Construct,
    construct_id: str,
    table_name: str,
    environment: str,
    **kwargs
  ) -> None:
    super().__init__(scope, construct_id, **kwargs)

    # Create DynamoDB table
    table = dynamodb.Table(
      self, "SSR001Table",
      table_name=table_name,
      partition_key=dynamodb.Attribute(
        name="pk",
        type=dynamodb.AttributeType.STRING
      ),
      sort_key=dynamodb.Attribute(
        name="sk",
        type=dynamodb.AttributeType.STRING
      ),
      billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
      removal_policy=RemovalPolicy.RETAIN,
      point_in_time_recovery=True,
    )

    # Add tags
    Tags.of(self).add("Environment", environment)
    Tags.of(self).add("Name", "ssr001-dynamodb")

    # Output
    self.table = table
