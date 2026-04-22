// ── Agent 认知阶段 ─────────────────────────────────────────────
export type AgentPhase =
  | "idle"
  | "observe"
  | "think"
  | "act"
  | "safety_check"
  | "reflect"
  | "completed"
  | "failed";

// ── Agent 运行状态 ─────────────────────────────────────────────
export interface AgentState {
  phase: AgentPhase;
  task_id: string;
  user_input: string;
  iteration: number;
  reflect_count: number;
  cycles_count: number;
  last_path: number[][];
  last_waypoints: number[][];
}

// ── 栅格空间状态 ───────────────────────────────────────────────
export interface GridState {
  size: [number, number, number];
  current_position: [number, number, number];
  obstacle_count: number;
  free_ratio: number;
  obstacles: number[][];
  obstacles_by_layer: Record<number, number>;
}

// ── 工具调用记录 ───────────────────────────────────────────────
export interface ToolCall {
  tool_name: string;
  arguments: Record<string, any>;
  result?: {
    success: boolean;
    result: string;
    data?: any;
  };
  iteration: number;
  timestamp: number;
}

// ── 安全检查结果 ───────────────────────────────────────────────
export interface SafetyResult {
  safe: boolean;
  needs_reflect: boolean;
  collision_point: number[] | null;
  nearby_obstacles: number[][];
  tool_name: string;
  skipped: boolean;
}

// ── 任务结果 ───────────────────────────────────────────────────
export interface TaskResult {
  status: "COMPLETED" | "FAILED";
  message: string;
  task_id: string;
  iterations: number;
  reflect_count: number;
  last_path: number[][];
  last_waypoints: number[][];
}

// ── 日志消息 ───────────────────────────────────────────────────
export type LogLevel = "info" | "success" | "warning" | "error" | "system";

export interface LogMessage {
  id: number;
  level: LogLevel;
  phase?: AgentPhase;
  content: string;
  timestamp: number;
  data?: any;
}

// ── 聊天消息 ───────────────────────────────────────────────────
export type MessageRole = "user" | "assistant" | "system";

export interface ChatMessage {
  id: number;
  role: MessageRole;
  content: string;
  timestamp: number;
}

// ── 代码文件 ───────────────────────────────────────────────────
export interface CodeFile {
  filename: string;
  url: string;
  content: string;
  size: number;
}

// ── 切片图文件 ─────────────────────────────────────────────────
export interface LayerMapFile {
  filename: string;
  url: string;
  size: number;
}
