#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.rag_stack import RagStack

app = cdk.App()

RagStack(
    app,
    "RagStack",
    env=cdk.Environment(
        account="020200816632",
        region="eu-west-1",
    ),
)

app.synth()
