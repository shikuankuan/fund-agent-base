"""Agent 结构化日志模块

每条日志都是 JSON，包含：时间戳、节点名、事件类型、耗时、输入输出摘要。
可直接导入到 ELK / Grafana / 本地文件分析。
"""

import time
import json
import functools
from typing import Any, Optional
from collections import deque

# ========== 日志存储：内存环形缓冲区（最近 1000 条）==========

_log_buffer: deque[dict] = deque(maxlen=1000)


def get_recent_logs(n: int = 100) -> list[dict]:
    """获取最近 n 条日志（供 API 查询）"""
    items = list(_log_buffer)
    return items[-n:]


def clear_logs():
    """清空日志"""
    _log_buffer.clear()


# ========== 日志写入（同时输出到控制台 + 内存缓冲区）==========


def log(node: str, event: str, **extra) -> dict:
    """记录一条结构化日志

    Args:
        node:  节点名称（如 "intent_recognizer", "compliance_checker"）
        event: 事件类型（如 "start", "end", "llm_call", "error"）
        **extra: 附加字段（duration_ms, input_keys, output_keys, tokens, ...）

    Returns:
        dict: 完整的日志条目
    """
    entry = {
        "timestamp": time.time(),
        "iso_time": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
        "node": node,
        "event": event,
        **extra,
    }

    # 1. 控制台输出（人类可读）
    duration = extra.get("duration_ms", "")
    dur_str = f" ({duration}ms)" if duration else ""
    summary = extra.get("output_summary", "")
    sum_str = f" → {summary}" if summary else ""
    print(f"[{entry['iso_time']}] {node}.{event}{dur_str}{sum_str}")

    # 2. 存入内存缓冲区
    _log_buffer.append(entry)

    return entry


# ========== 节点执行计时器（装饰器）==========


def trace_node(node_name: str):
    """节点装饰器：自动记录 start/end 和耗时

    用法：
        @trace_node("intent_recognizer")
        def intent_recognizer(state):
            ...

    效果：自动在函数执行前后打点，记录耗时和输入输出摘要。
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(state, *args, **kwargs):
            # 记录 start
            input_summary = _summarize_state(state, node_name)
            log(node_name, "start", input_summary=input_summary)

            t0 = time.time()

            try:
                result = func(state, *args, **kwargs)
            except Exception as e:
                duration_ms = round((time.time() - t0) * 1000)
                log(node_name, "error", duration_ms=duration_ms, error=str(e))
                raise

            duration_ms = round((time.time() - t0) * 1000)

            # 记录 end
            output_summary = _summarize_result(result, node_name)
            log(
                node_name, "end", duration_ms=duration_ms, output_summary=output_summary
            )

            return result

        return wrapper

    return decorator


# ========== LLM 调用追踪（在 get_llm 时配置回调）==========


def create_llm_logger(node_name: str):
    """创建 LLM 回调处理器：自动记录 token 消耗

    用法：
        llm = get_llm()
        llm.callbacks = [create_llm_logger("response_generator")]

    效果：每次 LLM 调用后自动记录 token 使用情况。
    """
    from langchain_core.callbacks import BaseCallbackHandler

    class LLMLogger(BaseCallbackHandler):
        def on_llm_start(self, serialized, prompts, **kwargs):
            log(
                node_name,
                "llm_start",
                prompt_length=sum(len(p) for p in prompts),
                prompt_count=len(prompts),
            )

        def on_llm_end(self, response, **kwargs):
            token_usage = {}
            if hasattr(response, "llm_output") and response.llm_output:
                usage = response.llm_output.get("token_usage", {})
                token_usage = {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                }

            # 也尝试从 generation info 取（OpenAI 兼容格式）
            if not token_usage and response.generations:
                gen = response.generations[0][0]
                if hasattr(gen, "generation_info"):
                    usage = gen.generation_info.get("token_usage", {}) or {}
                    token_usage = {
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    }

            log(node_name, "llm_end", **token_usage)

        def on_llm_error(self, error, **kwargs):
            log(node_name, "llm_error", error=str(error))

    return LLMLogger()


# ========== 内部辅助函数 ==========


def _summarize_state(state: dict, node_name: str) -> dict:
    """生成 state 摘要（只取该节点关心的字段）"""
    relevant_keys = {
        "intent_recognizer": ["messages"],
        "tool_selector": ["user_intent"],
        "data_fetcher": ["current_fund", "user_intent"],
        "analyzer": ["current_fund", "fund_info"],
        "compliance_checker": ["analysis_result"],
        "response_generator": ["user_intent", "current_fund", "compliance_result"],
    }

    keys = relevant_keys.get(node_name, [])
    summary = {}
    for k in keys:
        v = state.get(k)
        if v is not None:
            if k == "messages":
                summary[k] = f"[{len(v)} messages, last: {v[-1].content[:50]}...]"
            elif isinstance(v, (dict, list)):
                summary[k] = f"[{type(v).__name__} len={len(v)}]"
            else:
                s = str(v)
                summary[k] = s[:80] if len(s) > 80 else s
    return summary


def _summarize_result(result: dict, node_name: str) -> str:
    """生成返回值摘要"""
    if not result:
        return "{}"
    keys = list(result.keys())
    return f"updated: {keys}"
