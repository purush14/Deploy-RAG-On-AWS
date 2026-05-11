import boto3
from botocore.exceptions import NoCredentialsError
from langchain_aws import BedrockEmbeddings


def get_embedding_function(profile_name=None, region_name="eu-west-1"):
    print(f"Bedrock Embeddings — region: {region_name}, profile: {profile_name or 'default chain'}")
    session = boto3.Session(profile_name=profile_name, region_name=region_name)
    creds = session.get_credentials()
    if creds:
        print(f"Credential method: {creds.method}")
    else:
        print("No credentials found in session")
        raise NoCredentialsError()
    bedrock_client = session.client(service_name="bedrock-runtime")
    embeddings = BedrockEmbeddings(client=bedrock_client, model_id="amazon.titan-embed-text-v2:0")
    return embeddings
