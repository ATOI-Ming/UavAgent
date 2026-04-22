import React from "react";
import { useAgentStore } from "../../store/agentStore";
import { AgentPhase } from "../../types";

const PHASE_CONFIG: Record<
  AgentPhase,
  { label: string; color: string; icon: string }
> = {
  idle:         { label: "空闲",     color: "#4b5563", icon: "💤" },
  observe:      { label: "观察中",   color: "#3b82f6", icon: "👁" },
  think:        { label: "推理中",   color: "#8b5cf6", icon: "🧠" },
  act:          { label: "执行中",   color: "#f59e0b", icon: "⚡" },
  safety_check: { label: "安全检查", color: "#06b6d4", icon: "🛡" },
  reflect:      { label: "反思中",   color: "#f97316", icon: "🔄" },
  completed:    { label: "已完成",   color: "#10b981", icon: "✅" },
  failed:       { label: "已失败",   color: "#ef4444", icon: "❌" },
};

const PHASE_ORDER: AgentPhase[] = [
  "observe", "think", "act", "safety_check", "reflect",
];

const StatusBar: React.FC = () => {
  const { connected, agentState, gridState, isRunning } = useAgentStore();
  const phase = agentState.phase;
  const cfg = PHASE_CONFIG[phase] || PHASE_CONFIG.idle;

  return (
    <div style={styles.container}>
      {/* Logo */}
      <div style={styles.logo}>
        <span style={styles.logoIcon}>🚁</span>
        <div style={styles.logoText}>
          <span style={styles.logoName}>UavAgent</span>
          <span style={styles.logoSub}>无人机智能飞行系统</span>
        </div>
      </div>

      {/* 认知阶段流水线 */}
      <div style={styles.pipeline}>
        {PHASE_ORDER.map((p, idx) => {
          const c = PHASE_CONFIG[p];
          const isActive = phase === p;
          const isPast =
            PHASE_ORDER.indexOf(phase) > idx &&
            phase !== "idle" &&
            phase !== "completed" &&
            phase !== "failed";

          return (
            <React.Fragment key={p}>
              <div style={styles.pipelineItem}>
                <div
                  style={{
                    ...styles.pipelineDot,
                    backgroundColor: isActive
                      ? c.color
                      : isPast
                      ? `${c.color}60`
                      : "#1a2540",
                    boxShadow: isActive
                      ? `0 0 10px ${c.color}, 0 0 20px ${c.color}40`
                      : "none",
                    border: `2px solid ${
                      isActive ? c.color : isPast ? `${c.color}60` : "#2d3a50"
                    }`,
                  }}
                >
                  <span style={{ fontSize: "10px" }}>{c.icon}</span>
                </div>
                <span
                  style={{
                    ...styles.pipelineLabel,
                    color: isActive
                      ? c.color
                      : isPast
                      ? `${c.color}80`
                      : "#2d3a50",
                  }}
                >
                  {c.label}
                </span>
              </div>
              {idx < PHASE_ORDER.length - 1 && (
                <div
                  style={{
                    ...styles.pipelineArrow,
                    backgroundColor: isPast ? "#2d4060" : "#1a2540",
                  }}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* 右侧状态信息 */}
      <div style={styles.rightInfo}>
        {/* 当前任务状态 */}
        <div style={styles.statusChip}>
          <span style={{ ...styles.statusIcon, color: cfg.color }}>
            {cfg.icon}
          </span>
          <span style={{ ...styles.statusLabel, color: cfg.color }}>
            {cfg.label}
          </span>
        </div>

        {/* 统计数字 */}
        <div style={styles.statsRow}>
          <StatItem label="轮次" value={agentState.iteration} />
          <StatItem
            label="反思"
            value={agentState.reflect_count}
            color={agentState.reflect_count > 0 ? "#f97316" : undefined}
          />
          <StatItem
            label="障碍物"
            value={gridState.obstacle_count}
            color={gridState.obstacle_count > 0 ? "#f59e0b" : undefined}
          />
        </div>

        {/* 连接状态 */}
        <div style={styles.connBadge}>
          <div
            style={{
              ...styles.connDot,
              backgroundColor: connected ? "#10b981" : "#ef4444",
              boxShadow: connected
                ? "0 0 6px #10b981"
                : "0 0 6px #ef4444",
            }}
          />
          <span
            style={{
              ...styles.connText,
              color: connected ? "#10b981" : "#ef4444",
            }}
          >
            {connected ? "已连接" : "未连接"}
          </span>
        </div>
      </div>
    </div>
  );
};

const StatItem: React.FC<{
  label: string;
  value: number;
  color?: string;
}> = ({ label, value, color }) => (
  <div style={statStyles.container}>
    <span style={statStyles.label}>{label}</span>
    <span style={{ ...statStyles.value, color: color || "#c8d8f0" }}>
      {value}
    </span>
  </div>
);

// ── 样式 ──────────────────────────────────────────────────────
const styles: Record<string, React.CSSProperties> = {
  container: {
    height: "54px",
    display: "flex",
    alignItems: "center",
    padding: "0 16px",
    backgroundColor: "#060b14",
    borderBottom: "1px solid #1a2540",
    gap: "16px",
  },
  logo: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    flexShrink: 0,
    width: "200px",
  },
  logoIcon: { fontSize: "22px" },
  logoText: {
    display: "flex",
    flexDirection: "column",
    gap: "1px",
  },
  logoName: {
    fontSize: "15px",
    fontWeight: "bold",
    color: "#60a5fa",
    letterSpacing: "1px",
  },
  logoSub: {
    fontSize: "10px",
    color: "#2d4060",
    letterSpacing: "0.5px",
  },
  pipeline: {
    flex: 1,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "0px",
  },
  pipelineItem: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "3px",
  },
  pipelineDot: {
    width: "28px",
    height: "28px",
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    transition: "all 0.3s ease",
  },
  pipelineLabel: {
    fontSize: "9px",
    fontWeight: "500",
    letterSpacing: "0.3px",
    transition: "color 0.3s ease",
  },
  pipelineArrow: {
    width: "24px",
    height: "2px",
    marginBottom: "13px",
    transition: "background 0.3s ease",
  },
  rightInfo: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    flexShrink: 0,
  },
  statusChip: {
    display: "flex",
    alignItems: "center",
    gap: "5px",
    padding: "4px 10px",
    backgroundColor: "#0f1929",
    borderRadius: "20px",
    border: "1px solid #1a2540",
  },
  statusIcon: { fontSize: "12px" },
  statusLabel: {
    fontSize: "12px",
    fontWeight: "bold",
    minWidth: "48px",
    textAlign: "center",
  },
  statsRow: {
    display: "flex",
    gap: "12px",
    padding: "4px 10px",
    backgroundColor: "#0f1929",
    borderRadius: "20px",
    border: "1px solid #1a2540",
  },
  connBadge: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "4px 10px",
    backgroundColor: "#0f1929",
    borderRadius: "20px",
    border: "1px solid #1a2540",
  },
  connDot: {
    width: "8px",
    height: "8px",
    borderRadius: "50%",
    transition: "all 0.3s ease",
  },
  connText: {
    fontSize: "12px",
    fontWeight: "500",
    transition: "color 0.3s ease",
  },
};

const statStyles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "1px",
  },
  label: {
    fontSize: "9px",
    color: "#2d4060",
    letterSpacing: "0.3px",
  },
  value: {
    fontSize: "14px",
    fontWeight: "bold",
    fontFamily: "monospace",
    lineHeight: "1",
  },
};

export default StatusBar;
