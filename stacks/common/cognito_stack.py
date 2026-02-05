from aws_cdk import (
  Stack,
  aws_cognito as cognito,
  aws_ssm as ssm,
  Duration,
  RemovalPolicy,
  Tags,
)
from constructs import Construct


class CognitoStack(Stack):
  """
  Cognito User Pool and Client for WambdaInitProject (common)
  """

  def __init__(
    self,
    scope: Construct,
    construct_id: str,
    user_pool_name: str,
    client_name: str,
    ssm_prefix: str,
    environment: str,
    **kwargs
  ) -> None:
    super().__init__(scope, construct_id, **kwargs)

    # Create Cognito User Pool
    user_pool = cognito.UserPool(
      self, "WambdaCommonUserPool",
      user_pool_name=user_pool_name,
      self_sign_up_enabled=True,
      sign_in_aliases=cognito.SignInAliases(
        email=True,
        username=True,
      ),
      auto_verify=cognito.AutoVerifiedAttrs(email=True),
      password_policy=cognito.PasswordPolicy(
        min_length=8,
        require_lowercase=True,
        require_uppercase=True,
        require_digits=True,
        require_symbols=True,
      ),
      account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
      removal_policy=RemovalPolicy.RETAIN,
      sign_in_case_sensitive=False,
    )

    # Create Cognito User Pool Client
    user_pool_client = cognito.UserPoolClient(
      self, "WambdaCommonUserPoolClient",
      user_pool=user_pool,
      user_pool_client_name=client_name,
      generate_secret=True,
      auth_flows=cognito.AuthFlow(
        admin_user_password=True,
        custom=False,
        user_password=False,
        user_srp=False,
      ),
      access_token_validity=Duration.minutes(5),
      id_token_validity=Duration.minutes(5),
      refresh_token_validity=Duration.days(5),
      enable_token_revocation=True,
      prevent_user_existence_errors=True,
      supported_identity_providers=[
        cognito.UserPoolClientIdentityProvider.COGNITO
      ],
    )

    # Store Cognito details in SSM Parameter Store
    ssm.StringParameter(
      self, "UserPoolIdParameter",
      parameter_name=f"{ssm_prefix}/user_pool_id",
      string_value=user_pool.user_pool_id,
      description="Cognito User Pool ID for WambdaInitProject",
      tier=ssm.ParameterTier.STANDARD,
    )

    ssm.StringParameter(
      self, "ClientIdParameter",
      parameter_name=f"{ssm_prefix}/client_id",
      string_value=user_pool_client.user_pool_client_id,
      description="Cognito User Pool Client ID for WambdaInitProject",
      tier=ssm.ParameterTier.STANDARD,
    )

    ssm.StringParameter(
      self, "ClientSecretParameter",
      parameter_name=f"{ssm_prefix}/client_secret",
      string_value=user_pool_client.user_pool_client_secret.unsafe_unwrap(),
      description="Cognito User Pool Client Secret",
      tier=ssm.ParameterTier.STANDARD,
    )

    # Add tags
    Tags.of(self).add("Environment", environment)
    Tags.of(self).add("Name", "cognito-wambda-common")

    # Outputs
    self.user_pool = user_pool
    self.user_pool_client = user_pool_client
