"""API 适配器 — 处理不同提供商的请求/响应格式转换"""

from __future__ import annotations

import json
import time
import uuid
from typing import Any, AsyncGenerator


def _gen_id() -> str:
    return f"chatcmpl-{uuid.uuid4().hex[:24]}"


def _now() -> int:
    return int(time.time())


# ─────────────────────────────────────────────
# OpenAI Chat Completions
# ─────────────────────────────────────────────

def openai_to_internal(request: dict) -> dict:
    """OpenAI /v1/chat/completions → 内部格式"""
    messages = request.get("messages", [])
    return {
        "messages": messages,
        "stream": request.get("stream", False),
        "temperature": request.get("temperature"),
        "max_tokens": request.get("max_tokens"),
        "top_p": request.get("top_p"),
        "stop": request.get("stop"),
    }


def internal_to_openai(result: dict, model: str = "local") -> dict:
    """内部结果 → OpenAI 响应格式"""
    content = result.get("content", "")
    return {
        "id": _gen_id(),
        "object": "chat.completion",
        "created": _now(),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": result.get("prompt_tokens", 0),
            "completion_tokens": result.get("completion_tokens", 0),
            "total_tokens": result.get("total_tokens", 0),
        },
    }


async def openai_stream_chunks(
    content_generator: AsyncGenerator[str, None],
    model: str = "local",
) -> AsyncGenerator[str, None]:
    """生成 OpenAI SSE 流式 chunks"""
    chat_id = _gen_id()
    created = _now()

    # 第一个 chunk: role
    first_chunk = {
        "id": chat_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": {"role": "assistant", "content": ""},
                "finish_reason": None,
            }
        ],
    }
    yield f"data: {json.dumps(first_chunk)}\n\n"

    # 内容 chunks
    async for token in content_generator:
        chunk = {
            "id": chat_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {"content": token},
                    "finish_reason": None,
                }
            ],
        }
        yield f"data: {json.dumps(chunk)}\n\n"

    # 结束 chunk
    end_chunk = {
        "id": chat_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": {},
                "finish_reason": "stop",
            }
        ],
    }
    yield f"data: {json.dumps(end_chunk)}\n\n"
    yield "data: [DONE]\n\n"


# ─────────────────────────────────────────────
# Anthropic Messages
# ─────────────────────────────────────────────

def anthropic_to_internal(request: dict) -> dict:
    """Anthropic /v1/messages → 内部格式"""
    messages = []
    system = request.get("system", "")

    if system:
        messages.append({"role": "user", "content": system})

    for msg in request.get("messages", []):
        messages.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", ""),
        })

    return {
        "messages": messages,
        "stream": request.get("stream", False),
        "temperature": request.get("temperature"),
        "max_tokens": request.get("max_tokens", 4096),
        "top_p": request.get("top_p"),
        "stop": request.get("stop_sequences"),
    }


def internal_to_anthropic(result: dict, model: str = "local") -> dict:
    """内部结果 → Anthropic 响应格式"""
    content = result.get("content", "")
    return {
        "id": f"msg_{uuid.uuid4().hex[:24]}",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": content}],
        "model": model,
        "stop_reason": "end_turn",
        "usage": {
            "input_tokens": result.get("prompt_tokens", 0),
            "output_tokens": result.get("completion_tokens", 0),
        },
    }


async def anthropic_stream_events(
    content_generator: AsyncGenerator[str, None],
    model: str = "local",
) -> AsyncGenerator[str, None]:
    """生成 Anthropic SSE 流式事件"""
    msg_id = f"msg_{uuid.uuid4().hex[:24]}"

    # message_start
    yield json.dumps({
        "type": "message_start",
        "message": {
            "id": msg_id,
            "type": "message",
            "role": "assistant",
            "content": [],
            "model": model,
            "stop_reason": None,
            "usage": {"input_tokens": 0, "output_tokens": 0},
        },
    }) + "\n\n"

    # content_block_start
    yield json.dumps({
        "type": "content_block_start",
        "index": 0,
        "content_block": {"type": "text", "text": ""},
    }) + "\n\n"

    # 内容事件
    async for token in content_generator:
        yield json.dumps({
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "text_delta", "text": token},
        }) + "\n\n"

    # content_block_stop
    yield json.dumps({"type": "content_block_stop", "index": 0}) + "\n\n"

    # message_delta
    yield json.dumps({
        "type": "message_delta",
        "delta": {"stop_reason": "end_turn"},
        "usage": {"output_tokens": 0},
    }) + "\n\n"

    # message_stop
    yield json.dumps({"type": "message_stop"}) + "\n\n"


# ─────────────────────────────────────────────
# AWS Bedrock Converse
# ─────────────────────────────────────────────

def bedrock_to_internal(request: dict) -> dict:
    """Bedrock /bedrock/converse → 内部格式"""
    messages = []
    for msg in request.get("messages", []):
        role = msg.get("role", "user")
        content_blocks = msg.get("content", [])
        text = " ".join(
            b.get("text", "") for b in content_blocks if b.get("type") == "text"
        )
        messages.append({"role": role, "content": text})

    inference_config = request.get("inferenceConfig", {})

    return {
        "messages": messages,
        "stream": False,
        "temperature": inference_config.get("temperature"),
        "max_tokens": inference_config.get("maxTokens", 4096),
        "top_p": inference_config.get("topP"),
        "stop": inference_config.get("stopSequences"),
    }


def internal_to_bedrock(result: dict, model: str = "local") -> dict:
    """内部结果 → Bedrock 响应格式"""
    content = result.get("content", "")
    return {
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"text": content}],
            }
        },
        "usage": {
            "inputTokens": result.get("prompt_tokens", 0),
            "outputTokens": result.get("completion_tokens", 0),
            "totalTokens": result.get("total_tokens", 0),
        },
        "stopReason": "end_turn",
    }


# ─────────────────────────────────────────────
# Codex / Responses API
# ─────────────────────────────────────────────

def codex_to_internal(request: dict) -> dict:
    """Codex /v1/responses → 内部格式"""
    input_val = request.get("input", "")
    if isinstance(input_val, str):
        messages = [{"role": "user", "content": input_val}]
    elif isinstance(input_val, list):
        messages = []
        for item in input_val:
            if isinstance(item, dict) and item.get("type") == "message":
                messages.append({
                    "role": item.get("role", "user"),
                    "content": item.get("content", ""),
                })
            elif isinstance(item, str):
                messages.append({"role": "user", "content": item})
    else:
        messages = [{"role": "user", "content": str(input_val)}]

    return {
        "messages": messages,
        "stream": request.get("stream", False),
        "temperature": request.get("temperature"),
        "max_tokens": request.get("max_output_tokens") or request.get("max_tokens"),
        "top_p": request.get("top_p"),
    }


def internal_to_codex(result: dict, model: str = "local") -> dict:
    """内部结果 → Codex 响应格式"""
    content = result.get("content", "")
    output_id = f"resp_{uuid.uuid4().hex[:24]}"
    return {
        "id": output_id,
        "object": "response",
        "created_at": _now(),
        "model": model,
        "output": [
            {
                "type": "message",
                "id": f"msg_{uuid.uuid4().hex[:24]}",
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        "text": content,
                    }
                ],
            }
        ],
        "usage": {
            "input_tokens": result.get("prompt_tokens", 0),
            "output_tokens": result.get("completion_tokens", 0),
            "total_tokens": result.get("total_tokens", 0),
        },
    }


async def codex_stream_events(
    content_generator: AsyncGenerator[str, None],
    model: str = "local",
) -> AsyncGenerator[str, None]:
    """生成 Codex SSE 流式事件"""
    resp_id = f"resp_{uuid.uuid4().hex[:24]}"
    msg_id = f"msg_{uuid.uuid4().hex[:24]}"

    # response.created
    yield json.dumps({
        "type": "response.created",
        "response": {
            "id": resp_id,
            "object": "response",
            "status": "in_progress",
        },
    }) + "\n\n"

    # response.in_progress
    yield json.dumps({
        "type": "response.in_progress",
        "response": {"id": resp_id, "status": "in_progress"},
    }) + "\n\n"

    # 内容
    async for token in content_generator:
        yield json.dumps({
            "type": "response.output_item.delta",
            "delta": {
                "type": "content_delta",
                "content_index": 0,
                "delta": token,
            },
        }) + "\n\n"

    # response.completed
    yield json.dumps({
        "type": "response.completed",
        "response": {
            "id": resp_id,
            "object": "response",
            "status": "completed",
        },
    }) + "\n\n"
