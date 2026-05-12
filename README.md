# Deploy RAG on AWS

A Retrieval-Augmented Generation (RAG) application that uses Amazon Bedrock for embeddings and ChromaDB as a local vector store.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          RAG Pipeline                                │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────┐      ┌──────────────────┐      ┌──────────────────┐
│              │      │                  │      │                  │
│  PDF Source  │─────▶│  Document Loader │─────▶│  Text Splitter   │
│  Documents   │      │  (PyPDF)         │      │  (Recursive)     │
│              │      │                  │      │                  │
└──────────────┘      └──────────────────┘      └────────┬─────────┘
                                                         │
                                                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                        Embedding & Storage                        │
│                                                                  │
│  ┌─────────────────────┐         ┌─────────────────────────┐    │
│  │   Amazon Bedrock    │         │      ChromaDB            │    │
│  │   (Titan Embed v2)  │────────▶│   (Local Vector Store)  │    │
│  │                     │         │                         │    │
│  └─────────────────────┘         └─────────────────────────┘    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
         │
         │  AWS Credentials (login/SSO/profile)
         ▼
┌──────────────────────────────────────────────────────────────────┐
│                         AWS Cloud                                 │
│                                                                  │
│  ┌─────────────────────┐         ┌─────────────────────────┐    │
│  │   IAM / Identity    │         │   Bedrock Runtime       │    │
│  │   Center            │────────▶│   (eu-west-1)           │    │
│  │                     │         │                         │    │
│  └─────────────────────┘         └─────────────────────────┘    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Data Flow

1. PDF documents are loaded from `src/data/source/`
2. Documents are split into chunks (600 chars, 120 overlap)
3. Each chunk is embedded via Amazon Bedrock Titan Embed v2
4. Embeddings are stored in ChromaDB at `src/data/chroma/`
5. Duplicate detection prevents re-processing existing documents

## Project Structure

```
├── image/                        # Docker/Lambda container
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src/
│       ├── app_api_handler.py    # FastAPI + Mangum handler
│       ├── data/chroma/          # ChromaDB vector store
│       └── rag_app/
│           ├── get_chroma_db.py
│           ├── get_embedding_function.py
│           └── query_rag.py
├── infra/                        # AWS CDK infrastructure
│   ├── app.py                    # CDK app entry point
│   ├── cdk.json
│   ├── requirements.txt
│   └── stacks/
│       └── rag_stack.py          # Lambda + API Gateway + ECR
├── pyproject.toml
└── requirements.txt
```

## Usage

```bash
# Populate the vector database
AWS_PROFILE=your-profile AWS_REGION=eu-west-1 uv run python populate_database.py

# Reset and rebuild the database
AWS_PROFILE=your-profile AWS_REGION=eu-west-1 uv run python populate_database.py --reset
```

## Requirements

- Python 3.13
- AWS account with Bedrock access (Titan Embed v2 model enabled)
- AWS credentials configured (SSO login, profile, or environment variables)
