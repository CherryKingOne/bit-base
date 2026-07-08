"""API 密钥认证"""

from __future__ import annotations

import hashlib
import secrets
from pathlib import Path

from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)


class APIKeyManager:
    """API 密钥管理"""

    def __init__(self):
        self._keys_file = Path.home() / ".bit" / "api_keys.json"
        self._keys: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        """加载密钥"""
        if self._keys_file.exists():
            try:
                import json
                self._keys = json.loads(self._keys_file.read_text())
            except Exception:
                self._keys = {}

    def _save(self) -> None:
        """保存密钥"""
        import json
        self._keys_file.parent.mkdir(parents=True, exist_ok=True)
        self._keys_file.write_text(json.dumps(self._keys, indent=2))

    def create_key(self, name: str, description: str = "") -> str:
        """创建新密钥"""
        key = f"bit-{secrets.token_hex(32)}"
        key_hash = hashlib.sha256(key.encode()).hexdigest()

        self._keys[key_hash] = {
            "name": name,
            "description": description,
            "created_at": int(__import__("time").time()),
            "active": True,
        }
        self._save()

        return key

    def validate_key(self, key: str) -> bool:
        """验证密钥"""
        if not self._keys:
            # 没有配置密钥时，允许所有请求
            return True

        key_hash = hashlib.sha256(key.encode()).hexdigest()
        key_info = self._keys.get(key_hash)

        if key_info and key_info.get("active", True):
            return True

        return False

    def list_keys(self) -> list[dict]:
        """列出所有密钥（不显示完整密钥）"""
        result = []
        for key_hash, info in self._keys.items():
            result.append({
                "name": info.get("name", "unknown"),
                "description": info.get("description", ""),
                "created_at": info.get("created_at", 0),
                "active": info.get("active", True),
                "key_prefix": key_hash[:8] + "...",
            })
        return result

    def revoke_key(self, name: str) -> bool:
        """吊销密钥"""
        for key_hash, info in self._keys.items():
            if info.get("name") == name:
                info["active"] = False
                self._save()
                return True
        return False

    def delete_key(self, name: str) -> bool:
        """删除密钥"""
        for key_hash, info in list(self._keys.items()):
            if info.get("name") == name:
                del self._keys[key_hash]
                self._save()
                return True
        return False


# 全局实例
api_key_manager = APIKeyManager()


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> str | None:
    """验证 API 密钥（FastAPI 依赖注入）"""
    if credentials is None:
        # 没有提供密钥
        if api_key_manager._keys:
            # 已配置密钥，需要验证
            raise HTTPException(
                status_code=401,
                detail="Missing API key. Provide via Authorization: Bearer <key>",
            )
        return None

    if not api_key_manager.validate_key(credentials.credentials):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )

    return credentials.credentials
