import { create } from "zustand";
import {
  AgentState,
  GridState,
  LogMessage,
  ChatMessage,
  ToolCall,
  SafetyResult,
  TaskResult,
  CodeFile,
  LayerMapFile,
  LogLevel,
  AgentPhase,
} from "../types";

export interface CognitiveEvent {
  id: number;
  iteration: number;
  phase: AgentPhase;
  title: string;
  detail: string;
  status: "running" | "success" | "warning" | "error";
  timestamp: number;
  data?: any;
}

const initialAgentState: AgentState = {
  phase: "idle",
  task_id: "",
  user_input: "",
  iteration: 0,
  reflect_count: 0,
  cycles_count: 0,
  last_path: [],
  last_waypoints: [],
};

const initialGridState: GridState = {
  size: [100, 100, 20],
  current_position: [50, 50, 0],
  obstacle_count: 0,
  free_ratio: 1,
  obstacles: [],
  obstacles_by_layer: {},
};

type MessageRole = "user" | "assistant" | "system";

interface AgentStore {
  connected: boolean;
  setConnected: (v: boolean) => void;

  agentState: AgentState;
  setAgentState: (s: Partial<AgentState>) => void;

  gridState: GridState;
  setGridState: (g: Partial<GridState>) => void;

  logs: LogMessage[];
  addLog: (level: LogLevel, content: string, phase?: AgentPhase, data?: any) => void;
  clearLogs: () => void;

  messages: ChatMessage[];
  addMessage: (role: MessageRole, content: string) => void;
  clearMessages: () => void;

  cognitiveEvents: CognitiveEvent[];
  addCognitiveEvent: (event: Omit<CognitiveEvent, "id" | "timestamp">) => void;
  clearCognitiveEvents: () => void;

  toolCalls: ToolCall[];
  addToolCall: (tc: ToolCall) => void;
  clearToolCalls: () => void;

  lastSafety: SafetyResult | null;
  setLastSafety: (s: SafetyResult | null) => void;

  taskResult: TaskResult | null;
  setTaskResult: (r: TaskResult | null) => void;

  codeFiles: CodeFile[];
  setCodeFiles: (files: CodeFile[]) => void;

  layerMaps: LayerMapFile[];
  setLayerMaps: (files: LayerMapFile[]) => void;

  vizImageUrl: string | null;
  setVizImageUrl: (url: string | null) => void;

  isRunning: boolean;
  setIsRunning: (v: boolean) => void;
}

let logId = 0;
let msgId = 0;
let cogId = 0;

export const useAgentStore = create<AgentStore>((set) => ({
  connected: false,
  setConnected: (v) => set({ connected: v }),

  agentState: initialAgentState,
  setAgentState: (s) =>
    set((state) => ({ agentState: { ...state.agentState, ...s } })),

  gridState: initialGridState,
  setGridState: (g) =>
    set((state) => ({ gridState: { ...state.gridState, ...g } })),

  logs: [],
  addLog: (level, content, phase, data) =>
    set((state) => ({
      logs: [
        ...state.logs,
        { id: ++logId, level, content, phase, timestamp: Date.now(), data },
      ].slice(-300),
    })),
  clearLogs: () => set({ logs: [] }),

  messages: [],
  addMessage: (role, content) =>
    set((state) => ({
      messages: [
        ...state.messages,
        { id: ++msgId, role, content, timestamp: Date.now() },
      ],
    })),
  clearMessages: () => set({ messages: [] }),

  cognitiveEvents: [],
  addCognitiveEvent: (event) =>
    set((state) => ({
      cognitiveEvents: [
        ...state.cognitiveEvents,
        { ...event, id: ++cogId, timestamp: Date.now() },
      ].slice(-100),
    })),
  clearCognitiveEvents: () => set({ cognitiveEvents: [] }),

  toolCalls: [],
  addToolCall: (tc) =>
    set((state) => ({
      toolCalls: [...state.toolCalls, tc].slice(-50),
    })),
  clearToolCalls: () => set({ toolCalls: [] }),

  lastSafety: null,
  setLastSafety: (s) => set({ lastSafety: s }),

  taskResult: null,
  setTaskResult: (r) => set({ taskResult: r }),

  codeFiles: [],
  setCodeFiles: (files) => set({ codeFiles: files }),

  layerMaps: [],
  setLayerMaps: (files) => set({ layerMaps: files }),

  vizImageUrl: null,
  setVizImageUrl: (url) => set({ vizImageUrl: url }),

  isRunning: false,
  setIsRunning: (v) => set({ isRunning: v }),
}));
