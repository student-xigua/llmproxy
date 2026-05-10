#!/usr/bin/env python
from fastapi import Request
from fastapi.routing import APIRouter
import httpx

router = APIRouter()


def parse_api_key(request: Request) -> str:
    """从 Authorization header 解析 API key"""
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return ""


@router.post("/chat/completions")
async def groq_api(request: Request):
    body = await request.json()
    api_key = parse_api_key(request) or body.get("api_key", "")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": body.get("model", "llama-3.1-8b-instant"),
                "messages": body.get("messages", []),
                "temperature": body.get("temperature"),
                "max_tokens": body.get("max_tokens"),
                "stream": body.get("stream", False),
            }
        )

    return response.json()
