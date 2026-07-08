"""API 服务 — 支持 4 种 API 格式 + 流式输出"""

from __future__ import annotations

import json
import logging
import traceback
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse

from bit.server.adapters import (
    openai_to_internal,
    internal_to_openai,
    openai_stream_chunks,
    anthropic_to_internal,
    internal_to_anthropic,
    anthropic_stream_events,
    bedrock_to_internal,
    internal_to_bedrock,
    codex_to_internal,
    internal_to_codex,
    codex_stream_events,
)
from bit.server.auth import verify_api_key, api_key_manager

logger = logging.getLogger("bit.api")

app = FastAPI(title="bit API", version="0.1.0")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": str(exc),
                "type": "internal_error",
                "code": "server_error",
            }
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "type": "api_error",
                "code": exc.status_code,
            }
        },
    )

# 全局引擎引用（由 runner 设置）
_engine = None
_model_name: str = "local"


@app.get("/v1/models")
async def list_models():
    """列出可用模型"""
    return {
        "object": "list",
        "data": [
            {
                "id": _model_name,
                "object": "model",
                "created": 1,
                "owned_by": "bit",
            }
        ],
    }


# ─────────────────────────────────────────────
# 1. OpenAI Chat Completions
# ─────────────────────────────────────────────

@app.post("/v1/chat/completions")
async def openai_chat(request: Request, api_key: str = Depends(verify_api_key)):
    """OpenAI /v1/chat/completions"""
    _check_engine()
    body = await request.json()

    try:
        internal = openai_to_internal(body)

        if internal["stream"]:
            async def generate():
                async for chunk in _engine.chat_stream(
                    internal["messages"],
                    temperature=internal["temperature"],
                    max_tokens=internal["max_tokens"],
                ):
                    yield chunk

            return StreamingResponse(
                openai_stream_chunks(generate(), model=_model_name),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )
        else:
            result = _engine.chat(
                internal["messages"],
                stream=False,
                temperature=internal["temperature"],
                max_tokens=internal["max_tokens"],
            )
            return internal_to_openai(result, model=_model_name)
    except Exception as e:
        logger.exception("OpenAI chat error")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# 2. Anthropic Messages
# ─────────────────────────────────────────────

@app.post("/v1/messages")
async def anthropic_messages(request: Request, api_key: str = Depends(verify_api_key)):
    """Anthropic /v1/messages"""
    _check_engine()
    body = await request.json()

    try:
        internal = anthropic_to_internal(body)

        if internal["stream"]:
            async def generate():
                async for chunk in _engine.chat_stream(
                    internal["messages"],
                    temperature=internal["temperature"],
                    max_tokens=internal["max_tokens"],
                ):
                    yield chunk

            return StreamingResponse(
                anthropic_stream_events(generate(), model=_model_name),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )
        else:
            result = _engine.chat(
                internal["messages"],
                stream=False,
                temperature=internal["temperature"],
                max_tokens=internal["max_tokens"],
            )
            return internal_to_anthropic(result, model=_model_name)
    except Exception as e:
        logger.exception("Anthropic messages error")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# 3. AWS Bedrock Converse
# ─────────────────────────────────────────────

@app.post("/bedrock/converse")
async def bedrock_converse(request: Request, api_key: str = Depends(verify_api_key)):
    """AWS Bedrock /bedrock/converse"""
    _check_engine()
    body = await request.json()

    try:
        internal = bedrock_to_internal(body)
        result = _engine.chat(
            internal["messages"],
            stream=False,
            temperature=internal["temperature"],
            max_tokens=internal["max_tokens"],
        )
        return internal_to_bedrock(result, model=_model_name)
    except Exception as e:
        logger.exception("Bedrock converse error")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# 4. Codex / Responses API
# ─────────────────────────────────────────────

@app.post("/v1/responses")
async def codex_responses(request: Request, api_key: str = Depends(verify_api_key)):
    """OpenAI Codex / Responses API"""
    _check_engine()
    body = await request.json()

    try:
        internal = codex_to_internal(body)

        if internal["stream"]:
            async def generate():
                async for chunk in _engine.chat_stream(
                    internal["messages"],
                    temperature=internal["temperature"],
                    max_tokens=internal["max_tokens"],
                ):
                    yield chunk

            return StreamingResponse(
                codex_stream_events(generate(), model=_model_name),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )
        else:
            result = _engine.chat(
                internal["messages"],
                stream=False,
                temperature=internal["temperature"],
                max_tokens=internal["max_tokens"],
            )
            return internal_to_codex(result, model=_model_name)
    except Exception as e:
        logger.exception("Codex responses error")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# 通用接口
# ─────────────────────────────────────────────

@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "ok",
        "model": _model_name,
        "engine": _engine.name() if _engine else None,
    }


@app.get("/")
async def root():
    """API 概览"""
    return {
        "service": "bit",
        "version": "0.1.0",
        "model": _model_name,
        "endpoints": {
            "openai": "/v1/chat/completions",
            "anthropic": "/v1/messages",
            "bedrock": "/bedrock/converse",
            "codex": "/v1/responses",
            "models": "/v1/models",
            "health": "/health",
        },
    }


@app.post("/v1/api-keys")
async def create_api_key(request: Request):
    """创建 API 密钥"""
    body = await request.json()
    name = body.get("name", "")
    description = body.get("description", "")

    if not name:
        raise HTTPException(status_code=400, detail="Name is required")

    key = api_key_manager.create_key(name, description)
    return {"key": key, "name": name}


@app.get("/v1/api-keys")
async def list_api_keys():
    """列出 API 密钥"""
    return {"keys": api_key_manager.list_keys()}


@app.delete("/v1/api-keys/{name}")
async def delete_api_key(name: str):
    """删除 API 密钥"""
    if api_key_manager.delete_key(name):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Key not found")


def _check_engine():
    if _engine is None:
        raise HTTPException(status_code=503, detail="模型未加载，请先启动 bit run")
