from aws_cdk import (
  Stack,
  aws_s3 as s3,
  aws_cloudfront as cloudfront,
  aws_cloudfront_origins as origins,
  aws_certificatemanager as acm,
  aws_route53 as route53,
  aws_route53_targets as targets,
  aws_iam as iam,
  RemovalPolicy,
  CfnOutput,
  Duration,
  Tags,
  Fn,
)
from constructs import Construct


class SSR001MainStack(Stack):
  """
  S3 + CloudFront Stack for WambdaInitProject SSR001 (SSR + API Gateway)
  Static files are served from S3 via CloudFront,
  all other requests are forwarded to API Gateway (Lambda SSR).
  """

  def __init__(
    self,
    scope: Construct,
    construct_id: str,
    domain_name: str,
    acm_certificate_arn: str,
    s3_bucket_name: str,
    s3_origin_path: str,
    backend_stack_name: str,
    hosted_zone_name: str,
    environment: str,
    **kwargs
  ) -> None:
    super().__init__(scope, construct_id, **kwargs)

    # Import API Gateway URL from Backend (SAM) stack output
    api_gateway_url = Fn.import_value(f"{backend_stack_name}-ApiUrl")

    # Extract domain and stage from URL
    api_gateway_domain_name = Fn.select(2, Fn.split("/", api_gateway_url))
    api_gateway_stage_name = Fn.select(3, Fn.split("/", api_gateway_url))

    # Create S3 bucket for static files
    static_bucket = s3.Bucket(
      self, "SSR001StaticBucket",
      bucket_name=s3_bucket_name,
      block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
      removal_policy=RemovalPolicy.RETAIN,
      auto_delete_objects=False,
    )

    # Import existing ACM certificate
    certificate = acm.Certificate.from_certificate_arn(
      self, "Certificate",
      certificate_arn=acm_certificate_arn
    )

    # Create Origin Access Control for S3
    s3_oac = cloudfront.S3OriginAccessControl(
      self, "SSR001S3OAC",
      signing=cloudfront.Signing.SIGV4_NO_OVERRIDE,
    )

    # Create S3 Origin (for static files)
    s3_origin = origins.S3BucketOrigin(
      static_bucket,
      origin_path=s3_origin_path,
      origin_access_control_id=s3_oac.origin_access_control_id,
    )

    # Create API Gateway Origin (SSR - default behavior)
    api_origin = origins.HttpOrigin(
      api_gateway_domain_name,
      origin_path=f"/{api_gateway_stage_name}",
      protocol_policy=cloudfront.OriginProtocolPolicy.HTTPS_ONLY,
    )

    # CloudFront distribution
    # SSR: API Gateway is the default origin, S3 is for static files only
    distribution = cloudfront.Distribution(
      self, "SSR001Distribution",
      default_behavior=cloudfront.BehaviorOptions(
        origin=api_origin,
        viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
        origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
        compress=True,
        allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
      ),
      additional_behaviors={
        "/static/*": cloudfront.BehaviorOptions(
          origin=s3_origin,
          viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
          compress=True,
          allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD,
        ),
        "/favicon.ico": cloudfront.BehaviorOptions(
          origin=s3_origin,
          viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
          compress=True,
          allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD,
        ),
      },
      domain_names=[domain_name],
      certificate=certificate,
      minimum_protocol_version=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
      enable_ipv6=True,
      http_version=cloudfront.HttpVersion.HTTP2,
      price_class=cloudfront.PriceClass.PRICE_CLASS_100,
    )

    # Grant CloudFront access to S3 bucket
    static_bucket.add_to_resource_policy(
      iam.PolicyStatement(
        actions=["s3:GetObject"],
        resources=[static_bucket.arn_for_objects("*")],
        principals=[iam.ServicePrincipal("cloudfront.amazonaws.com")],
        conditions={
          "StringEquals": {
            "AWS:SourceArn": f"arn:aws:cloudfront::{self.account}:distribution/{distribution.distribution_id}"
          }
        },
      )
    )

    # Lookup existing hosted zone
    hosted_zone = route53.HostedZone.from_lookup(
      self, "HostedZone",
      domain_name=hosted_zone_name,
    )

    # Create Route53 A record pointing to CloudFront
    route53.ARecord(
      self, "SSR001AliasRecord",
      zone=hosted_zone,
      record_name=domain_name,
      target=route53.RecordTarget.from_alias(targets.CloudFrontTarget(distribution)),
    )

    # Add tags
    Tags.of(self).add("Environment", environment)
    Tags.of(self).add("Name", "ssr001-main")

    # Outputs
    CfnOutput(
      self, "BucketName",
      value=static_bucket.bucket_name,
      description="S3 bucket name for SSR001 static files",
    )

    CfnOutput(
      self, "DistributionId",
      value=distribution.distribution_id,
      description="CloudFront distribution ID",
      export_name=f"{construct_id}-DistributionId",
    )

    CfnOutput(
      self, "DistributionDomainName",
      value=distribution.distribution_domain_name,
      description="CloudFront distribution domain name",
    )

    CfnOutput(
      self, "WebsiteURL",
      value=f"https://{domain_name}",
      description="Website URL",
    )

    self.bucket = static_bucket
    self.distribution = distribution
