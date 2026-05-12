from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_ecr_assets as ecr_assets,
)
from constructs import Construct
import os


class RagStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Lambda function — CDK builds and pushes the image automatically
        rag_function = _lambda.DockerImageFunction(
            self,
            "RagFunction",
            function_name="rag-app-handler",
            code=_lambda.DockerImageCode.from_image_asset(
                directory=os.path.join(os.path.dirname(__file__), "../../image"),
                platform=ecr_assets.Platform.LINUX_AMD64,
            ),
            memory_size=1024,
            timeout=Duration.seconds(60),
            architecture=_lambda.Architecture.X86_64,
            environment={
                "IS_USING_IMAGE_RUNTIME": "True",
                "CHROMA_PATH": "data/chroma",
            },
        )

        # Grant Bedrock access to the Lambda function
        rag_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                resources=["*"],
            )
        )

        # API Gateway REST API (publicly accessible)
        api = apigw.RestApi(
            self,
            "RagApi",
            rest_api_name="RAG API",
            description="Public API for RAG application",
            endpoint_types=[apigw.EndpointType.EDGE],
            deploy_options=apigw.StageOptions(stage_name="prod"),
        )

        # Lambda integration (proxy forwards all requests to FastAPI)
        integration = apigw.LambdaIntegration(rag_function)

        # Root route
        api.root.add_method("ANY", integration)

        # Catch-all proxy route — forwards /docs, /openapi.json, /submit_query, etc.
        proxy = api.root.add_proxy(
            default_integration=integration,
            any_method=True,
        )

        # Output the public URLs
        CfnOutput(
            self,
            "ApiUrl",
            value=api.url,
            description="Public API Gateway URL",
        )
        CfnOutput(
            self,
            "SwaggerUrl",
            value=f"{api.url}docs",
            description="Swagger UI URL",
        )
