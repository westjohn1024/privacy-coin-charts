import aws_cdk as core
from aws_cdk import assertions
from infra.infra_stack import InfraStack


def test_fetcher_lambda_created():
    app = core.App()
    stack = InfraStack(app, "infra")
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::Lambda::Function", 1)