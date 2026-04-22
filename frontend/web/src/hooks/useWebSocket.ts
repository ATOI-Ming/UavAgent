import { useEffect, useRef, useCallback } from "react";
import { io, Socket } from "socket.io-client";
import { useAgentStore } from "../store/agentStore";

const SERVER_URL = "http://localhost:5000";

export function useWebSocket() {
  const socketRef = useRef<Socket | null>(null);

  const {
    setConnected,
    setAgentState,
    setGridState,
    setIsRunning,
    setTaskResult,
    setLastSafety,
    setCodeFiles,
    setLayerMaps,
    setVizImageUrl,
    addLog,
    addMessage,
    addToolCall,
    addCognitiveEvent,
  } = useAgentStore();

  // ── 初始化 WebSocket 连接 ──────────────────────────────────
  useEffect(() => {
    const socket = io(SERVER_URL, {
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 2000,
    });

    socketRef.current = socket;

    // ── 连接事件 ────────────────────────────────────────────
    socket.on("connect", () => {
      setConnected(true);
      addLog("system", "已连接到 UAV Agent 服务器");
      socket.emit("request_state");
    });

    socket.on("disconnect", () => {
      setConnected(false);
      addLog("error", "与服务器断开连接，正在重连...");
    });

    socket.on("connect_error", (err) => {
      addLog("error", `连接错误: ${err.message}`);
    });

    // ── 初始状态 ────────────────────────────────────────────
    socket.on("connected", (data: any) => {
      if (data.agent_state) {
        setAgentState(data.agent_state);
      }
      if (data.grid) {
        setGridState({
          size: data.grid.size,
          current_position: data.grid.current_position,
          obstacle_count: data.grid.obstacle_count,
          free_ratio: data.grid.free_ratio,
          obstacles_by_layer: data.grid.obstacles_by_layer || {},
          obstacles: data.obstacles || [],
        });
      }
      addLog("success", "服务器连接成功，系统就绪");
    });

    // ── 消息确认 ────────────────────────────────────────────
    socket.on("message_received", (data: any) => {
      addLog("info", `指令已接收: ${data.message}`);
    });

    // ── 任务开始 ────────────────────────────────────────────
    socket.on("agent_task_start", (data: any) => {
      setIsRunning(true);
      setTaskResult(null);
      setLastSafety(null);
      setAgentState({
        phase: "observe",
        task_id: data.task_id,
        user_input: data.user_input,
        iteration: 0,
        reflect_count: 0,
        cycles_count: 0,
      });
      addLog("system", `任务开始: ${data.user_input}`, "observe");
      addMessage("assistant", `🚀 开始执行任务: ${data.user_input}`);
    });

    // ── OBSERVE 阶段 ─────────────────────────────────────────
    socket.on("agent_observe", (data: any) => {
      setAgentState({ phase: "observe", iteration: data.iteration });
      addLog("info", `第 ${data.iteration} 轮 — OBSERVE: 收集环境状态`, "observe");
      addCognitiveEvent({
        iteration: data.iteration,
        phase: "observe",
        title: `第 ${data.iteration} 轮 — 环境观察`,
        detail: "收集环境状态、位置信息、障碍物分布...",
        status: "running",
      });
    });

    socket.on("agent_observe_done", (data: any) => {
      const obs = data.observation || {};
      const env = obs.environment || {};
      addLog(
        "info",
        `观察完成 — 位置: [${env.current_position}], 障碍物: ${env.obstacle_count}个`,
        "observe",
        obs
      );
      addCognitiveEvent({
        iteration: obs.iteration || 0,
        phase: "observe",
        title: "观察完成",
        detail: `位置: [${env.current_position}] | 障碍物: ${env.obstacle_count}个`,
        status: "success",
        data: env,
      });
    });

    // ── THINK 阶段 ───────────────────────────────────────────
    socket.on("agent_think", (data: any) => {
      setAgentState({ phase: "think" });
      addLog("info", `第 ${data.iteration} 轮 — THINK: 调用 LLM 决策中...`, "think");
      addCognitiveEvent({
        iteration: data.iteration,
        phase: "think",
        title: `第 ${data.iteration} 轮 — LLM推理`,
        detail: "分析任务意图，选择最合适的工具...",
        status: "running",
      });
    });

    socket.on("agent_think_done", (data: any) => {
      const decision = data.decision || {};
      addLog("success", `LLM 决策: ${decision.tool_name}`, "think", decision);
      addCognitiveEvent({
        iteration: data.iteration || 0,
        phase: "think",
        title: "推理完成",
        detail: `选择工具: ${decision.tool_name}`,
        status: "success",
        data: decision,
      });
    });

    // ── ACT 阶段 ─────────────────────────────────────────────
    socket.on("agent_act", (data: any) => {
      setAgentState({ phase: "act" });
      addLog("info", `第 ${data.iteration} 轮 — ACT: 执行 ${data.tool_name}`, "act", data);
      addCognitiveEvent({
        iteration: data.iteration,
        phase: "act",
        title: "执行工具",
        detail: `${data.tool_name}(${JSON.stringify(data.arguments || {}).slice(0, 80)}...)`,
        status: "running",
        data: data,
      });
    });

    socket.on("agent_act_done", (data: any) => {
      const result = data.result || {};

      addToolCall({
        tool_name: data.tool_name,
        arguments: data.arguments || {},
        result: result,
        iteration: data.iteration,
        timestamp: Date.now(),
      });

      if (data.state) {
        setAgentState(data.state);
      }

      if (result.success) {
        addLog("success", `${data.tool_name} 执行成功: ${result.result?.slice(0, 80) || ""}`, "act", result);
        addCognitiveEvent({
          iteration: data.iteration,
          phase: "act",
          title: "执行成功",
          detail: result.result?.slice(0, 100) || "",
          status: "success",
          data: result,
        });

        const resData = result.data || {};
        if (resData.filename && resData.file_path) {
          if (resData.filename.startsWith("flight_")) {
            setVizImageUrl(`http://localhost:5000/api/files/visualizations/${resData.filename}`);
          }
        }
        if (resData.files && Array.isArray(resData.files) && resData.count > 0) {
          const layerFiles = resData.files
            .filter((f: any) => f.filename?.includes("layer_"))
            .map((f: any) => ({
              filename: f.filename,
              url: `http://localhost:5000/api/files/layer_maps/${f.filename}`,
              size: 0,
            }));
          if (layerFiles.length > 0) setLayerMaps(layerFiles);

          const codeFilesList = resData.files
            .filter((f: any) => f.filename?.endsWith(".py"))
            .map((f: any) => ({
              filename: f.filename,
              url: `http://localhost:5000/api/files/missions/${f.filename}`,
              content: "",
              size: 0,
            }));
          if (codeFilesList.length > 0) setCodeFiles(codeFilesList);
        }
      } else {
        addLog("warning", `${data.tool_name} 执行失败: ${result.result || "未知错误"}`, "act");
        addCognitiveEvent({
          iteration: data.iteration,
          phase: "act",
          title: "执行失败",
          detail: result.result || "未知错误",
          status: "error",
          data: result,
        });
      }
    });

    // ── SAFETY_CHECK 阶段 ─────────────────────────────────────
    socket.on("agent_safety_check", (data: any) => {
      setAgentState({ phase: "safety_check" });
      addLog(
        "info",
        `第 ${data.iteration} 轮 — SAFETY CHECK: 检查 ${data.tool_name}`,
        "safety_check"
      );
    });

    socket.on("agent_safety_check_done", (data: any) => {
      const safety = data.safety || {};
      setLastSafety(safety);

      addCognitiveEvent({
        iteration: data.iteration || 0,
        phase: "safety_check",
        title: safety.skipped ? "安全检查跳过"
          : safety.safe ? "✓ 安全检查通过" : "✗ 检测到碰撞",
        detail: safety.skipped ? "非路径工具，无需检查"
          : safety.safe ? "路径无障碍物碰撞"
          : `碰撞点: [${safety.collision_point}]`,
        status: safety.safe ? "success" : "warning",
        data: safety,
      });

      if (safety.skipped) {
        addLog("info", "安全检查: 跳过（非路径工具）", "safety_check");
      } else if (safety.safe) {
        addLog("success", "✓ 安全检查通过，路径无碰撞", "safety_check");
      } else {
        addLog("warning", `✗ 检测到碰撞: ${JSON.stringify(safety.collision_point)}`, "safety_check", safety);
      }
    });

    // ── REFLECT 阶段 ─────────────────────────────────────────
    socket.on("agent_reflect", (data: any) => {
      setAgentState({ phase: "reflect", reflect_count: data.retry_count });
      addLog(
        "warning",
        `第 ${data.iteration} 轮 — REFLECT: 第 ${data.retry_count} 次反思重规划`,
        "reflect"
      );
    });

    socket.on("agent_reflect_done", (data: any) => {
      const guide = data.reflect_guide || {};
      addLog("info", `反思完成 — 推荐策略: ${guide.recommended_strategy}`, "reflect", guide);
      addMessage("assistant", `⚠️ 路径碰撞！使用 "${guide.recommended_strategy}" 策略重新规划...`);
      addCognitiveEvent({
        iteration: data.iteration || 0,
        phase: "reflect",
        title: `反思重规划 (第${data.retry_count}次)`,
        detail: `推荐策略: ${guide.recommended_strategy}`,
        status: "warning",
        data: guide,
      });
    });

    // ── 任务完成 ─────────────────────────────────────────────
    socket.on("agent_task_complete", (data: any) => {
      setIsRunning(false);
      setAgentState({
        phase: data.result?.status === "COMPLETED" ? "completed" : "failed"
      });
      addLog(
        data.result?.status === "COMPLETED" ? "success" : "error",
        `任务${data.result?.status === "COMPLETED" ? "完成" : "失败"}: ${data.result?.message || ""}`,
      );
    });

    // ── 任务结果 ─────────────────────────────────────────────
    socket.on("task_result", (data: any) => {
      const result = data.result || {};
      setTaskResult(result);
      setIsRunning(false);

      if (result.status === "COMPLETED") {
        addMessage("assistant",
          `✅ 任务完成！\n` +
          `• 执行轮次: ${result.iterations}\n` +
          `• 反思次数: ${result.reflect_count}\n` +
          `• ${result.message}`
        );
        addLog("success", `🎉 任务成功完成！共 ${result.iterations} 轮循环`);
      } else {
        addMessage("assistant", `❌ 任务失败: ${result.message}`);
        addLog("error", `任务失败: ${result.message}`);
      }

      if (data.grid_state) {
        setGridState({
          size: data.grid_state.size,
          current_position: data.grid_state.current_position,
          obstacle_count: data.grid_state.obstacle_count,
          free_ratio: data.grid_state.free_ratio,
          obstacles_by_layer: data.grid_state.obstacles_by_layer || {},
          obstacles: data.obstacles || [],
        });
      }

      // 拉取最新文件
      fetch("http://localhost:5000/api/code-files")
        .then((r) => r.json())
        .then((d) => { if (d.files) setCodeFiles(d.files); })
        .catch(() => {});

      fetch("http://localhost:5000/api/layer-maps")
        .then((r) => r.json())
        .then((d) => { if (d.files) setLayerMaps(d.files); })
        .catch(() => {});
    });

    // ── 栅格更新 ─────────────────────────────────────────────
    socket.on("grid_update", (data: any) => {
      if (data.grid) {
        setGridState({
          size: data.grid.size,
          current_position: data.grid.current_position,
          obstacle_count: data.grid.obstacle_count,
          free_ratio: data.grid.free_ratio,
          obstacles_by_layer: data.grid.obstacles_by_layer || {},
          obstacles: data.obstacles || [],
        });
      }
    });

    // ── 障碍物更新 ───────────────────────────────────────────
    socket.on("obstacles_updated", (data: any) => {
      if (data.obstacles !== undefined) {
        setGridState({ obstacles: data.obstacles, obstacle_count: data.total });
      }
      addLog("info", data.message || `障碍物已更新，共 ${data.total} 个`);
    });

    // ── 位置重置 ─────────────────────────────────────────────
    socket.on("position_reset", (data: any) => {
      addLog("info", `位置已重置: [${data.position}]`);
    });

    // ── 状态同步 ─────────────────────────────────────────────
    socket.on("agent_state_update", (data: any) => {
      if (data.agent) setAgentState(data.agent);
      if (data.grid) {
        setGridState({
          size: data.grid.size,
          current_position: data.grid.current_position,
          obstacle_count: data.grid.obstacle_count,
          free_ratio: data.grid.free_ratio,
          obstacles_by_layer: data.grid.obstacles_by_layer || {},
          obstacles: data.obstacles || [],
        });
      }
    });

    // ── 错误处理 ─────────────────────────────────────────────
    socket.on("agent_error", (data: any) => {
      setIsRunning(false);
      addLog("error", `Agent 错误: ${data.error}`);
      addMessage("assistant", `❌ 系统错误: ${data.error}`);
    });

    socket.on("error", (data: any) => {
      addLog("error", `错误: ${data.message || data}`);
    });

    // ── 清理 ─────────────────────────────────────────────────
    return () => {
      socket.disconnect();
    };
  }, []);

  // ── 发送方法 ──────────────────────────────────────────────
  const sendMessage = useCallback((message: string) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit("user_message", { message });
    }
  }, []);

  const addObstacles = useCallback((obstacles: number[][]) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit("add_obstacles", { obstacles });
    }
  }, []);

  const clearObstacles = useCallback(() => {
    if (socketRef.current?.connected) {
      socketRef.current.emit("clear_obstacles");
    }
  }, []);

  const resetPosition = useCallback(() => {
    if (socketRef.current?.connected) {
      socketRef.current.emit("reset_position");
    }
  }, []);

  const requestState = useCallback(() => {
    if (socketRef.current?.connected) {
      socketRef.current.emit("request_state");
    }
  }, []);

  return {
    sendMessage,
    addObstacles,
    clearObstacles,
    resetPosition,
    requestState,
  };
}
