import React from "react";
import { useWebSocket } from "./hooks/useWebSocket";
import StatusBar from "./components/StatusBar/StatusBar";
import ChatPanel from "./components/ChatPanel/ChatPanel";
import GridViewer from "./components/GridViewer/GridViewer";
import RightPanel from "./components/RightPanel/RightPanel";

const App: React.FC = () => {
  const ws = useWebSocket();

  return (
    <div style={styles.container}>
      {/* 顶部状态栏 */}
      <div style={styles.topBar}>
        <StatusBar />
      </div>

      {/* 主体三栏布局 */}
      <div style={styles.main}>
        {/* 左侧：纯对话框 */}
        <div style={styles.left}>
          <ChatPanel onSendMessage={ws.sendMessage} />
        </div>

        {/* 中间：三维栅格空间 */}
        <div style={styles.center}>
          <GridViewer />
        </div>

        {/* 右侧：认知日志 + 结果 + 工具 */}
        <div style={styles.right}>
          <RightPanel
            onAddObstacles={ws.addObstacles}
            onClearObstacles={ws.clearObstacles}
            onResetPosition={ws.resetPosition}
          />
        </div>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: "100vw",
    height: "100vh",
    display: "flex",
    flexDirection: "column",
    backgroundColor: "#080d18",
    color: "#e0e6f0",
    overflow: "hidden",
  },
  topBar: {
    height: "54px",
    flexShrink: 0,
    borderBottom: "1px solid #1a2540",
  },
  main: {
    flex: 1,
    display: "flex",
    overflow: "hidden",
    minHeight: 0,
  },
  left: {
    width: "320px",
    flexShrink: 0,
    borderRight: "1px solid #1a2540",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
  },
  center: {
    flex: 1,
    overflow: "hidden",
    display: "flex",
    flexDirection: "column",
    minWidth: 0,
    position: "relative",
  },
  right: {
    width: "360px",
    flexShrink: 0,
    borderLeft: "1px solid #1a2540",
    overflow: "hidden",
    display: "flex",
    flexDirection: "column",
  },
};

export default App;
