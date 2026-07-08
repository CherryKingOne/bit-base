"""llama.cpp 引擎适配 — 通过 llama-server"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any, AsyncGenerator

import httpx

from bit.engines.base import BaseEngine


class LlamaCppEngine(BaseEngine):
    """llama.cpp 推理引擎"""

    def __init__(self):
        self._process: subprocess.Popen | None = None
        self._port: int = 0
        self._model_name: str = ""
        self._start_time: float = 0
        self._request_count: int = 0

    def name(self) -> str:
        return "llama.cpp"

    def load_model(self, model_path: Path, precision: str, **kwargs) -> None:
        self._port = kwargs.get("port", 8080)
        self._model_name = model_path.name
        self._start_time = time.time()

        # 查找 GGUF 文件
        gguf_files = list(model_path.glob("*.gguf"))
        if not gguf_files:
            raise FileNotFoundError(f"未找到 GGUF 模型文件: {model_path}")

        model_file = gguf_files[0]

        cmd = [
            "llama-server",
            "-m", str(model_file),
            "--port", str(self._port),
            "--host", "0.0.0.0",
        ]

        # 根据精度设置线程数
        n_threads = kwargs.get("n_threads", 4)
        cmd.extend(["-t", str(n_threads)])

        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # 等待服务就绪
        self._wait_ready()

    def _wait_ready(self, timeout: int = 30) -> None:
        """等待服务启动"""
        start = time.time()
        while time.time() - start < timeout:
            try:
                resp = httpx.get(f"http://localhost:{self._port}/health", timeout=2)
                if resp.status_code == 200:
                    return
            except Exception:
                pass
            time.sleep(0.5)
        raise TimeoutError(f"llama-server 启动超时 ({timeout}s)")

    def chat(self, messages: list[dict], stream: bool = False, **kwargs) -> Any:
        self._request_count += 1

        payload = {
            "messages": messages,
            "stream": stream,
        }
        if kwargs.get("temperature") is not None:
            payload["temperature"] = kwargs["temperature"]
        if kwargs.get("max_tokens") is not None:
            payload["max_tokens"] = kwargs["max_tokens"]

        resp = httpx.post(
            f"http://localhost:{self._port}/v1/chat/completions",
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()

    async def chat_stream(
        self, messages: list[dict], **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式对话推理"""
        self._request_count += 1

        payload = {
            "messages": messages,
            "stream": True,
        }
        if kwargs.get("temperature") is not None:
            payload["temperature"] = kwargs["temperature"]
        if kwargs.get("max_tokens") is not None:
            payload["max_tokens"] = kwargs["max_tokens"]

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"http://localhost:{self._port}/v1/chat/completions",
                json=payload,
                timeout=120,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    def unload(self) -> None:
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None

    def stats(self) -> dict:
        uptime = time.time() - self._start_time if self._start_time else 0
        return {
            "engine": self.name(),
            "port": self._port,
            "uptime": f"{uptime / 3600:.1f}h",
            "requests": self._request_count,
            "pid": self._process.pid if self._process else None,
        }
