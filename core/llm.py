"""
llama.cpp 调用封装模块
提供与 Qwen3.5 本地大模型交互的统一接口
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Optional

from core.config import MODEL_CONFIG


def call_llama_cpp(
    prompt: str,
    max_tokens: int = 2048,
    temperature: float = 0.7,
    context_size: Optional[int] = None,
    timeout: int = 600,
) -> str:
    """
    调用 llama.cpp 运行 Qwen3.5 模型

    Args:
        prompt: 输入提示词
        max_tokens: 最大生成 token 数
        temperature: 生成温度
        context_size: 上下文窗口大小，默认使用配置值
        timeout: 超时秒数（默认 600 秒）

    Returns:
        模型生成的文本

    Raises:
        RuntimeError: 当模型调用失败时
    """
    llm_cli = MODEL_CONFIG["llm_cli"]
    model_path = MODEL_CONFIG["llm_path"]
    ctx_size = context_size or MODEL_CONFIG["context_size"]

    if not os.path.exists(llm_cli):
        raise RuntimeError(f"llama.cpp 可执行文件不存在: {llm_cli}")
    if not os.path.exists(model_path):
        raise RuntimeError(f"模型文件不存在: {model_path}")

    # 将 prompt 写入临时文件（避免命令行长度限制）
    prompt_dir = Path("runtime")
    prompt_dir.mkdir(exist_ok=True)
    prompt_file = prompt_dir / "_prompt.txt"
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(prompt)

    try:
        # 使用二进制模式捕获输出，避免编码问题
        process = subprocess.Popen(
            [
                llm_cli,
                "-m", model_path,
                "-f", str(prompt_file),
                "--temp", str(temperature),
                "-n", str(max_tokens),
                "-c", str(ctx_size),
                "--repeat-penalty", "1.1",
                "--no-display-prompt",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = process.communicate(timeout=timeout)

        # 尝试用 UTF-8 解码，失败时用 GBK 并忽略错误
        try:
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
        except UnicodeDecodeError:
            stdout = stdout_bytes.decode("gbk", errors="replace")
            stderr = stderr_bytes.decode("gbk", errors="replace")

        if process.returncode != 0:
            raise RuntimeError(f"llama.cpp 调用失败: {stderr[:500]}")

        return stdout.strip()

    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        raise RuntimeError(f"llama.cpp 调用超时（{timeout}秒）")
    except FileNotFoundError:
        raise RuntimeError(f"找不到 llama.cpp 可执行文件: {llm_cli}")
    finally:
        # 清理临时文件
        if prompt_file.exists():
            prompt_file.unlink()


def parse_json_from_response(response: str) -> dict:
    """
    从模型响应中解析 JSON 内容
    处理模型可能输出额外文本的情况

    Args:
        response: 模型原始响应

    Returns:
        解析后的 JSON 字典
    """
    # 尝试提取 ```json ... ``` 块
    import re
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        json_str = response.strip()

    # 尝试查找第一个 { 到最后一个 }
    first_brace = json_str.find("{")
    last_brace = json_str.rfind("}")
    if first_brace != -1 and last_brace != -1:
        json_str = json_str[first_brace:last_brace + 1]

    return json.loads(json_str)


def estimate_tokens(text: str) -> int:
    """
    粗略估计文本的 token 数（中英文混合场景）

    Args:
        text: 输入文本

    Returns:
        估计的 token 数
    """
    # 中文约 1.5 tokens/字，英文约 0.25 tokens/字符
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    other_chars = len(text) - chinese_chars
    return int(chinese_chars * 1.5 + other_chars * 0.25)
