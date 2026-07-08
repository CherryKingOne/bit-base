# bit — 多引擎模型推理平台

一条命令拉取模型、选引擎、指定精度启动推理，自动暴露 OpenAI 兼容 API。

## 特性

- **多引擎支持**: llama.cpp / vLLM / SGLang
- **多 API 格式**: OpenAI / Anthropic / Bedrock / Codex
- **流式输出**: 所有 API 格式均支持 SSE 流式响应
- **模型市场**: 搜索 HuggingFace 模型，预置常用模型
- **多模型管理**: 同时运行多个模型，独立端口
- **后台运行**: 支持 daemon 模式，日志自动记录
- **API 认证**: 可选的 API 密钥管理

## 安装

```bash
pip install -e .
```

## 快速开始

### 1. 搜索模型

```bash
bit search qwen
```

### 2. 拉取模型

```bash
bit pull Qwen/Qwen3-8B
```

### 3. 启动服务

```bash
bit run Qwen/Qwen3-8B
```

启动后会显示可用的 API 端点。

### 4. 调用 API

```bash
# OpenAI 格式
curl http://localhost:12345/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

## CLI 命令

| 命令 | 说明 |
|------|------|
| `bit version` | 显示版本 |
| `bit search <关键词>` | 搜索模型市场 |
| `bit info <模型>` | 查看模型详情 |
| `bit pull <模型>` | 拉取模型 |
| `bit list` | 查看已下载模型 |
| `bit remove <模型>` | 删除模型 |
| `bit run <模型>` | 启动推理服务 |
| `bit ps` | 查看运行中的模型 |
| `bit stats [模型]` | 查看运行指标 |
| `bit stop <模型>` | 停止服务 |
| `bit engines` | 列出可用引擎 |
| `bit categories` | 查看模型分类 |
| `bit daemon status` | 查看守护进程状态 |
| `bit apikey create --name <名称>` | 创建 API 密钥 |

## API 端点

启动服务后，支持以下 API 格式：

| 格式 | 端点 |
|------|------|
| OpenAI | `/v1/chat/completions` |
| Anthropic | `/v1/messages` |
| Bedrock | `/bedrock/converse` |
| Codex | `/v1/responses` |
| 模型列表 | `/v1/models` |
| 健康检查 | `/health` |

## 配置

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `BIT_MODEL_DIR` | 模型存储目录 | `~/.bit/models/` |

### API 密钥

```bash
# 创建密钥
bit apikey create --name mykey

# 使用密钥
curl -H "Authorization: Bearer bit-xxx" http://localhost:12345/v1/chat/completions
```

## 部署

### 单机部署

```bash
# 安装
pip install -e .

# 下载模型
bit pull Qwen/Qwen3-8B

# 后台启动
bit run Qwen/Qwen3-8B --daemon

# 查看状态
bit ps
bit stats
```

### Systemd 服务

创建 `/etc/systemd/system/bit.service`:

```ini
[Unit]
Description=bit Inference Service
After=network.target

[Service]
Type=simple
User=bit
WorkingDirectory=/home/bit
ExecStart=/usr/local/bin/bit run Qwen/Qwen3-8B
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable bit
sudo systemctl start bit
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -e .

EXPOSE 12345
CMD ["bit", "run", "Qwen/Qwen3-8B"]
```

## 日志

日志文件位于 `~/.bit/logs/bit.log`

查看日志:

```bash
tail -f ~/.bit/logs/bit.log
```

## 支持的模型

### 推荐模型

| 模型 | 引擎 | 大小 |
|------|------|------|
| Qwen/Qwen3-8B | llama.cpp | ~5GB |
| Qwen/Qwen2.5-7B-Instruct | llama.cpp | ~4GB |
| meta-llama/Llama-3.1-8B-Instruct | llama.cpp | ~5GB |
| deepseek-ai/DeepSeek-R1-Distill-Qwen-7B | llama.cpp | ~4GB |

### 精度选项

| 精度 | 说明 |
|------|------|
| `q4_k_m` | 4-bit 量化，平衡质量和速度 |
| `q4_k_s` | 4-bit 量化，更小体积 |
| `q5_k_m` | 5-bit 量化，更高质量 |
| `q8_0` | 8-bit 量化，接近原始质量 |
| `fp16` | 半精度浮点 |

## License

MIT
