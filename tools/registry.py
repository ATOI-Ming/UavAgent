import json
import logging
from typing import Dict, List, Callable, Optional, Any

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    工具注册中心
    管理两类工具：
    1. 飞行工具 (flight_tools)  — LLM 通过 Function Calling 选择
    2. 认知工具 (cognitive_tools) — Orchestrator 内部调用，LLM 不可见
    """

    def __init__(self):
        self._flight_tools: Dict[str, Dict] = {}
        self._cognitive_tools: Dict[str, Callable] = {}
        logger.info("ToolRegistry 初始化")

    # ── 飞行工具注册 ──────────────────────────────────────────
    def register_flight_tool(
        self,
        name: str,
        func: Optional[Callable],
        description: str,
        parameters: Dict,
        category: str = "general",
    ):
        """
        注册飞行工具
        
        参数:
            name: 工具名称
            func: 工具函数（可以为 None，如 task_complete）
            description: 工具描述
            parameters: OpenAI Function Calling 格式的参数 Schema
            category: 工具分类（input/planning/visualization等）
        """
        self._flight_tools[name] = {
            "name": name,
            "func": func,
            "description": description,
            "parameters": parameters,
            "category": category,
        }
        logger.debug(f"注册飞行工具: {name} [{category}]")

    def execute_flight_tool(self, name: str, arguments: Dict) -> Dict:
        """
        执行飞行工具
        
        返回统一格式:
        {
            "success": bool,
            "result": str,      # 文本描述
            "data": dict,       # 结构化数据
        }
        """
        if name not in self._flight_tools:
            logger.error(f"工具不存在: {name}")
            return {
                "success": False,
                "result": f"工具 '{name}' 不存在",
                "data": None,
            }

        tool = self._flight_tools[name]

        # ── task_complete 特殊处理 ────────────────────────────
        if name == "task_complete":
            summary = arguments.get("summary", "任务完成")
            logger.info(f"任务完成标记: {summary}")
            return {
                "success": True,
                "result": summary,
                "data": {"status": "completed"},
            }

        # ── 执行普通工具 ──────────────────────────────────────
        func = tool.get("func")
        if func is None:
            logger.error(f"工具函数未实现: {name}")
            return {
                "success": False,
                "result": "工具函数未实现",
                "data": None,
            }

        try:
            logger.info(f"执行飞行工具: {name}({arguments})")
            raw_result = func(**arguments)

            # ── 统一返回格式 ──────────────────────────────────
            if isinstance(raw_result, dict):
                # 如果工具已返回标准格式
                if "success" in raw_result:
                    return {
                        "success": raw_result.get("success", True),
                        "result": raw_result.get("message", str(raw_result)),
                        "data": raw_result,
                    }
                # 如果只是普通字典
                return {
                    "success": True,
                    "result": str(raw_result),
                    "data": raw_result,
                }
            else:
                # 其他类型（字符串等）
                return {
                    "success": True,
                    "result": str(raw_result),
                    "data": None,
                }

        except TypeError as e:
            logger.exception(f"工具参数错误: {name}")
            return {
                "success": False,
                "result": f"参数错误: {str(e)}",
                "data": None,
            }
        except Exception as e:
            logger.exception(f"工具执行异常: {name}")
            return {
                "success": False,
                "result": f"执行错误: {str(e)}",
                "data": None,
            }

    def get_flight_tools_schema(self) -> List[Dict]:
        """
        获取所有飞行工具的 OpenAI Function Calling Schema
        供 LLMClient.chat() 使用
        """
        schemas = []
        for name, tool in self._flight_tools.items():
            schemas.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                },
            })
        return schemas

    def get_flight_tool_names(self) -> List[str]:
        """获取所有飞行工具名称列表"""
        return list(self._flight_tools.keys())

    def list_flight_tools(self) -> List[Dict]:
        """获取飞行工具列表（供前端展示）"""
        return [
            {
                "name": t["name"],
                "description": t["description"],
                "category": t["category"],
            }
            for t in self._flight_tools.values()
        ]

    # ── 认知工具注册 ──────────────────────────────────────────
    def register_cognitive_tool(self, name: str, func: Callable):
        """
        注册认知工具
        认知工具由 Orchestrator 在各阶段自动调用，LLM 看不到
        """
        self._cognitive_tools[name] = func
        logger.debug(f"注册认知工具: {name}")

    def execute_cognitive_tool(self, name: str, **kwargs) -> Any:
        """
        执行认知工具
        直接返回工具的原始结果（通常是 Dict）
        """
        if name not in self._cognitive_tools:
            logger.error(
                f"认知工具不存在: '{name}', "
                f"已注册认知工具: {list(self._cognitive_tools.keys())}, "
                f"id(self)={id(self)}"
            )
            raise KeyError(
                f"认知工具 '{name}' 不存在, "
                f"已注册: {list(self._cognitive_tools.keys())}"
            )

        logger.debug(f"执行认知工具: {name}")
        return self._cognitive_tools[name](**kwargs)

    def list_cognitive_tools(self) -> List[str]:
        """获取认知工具名称列表"""
        return list(self._cognitive_tools.keys())

    # ── 调试信息 ──────────────────────────────────────────────
    def get_stats(self) -> Dict:
        """获取工具统计信息"""
        return {
            "flight_tools_count": len(self._flight_tools),
            "cognitive_tools_count": len(self._cognitive_tools),
            "flight_tools": list(self._flight_tools.keys()),
            "cognitive_tools": list(self._cognitive_tools.keys()),
        }
