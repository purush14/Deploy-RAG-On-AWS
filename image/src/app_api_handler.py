import os
import uuid
from datetime import datetime, timezone

import boto3
import uvicorn
from fastapi import FastAPI, HTTPException
from mangum import Mangum
from pydantic import BaseModel
from query_rag import QueryResponse, query_rag

app = FastAPI(root_path="/prod")
handler = Mangum(app)  # Entry point for AWS Lambda.

QUERIES_TABLE_NAME = os.environ.get("QUERIES_TABLE_NAME", "rag-queries")


def get_dynamodb_table():
    dynamodb = boto3.resource("dynamodb")
    return dynamodb.Table(QUERIES_TABLE_NAME)


class SubmitQueryRequest(BaseModel):
    query_text: str


class SubmitQueryResponse(BaseModel):
    query_id: str
    query_text: str
    response_text: str
    sources: list[str]
    created_at: str


class GetQueryResponse(BaseModel):
    query_id: str
    query_text: str
    response_text: str
    sources: list[str]
    created_at: str


@app.get("/")
def index():
    return {"Hello": "World"}


@app.post("/submit_query")
def submit_query_endpoint(request: SubmitQueryRequest) -> SubmitQueryResponse:
    # Run RAG query
    query_response = query_rag(request.query_text)

    # Generate unique ID and timestamp
    query_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    # Persist to DynamoDB
    table = get_dynamodb_table()
    item = {
        "query_id": query_id,
        "query_text": query_response.query_text,
        "response_text": query_response.response_text,
        "sources": query_response.sources,
        "created_at": created_at,
    }
    table.put_item(Item=item)

    return SubmitQueryResponse(
        query_id=query_id,
        query_text=query_response.query_text,
        response_text=query_response.response_text,
        sources=query_response.sources,
        created_at=created_at,
    )


@app.get("/get_query/{query_id}")
def get_query_endpoint(query_id: str) -> GetQueryResponse:
    table = get_dynamodb_table()
    response = table.get_item(Key={"query_id": query_id})

    item = response.get("Item")
    if not item:
        raise HTTPException(status_code=404, detail=f"Query {query_id} not found")

    return GetQueryResponse(
        query_id=item["query_id"],
        query_text=item["query_text"],
        response_text=item["response_text"],
        sources=item["sources"],
        created_at=item["created_at"],
    )


if __name__ == "__main__":
    # Run this as a server directly.
    port = 8000
    print(f"Running the FastAPI server on port {port}.")
    uvicorn.run("app_api_handler:app", host="0.0.0.0", port=port)
