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


def convert_response_to_chat(body: dict) -> dict:
    """将 responses API 格式转换为 chat completions 格式"""
    model = body.get("model", "llama-3.1-8b-instant")

    # 处理 input 字段（可能是字符串或列表）
    input_text = ""
    input_data = body.get("input", "")
    if isinstance(input_data, str) and input_data:
        input_text = input_data
    elif isinstance(input_data, list):
        # 处理 [{"type": "text", "text": "..."}] 格式
        input_text = " ".join([item.get("text", "") for item in input_data if item.get("type") == "text"])

    # 处理 messages 字段
    messages = body.get("messages", [])

    # 如果有 input，构建 messages
    if input_text:
        messages = [{"role": "user", "content": input_text}]

    # 如果还是没有 messages，返回错误
    if not messages:
        messages = [{"role": "user", "content": ""}]

    return {
        "model": model,
        "messages": messages,
        "temperature": body.get("temperature"),
        "max_tokens": body.get("max_tokens"),
        "stream": body.get("stream", False),
    }


@router.post("/chat/completions")
@router.post("/responses")
async def groq_api(request: Request):
    body = await request.json()
    api_key = parse_api_key(request) or body.get("api_key", "")

    # 转换请求格式
    chat_body = convert_response_to_chat(body)

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=chat_body
        )

    return response.json()
