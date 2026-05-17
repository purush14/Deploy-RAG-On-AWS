# Deploy RAG on AWS

A Retrieval-Augmented Generation (RAG) application deployed on AWS using Lambda, API Gateway, DynamoDB, and Amazon Bedrock.

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              Frontend                                         │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │              GitHub Pages (Static Chat UI)                           │     │
│  │              https://username.github.io                              │     │
│  └──────────────────────────────────┬──────────────────────────────────┘     │
│                                     │                                        │
└─────────────────────────────────────┼────────────────────────────────────────┘
                                      │ HTTPS
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                              AWS Cloud (eu-west-1)                            │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │                    API Gateway (REST, Edge)                          │     │
│  │                    /prod/submit_query  (POST)                        │     │
│  │                    /prod/get_query/{id} (GET)                        │     │
│  │                    /prod/docs          (Swagger UI)                  │     │
│  └──────────────────────────────────┬──────────────────────────────────┘     │
│                                     │                                        │
│                                     ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │                 Lambda (Docker Image, x86_64)                        │     │
│  │                 FastAPI + Mangum                                     │     │
│  │                                                                     │     │
│  │  ┌───────────┐    ┌──────────────┐    ┌─────────────────────────┐  │     │
│  │  │ ChromaDB  │    │ query_rag.py │    │ get_embedding_function  │  │     │
│  │  │ (vectors) │◀──▶│ (RAG logic)  │───▶│ (Bedrock Titan v2)      │  │     │
│  │  └───────────┘    └──────┬───────┘    └─────────────────────────┘  │     │
│  │                          │                                          │     │
│  └──────────────────────────┼──────────────────────────────────────────┘     │
│                             │                                                │
│              ┌──────────────┼──────────────────┐                             │
│              ▼              ▼                   ▼                             │
│  ┌────────────────┐  ┌───────────────┐  ┌──────────────────┐                │
│  │   DynamoDB     │  │   Bedrock     │  │      ECR         │                │
│  │  (rag-queries) │  │  (Claude +    │  │  (Docker Image)  │                │
│  │  Pay-per-req   │  │   Titan v2)   │  │                  │                │
│  └────────────────┘  └───────────────┘  └──────────────────┘                │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Ingestion (populate_database.py)
1. PDF documents are loaded from `image/src/data/source/`
2. Documents are split into chunks (600 chars, 120 overlap)
3. Each chunk is embedded via Amazon Bedrock Titan Embed v2
4. Embeddings are stored in ChromaDB at `image/src/data/chroma/`
5. Duplicate detection prevents re-processing existing documents

### Query (API)
1. User sends a question via `POST /submit_query`
2. ChromaDB performs similarity search to find relevant chunks
3. Relevant context + question are sent to Claude (Bedrock) for answer
4. Query, response, and sources are persisted to DynamoDB
5. Response with `query_id` is returned to the user
6. User can retrieve past queries via `GET /get_query/{query_id}`

## Project Structure

```
├── image/                        # Docker/Lambda container
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .containerignore
│   └── src/
│       ├── app_api_handler.py    # FastAPI + Mangum + DynamoDB
│       ├── .env                  # Local env vars
│       ├── data/chroma/          # ChromaDB vector store
│       └── rag_app/
│           ├── get_chroma_db.py
│           ├── get_embedding_function.py
│           └── query_rag.py
├── infra/                        # AWS CDK infrastructure
│   ├── app.py                    # CDK app entry point
│   ├── cdk.json
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── stacks/
│       └── rag_stack.py          # Lambda + API GW + DynamoDB + ECR
├── frontend/                     # Chat UI (GitHub Pages)
├── pyproject.toml
└── README.md
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |
| POST | `/submit_query` | Submit a question, get RAG response |
| GET | `/get_query/{query_id}` | Retrieve a previous query by ID |
| GET | `/docs` | Swagger UI |

## Usage

### Local Development
```bash
# Populate the vector database
AWS_PROFILE=bepurushoth-development AWS_REGION=eu-west-1 uv run python populate_database.py

# Run the API locally
AWS_PROFILE=bepurushoth-development AWS_REGION=eu-west-1 PYTHONPATH=image/src/rag_app uv run python image/src/app_api_handler.py

# Run in container
podman build --platform linux/amd64 -t localhost/aws_rag_app:latest image/
podman run --rm -d -p 8000:8000 --entrypoint python --env-file image/src/.env --name rag_app localhost/aws_rag_app app_api_handler.py
```

### Deploy to AWS
```bash
cd infra
CDK_DOCKER=podman cdk bootstrap
CDK_DOCKER=podman cdk deploy
```

## Requirements

- Python 3.13
- AWS account with Bedrock access (Titan Embed v2 + Claude enabled)
- AWS credentials configured (login/SSO/profile)
- Podman (for container builds)
- Node.js + AWS CDK CLI (for infrastructure deployment)
