"""
Orchestrator — ReAct 认知循环编排器
核心工作流: OBSERVE → THINK → ACT → SAFETY_CHECK → [REFLECT →] 循环
"""
import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from agent.llm_client import LLMClient
from agent.safety_guard import SafetyGuard
from agent.reflector import Reflector
from tools.registry import ToolRegistry
from config.settings import AGENT_MAX_ITERATIONS, AGENT_MAX_REFLECT_RETRIES

logger = logging.getLogger(__name__)


# ── 枚举和数据类 ──────────────────────────────────────────────
class AgentPhase(str, Enum):
    """Agent 认知阶段"""
    IDLE = "idle"
    OBSERVE = "observe"
    THINK = "think"
    ACT = "act"
    SAFETY_CHECK = "safety_check"
    REFLECT = "reflect"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CycleRecord:
    """单轮认知循环记录"""
    iteration: int
    observation: Dict = field(default_factory=dict)
    thought: Dict = field(default_factory=dict)
    action: Dict = field(default_factory=dict)
    action_result: Dict = field(default_factory=dict)
    safety_result: Dict = field(default_factory=dict)
    reflection: Dict = field(default_factory=dict)


@dataclass
class AgentState:
    """Agent 运行状态"""
    phase: AgentPhase = AgentPhase.IDLE
    task_id: str = ""
    user_input: str = ""
    iteration: int = 0
    reflect_count: int = 0
    cycles: List[CycleRecord] = field(default_factory=list)
    current_cycle: Optional[CycleRecord] = None
    final_result: Dict = field(default_factory=dict)
    error: str = ""

    # 任务关键数据（跨循环保持）
    last_path: List = field(default_factory=list)
    last_waypoints: List = field(default_factory=list)
    task_description: str = ""


# ── Orchestrator 类 ───────────────────────────────────────────
class Orchestrator:
    """
    ReAct 认知循环编排器

    职责：
    1. 驱动 5 阶段认知循环
    2. 调用 LLM 做出决策
    3. 执行飞行工具
    4. 安全检查与反思
    5. 推送事件到前端
    """

    def __init__(
        self,
        grid_space,
        tool_registry: ToolRegistry,
        safety_guard: SafetyGuard,
        reflector: Reflector,
        memory=None,
        event_callback=None,
    ):
        self.grid = grid_space
        self.registry = tool_registry
        self.safety_guard = safety_guard
        self.reflector = reflector
        self.memory = memory
        self.emit = event_callback or (lambda event, data: None)

        # LLM 客户端
        self.llm = LLMClient()

        # Agent 状态
        self.state = AgentState()

        logger.info("Orchestrator 初始化完成")

    # ── 公开接口 ──────────────────────────────────────────────
    def run(self, user_input: str, task_id: str = "") -> Dict:
        """
        启动任务，执行完整认知循环
        返回: {"status": str, "message": str, ...}
        """
        import uuid
        task_id = task_id or str(uuid.uuid4())

        self._init_task(user_input, task_id)

        # 推送任务开始事件
        self.emit("agent_task_start", {
            "task_id": task_id,
            "user_input": user_input,
        })

        # 执行主循环
        result = self._run_loop()

        # 推送任务完成事件
        self.emit("agent_task_complete", {
            "task_id": task_id,
            "result": result,
            "phase": self.state.phase.value,
            "iterations": self.state.iteration,
        })

        return result

    def get_state(self) -> Dict:
        """获取当前状态（供前端查询）"""
        return {
            "phase": self.state.phase.value,
            "task_id": self.state.task_id,
            "user_input": self.state.user_input,
            "iteration": self.state.iteration,
            "reflect_count": self.state.reflect_count,
            "cycles_count": len(self.state.cycles),
            "last_path": self.state.last_path,
            "last_waypoints": self.state.last_waypoints,
        }

    # ── 内部核心循环 ──────────────────────────────────────────
    def _init_task(self, user_input: str, task_id: str):
        """初始化任务"""
        self.llm.reset_conversation()
        self.state = AgentState(
            user_input=user_input,
            task_id=task_id,
            task_description=user_input,
        )

        if self.memory:
            self.memory.start_task(task_id, user_input)

        logger.info(f"任务初始化: {task_id} - {user_input}")

    def _run_loop(self) -> Dict:
        """
        主认知循环
        """
        max_iter = AGENT_MAX_ITERATIONS

        while self.state.iteration < max_iter:
            self.state.iteration += 1
            self.state.current_cycle = CycleRecord(
                iteration=self.state.iteration
            )

            logger.info(f"\n{'='*50}")
            logger.info(f"第 {self.state.iteration} 轮认知循环")
            logger.info(f"{'='*50}")

            # ── 1. OBSERVE ────────────────────────────────────
            observation = self._phase_observe()

            # ── 2. THINK ──────────────────────────────────────
            decision = self._phase_think(observation)
            if decision is None:
                return self._finish("FAILED", "LLM 决策失败")

            tool_name = decision.get("tool_name", "")
            arguments = decision.get("arguments", {})

            # ── 检查是否完成任务 ───────────────────────────────
            if tool_name == "task_complete":
                self.state.phase = AgentPhase.COMPLETED
                summary = arguments.get("summary", "任务完成")
                return self._finish("COMPLETED", summary)

            # ── 3. ACT ────────────────────────────────────────
            tool_result = self._phase_act(tool_name, arguments)

            # ── 4. SAFETY_CHECK ───────────────────────────────
            safety = self._phase_safety_check(tool_name, tool_result)

            # ── 5. REFLECT（如果安全检查失败）──────────────────
            if safety["needs_reflect"]:
                should_continue = self._phase_reflect(safety)
                if not should_continue:
                    return self._finish(
                        "FAILED",
                        f"超过最大反思次数 {AGENT_MAX_REFLECT_RETRIES}，任务失败"
                    )
                # 反思后继续下一轮
                continue

            # ── 记录本轮循环 ──────────────────────────────────
            self._record_cycle()

        # 超过最大迭代次数
        return self._finish("FAILED", f"超过最大迭代次数 {max_iter}")

    # ── 各阶段实现 ────────────────────────────────────────────
    def _phase_observe(self) -> Dict:
        """
        OBSERVE 阶段
        调用认知工具收集环境信息
        """
        self.state.phase = AgentPhase.OBSERVE

        self.emit("agent_observe", {
            "iteration": self.state.iteration,
            "phase": "observe",
        })

        logger.info("OBSERVE: 收集环境状态...")

        observation = self.registry.execute_cognitive_tool(
            "agent_observe",
            user_input=self.state.user_input,
            iteration=self.state.iteration,
            cycles_so_far=self._cycles_summary(),
        )

        self.state.current_cycle.observation = observation

        self.emit("agent_observe_done", {
            "iteration": self.state.iteration,
            "observation": observation,
        })

        return observation

    def _phase_think(self, observation: Dict) -> Optional[Dict]:
        """
        THINK 阶段
        调用 LLM 做出工具选择决策
        """
        self.state.phase = AgentPhase.THINK

        self.emit("agent_think", {
            "iteration": self.state.iteration,
            "phase": "think",
        })

        logger.info("THINK: 调用 LLM 做决策...")

        # ── 获取决策指南 ──────────────────────────────────────
        guide = self.registry.execute_cognitive_tool(
            "agent_think",
            observation=observation,
            user_input=self.state.user_input,
            cycles_so_far=self._cycles_summary(),
        )

        # ── 构建 LLM 提示 ─────────────────────────────────────
        system_prompt = self._build_system_prompt()
        user_message = self._build_think_message(observation, guide)

        # ── 获取飞行工具 Schema ───────────────────────────────
        tools_schema = self.registry.get_flight_tools_schema()

        # ── 调用 LLM ──────────────────────────────────────────
        response = self.llm.chat(
            message=user_message,
            system_prompt=system_prompt,
            tools=tools_schema,
            tool_choice="required",  # 强制选择工具
        )

        if not response["success"]:
            logger.error(f"LLM 调用失败: {response['error']}")
            self.emit("agent_error", {"error": response["error"]})
            return None

        tool_call = response.get("tool_call")
        if not tool_call:
            logger.warning("LLM 未返回工具调用")
            return None

        decision = {
            "tool_name": tool_call["name"],
            "arguments": tool_call["arguments"],
            "call_id": tool_call.get("call_id", ""),
            "llm_content": response.get("content", ""),
        }

        self.state.current_cycle.thought = {
            "guide": guide,
            "decision": decision,
        }

        self.emit("agent_think_done", {
            "iteration": self.state.iteration,
            "decision": decision,
        })

        logger.info(f"LLM 决策: {decision['tool_name']}({decision['arguments']})")
        return decision

    def _phase_act(self, tool_name: str, arguments: Dict) -> Dict:
        """
        ACT 阶段
        执行 LLM 选择的飞行工具
        """
        self.state.phase = AgentPhase.ACT

        self.emit("agent_act", {
            "iteration": self.state.iteration,
            "tool_name": tool_name,
            "arguments": arguments,
            "phase": "act",
        })

        logger.info(f"ACT: 执行工具 {tool_name}")

        # ── 执行工具 ──────────────────────────────────────────
        tool_result = self.registry.execute_flight_tool(tool_name, arguments)

        # ── 更新关键状态 ──────────────────────────────────────
        data = tool_result.get("data") or {}
        if "path" in data and data["path"]:
            self.state.last_path = data["path"]
        if "waypoints" in data and data["waypoints"]:
            self.state.last_waypoints = data["waypoints"]

        # ── 将工具结果回传给 LLM 对话历史 ──────────────────────
        call_id = (
            self.state.current_cycle.thought
            .get("decision", {})
            .get("call_id", "call_0")
        )
        result_str = json.dumps(tool_result, ensure_ascii=False)
        self.llm.add_tool_result(call_id, tool_name, result_str)

        # ── 记录到当前循环 ────────────────────────────────────
        self.state.current_cycle.action = {
            "tool_name": tool_name,
            "arguments": arguments,
        }
        self.state.current_cycle.action_result = tool_result

        self.emit("agent_act_done", {
            "iteration": self.state.iteration,
            "tool_name": tool_name,
            "result": tool_result,
            "state": self.get_state(),
        })

        logger.info(
            f"工具执行完成: success={tool_result.get('success')}, "
            f"result={tool_result.get('result', '')[:100]}"
        )

        return tool_result

    def _phase_safety_check(self, tool_name: str, tool_result: Dict) -> Dict:
        """
        SAFETY_CHECK 阶段
        对路径进行碰撞检测
        """
        self.state.phase = AgentPhase.SAFETY_CHECK

        self.emit("agent_safety_check", {
            "iteration": self.state.iteration,
            "tool_name": tool_name,
            "phase": "safety_check",
        })

        logger.info("SAFETY_CHECK: 执行安全检查...")

        safety = self.safety_guard.check(tool_name, tool_result)
        self.state.current_cycle.safety_result = safety

        self.emit("agent_safety_check_done", {
            "iteration": self.state.iteration,
            "safety": safety,
        })

        if safety["safe"]:
            logger.info("安全检查通过")
        else:
            logger.warning(f"检测到碰撞: {safety['collision_point']}")

        return safety

    def _phase_reflect(self, safety_result: Dict) -> bool:
        """
        REFLECT 阶段
        碰撞后生成重规划策略

        返回: True=可以继续, False=超过重试次数
        """
        if self.state.reflect_count >= AGENT_MAX_REFLECT_RETRIES:
            logger.warning("超过最大反思次数")
            return False

        self.state.phase = AgentPhase.REFLECT
        self.state.reflect_count += 1

        self.emit("agent_reflect", {
            "iteration": self.state.iteration,
            "retry_count": self.state.reflect_count,
            "phase": "reflect",
        })

        logger.info(f"REFLECT: 第 {self.state.reflect_count} 次反思...")

        # ── 生成反思指南 ──────────────────────────────────────
        reflect_guide = self.reflector.build_reflect_guide(
            safety_result=safety_result,
            cycles_so_far=self._cycles_summary(),
            retry_count=self.state.reflect_count,
        )

        self.state.current_cycle.reflection = reflect_guide

        # ── 将反思信息注入 LLM 对话历史 ────────────────────────
        reflect_message = (
            f"安全检查失败！路径与障碍物碰撞。\n\n"
            f"碰撞点: {safety_result.get('collision_point')}\n"
            f"附近障碍物: {len(safety_result.get('nearby_obstacles', []))}个\n"
            f"推荐策略: {reflect_guide.get('recommended_strategy')}\n\n"
            f"请使用 ai_replan_with_obstacles 工具重新规划路径。\n"
            f"建议参数:\n{json.dumps(reflect_guide.get('suggested_call', {}).get('arguments', {}), ensure_ascii=False, indent=2)}"
        )

        self.llm.conversation_history.append({
            "role": "user",
            "content": reflect_message,
        })

        self.emit("agent_reflect_done", {
            "iteration": self.state.iteration,
            "reflect_guide": reflect_guide,
            "retry_count": self.state.reflect_count,
        })

        logger.info(f"推荐策略: {reflect_guide.get('recommended_strategy')}")
        return True

    # ── 辅助方法 ──────────────────────────────────────────────
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return f"""你是一个无人机自主飞行规划 AI 助手。
你需要通过调用工具来完成无人机飞行任务。

【当前任务】
{self.state.user_input}

【环境信息】
- 当前位置: {list(self.grid.current_position)}
- 栅格空间: {self.grid.size_x}x{self.grid.size_y}x{self.grid.size_z} 米
- 障碍物数量: {self.grid.get_obstacle_count()}

【工作原则】
1. 每次只调用一个工具
2. 按照标准工作流顺序执行：
   ai_translate_flight → parse_command → plan_flight → visualize_flight → generate_uav_code → task_complete
3. 如果路径规划发现碰撞，使用 ai_replan_with_obstacles 重规划
4. 所有步骤完成后必须调用 task_complete 标记任务完成
5. 必须通过 function calling 机制选择工具

【重要提示】
- 你必须使用工具来完成任务，不能只回复文本
- 任务完成后必须调用 task_complete 工具
"""

    def _build_think_message(self, observation: Dict, guide: Dict) -> str:
        """构建 THINK 阶段的用户消息"""
        actions_taken = observation.get("actions_taken", [])
        recommended = guide.get("recommended_next_tool", "ai_translate_flight")
        workflow = guide.get("standard_workflow", "")

        return (
            f"【当前状态】\n"
            f"- 轮次: 第 {self.state.iteration} 轮认知循环\n"
            f"- 已执行工具: {actions_taken}\n"
            f"- 推荐下一步: {recommended}\n\n"
            f"【标准工作流】\n{workflow}\n\n"
            f"请根据当前状态和推荐，选择合适的工具继续执行任务。"
        )

    def _cycles_summary(self) -> List[Dict]:
        """生成循环历史摘要（传给认知工具）"""
        summaries = []

        for cycle in self.state.cycles:
            summaries.append({
                "iteration": cycle.iteration,
                "action": {
                    "tool_name": cycle.action.get("tool_name", ""),
                },
                "action_result": cycle.action_result,
                "safe": cycle.safety_result.get("safe", True),
            })

        # 加入当前轮（如果有）
        if (
            self.state.current_cycle
            and self.state.current_cycle.action
        ):
            c = self.state.current_cycle
            summaries.append({
                "iteration": c.iteration,
                "action": c.action,
                "action_result": c.action_result,
                "safe": c.safety_result.get("safe", True),
            })

        return summaries

    def _record_cycle(self):
        """记录完成的循环"""
        if self.state.current_cycle:
            self.state.cycles.append(self.state.current_cycle)

    def _finish(self, status: str, message: str) -> Dict:
        """结束任务"""
        if status == "COMPLETED":
            self.state.phase = AgentPhase.COMPLETED
        else:
            self.state.phase = AgentPhase.FAILED

        result = {
            "status": status,
            "message": message,
            "task_id": self.state.task_id,
            "iterations": self.state.iteration,
            "reflect_count": self.state.reflect_count,
            "last_path": self.state.last_path,
            "last_waypoints": self.state.last_waypoints,
        }

        self.state.final_result = result

        if self.memory:
            self.memory.end_task(
                self.state.task_id,
                status=status,
                result=result,
            )

        logger.info(f"\n任务结束: {status} - {message}")
        return result
