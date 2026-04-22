import json
import logging
from typing import List, Dict, Optional
from openai import OpenAI
from config.settings import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
)

logger = logging.getLogger(__name__)


class LLMClient:
    """
    LLM 客户端
    封装 OpenAI 兼容 API 调用
    使用同步客户端避免异步环境死锁
    """

    def __init__(self):
        self.client = OpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL,
        )
        self.model = LLM_MODEL
        self.temperature = LLM_TEMPERATURE
        self.max_tokens = LLM_MAX_TOKENS
        
        # 对话历史（支持多轮对话）
        self.conversation_history: List[Dict] = []
        
        logger.info(f"LLM客户端初始化: {self.model}")

    # ── 核心方法 ──────────────────────────────────────────────
    def chat(
        self,
        message: str,
        system_prompt: str = None,
        tools: List[Dict] = None,
        tool_choice: str = "auto",
    ) -> Dict:
        """
        发送消息到 LLM，返回响应
        
        参数:
            message: 用户消息
            system_prompt: 系统提示词（可选）
            tools: OpenAI Function Calling 格式的工具列表
            tool_choice: "auto" | "required" | "none"
        
        返回:
            {
                "content": str,              # LLM 文本回复
                "tool_call": {               # 工具调用（如果有）
                    "name": str,
                    "arguments": dict,
                    "call_id": str,
                } or None,
                "success": bool,
                "error": str or None,
            }
        """
        try:
            messages = []

            # 添加系统提示词
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt,
                })

            # 添加历史对话
            messages.extend(self.conversation_history)

            # 添加当前消息
            messages.append({
                "role": "user",
                "content": message,
            })

            # 构建请求参数
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }

            # 如果提供了工具列表，启用 Function Calling
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = tool_choice

            # 调用 LLM
            logger.info(f"调用 LLM: {self.model}")
            response = self.client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            message_obj = choice.message

            # 记录用户消息到历史
            self.conversation_history.append({
                "role": "user",
                "content": message,
            })

            # 构建返回结果
            result = {
                "content": message_obj.content or "",
                "tool_call": None,
                "success": True,
                "error": None,
            }

            # 解析工具调用
            if message_obj.tool_calls:
                tc = message_obj.tool_calls[0]
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}
                    logger.warning(f"工具参数JSON解析失败: {tc.function.arguments}")

                result["tool_call"] = {
                    "name": tc.function.name,
                    "arguments": args,
                    "call_id": tc.id,
                }

                # 记录助手的工具调用到历史
                self.conversation_history.append({
                    "role": "assistant",
                    "content": message_obj.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                    ],
                })

                logger.info(f"LLM 选择工具: {tc.function.name}")
            else:
                # 纯文本回复
                self.conversation_history.append({
                    "role": "assistant",
                    "content": message_obj.content or "",
                })
                logger.info("LLM 返回文本回复（无工具调用）")

            return result

        except Exception as e:
            logger.exception("LLM 调用失败")
            return {
                "content": "",
                "tool_call": None,
                "success": False,
                "error": str(e),
            }

    # ── 工具结果回传 ──────────────────────────────────────────
    def add_tool_result(self, tool_call_id: str, tool_name: str, result: str):
        """
        将工具执行结果添加到对话历史
        这是 OpenAI Function Calling 多轮对话的关键步骤
        """
        self.conversation_history.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": result,
        })
        logger.debug(f"工具结果已加入对话历史: {tool_name}")

    # ── 对话管理 ──────────────────────────────────────────────
    def reset_conversation(self):
        """重置对话历史（新任务开始时调用）"""
        self.conversation_history = []
        logger.info("对话历史已重置")

    def simple_chat(self, message: str, system_prompt: str = None) -> str:
        """
        简单文本对话（不使用工具）
        返回纯文本内容
        """
        result = self.chat(message, system_prompt=system_prompt, tools=None)
        return result.get("content", "")

    def get_conversation_length(self) -> int:
        """获取对话历史长度（用于调试）"""
        return len(self.conversation_history)
