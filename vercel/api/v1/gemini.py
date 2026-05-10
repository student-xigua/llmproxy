#!/usr/bin/env python
import typing

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


def reformat_messages(messages: list) -> list:
    """将 OpenAI 格式转换为 Gemini 格式"""
    formatted = []
    for msg in messages:
        role = "user" if msg.get("role") == "user" else "model"
        formatted.append({
            "role": role,
            "parts": [{"text": msg.get("content", "")}]
        })
    # 确保第一条是 user 消息
    if formatted and formatted[0].get("role") != "user":
        formatted.pop(0)
    return formatted


@router.post("/chat/completions")
async def gemini_proxy(request: Request):
    body = await request.json()
    api_key = parse_api_key(request) or body.get("api_key", "")

    model = body.get("model", "gemini-1.5-flash")
    # 移除 "models/" 前缀如果存在
    if model.startswith("models/"):
        model = model.split("/")[-1]

    messages = body.get("messages", [])
    contents = reformat_messages(messages)

    # 构建 Gemini 请求
    gemini_request = {
        "contents": contents,
        "generationConfig": {
            "temperature": body.get("temperature", 0.9),
            "maxOutputTokens": body.get("max_tokens", 2048),
            "topP": body.get("top_p", 0.95),
            "topK": body.get("top_logprobs", 32),
        }
    }

    # 调用 Gemini API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=gemini_request)

    if response.status_code != 200:
        return {
            "error": {
                "message": f"Gemini API error: {response.text}",
                "type": "api_error",
                "code": response.status_code
            }
        }

    data = response.json()

    # 转换为 OpenAI 格式返回
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return {
            "id": "gemini-" + model,
            "object": "chat.completion",
            "created": 1234567890,
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": text
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }
    except (KeyError, IndexError) as e:
        return {
            "error": {
                "message": f"Failed to parse Gemini response: {str(e)}",
                "type": "api_error",
                "code": 500
            }
        }
