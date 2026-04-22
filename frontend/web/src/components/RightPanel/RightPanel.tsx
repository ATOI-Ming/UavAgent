import React, { useState, useRef, useEffect } from "react";
import { useAgentStore } from "../../store/agentStore";
import { LogMessage, AgentPhase } from "../../types";

interface RightPanelProps {
  onAddObstacles: (obstacles: number[][]) => void;
  onClearObstacles: () => void;
  onResetPosition: () => void;
}

type TabType = "logs" | "tools" | "result" | "env";

const TAB_CONFIG: { key: TabType; label: string; icon: string }[] = [
  { key: "logs",   label: "认知日志", icon: "📋" },
  { key: "tools",  label: "工具调用", icon: "🔧" },
  { key: "result", label: "任务结果", icon: "📊" },
  { key: "env",    label: "环境控制", icon: "🌍" },
];

const RightPanel: React.FC<RightPanelProps> = ({
  onAddObstacles,
  onClearObstacles,
  onResetPosition,
}) => {
  const [activeTab, setActiveTab] = useState<TabType>("logs");

  const {
    logs,
    toolCalls,
    taskResult,
    gridState,
    agentState,
    lastSafety,
    vizImageUrl,
    codeFiles,
    layerMaps,
    clearLogs,
    clearToolCalls,
  } = useAgentStore();

  const prevLogLen = useRef(logs.length);
  useEffect(() => {
    prevLogLen.current = logs.length;
  }, [logs.length]);

  return (
    <div style={styles.container}>
      {/* 标签栏 */}
      <div style={styles.tabBar}>
        {TAB_CONFIG.map((tab) => {
          const badge =
            tab.key === "logs" ? logs.length :
            tab.key === "tools" ? toolCalls.length : 0;

          return (
            <button
              key={tab.key}
              style={{
                ...styles.tab,
                ...(activeTab === tab.key ? styles.tabActive : {}),
              }}
              onClick={() => setActiveTab(tab.key)}
            >
              <span style={styles.tabIcon}>{tab.icon}</span>
              <span style={styles.tabLabel}>{tab.label}</span>
              {badge > 0 && (
                <span style={{
                  ...styles.tabBadge,
                  backgroundColor:
                    activeTab === tab.key
                      ? "rgba(96,165,250,0.25)"
                      : "rgba(96,165,250,0.1)",
                }}>
                  {badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* 内容区域 */}
      <div style={styles.content}>
        {activeTab === "logs"   && <LogsPanel logs={logs} onClear={clearLogs} />}
        {activeTab === "tools"  && <ToolsPanel toolCalls={toolCalls} onClear={clearToolCalls} />}
        {activeTab === "result" && (
          <ResultPanel
            taskResult={taskResult}
            lastSafety={lastSafety}
            agentState={agentState}
            vizImageUrl={vizImageUrl}
            codeFiles={codeFiles}
            layerMaps={layerMaps}
          />
        )}
        {activeTab === "env" && (
          <EnvPanel
            gridState={gridState}
            onAddObstacles={onAddObstacles}
            onClearObstacles={onClearObstacles}
            onResetPosition={onResetPosition}
          />
        )}
      </div>
    </div>
  );
};

// ══════════════════════════════════════════════════════════════
// 认知日志面板
// ══════════════════════════════════════════════════════════════
const LOG_COLORS: Record<string, string> = {
  info:    "#60a5fa",
  success: "#10b981",
  warning: "#f59e0b",
  error:   "#ef4444",
  system:  "#8b5cf6",
};

const LOG_ICONS: Record<string, string> = {
  info:    "\u2139",
  success: "\u2713",
  warning: "\u26A0",
  error:   "\u2717",
  system:  "\u25C6",
};

const PHASE_COLORS: Partial<Record<AgentPhase, string>> = {
  observe:      "#3b82f6",
  think:        "#8b5cf6",
  act:          "#f59e0b",
  safety_check: "#06b6d4",
  reflect:      "#f97316",
};

const LogsPanel: React.FC<{
  logs: LogMessage[];
  onClear: () => void;
}> = ({ logs, onClear }) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [filter, setFilter] = useState<string>("all");

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const handleScroll = () => {
    if (!scrollRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 30;
    setAutoScroll(isAtBottom);
  };

  const filteredLogs = filter === "all"
    ? logs
    : logs.filter((l) => l.level === filter);

  return (
    <div style={panelStyles.container}>
      <div style={panelStyles.actionBar}>
        <div style={panelStyles.filterRow}>
          {["all", "info", "success", "warning", "error", "system"].map((f) => (
            <button
              key={f}
              style={{
                ...panelStyles.filterBtn,
                ...(filter === f ? {
                  backgroundColor: "rgba(96,165,250,0.15)",
                  borderColor: "#3b82f6",
                  color: "#60a5fa",
                } : {}),
              }}
              onClick={() => setFilter(f)}
            >
              {f === "all" ? "\u5168\u90E8" :
               f === "info" ? "\u4FE1\u606F" :
               f === "success" ? "\u6210\u529F" :
               f === "warning" ? "\u8B66\u544A" :
               f === "error" ? "\u9519\u8BEF" : "\u7CFB\u7EDF"}
            </button>
          ))}
        </div>
        <div style={panelStyles.actionRight}>
          <span style={panelStyles.countText}>{filteredLogs.length} \u6761</span>
          <button style={panelStyles.clearBtn} onClick={onClear}>
            \u6E05\u7A7A
          </button>
        </div>
      </div>

      {!autoScroll && (
        <div
          style={panelStyles.scrollHint}
          onClick={() => {
            setAutoScroll(true);
            if (scrollRef.current) {
              scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
            }
          }}
        >
          \u2193 \u70B9\u51FB\u56DE\u5230\u5E95\u90E8\uFF08\u65B0\u65E5\u5FD7\u6301\u7EED\u66F4\u65B0\u4E2D\uFF09
        </div>
      )}

      <div
        ref={scrollRef}
        style={panelStyles.scrollArea}
        onScroll={handleScroll}
      >
        {filteredLogs.length === 0 ? (
          <EmptyTip icon="\uD83D\uDCCB" text="\u6682\u65E0\u65E5\u5FD7" />
        ) : (
          filteredLogs.map((log) => (
            <LogEntry key={log.id} log={log} />
          ))
        )}
      </div>
    </div>
  );
};

const LogEntry: React.FC<{ log: LogMessage }> = ({ log }) => {
  const [expanded, setExpanded] = useState(false);
  const color = LOG_COLORS[log.level] || "#6b7280";
  const icon  = LOG_ICONS[log.level] || "\u2022";
  const phaseColor = log.phase ? (PHASE_COLORS[log.phase] || "#4b6080") : "#4b6080";
  const hasData = log.data != null;

  return (
    <div
      style={{
        ...logEntryStyles.container,
        borderLeft: `2px solid ${color}30`,
      }}
      onClick={() => hasData && setExpanded(!expanded)}
    >
      <div style={logEntryStyles.header}>
        <span style={{ ...logEntryStyles.icon, color }}>{icon}</span>
        <div style={logEntryStyles.body}>
          <span style={{ ...logEntryStyles.text, color }}>
            {log.content}
          </span>
          <div style={logEntryStyles.meta}>
            {log.phase && (
              <span style={{
                ...logEntryStyles.phaseBadge,
                color: phaseColor,
                borderColor: phaseColor + "40",
                backgroundColor: phaseColor + "10",
              }}>
                {log.phase}
              </span>
            )}
            <span style={logEntryStyles.time}>
              {new Date(log.timestamp).toLocaleTimeString("zh-CN")}
            </span>
            {hasData && (
              <span style={logEntryStyles.expandBtn}>
                {expanded ? "\u25B2" : "\u25BC"}
              </span>
            )}
          </div>
        </div>
      </div>

      {expanded && log.data && (
        <div style={logEntryStyles.detail}>
          <pre style={logEntryStyles.pre}>
            {JSON.stringify(log.data, null, 2).slice(0, 600)}
          </pre>
        </div>
      )}
    </div>
  );
};

// ══════════════════════════════════════════════════════════════
// 工具调用面板
// ══════════════════════════════════════════════════════════════
const ToolsPanel: React.FC<{
  toolCalls: any[];
  onClear: () => void;
}> = ({ toolCalls, onClear }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [toolCalls]);

  return (
    <div style={panelStyles.container}>
      <div style={panelStyles.actionBar}>
        <span style={panelStyles.countText}>
          \u5171 {toolCalls.length} \u6B21\u5DE5\u5177\u8C03\u7528
        </span>
        <button style={panelStyles.clearBtn} onClick={onClear}>
          \u6E05\u7A7A
        </button>
      </div>

      <div ref={scrollRef} style={panelStyles.scrollArea}>
        {toolCalls.length === 0 ? (
          <EmptyTip icon="\uD83D\uDD27" text="\u6682\u65E0\u5DE5\u5177\u8C03\u7528\u8BB0\u5F55" />
        ) : (
          [...toolCalls].reverse().map((tc, i) => (
            <ToolCallEntry key={i} toolCall={tc} index={toolCalls.length - i} />
          ))
        )}
      </div>
    </div>
  );
};

const ToolCallEntry: React.FC<{ toolCall: any; index: number }> = ({
  toolCall,
  index,
}) => {
  const [expanded, setExpanded] = useState(false);
  const success = toolCall.result?.success;
  const statusColor = success === false ? "#ef4444" : "#10b981";

  return (
    <div style={toolEntryStyles.container}>
      <div
        style={toolEntryStyles.header}
        onClick={() => setExpanded(!expanded)}
      >
        <div style={{
          ...toolEntryStyles.statusDot,
          backgroundColor: statusColor,
          boxShadow: `0 0 4px ${statusColor}`,
        }} />
        <div style={toolEntryStyles.info}>
          <span style={toolEntryStyles.name}>{toolCall.tool_name}</span>
          <div style={toolEntryStyles.meta}>
            <span style={toolEntryStyles.iter}>第 {toolCall.iteration} 轮</span>
            <span style={toolEntryStyles.time}>
              {new Date(toolCall.timestamp).toLocaleTimeString("zh-CN")}
            </span>
          </div>
        </div>
        <span style={toolEntryStyles.expand}>{expanded ? "\u25B2" : "\u25BC"}</span>
      </div>

      {expanded && (
        <div style={toolEntryStyles.detail}>
          <div style={toolEntryStyles.section}>
            <div style={toolEntryStyles.sectionTitle}>📥 输入参数</div>
            <pre style={toolEntryStyles.pre}>
              {JSON.stringify(toolCall.arguments, null, 2).slice(0, 400)}
            </pre>
          </div>
          {toolCall.result && (
            <div style={toolEntryStyles.section}>
              <div style={toolEntryStyles.sectionTitle}>
                {success ? "✅ 执行结果" : "❌ 执行失败"}
              </div>
              <pre style={{
                ...toolEntryStyles.pre,
                color: success ? "#9ca3af" : "#f87171",
              }}>
                {(toolCall.result.result || "").slice(0, 300)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ══════════════════════════════════════════════════════════════
// 任务结果面板
// ══════════════════════════════════════════════════════════════
const ResultPanel: React.FC<{
  taskResult: any;
  lastSafety: any;
  agentState: any;
  vizImageUrl: string | null;
  codeFiles: any[];
  layerMaps: any[];
}> = ({ taskResult, lastSafety, agentState, vizImageUrl, codeFiles, layerMaps }) => {
  return (
    <div style={panelStyles.scrollArea}>
      {taskResult ? (
        <ResultCard taskResult={taskResult} agentState={agentState} />
      ) : (
        <div style={resultStyles.noTask}>
          <EmptyTip
            icon="📊"
            text="暂无任务结果"
            hint="发送飞行指令后查看执行结果"
          />
        </div>
      )}

      {lastSafety && !lastSafety.skipped && (
        <SectionCard title="最近安全检查">
          <div style={{
            ...resultStyles.safetyBox,
            borderColor: lastSafety.safe ? "#10b981" : "#ef4444",
            backgroundColor: lastSafety.safe
              ? "rgba(16,185,129,0.07)"
              : "rgba(239,68,68,0.07)",
          }}>
            <span style={{
              color: lastSafety.safe ? "#10b981" : "#ef4444",
              fontWeight: "bold",
              fontSize: "13px",
            }}>
              {lastSafety.safe ? "✓ 路径安全" : "✗ 检测到碰撞"}
            </span>
            {!lastSafety.safe && lastSafety.collision_point && (
              <div style={resultStyles.collisionInfo}>
                碰撞点: [{lastSafety.collision_point.join(", ")}]
              </div>
            )}
          </div>
        </SectionCard>
      )}

      {vizImageUrl && (
        <SectionCard title="3D 飞行路径图">
          <img
            src={vizImageUrl}
            alt="飞行路径"
            style={resultStyles.vizImage}
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = "none";
            }}
          />
          <a
            href={vizImageUrl}
            target="_blank"
            rel="noreferrer"
            style={resultStyles.viewLink}
          >
            🔍 在新窗口查看大图
          </a>
        </SectionCard>
      )}

      {layerMaps.length > 0 && (
        <SectionCard title={`分层切片图（${layerMaps.length} 张）`}>
          <div style={resultStyles.fileList}>
            {layerMaps.map((f: any, i: number) => (
              <a
                key={i}
                href={f.url}
                target="_blank"
                rel="noreferrer"
                style={resultStyles.fileLink}
              >
                <span>📄</span>
                <span style={resultStyles.fileName}>{f.filename}</span>
                <span style={resultStyles.fileOpen}>查看 →</span>
              </a>
            ))}
          </div>
        </SectionCard>
      )}

      {codeFiles.length > 0 && (
        <SectionCard title={`生成飞行代码（${codeFiles.length} 个文件）`}>
          <div style={resultStyles.fileList}>
            {codeFiles.map((f: any, i: number) => (
              <a
                key={i}
                href={f.url}
                target="_blank"
                rel="noreferrer"
                style={resultStyles.fileLink}
              >
                <span>🐍</span>
                <span style={resultStyles.fileName}>{f.filename}</span>
                <span style={resultStyles.fileOpen}>查看 →</span>
              </a>
            ))}
          </div>

          {codeFiles[0]?.content && (
            <div style={resultStyles.codePreview}>
              <div style={resultStyles.codePreviewTitle}>
                预览：{codeFiles[0].filename}
              </div>
              <pre style={resultStyles.codePre}>
                {codeFiles[0].content.slice(0, 400)}
                {codeFiles[0].content.length > 400 && "\n..."}
              </pre>
            </div>
          )}
        </SectionCard>
      )}
    </div>
  );
};

const ResultCard: React.FC<{ taskResult: any; agentState: any }> = ({
  taskResult,
}) => {
  const isOk = taskResult.status === "COMPLETED";
  return (
    <SectionCard title="任务执行结果">
      <div style={{
        ...resultStyles.resultBox,
        borderColor: isOk ? "#10b981" : "#ef4444",
        backgroundColor: isOk
          ? "rgba(16,185,129,0.07)"
          : "rgba(239,68,68,0.07)",
      }}>
        <div style={{
          color: isOk ? "#10b981" : "#ef4444",
          fontWeight: "bold",
          fontSize: "16px",
          marginBottom: "10px",
        }}>
          {isOk ? "✅ 任务完成" : "❌ 任务失败"}
        </div>
        <div style={resultStyles.resultMessage}>{taskResult.message}</div>
        <div style={resultStyles.statGrid}>
          <StatBox label="执行轮次" value={taskResult.iterations} />
          <StatBox
            label="反思次数"
            value={taskResult.reflect_count}
            color={taskResult.reflect_count > 0 ? "#f97316" : undefined}
          />
          <StatBox
            label="关键航点"
            value={taskResult.last_waypoints?.length || 0}
          />
          <StatBox
            label="路径节点"
            value={taskResult.last_path?.length || 0}
          />
        </div>
      </div>
    </SectionCard>
  );
};

const StatBox: React.FC<{
  label: string;
  value: number;
  color?: string;
}> = ({ label, value, color }) => (
  <div style={resultStyles.statBox}>
    <div style={{ ...resultStyles.statValue, color: color || "#c8d8f0" }}>
      {value}
    </div>
    <div style={resultStyles.statLabel}>{label}</div>
  </div>
);

// ══════════════════════════════════════════════════════════════
// 环境控制面板
// ══════════════════════════════════════════════════════════════
const PRESET_OBSTACLES = [
  {
    label: "前方墙壁",
    desc: "正前方 3×3 障碍物",
    data: "60,48,0\n60,49,0\n60,50,0\n60,51,0\n60,52,0",
  },
  {
    label: "高空障碍",
    desc: "高度5米障碍物",
    data: "60,50,5\n61,50,5\n62,50,5",
  },
  {
    label: "L形障碍",
    desc: "L型障碍物组合",
    data: "55,50,0\n56,50,0\n57,50,0\n57,51,0\n57,52,0",
  },
];

const QUICK_CMDS = [
  { label: "正方形飞行", cmd: "飞一个边长3米的正方形" },
  { label: "向前10米",   cmd: "向前飞10米" },
  { label: "上升5米",    cmd: "上升5米" },
  { label: "Z字形",      cmd: "飞一个Z字形路径" },
  { label: "查看切片",   cmd: "显示当前环境的分层切片图" },
  { label: "生成代码",   cmd: "根据当前路径生成飞行代码" },
];

const EnvPanel: React.FC<{
  gridState: any;
  onAddObstacles: (o: number[][]) => void;
  onClearObstacles: () => void;
  onResetPosition: () => void;
}> = ({ gridState, onAddObstacles, onClearObstacles, onResetPosition }) => {
  const [obsInput, setObsInput] = useState("60,50,0\n60,51,0\n60,52,0");
  const [obsError, setObsError] = useState("");
  const [addSuccess, setAddSuccess] = useState(false);

  const handleAdd = () => {
    setObsError("");
    setAddSuccess(false);
    try {
      const lines = obsInput
        .split("\n")
        .map((l) => l.trim())
        .filter(Boolean);
      const obstacles: number[][] = [];
      for (const line of lines) {
        const parts = line.split(",").map((p) => parseInt(p.trim()));
        if (parts.length !== 3 || parts.some(isNaN)) {
          setObsError(`格式错误: "${line}"，正确格式为 x,y,z`);
          return;
        }
        obstacles.push(parts);
      }
      if (obstacles.length === 0) {
        setObsError("请至少输入一个坐标");
        return;
      }
      onAddObstacles(obstacles);
      setAddSuccess(true);
      setTimeout(() => setAddSuccess(false), 2000);
    } catch {
      setObsError("解析失败，请检查格式");
    }
  };

  const handlePreset = (data: string) => {
    setObsInput(data);
    setObsError("");
  };

  return (
    <div style={panelStyles.scrollArea}>
      <SectionCard title="当前环境信息">
        <div style={envStyles.infoGrid}>
          <InfoRow label="栅格大小" value={gridState.size?.join(" × ") || "--"} />
          <InfoRow
            label="当前位置"
            value={`[${(gridState.current_position || []).join(", ")}]`}
          />
          <InfoRow
            label="障碍物数量"
            value={`${gridState.obstacle_count || 0} 个`}
            color={gridState.obstacle_count > 0 ? "#f59e0b" : "#10b981"}
          />
          <InfoRow
            label="空闲比例"
            value={`${((gridState.free_ratio || 1) * 100).toFixed(2)}%`}
          />
        </div>
      </SectionCard>

      <SectionCard title="位置控制">
        <button style={envStyles.resetBtn} onClick={onResetPosition}>
          🔄 重置到初始位置 (50, 50, 0)
        </button>
      </SectionCard>

      <SectionCard title="预设障碍物场景">
        <div style={envStyles.presetList}>
          {PRESET_OBSTACLES.map((p, i) => (
            <div
              key={i}
              style={envStyles.presetItem}
              onClick={() => handlePreset(p.data)}
            >
              <span style={envStyles.presetLabel}>{p.label}</span>
              <span style={envStyles.presetDesc}>{p.desc}</span>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard title="障碍物管理">
        <div style={envStyles.fieldLabel}>
          坐标输入（每行一个，格式：x,y,z）
        </div>
        <textarea
          style={envStyles.textarea}
          value={obsInput}
          onChange={(e) => {
            setObsInput(e.target.value);
            setObsError("");
          }}
          rows={4}
          placeholder={"60,50,0\n60,51,0\n60,52,0"}
        />
        {obsError && (
          <div style={envStyles.errorText}>⚠ {obsError}</div>
        )}
        {addSuccess && (
          <div style={envStyles.successText}>✓ 障碍物添加成功</div>
        )}
        <div style={envStyles.btnRow}>
          <button style={envStyles.addBtn} onClick={handleAdd}>
            ➕ 添加障碍物
          </button>
          <button style={envStyles.clearBtn} onClick={onClearObstacles}>
            🗑 清除全部
          </button>
        </div>
      </SectionCard>

      <SectionCard title="快捷飞行指令">
        <div style={envStyles.quickGrid}>
          {QUICK_CMDS.map((q, i) => (
            <button
              key={i}
              style={envStyles.quickBtn}
              onClick={() => {
                useAgentStore.getState().addMessage("user", q.cmd);
              }}
              title={q.cmd}
            >
              {q.label}
            </button>
          ))}
        </div>
        <div style={envStyles.quickHint}>
          点击后在对话框发送该指令
        </div>
      </SectionCard>
    </div>
  );
};

// ── 通用子组件 ────────────────────────────────────────────────
const SectionCard: React.FC<{
  title: string;
  children: React.ReactNode;
}> = ({ title, children }) => (
  <div style={sectionStyles.container}>
    <div style={sectionStyles.header}>
      <div style={sectionStyles.headerLine} />
      <span style={sectionStyles.title}>{title}</span>
    </div>
    <div style={sectionStyles.body}>{children}</div>
  </div>
);

const InfoRow: React.FC<{
  label: string;
  value: string;
  color?: string;
}> = ({ label, value, color }) => (
  <div style={envStyles.infoRow}>
    <span style={envStyles.infoLabel}>{label}</span>
    <span style={{ ...envStyles.infoValue, color: color || "#c8d8f0" }}>
      {value}
    </span>
  </div>
);

const EmptyTip: React.FC<{
  icon: string;
  text: string;
  hint?: string;
}> = ({ icon, text, hint }) => (
  <div style={emptyStyles.container}>
    <div style={emptyStyles.icon}>{icon}</div>
    <div style={emptyStyles.text}>{text}</div>
    {hint && <div style={emptyStyles.hint}>{hint}</div>}
  </div>
);

// ══════════════════════════════════════════════════════════════
// 样式
// ══════════════════════════════════════════════════════════════
const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
    backgroundColor: "#0b1220",
    overflow: "hidden",
  },
  tabBar: {
    display: "flex",
    borderBottom: "1px solid #1a2540",
    flexShrink: 0,
    backgroundColor: "#080d18",
  },
  tab: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: "2px",
    padding: "8px 4px",
    background: "none",
    border: "none",
    borderBottom: "2px solid transparent",
    color: "#2d4060",
    cursor: "pointer",
    fontSize: "10px",
    transition: "all 0.2s",
    position: "relative",
  },
  tabActive: {
    color: "#60a5fa",
    borderBottom: "2px solid #3b82f6",
    backgroundColor: "rgba(59,130,246,0.05)",
  },
  tabIcon: { fontSize: "14px" },
  tabLabel: { fontSize: "10px", letterSpacing: "0.3px" },
  tabBadge: {
    position: "absolute",
    top: "5px",
    right: "6px",
    fontSize: "9px",
    padding: "1px 4px",
    borderRadius: "8px",
    color: "#60a5fa",
    minWidth: "16px",
    textAlign: "center",
  },
  content: {
    flex: 1,
    overflow: "hidden",
    display: "flex",
    flexDirection: "column",
    minHeight: 0,
  },
};

const panelStyles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
    minHeight: 0,
    overflow: "hidden",
  },
  actionBar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "7px 12px",
    borderBottom: "1px solid #1a2540",
    flexShrink: 0,
    gap: "8px",
    flexWrap: "wrap",
  },
  filterRow: {
    display: "flex",
    gap: "4px",
    flexWrap: "wrap",
  },
  filterBtn: {
    padding: "2px 8px",
    background: "none",
    border: "1px solid #1a2540",
    borderRadius: "10px",
    color: "#4b6080",
    cursor: "pointer",
    fontSize: "10px",
    transition: "all 0.2s",
  },
  actionRight: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  countText: {
    fontSize: "10px",
    color: "#2d4060",
  },
  clearBtn: {
    padding: "3px 10px",
    background: "none",
    border: "1px solid #1a2540",
    borderRadius: "6px",
    color: "#4b6080",
    cursor: "pointer",
    fontSize: "10px",
  },
  scrollHint: {
    textAlign: "center",
    padding: "5px",
    backgroundColor: "rgba(59,130,246,0.1)",
    color: "#60a5fa",
    fontSize: "11px",
    cursor: "pointer",
    flexShrink: 0,
    borderBottom: "1px solid #1a2540",
  },
  scrollArea: {
    flex: 1,
    overflowY: "auto",
    overflowX: "hidden",
    padding: "8px",
    display: "flex",
    flexDirection: "column",
    gap: "4px",
    minHeight: 0,
  },
};

const logEntryStyles: Record<string, React.CSSProperties> = {
  container: {
    padding: "6px 8px",
    borderRadius: "6px",
    backgroundColor: "#0f1929",
    cursor: "pointer",
    transition: "background 0.15s",
    flexShrink: 0,
  },
  header: {
    display: "flex",
    gap: "8px",
    alignItems: "flex-start",
  },
  icon: {
    fontSize: "11px",
    flexShrink: 0,
    marginTop: "2px",
  },
  body: {
    flex: 1,
    minWidth: 0,
  },
  text: {
    fontSize: "12px",
    lineHeight: "1.5",
    wordBreak: "break-word",
    display: "block",
  },
  meta: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    marginTop: "3px",
    flexWrap: "wrap",
  },
  phaseBadge: {
    fontSize: "9px",
    padding: "1px 6px",
    borderRadius: "8px",
    border: "1px solid",
    fontFamily: "monospace",
  },
  time: {
    fontSize: "10px",
    color: "#1e3050",
    fontFamily: "monospace",
  },
  expandBtn: {
    fontSize: "9px",
    color: "#2d4060",
  },
  detail: {
    marginTop: "6px",
    paddingTop: "6px",
    borderTop: "1px solid #0d1929",
  },
  pre: {
    fontSize: "10px",
    color: "#4b6080",
    fontFamily: "monospace",
    whiteSpace: "pre-wrap",
    wordBreak: "break-all",
    margin: 0,
    backgroundColor: "#080d18",
    padding: "6px",
    borderRadius: "4px",
    maxHeight: "120px",
    overflowY: "auto",
  },
};

const toolEntryStyles: Record<string, React.CSSProperties> = {
  container: {
    backgroundColor: "#0f1929",
    borderRadius: "8px",
    border: "1px solid #1a2540",
    overflow: "hidden",
    flexShrink: 0,
  },
  header: {
    display: "flex",
    alignItems: "center",
    padding: "9px 12px",
    cursor: "pointer",
    gap: "10px",
  },
  statusDot: {
    width: "8px",
    height: "8px",
    borderRadius: "50%",
    flexShrink: 0,
  },
  info: {
    flex: 1,
    minWidth: 0,
  },
  name: {
    fontSize: "12px",
    fontWeight: "bold",
    color: "#60a5fa",
    fontFamily: "monospace",
    display: "block",
  },
  meta: {
    display: "flex",
    gap: "8px",
    marginTop: "2px",
  },
  iter: {
    fontSize: "10px",
    color: "#2d4060",
  },
  time: {
    fontSize: "10px",
    color: "#1e3050",
    fontFamily: "monospace",
  },
  expand: {
    fontSize: "10px",
    color: "#2d4060",
    flexShrink: 0,
  },
  detail: {
    padding: "8px 12px",
    borderTop: "1px solid #1a2540",
  },
  section: { marginBottom: "8px" },
  sectionTitle: {
    fontSize: "10px",
    color: "#4b6080",
    marginBottom: "4px",
    fontWeight: "bold",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },
  pre: {
    fontSize: "10px",
    color: "#4b6080",
    fontFamily: "monospace",
    whiteSpace: "pre-wrap",
    wordBreak: "break-all",
    margin: 0,
    backgroundColor: "#080d18",
    padding: "6px",
    borderRadius: "4px",
    maxHeight: "140px",
    overflowY: "auto",
  },
};

const resultStyles: Record<string, React.CSSProperties> = {
  noTask: { padding: "20px 0" },
  resultBox: {
    padding: "14px",
    borderRadius: "8px",
    border: "1px solid",
  },
  resultMessage: {
    fontSize: "12px",
    color: "#6b7280",
    marginBottom: "12px",
    lineHeight: "1.5",
  },
  statGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "8px",
  },
  statBox: {
    backgroundColor: "#080d18",
    borderRadius: "6px",
    padding: "8px",
    textAlign: "center",
    border: "1px solid #1a2540",
  },
  statValue: {
    fontSize: "20px",
    fontWeight: "bold",
    fontFamily: "monospace",
    display: "block",
  },
  statLabel: {
    fontSize: "10px",
    color: "#2d4060",
    marginTop: "2px",
    display: "block",
  },
  safetyBox: {
    padding: "10px 12px",
    borderRadius: "6px",
    border: "1px solid",
  },
  collisionInfo: {
    fontSize: "11px",
    color: "#f87171",
    marginTop: "4px",
    fontFamily: "monospace",
  },
  vizImage: {
    width: "100%",
    borderRadius: "6px",
    border: "1px solid #1a2540",
    marginBottom: "8px",
  },
  viewLink: {
    fontSize: "11px",
    color: "#60a5fa",
    textDecoration: "none",
    display: "block",
    textAlign: "center",
  },
  fileList: {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
  },
  fileLink: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "7px 10px",
    backgroundColor: "#080d18",
    borderRadius: "6px",
    border: "1px solid #1a2540",
    textDecoration: "none",
    color: "#c8d8f0",
    transition: "border-color 0.2s",
  },
  fileName: {
    flex: 1,
    fontSize: "11px",
    fontFamily: "monospace",
    color: "#6b7280",
  },
  fileOpen: {
    fontSize: "10px",
    color: "#60a5fa",
  },
  codePreview: {
    marginTop: "8px",
  },
  codePreviewTitle: {
    fontSize: "10px",
    color: "#2d4060",
    marginBottom: "4px",
  },
  codePre: {
    fontSize: "10px",
    color: "#4b6080",
    fontFamily: "monospace",
    whiteSpace: "pre-wrap",
    wordBreak: "break-all",
    backgroundColor: "#080d18",
    padding: "8px",
    borderRadius: "6px",
    margin: 0,
    maxHeight: "180px",
    overflowY: "auto",
  },
};

const envStyles: Record<string, React.CSSProperties> = {
  infoGrid: {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
  },
  infoRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "5px 0",
    borderBottom: "1px solid #0d1929",
  },
  infoLabel: {
    fontSize: "11px",
    color: "#2d4060",
  },
  infoValue: {
    fontSize: "12px",
    fontFamily: "monospace",
    fontWeight: "bold",
  },
  resetBtn: {
    width: "100%",
    padding: "8px",
    backgroundColor: "#0f1929",
    border: "1px solid #1a2540",
    borderRadius: "7px",
    color: "#60a5fa",
    cursor: "pointer",
    fontSize: "12px",
    transition: "all 0.2s",
  },
  presetList: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  presetItem: {
    padding: "8px 12px",
    backgroundColor: "#080d18",
    borderRadius: "6px",
    border: "1px solid #1a2540",
    cursor: "pointer",
    transition: "border-color 0.2s",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  presetLabel: {
    fontSize: "12px",
    color: "#60a5fa",
    fontWeight: "bold",
  },
  presetDesc: {
    fontSize: "10px",
    color: "#2d4060",
  },
  fieldLabel: {
    fontSize: "10px",
    color: "#2d4060",
    marginBottom: "6px",
  },
  textarea: {
    width: "100%",
    backgroundColor: "#080d18",
    border: "1px solid #1a2540",
    borderRadius: "7px",
    color: "#c8d8f0",
    padding: "8px 10px",
    fontSize: "12px",
    fontFamily: "monospace",
    resize: "vertical",
    outline: "none",
    boxSizing: "border-box",
    lineHeight: "1.6",
  },
  errorText: {
    fontSize: "11px",
    color: "#ef4444",
    marginTop: "5px",
  },
  successText: {
    fontSize: "11px",
    color: "#10b981",
    marginTop: "5px",
  },
  btnRow: {
    display: "flex",
    gap: "8px",
    marginTop: "8px",
  },
  addBtn: {
    flex: 1,
    padding: "8px",
    backgroundColor: "rgba(29,78,216,0.3)",
    border: "1px solid #1d4ed8",
    borderRadius: "7px",
    color: "#60a5fa",
    cursor: "pointer",
    fontSize: "12px",
    fontWeight: "bold",
    transition: "all 0.2s",
  },
  clearBtn: {
    flex: 1,
    padding: "8px",
    backgroundColor: "rgba(127,29,29,0.3)",
    border: "1px solid #7f1d1d",
    borderRadius: "7px",
    color: "#f87171",
    cursor: "pointer",
    fontSize: "12px",
    transition: "all 0.2s",
  },
  quickGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "6px",
    marginBottom: "6px",
  },
  quickBtn: {
    padding: "7px 8px",
    backgroundColor: "#080d18",
    border: "1px solid #1a2540",
    borderRadius: "7px",
    color: "#60a5fa",
    cursor: "pointer",
    fontSize: "11px",
    transition: "all 0.2s",
    textAlign: "center",
  },
  quickHint: {
    fontSize: "10px",
    color: "#1e3050",
    textAlign: "center",
    marginTop: "2px",
  },
};

const sectionStyles: Record<string, React.CSSProperties> = {
  container: {
    backgroundColor: "#0f1929",
    borderRadius: "8px",
    border: "1px solid #1a2540",
    overflow: "hidden",
    flexShrink: 0,
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    padding: "8px 12px",
    borderBottom: "1px solid #1a2540",
    backgroundColor: "#080d18",
  },
  headerLine: {
    width: "3px",
    height: "12px",
    backgroundColor: "#3b82f6",
    borderRadius: "2px",
    flexShrink: 0,
  },
  title: {
    fontSize: "11px",
    fontWeight: "bold",
    color: "#4b6080",
    letterSpacing: "0.5px",
    textTransform: "uppercase",
  },
  body: {
    padding: "10px 12px",
  },
};

const emptyStyles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    padding: "30px 20px",
    gap: "8px",
  },
  icon: { fontSize: "32px" },
  text: {
    fontSize: "13px",
    color: "#2d4060",
  },
  hint: {
    fontSize: "11px",
    color: "#1e3050",
    textAlign: "center",
  },
};

export default RightPanel;
