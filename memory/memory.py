import logging
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TaskRecord:
    """任务记录"""
    task_id: str
    user_input: str
    start_time: str
    end_time: str = ""
    status: str = "running"
    iterations: int = 0
    result: Dict = field(default_factory=dict)


class Memory:
    """
    简化版记忆系统
    功能：
    1. 工作记忆：当前任务的状态
    2. 任务历史：已完成任务的归档
    3. 策略统计：避障策略成功率
    """

    def __init__(self):
        self._current_task: Optional[TaskRecord] = None
        self._task_history: List[TaskRecord] = []
        self._strategy_stats: Dict[str, Dict] = {}

    # ── 任务生命周期 ──────────────────────────────────────────
    def start_task(self, task_id: str, user_input: str):
        """开始新任务"""
        self._current_task = TaskRecord(
            task_id=task_id,
            user_input=user_input,
            start_time=datetime.now().isoformat(),
        )
        logger.info(f"任务开始: {task_id} - {user_input}")

    def end_task(self, task_id: str, status: str, result: Dict):
        """结束任务并归档"""
        if self._current_task and self._current_task.task_id == task_id:
            self._current_task.end_time = datetime.now().isoformat()
            self._current_task.status = status
            self._current_task.result = result
            self._current_task.iterations = result.get("iterations", 0)

            # 归档到历史
            self._task_history.append(self._current_task)
            logger.info(
                f"任务完成: {task_id} - 状态={status}, "
                f"迭代={self._current_task.iterations}轮"
            )

            self._current_task = None

    # ── 策略统计 ──────────────────────────────────────────────
    def record_strategy(self, strategy: str, success: bool):
        """记录策略执行结果"""
        if strategy not in self._strategy_stats:
            self._strategy_stats[strategy] = {"success": 0, "fail": 0}

        if success:
            self._strategy_stats[strategy]["success"] += 1
        else:
            self._strategy_stats[strategy]["fail"] += 1

        logger.debug(f"策略记录: {strategy} - {'成功' if success else '失败'}")

    # ── 提示生成 ──────────────────────────────────────────────
    def get_hints(self) -> Dict:
        """
        获取记忆提示（注入到 OBSERVE 阶段）
        返回历史任务和最佳策略信息
        """
        hints = {
            "total_tasks": len(self._task_history),
            "recent_tasks": [
                {
                    "input": t.user_input,
                    "status": t.status,
                    "iterations": t.iterations,
                }
                for t in self._task_history[-3:]  # 最近3个任务
            ],
        }

        # 推荐最佳策略
        if self._strategy_stats:
            best = max(
                self._strategy_stats.items(),
                key=lambda x: x[1]["success"],
            )
            hints["best_strategy"] = {
                "name": best[0],
                "success_count": best[1]["success"],
            }

        return hints

    # ── 查询接口 ──────────────────────────────────────────────
    def get_current_task(self) -> Optional[TaskRecord]:
        """获取当前任务"""
        return self._current_task

    def get_history(self) -> List[Dict]:
        """获取任务历史（供前端展示）"""
        return [
            {
                "task_id": t.task_id,
                "user_input": t.user_input,
                "status": t.status,
                "start_time": t.start_time,
                "end_time": t.end_time,
                "iterations": t.iterations,
            }
            for t in self._task_history
        ]

    def get_strategy_stats(self) -> Dict:
        """获取策略统计"""
        return dict(self._strategy_stats)
