"""Claude CLI 调用包装。通过 subprocess 跑 `claude -p PROMPT`。

为什么用 CLI：用户偏好；不用管 API key；模型版本能跟 claude 配置走。
代价：每次启动 CLI 有秒级开销，所以一次 prompt 内尽量多塞东西。
"""

import json
import subprocess
from typing import Any

DEFAULT_MODEL = "claude-sonnet-4-6"


def claude_prompt(prompt: str, model: str = DEFAULT_MODEL, timeout: int = 60) -> str:
    """单次 prompt 调用。返回纯文本输出。"""
    result = subprocess.run(
        ["claude", "-p", prompt, "--model", model],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI failed: {result.stderr}")
    return result.stdout.strip()


def claude_json(prompt: str, model: str = DEFAULT_MODEL, timeout: int = 60) -> Any:
    """要求 LLM 输出 JSON 的 prompt。会自动去掉 ```json fence。"""
    raw = claude_prompt(prompt, model=model, timeout=timeout)
    if raw.startswith("```"):
        raw = "\n".join(line for line in raw.splitlines() if not line.startswith("```"))
    return json.loads(raw)
