"""SGLang 引擎适配"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any

import httpx

from bit.engines.base import BaseEngine


class SglangEngine(BaseEngine):
    """SGLang 推理引擎"""

    def __init__(self):
        self._process: subprocess.Popen | None = None
        self._port: int = 0
        self._model_name: str = ""
        self._start_time: float = 0
        self._request_count: int = 0

    def name(self) -> str:
        return "sglang"

    def load_model(self, model_path: Path, precision: str, **kwargs) -> None:
        self._port = kwargs.get("port", 30000)
        self._model_name = model_path.name
        self._start_time = time.time()

        cmd = [
            "python", "-m", "sglang.launch_server",
            "--model-path", str(model_path),
            "--port", str(self._port),
            "--host", "0.0.0.0",
        ]

        # 精度
        if precision in ("fp16", "bf16"):
            cmd.extend(["--dtype", precision])

        # 量化
        if "awq" in precision.lower():
            cmd.extend(["--quantization", "awq"])
        elif "gptq" in precision.lower():
            cmd.extend(["--quantization", "gptq"])

        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self._wait_ready()

    def _wait_ready(self, timeout: int = 120) -> None:
        """等待 SGLang 启动"""
        start = time.time()
        while time.time() - start < timeout:
            try:
                resp = httpx.get(f"http://localhost:{self._port}/health", timeout=2)
                if resp.status_code == 200:
                    return
            except Exception:
                pass
            time.sleep(1)
        raise TimeoutError(f"SGLang 启动超时 ({timeout}s)")

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
