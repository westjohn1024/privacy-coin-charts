from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_ssm as ssm,
)
from constructs import Construct


class InfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Private, versioned bucket for the price history.
        # RETAIN keeps the data even if this stack is ever deleted.
        bucket = s3.Bucket(
            self, "DataBucket",
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # The fetcher. Only lambda_function.py from the repo root is uploaded.
        fn = _lambda.Function(
            self, "Fetcher",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset(
                "..", exclude=["*", ".*", "!lambda_function.py"]
            ),
            timeout=Duration.seconds(30),
            environment={"BUCKET_NAME": bucket.bucket_name},
        )

        # Permissions: read/write/list the bucket, read the API key.
        bucket.grant_read_write(fn)
        cmc_key = ssm.StringParameter.from_secure_string_parameter_attributes(
            self, "CmcKey", parameter_name="/privacy-coins/cmc-api-key"
        )
        cmc_key.grant_read(fn)

        CfnOutput(self, "BucketName", value=bucket.bucket_name)
        CfnOutput(self, "FunctionName", value=fn.function_name)