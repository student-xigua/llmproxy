#!/usr/bin/env python
import typing

from fastapi import Request
from fastapi.routing import APIRouter
from openai import AsyncClient

router = APIRouter()


def parse_api_key(request: Request) -> str:
    """从 Authorization header 解析 API key"""
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return ""


@router.post("/chat/completions")
async def openai_proxy(request: Request):
    body = await request.json()
    api_key = parse_api_key(request) or body.get("api_key", "")

    client = AsyncClient(api_key=api_key)

    return await client.chat.completions.create(
        model=body.get("model", "gpt-3.5-turbo"),
        messages=body.get("messages", []),
        temperature=body.get("temperature"),
        max_tokens=body.get("max_tokens"),
        stream=body.get("stream", False),
    )
