from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_ssm as ssm,
    aws_events as events,
    aws_events_targets as targets,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
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

        # Run at 00:00, 06:00, 12:00 and 18:00 UTC.
        events.Rule(
            self, "FourTimesDaily",
            schedule=events.Schedule.cron(minute="0", hour="0,6,12,18"),
            targets=[targets.LambdaFunction(fn, retry_attempts=2)],
        )

        # Email me if the function errors.
        alert_email = self.node.try_get_context("alert_email")
        topic = sns.Topic(self, "Alerts")
        if alert_email:
            topic.add_subscription(subs.EmailSubscription(alert_email))

        alarm = cloudwatch.Alarm(
            self, "FetcherErrors",
            metric=fn.metric_errors(period=Duration.hours(1)),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            alarm_description="privacy-coin fetcher failed at least once in the last hour",
        )
        alarm.add_alarm_action(cw_actions.SnsAction(topic))

        CfnOutput(self, "BucketName", value=bucket.bucket_name)
        CfnOutput(self, "FunctionName", value=fn.function_name)