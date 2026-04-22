import React, { useState, useRef, useEffect } from "react";
import { useAgentStore } from "../../store/agentStore";
import { ChatMessage } from "../../types";

interface ChatPanelProps {
  onSendMessage: (message: string) => void;
}

const QUICK_COMMANDS = [
  "飞一个边长3米的正方形",
  "向前飞10米",
  "上升5米后向右飞8米",
  "飞一个Z字形路径",
  "上升3米，绕一个圆形",
];

const ChatPanel: React.FC<ChatPanelProps> = ({ onSendMessage }) => {
  const [input, setInput] = useState("");
  const [showQuick, setShowQuick] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const { messages, isRunning, addMessage, clearMessages } = useAgentStore();

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    const msg = input.trim();
    if (!msg || isRunning) return;
    addMessage("user", msg);
    onSendMessage(msg);
    setInput("");
    setShowQuick(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
    if (e.key === "Escape") setShowQuick(false);
  };

  const handleQuick = (cmd: string) => {
    setInput(cmd);
    setShowQuick(false);
  };

  return (
    <div style={styles.container}>
      {/* 标题栏 */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <span style={styles.headerIcon}>💬</span>
          <span style={styles.headerTitle}>任务对话</span>
          {isRunning && <span style={styles.runningBadge}>执行中</span>}
        </div>
        <button style={styles.clearBtn} onClick={clearMessages}>
          清空
        </button>
      </div>

      {/* 消息列表 */}
      <div style={styles.messageList}>
        {messages.length === 0 ? (
          <EmptyState onQuickClick={handleQuick} />
        ) : (
          messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))
        )}
        <div ref={chatEndRef} />
      </div>

      {/* 输入区 */}
      <div style={styles.inputArea}>
        {showQuick && (
          <div style={styles.quickMenu}>
            {QUICK_COMMANDS.map((cmd, i) => (
              <div
                key={i}
                style={styles.quickItem}
                onClick={() => handleQuick(cmd)}
              >
                <span style={styles.quickIcon}>⚡</span>
                <span>{cmd}</span>
              </div>
            ))}
          </div>
        )}

        <div style={styles.inputRow}>
          <button
            style={styles.quickBtn}
            onClick={() => setShowQuick(!showQuick)}
            title="快捷指令"
          >
            ⚡
          </button>
          <textarea
            style={{
              ...styles.input,
              ...(isRunning ? styles.inputDisabled : {}),
            }}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              isRunning ? "Agent 执行中，请稍候..." : "输入飞行指令..."
            }
            disabled={isRunning}
            rows={2}
          />
          <button
            style={{
              ...styles.sendBtn,
              ...(isRunning || !input.trim() ? styles.sendBtnDisabled : {}),
            }}
            onClick={handleSend}
            disabled={isRunning || !input.trim()}
          >
            {isRunning ? "⏳" : "↑"}
          </button>
        </div>
      </div>
    </div>
  );
};

// ── 空状态引导 ────────────────────────────────────────────────
const EmptyState: React.FC<{ onQuickClick: (cmd: string) => void }> = ({
  onQuickClick,
}) => (
  <div style={emptyStyles.container}>
    <div style={emptyStyles.icon}>🚁</div>
    <div style={emptyStyles.title}>无人机智能飞行助手</div>
    <div style={emptyStyles.desc}>
      输入自然语言飞行指令，AI 将自动完成
      <br />
      路径规划、安全验证和代码生成
    </div>
    <div style={emptyStyles.label}>快捷示例：</div>
    <div style={emptyStyles.list}>
      {["飞一个边长3米的正方形", "向前飞10米", "上升5米后向右飞8米"].map(
        (cmd, i) => (
          <div
            key={i}
            style={emptyStyles.item}
            onClick={() => onQuickClick(cmd)}
          >
            {cmd}
          </div>
        )
      )}
    </div>
  </div>
);

// ── 消息气泡 ──────────────────────────────────────────────────
const MessageBubble: React.FC<{ message: ChatMessage }> = ({ message }) => {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  return (
    <div
      style={{
        ...bubbleStyles.wrapper,
        justifyContent: isUser ? "flex-end" : "flex-start",
      }}
    >
      {!isUser && (
        <div style={bubbleStyles.avatar}>
          {isSystem ? "🔧" : "🤖"}
        </div>
      )}
      <div
        style={{
          ...bubbleStyles.bubble,
          backgroundColor: isUser
            ? "#1d4ed8"
            : isSystem
            ? "#1a2535"
            : "#152034",
          borderRadius: isUser
            ? "14px 14px 4px 14px"
            : "14px 14px 14px 4px",
          maxWidth: "82%",
        }}
      >
        {!isUser && (
          <div style={bubbleStyles.role}>
            {isSystem ? "系统" : "🤖 Agent"}
          </div>
        )}
        <div style={bubbleStyles.text}>{message.content}</div>
        <div style={bubbleStyles.time}>
          {new Date(message.timestamp).toLocaleTimeString("zh-CN")}
        </div>
      </div>
      {isUser && <div style={bubbleStyles.avatarUser}>👤</div>}
    </div>
  );
};

// ── 样式 ──────────────────────────────────────────────────────
const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
    backgroundColor: "#0b1220",
    overflow: "hidden",
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "10px 14px",
    backgroundColor: "#080d18",
    borderBottom: "1px solid #1a2540",
    flexShrink: 0,
  },
  headerLeft: {
    display: "flex",
    alignItems: "center",
    gap: "7px",
  },
  headerIcon: { fontSize: "15px" },
  headerTitle: {
    fontSize: "13px",
    fontWeight: "bold",
    color: "#60a5fa",
    letterSpacing: "0.5px",
  },
  runningBadge: {
    fontSize: "10px",
    padding: "2px 7px",
    backgroundColor: "rgba(245,158,11,0.15)",
    color: "#f59e0b",
    borderRadius: "10px",
    border: "1px solid rgba(245,158,11,0.35)",
    animation: "pulse 1.5s infinite",
  },
  clearBtn: {
    padding: "4px 10px",
    background: "none",
    border: "1px solid #1e2a3a",
    borderRadius: "5px",
    color: "#4b5563",
    cursor: "pointer",
    fontSize: "11px",
    transition: "all 0.2s",
  },
  messageList: {
    flex: 1,
    overflowY: "auto",
    padding: "12px 10px",
    display: "flex",
    flexDirection: "column",
    gap: "10px",
    minHeight: 0,
  },
  inputArea: {
    padding: "10px 12px",
    borderTop: "1px solid #1a2540",
    flexShrink: 0,
    position: "relative",
    backgroundColor: "#080d18",
  },
  quickMenu: {
    position: "absolute",
    bottom: "100%",
    left: "12px",
    right: "12px",
    backgroundColor: "#152034",
    border: "1px solid #1e2a3a",
    borderRadius: "10px",
    overflow: "hidden",
    zIndex: 200,
    boxShadow: "0 -6px 24px rgba(0,0,0,0.5)",
    marginBottom: "4px",
  },
  quickItem: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "11px 14px",
    fontSize: "12px",
    color: "#c8d8f0",
    cursor: "pointer",
    borderBottom: "1px solid #1a2540",
    transition: "background 0.15s",
  },
  quickIcon: {
    fontSize: "12px",
    color: "#f59e0b",
  },
  inputRow: {
    display: "flex",
    gap: "8px",
    alignItems: "flex-end",
  },
  quickBtn: {
    width: "36px",
    height: "52px",
    backgroundColor: "#152034",
    border: "1px solid #1e2a3a",
    borderRadius: "10px",
    color: "#f59e0b",
    cursor: "pointer",
    fontSize: "15px",
    flexShrink: 0,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  input: {
    flex: 1,
    backgroundColor: "#152034",
    border: "1px solid #1e2a3a",
    borderRadius: "10px",
    color: "#e0e6f0",
    padding: "10px 12px",
    fontSize: "13px",
    resize: "none",
    outline: "none",
    fontFamily: "inherit",
    lineHeight: "1.5",
    transition: "border-color 0.2s",
  },
  inputDisabled: {
    opacity: 0.45,
    cursor: "not-allowed",
  },
  sendBtn: {
    width: "36px",
    height: "52px",
    backgroundColor: "#1d4ed8",
    border: "none",
    borderRadius: "10px",
    color: "#fff",
    cursor: "pointer",
    fontSize: "18px",
    fontWeight: "bold",
    flexShrink: 0,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    transition: "background 0.2s",
  },
  sendBtnDisabled: {
    backgroundColor: "#1a2540",
    color: "#374151",
    cursor: "not-allowed",
  },
};

const emptyStyles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    padding: "30px 20px",
    gap: "10px",
    flex: 1,
  },
  icon: { fontSize: "42px", marginBottom: "4px" },
  title: {
    fontSize: "14px",
    fontWeight: "bold",
    color: "#60a5fa",
    letterSpacing: "0.5px",
  },
  desc: {
    fontSize: "12px",
    color: "#4b5563",
    textAlign: "center",
    lineHeight: "1.7",
  },
  label: {
    fontSize: "11px",
    color: "#374151",
    marginTop: "6px",
  },
  list: {
    width: "100%",
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  item: {
    padding: "9px 14px",
    backgroundColor: "#152034",
    border: "1px solid #1e2a3a",
    borderRadius: "8px",
    fontSize: "12px",
    color: "#60a5fa",
    cursor: "pointer",
    textAlign: "center",
    transition: "all 0.2s",
  },
};

const bubbleStyles: Record<string, React.CSSProperties> = {
  wrapper: {
    display: "flex",
    alignItems: "flex-end",
    gap: "7px",
  },
  avatar: {
    width: "30px",
    height: "30px",
    borderRadius: "50%",
    backgroundColor: "#1a2535",
    border: "1px solid #1e2a3a",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "14px",
    flexShrink: 0,
  },
  avatarUser: {
    width: "30px",
    height: "30px",
    borderRadius: "50%",
    backgroundColor: "#1d4ed8",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "14px",
    flexShrink: 0,
  },
  bubble: {
    padding: "9px 13px",
  },
  role: {
    fontSize: "10px",
    color: "#60a5fa",
    marginBottom: "4px",
  },
  text: {
    fontSize: "13px",
    lineHeight: "1.55",
    color: "#e0e6f0",
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
  },
  time: {
    fontSize: "10px",
    color: "#374151",
    marginTop: "5px",
    textAlign: "right",
  },
};

export default ChatPanel;
