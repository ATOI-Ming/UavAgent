import React, { useRef, useEffect, useState, useCallback } from "react";
import { useAgentStore } from "../../store/agentStore";

// ── 视图类型 ──────────────────────────────────────────────────
type ViewMode = "iso" | "top" | "side";

const VIEW_LABELS: Record<ViewMode, string> = {
  iso:  "等轴测 3D",
  top:  "俯视图 XY",
  side: "侧视图 XZ",
};

// ── 颜色配置 ──────────────────────────────────────────────────
const COLORS = {
  bg:         "#060b14",
  grid:       "#0f1929",
  gridLine:   "#0d1f35",
  gridAxis:   "#1a3050",
  obstacle:   "#ef4444",
  obstacleBg: "rgba(239,68,68,0.18)",
  path:       "#3b82f6",
  pathGlow:   "rgba(59,130,246,0.4)",
  waypoint:   "#f59e0b",
  drone:      "#10b981",
  droneGlow:  "rgba(16,185,129,0.5)",
  start:      "#22d3ee",
  end:        "#f97316",
  axisX:      "#ef4444",
  axisY:      "#22c55e",
  axisZ:      "#3b82f6",
  text:       "#2d4060",
  textBright: "#4b6080",
};

// ── 等轴测投影工具 ─────────────────────────────────────────────
function isoProject(
  x: number, y: number, z: number,
  cx: number, cy: number,
  scale: number,
  angle: number
): { px: number; py: number } {
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);
  const ix = (x - y) * cos * scale;
  const iy = (x + y) * sin * scale - z * scale * 0.8;
  return { px: cx + ix, py: cy + iy };
}

const GridViewer: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("iso");
  const [canvasSize, setCanvasSize] = useState({ w: 600, h: 480 });

  // 鼠标拖拽旋转（仅等轴测模式）
  const [isoAngle, setIsoAngle] = useState(Math.PI / 6);
  const dragRef = useRef<{ dragging: boolean; lastX: number; angle: number }>({
    dragging: false,
    lastX: 0,
    angle: Math.PI / 6,
  });

  const { gridState, agentState } = useAgentStore();

  // ── 响应容器大小 ────────────────────────────────────────────
  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setCanvasSize({
          w: Math.floor(rect.width),
          h: Math.floor(rect.height),
        });
      }
    };
    updateSize();
    const ro = new ResizeObserver(updateSize);
    if (containerRef.current) ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  // ── 鼠标事件（旋转）────────────────────────────────────────
  const onMouseDown = useCallback((e: React.MouseEvent) => {
    if (viewMode !== "iso") return;
    dragRef.current = {
      dragging: true,
      lastX: e.clientX,
      angle: isoAngle,
    };
  }, [viewMode, isoAngle]);

  const onMouseMove = useCallback((e: React.MouseEvent) => {
    if (!dragRef.current.dragging) return;
    const dx = e.clientX - dragRef.current.lastX;
    const newAngle = dragRef.current.angle + dx * 0.005;
    setIsoAngle(Math.max(0.1, Math.min(Math.PI / 2.2, newAngle)));
  }, []);

  const onMouseUp = useCallback(() => {
    dragRef.current.dragging = false;
  }, []);

  // ── 主绘制函数 ─────────────────────────────────────────────
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const W = canvasSize.w;
    const H = canvasSize.h;
    canvas.width = W;
    canvas.height = H;

    const GX = gridState.size[0];
    const GY = gridState.size[1];
    const GZ = gridState.size[2];

    ctx.fillStyle = COLORS.bg;
    ctx.fillRect(0, 0, W, H);

    if (viewMode === "iso") {
      drawIso(ctx, W, H, GX, GY, GZ, gridState, agentState, isoAngle);
    } else if (viewMode === "top") {
      drawTopView(ctx, W, H, GX, GY, gridState, agentState);
    } else {
      drawSideView(ctx, W, H, GX, GZ, gridState, agentState);
    }

  }, [canvasSize, viewMode, gridState, agentState, isoAngle]);

  return (
    <div style={styles.container}>
      {/* 工具栏 */}
      <div style={styles.toolbar}>
        <div style={styles.toolbarLeft}>
          <span style={styles.viewTitle}>🗺 三维栅格空间</span>
          {viewMode === "iso" && (
            <span style={styles.dragHint}>拖拽旋转视角</span>
          )}
        </div>

        {/* 视图切换 */}
        <div style={styles.viewBtns}>
          {(["iso", "top", "side"] as ViewMode[]).map((v) => (
            <button
              key={v}
              style={{
                ...styles.viewBtn,
                ...(viewMode === v ? styles.viewBtnActive : {}),
              }}
              onClick={() => setViewMode(v)}
            >
              {VIEW_LABELS[v]}
            </button>
          ))}
        </div>

        {/* 图例 */}
        <div style={styles.legend}>
          {LEGEND_ITEMS.map((item) => (
            <div key={item.label} style={styles.legendItem}>
              <div
                style={{
                  ...styles.legendDot,
                  backgroundColor: item.color,
                  boxShadow: item.glow ? `0 0 4px ${item.color}` : "none",
                }}
              />
              <span style={styles.legendLabel}>{item.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Canvas */}
      <div
        ref={containerRef}
        style={{
          ...styles.canvasWrapper,
          cursor: viewMode === "iso" ? "grab" : "default",
        }}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
      >
        <canvas
          ref={canvasRef}
          style={styles.canvas}
        />
      </div>

      {/* 底部信息栏 */}
      <div style={styles.infoBar}>
        <InfoBadge
          label="当前位置"
          value={`[${gridState.current_position.join(", ")}]`}
          color="#10b981"
        />
        <InfoBadge
          label="障碍物"
          value={`${gridState.obstacle_count} 个`}
          color={gridState.obstacle_count > 0 ? "#f59e0b" : "#4b6080"}
        />
        <InfoBadge
          label="航点"
          value={`${agentState.last_waypoints?.length || 0} 个`}
          color="#f59e0b"
        />
        <InfoBadge
          label="路径点"
          value={`${agentState.last_path?.length || 0} 个`}
          color="#3b82f6"
        />
        <InfoBadge
          label="空间大小"
          value={`${gridState.size.join(" × ")}`}
          color="#4b6080"
        />
      </div>
    </div>
  );
};

// ══════════════════════════════════════════════════════════════
// 等轴测 3D 绘制
// ══════════════════════════════════════════════════════════════
function drawIso(
  ctx: CanvasRenderingContext2D,
  W: number, H: number,
  GX: number, GY: number, GZ: number,
  gridState: any, agentState: any,
  angle: number
) {
  const scale = Math.min(W, H) / (GX + GY) * 0.48;
  const cx = W / 2;
  const cy = H * 0.58;

  const proj = (x: number, y: number, z: number) =>
    isoProject(x, y, z, cx, cy, scale, angle);

  // ── 绘制底面栅格 ────────────────────────────────────────────
  const STEP = 10;

  for (let x = 0; x <= GX; x += STEP) {
    const p0 = proj(x, 0, 0);
    const p1 = proj(x, GY, 0);
    ctx.beginPath();
    ctx.moveTo(p0.px, p0.py);
    ctx.lineTo(p1.px, p1.py);
    ctx.strokeStyle = x === 0 || x === GX
      ? COLORS.gridAxis
      : COLORS.gridLine;
    ctx.lineWidth = x === 0 || x === GX ? 1.2 : 0.5;
    ctx.stroke();
  }
  for (let y = 0; y <= GY; y += STEP) {
    const p0 = proj(0, y, 0);
    const p1 = proj(GX, y, 0);
    ctx.beginPath();
    ctx.moveTo(p0.px, p0.py);
    ctx.lineTo(p1.px, p1.py);
    ctx.strokeStyle = y === 0 || y === GY
      ? COLORS.gridAxis
      : COLORS.gridLine;
    ctx.lineWidth = y === 0 || y === GY ? 1.2 : 0.5;
    ctx.stroke();
  }

  // ── 侧面边框（高度方向）──────────────────────────────────────
  {
    const p0 = proj(0, 0, 0);
    const p1 = proj(0, 0, GZ);
    ctx.beginPath();
    ctx.moveTo(p0.px, p0.py);
    ctx.lineTo(p1.px, p1.py);
    ctx.strokeStyle = COLORS.axisZ;
    ctx.lineWidth = 1.0;
    ctx.stroke();
  }

  // ── 坐标轴标签 ────────────────────────────────────────────────
  const drawAxisLabel = (text: string, p: {px:number;py:number}, color: string) => {
    ctx.fillStyle = color;
    ctx.font = "bold 11px monospace";
    ctx.textAlign = "center";
    ctx.fillText(text, p.px, p.py);
  };
  drawAxisLabel("X", proj(GX + 5, 0, 0), COLORS.axisX);
  drawAxisLabel("Y", proj(0, GY + 5, 0), COLORS.axisY);
  drawAxisLabel("Z", proj(0, 0, GZ + 2), COLORS.axisZ);

  // ── 刻度标注（每20格）────────────────────────────────────────
  ctx.fillStyle = COLORS.text;
  ctx.font = "9px monospace";
  ctx.textAlign = "center";
  [0, 20, 40, 60, 80, 100].forEach((v) => {
    if (v <= GX) {
      const p = proj(v, 0, 0);
      ctx.fillText(String(v), p.px, p.py + 10);
    }
  });
  [0, 20, 40, 60, 80, 100].forEach((v) => {
    if (v <= GY) {
      const p = proj(0, v, 0);
      ctx.fillText(String(v), p.px - 14, p.py + 4);
    }
  });

  // ── 障碍物（等轴测方块）──────────────────────────────────────
  const obstacles = gridState.obstacles || [];
  for (const obs of obstacles) {
    drawIsoBox(ctx, obs[0], obs[1], obs[2], 1, 1, 1, proj, COLORS.obstacle, 0.75);
  }

  // ── 飞行路径 ─────────────────────────────────────────────────
  const path = agentState.last_path || [];
  if (path.length > 1) {
    // 发光效果
    ctx.beginPath();
    const p0 = proj(path[0][0], path[0][1], path[0][2]);
    ctx.moveTo(p0.px, p0.py);
    for (let i = 1; i < path.length; i++) {
      const p = proj(path[i][0], path[i][1], path[i][2]);
      ctx.lineTo(p.px, p.py);
    }
    ctx.strokeStyle = COLORS.pathGlow;
    ctx.lineWidth = 5;
    ctx.lineJoin = "round";
    ctx.stroke();

    // 实线
    ctx.beginPath();
    ctx.moveTo(p0.px, p0.py);
    for (let i = 1; i < path.length; i++) {
      const p = proj(path[i][0], path[i][1], path[i][2]);
      ctx.lineTo(p.px, p.py);
    }
    ctx.strokeStyle = COLORS.path;
    ctx.lineWidth = 2;
    ctx.stroke();

    // 起点
    const ps = proj(path[0][0], path[0][1], path[0][2]);
    drawGlowCircle(ctx, ps.px, ps.py, 5, COLORS.start);

    // 终点
    const pe = proj(path[path.length-1][0], path[path.length-1][1], path[path.length-1][2]);
    drawGlowCircle(ctx, pe.px, pe.py, 5, COLORS.end);
  }

  // ── 航点 ─────────────────────────────────────────────────────
  const waypoints = agentState.last_waypoints || [];
  for (const wp of waypoints) {
    const p = proj(wp[0], wp[1], wp[2]);
    drawGlowCircle(ctx, p.px, p.py, 4, COLORS.waypoint);
  }

  // ── 无人机 ───────────────────────────────────────────────────
  const pos = gridState.current_position;
  const dp = proj(pos[0], pos[1], pos[2]);

  // 悬停线（从地面到当前位置）
  if (pos[2] > 0) {
    const ground = proj(pos[0], pos[1], 0);
    ctx.beginPath();
    ctx.setLineDash([3, 3]);
    ctx.moveTo(ground.px, ground.py);
    ctx.lineTo(dp.px, dp.py);
    ctx.strokeStyle = "rgba(16,185,129,0.3)";
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.setLineDash([]);
  }

  // 无人机图标（发光圆）
  drawGlowCircle(ctx, dp.px, dp.py, 9, COLORS.drone);
  ctx.fillStyle = "#fff";
  ctx.font = "14px sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("🚁", dp.px, dp.py);
  ctx.textBaseline = "alphabetic";

  // 位置标注
  ctx.fillStyle = COLORS.drone;
  ctx.font = "10px monospace";
  ctx.textAlign = "center";
  ctx.fillText(
    `(${pos[0]},${pos[1]},${pos[2]})`,
    dp.px, dp.py - 16
  );
}

// ── 等轴测方块绘制 ──────────────────────────────────────────
function drawIsoBox(
  ctx: CanvasRenderingContext2D,
  x: number, y: number, z: number,
  w: number, d: number, h: number,
  proj: (x:number,y:number,z:number)=>{px:number;py:number},
  color: string,
  alpha: number
) {
  const p = [
    proj(x,   y,   z),
    proj(x+w, y,   z),
    proj(x+w, y+d, z),
    proj(x,   y+d, z),
    proj(x,   y,   z+h),
    proj(x+w, y,   z+h),
    proj(x+w, y+d, z+h),
    proj(x,   y+d, z+h),
  ];

  ctx.globalAlpha = alpha;

  // 顶面
  ctx.beginPath();
  ctx.moveTo(p[4].px, p[4].py);
  ctx.lineTo(p[5].px, p[5].py);
  ctx.lineTo(p[6].px, p[6].py);
  ctx.lineTo(p[7].px, p[7].py);
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.fill();
  ctx.strokeStyle = "rgba(255,255,255,0.15)";
  ctx.lineWidth = 0.5;
  ctx.stroke();

  // 左侧面
  ctx.beginPath();
  ctx.moveTo(p[0].px, p[0].py);
  ctx.lineTo(p[4].px, p[4].py);
  ctx.lineTo(p[7].px, p[7].py);
  ctx.lineTo(p[3].px, p[3].py);
  ctx.closePath();
  ctx.fillStyle = shadeColor(color, -30);
  ctx.fill();
  ctx.strokeStyle = "rgba(255,255,255,0.1)";
  ctx.lineWidth = 0.5;
  ctx.stroke();

  // 右侧面
  ctx.beginPath();
  ctx.moveTo(p[1].px, p[1].py);
  ctx.lineTo(p[5].px, p[5].py);
  ctx.lineTo(p[6].px, p[6].py);
  ctx.lineTo(p[2].px, p[2].py);
  ctx.closePath();
  ctx.fillStyle = shadeColor(color, -50);
  ctx.fill();
  ctx.strokeStyle = "rgba(255,255,255,0.08)";
  ctx.lineWidth = 0.5;
  ctx.stroke();

  ctx.globalAlpha = 1;
}

// ══════════════════════════════════════════════════════════════
// 俯视图 XY
// ══════════════════════════════════════════════════════════════
function drawTopView(
  ctx: CanvasRenderingContext2D,
  W: number, H: number,
  GX: number, GY: number,
  gridState: any, agentState: any
) {
  const PAD = 45;
  const cellW = (W - PAD * 2) / GX;
  const cellH = (H - PAD * 2) / GY;

  // 背景格子填充
  for (let x = 0; x < GX; x += 2) {
    for (let y = 0; y < GY; y += 2) {
      if ((x + y) % 4 === 0) {
        ctx.fillStyle = "rgba(15,25,45,0.6)";
        ctx.fillRect(PAD + x * cellW, PAD + y * cellH, cellW * 2, cellH * 2);
      }
    }
  }

  // 栅格线
  for (let x = 0; x <= GX; x++) {
    const isMajor = x % 10 === 0;
    ctx.beginPath();
    ctx.moveTo(PAD + x * cellW, PAD);
    ctx.lineTo(PAD + x * cellW, H - PAD);
    ctx.strokeStyle = isMajor ? COLORS.gridAxis : COLORS.gridLine;
    ctx.lineWidth = isMajor ? 0.8 : 0.3;
    ctx.stroke();

    if (isMajor && x < GX) {
      ctx.fillStyle = COLORS.text;
      ctx.font = "9px monospace";
      ctx.textAlign = "center";
      ctx.fillText(String(x), PAD + x * cellW + cellW * 5, H - PAD + 12);
    }
  }
  for (let y = 0; y <= GY; y++) {
    const isMajor = y % 10 === 0;
    ctx.beginPath();
    ctx.moveTo(PAD, PAD + y * cellH);
    ctx.lineTo(W - PAD, PAD + y * cellH);
    ctx.strokeStyle = isMajor ? COLORS.gridAxis : COLORS.gridLine;
    ctx.lineWidth = isMajor ? 0.8 : 0.3;
    ctx.stroke();

    if (isMajor && y < GY) {
      ctx.fillStyle = COLORS.text;
      ctx.font = "9px monospace";
      ctx.textAlign = "right";
      ctx.fillText(String(y), PAD - 4, PAD + y * cellH + cellH * 5 + 3);
    }
  }

  // 坐标轴标签
  ctx.fillStyle = COLORS.axisX;
  ctx.font = "bold 11px monospace";
  ctx.textAlign = "center";
  ctx.fillText("X →", W - PAD + 18, H - PAD + 2);
  ctx.fillStyle = COLORS.axisY;
  ctx.save();
  ctx.translate(PAD - 28, PAD + 20);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText("Y →", 0, 0);
  ctx.restore();

  // 障碍物
  for (const obs of (gridState.obstacles || [])) {
    const px = PAD + obs[0] * cellW;
    const py = PAD + obs[1] * cellH;
    ctx.fillStyle = COLORS.obstacleBg;
    ctx.fillRect(px - 1, py - 1, cellW + 2, cellH + 2);
    ctx.fillStyle = COLORS.obstacle;
    ctx.fillRect(px, py, Math.max(cellW, 1.5), Math.max(cellH, 1.5));
  }

  // 飞行路径
  const path = agentState.last_path || [];
  if (path.length > 1) {
    ctx.beginPath();
    ctx.moveTo(
      PAD + path[0][0] * cellW + cellW / 2,
      PAD + path[0][1] * cellH + cellH / 2
    );
    for (let i = 1; i < path.length; i++) {
      ctx.lineTo(
        PAD + path[i][0] * cellW + cellW / 2,
        PAD + path[i][1] * cellH + cellH / 2
      );
    }
    ctx.strokeStyle = COLORS.pathGlow;
    ctx.lineWidth = 4;
    ctx.lineJoin = "round";
    ctx.stroke();
    ctx.strokeStyle = COLORS.path;
    ctx.lineWidth = 2;
    ctx.stroke();

    const ps = path[0];
    const pe = path[path.length - 1];
    drawGlowCircle(ctx, PAD + ps[0] * cellW + cellW / 2, PAD + ps[1] * cellH + cellH / 2, 5, COLORS.start);
    drawGlowCircle(ctx, PAD + pe[0] * cellW + cellW / 2, PAD + pe[1] * cellH + cellH / 2, 5, COLORS.end);
  }

  // 航点
  for (const wp of (agentState.last_waypoints || [])) {
    drawGlowCircle(ctx, PAD + wp[0] * cellW + cellW / 2, PAD + wp[1] * cellH + cellH / 2, 4, COLORS.waypoint);
  }

  // 无人机
  const pos = gridState.current_position;
  const dpx = PAD + pos[0] * cellW + cellW / 2;
  const dpy = PAD + pos[1] * cellH + cellH / 2;
  drawGlowCircle(ctx, dpx, dpy, 9, COLORS.drone);
  ctx.font = "13px sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("🚁", dpx, dpy);
  ctx.textBaseline = "alphabetic";

  ctx.fillStyle = COLORS.textBright;
  ctx.font = "11px monospace";
  ctx.textAlign = "left";
  ctx.fillText("俯视图 (XY平面)", PAD, PAD - 10);
}

// ══════════════════════════════════════════════════════════════
// 侧视图 XZ
// ══════════════════════════════════════════════════════════════
function drawSideView(
  ctx: CanvasRenderingContext2D,
  W: number, H: number,
  GX: number, GZ: number,
  gridState: any, agentState: any
) {
  const PAD = 45;
  const cellW = (W - PAD * 2) / GX;
  const cellH = (H - PAD * 2) / GZ;

  // 地面填充
  ctx.fillStyle = "rgba(10,20,35,0.8)";
  ctx.fillRect(PAD, H - PAD - cellH, W - PAD * 2, cellH);

  // 棋盘格背景
  for (let x = 0; x < GX; x += 2) {
    for (let z = 0; z < GZ; z += 2) {
      if ((x + z) % 4 === 0) {
        ctx.fillStyle = "rgba(15,25,45,0.5)";
        ctx.fillRect(PAD + x * cellW, PAD + (GZ - z - 2) * cellH, cellW * 2, cellH * 2);
      }
    }
  }

  // 栅格线
  for (let x = 0; x <= GX; x++) {
    const isMajor = x % 10 === 0;
    ctx.beginPath();
    ctx.moveTo(PAD + x * cellW, PAD);
    ctx.lineTo(PAD + x * cellW, H - PAD);
    ctx.strokeStyle = isMajor ? COLORS.gridAxis : COLORS.gridLine;
    ctx.lineWidth = isMajor ? 0.8 : 0.3;
    ctx.stroke();
    if (isMajor && x < GX) {
      ctx.fillStyle = COLORS.text;
      ctx.font = "9px monospace";
      ctx.textAlign = "center";
      ctx.fillText(String(x), PAD + x * cellW + cellW * 5, H - PAD + 12);
    }
  }
  for (let z = 0; z <= GZ; z++) {
    const isMajor = z % 5 === 0;
    ctx.beginPath();
    ctx.moveTo(PAD, PAD + (GZ - z) * cellH);
    ctx.lineTo(W - PAD, PAD + (GZ - z) * cellH);
    ctx.strokeStyle = isMajor ? COLORS.gridAxis : COLORS.gridLine;
    ctx.lineWidth = isMajor ? 0.8 : 0.3;
    ctx.stroke();
    if (isMajor) {
      ctx.fillStyle = COLORS.text;
      ctx.font = "9px monospace";
      ctx.textAlign = "right";
      ctx.fillText(String(z), PAD - 4, PAD + (GZ - z) * cellH + 3);
    }
  }

  // 坐标轴标签
  ctx.fillStyle = COLORS.axisX;
  ctx.font = "bold 11px monospace";
  ctx.textAlign = "center";
  ctx.fillText("X →", W - PAD + 18, H - PAD + 2);
  ctx.fillStyle = COLORS.axisZ;
  ctx.save();
  ctx.translate(PAD - 28, PAD + 20);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText("Z (高度) →", 0, 0);
  ctx.restore();

  // 障碍物（XZ截面）
  const obsXZ = new Set<string>();
  for (const obs of (gridState.obstacles || [])) {
    const key = `${obs[0]},${obs[2]}`;
    if (!obsXZ.has(key)) {
      obsXZ.add(key);
      const px = PAD + obs[0] * cellW;
      const py = PAD + (GZ - obs[2] - 1) * cellH;
      ctx.fillStyle = COLORS.obstacleBg;
      ctx.fillRect(px - 1, py - 1, cellW + 2, cellH + 2);
      ctx.fillStyle = COLORS.obstacle;
      ctx.fillRect(px, py, Math.max(cellW, 1.5), Math.max(cellH, 1.5));
    }
  }

  // 路径
  const path = agentState.last_path || [];
  if (path.length > 1) {
    ctx.beginPath();
    ctx.moveTo(PAD + path[0][0] * cellW + cellW / 2, PAD + (GZ - path[0][2]) * cellH);
    for (let i = 1; i < path.length; i++) {
      ctx.lineTo(PAD + path[i][0] * cellW + cellW / 2, PAD + (GZ - path[i][2]) * cellH);
    }
    ctx.strokeStyle = COLORS.pathGlow;
    ctx.lineWidth = 4;
    ctx.stroke();
    ctx.strokeStyle = COLORS.path;
    ctx.lineWidth = 2;
    ctx.stroke();
  }

  // 无人机
  const pos = gridState.current_position;
  const dpx = PAD + pos[0] * cellW + cellW / 2;
  const dpy = PAD + (GZ - pos[2]) * cellH;
  drawGlowCircle(ctx, dpx, dpy, 9, COLORS.drone);
  ctx.font = "13px sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("🚁", dpx, dpy);
  ctx.textBaseline = "alphabetic";

  ctx.fillStyle = COLORS.textBright;
  ctx.font = "11px monospace";
  ctx.textAlign = "left";
  ctx.fillText("侧视图 (XZ平面)", PAD, PAD - 10);
}

// ── 工具函数 ──────────────────────────────────────────────────
function drawGlowCircle(
  ctx: CanvasRenderingContext2D,
  x: number, y: number,
  r: number, color: string
) {
  const grad = ctx.createRadialGradient(x, y, 0, x, y, r * 3);
  grad.addColorStop(0, color + "80");
  grad.addColorStop(1, color + "00");
  ctx.beginPath();
  ctx.arc(x, y, r * 3, 0, Math.PI * 2);
  ctx.fillStyle = grad;
  ctx.fill();

  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.fillStyle = color;
  ctx.fill();
}

function shadeColor(hex: string, amount: number): string {
  const num = parseInt(hex.slice(1), 16);
  const r = Math.max(0, Math.min(255, (num >> 16) + amount));
  const g = Math.max(0, Math.min(255, ((num >> 8) & 0xff) + amount));
  const b = Math.max(0, Math.min(255, (num & 0xff) + amount));
  return `rgb(${r},${g},${b})`;
}

// ── 图例配置 ──────────────────────────────────────────────────
const LEGEND_ITEMS = [
  { label: "无人机", color: COLORS.drone,    glow: true },
  { label: "障碍物", color: COLORS.obstacle, glow: false },
  { label: "飞行路径", color: COLORS.path,   glow: true },
  { label: "航点",   color: COLORS.waypoint, glow: true },
  { label: "起点",   color: COLORS.start,    glow: true },
  { label: "终点",   color: COLORS.end,      glow: true },
];

// ── 子组件 ────────────────────────────────────────────────────
const InfoBadge: React.FC<{
  label: string;
  value: string;
  color: string;
}> = ({ label, value, color }) => (
  <div style={infoBadgeStyles.container}>
    <span style={infoBadgeStyles.label}>{label}</span>
    <span style={{ ...infoBadgeStyles.value, color }}>{value}</span>
  </div>
);

// ── 样式 ──────────────────────────────────────────────────────
const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
    backgroundColor: COLORS.bg,
    overflow: "hidden",
  },
  toolbar: {
    display: "flex",
    alignItems: "center",
    padding: "8px 14px",
    borderBottom: "1px solid #1a2540",
    flexShrink: 0,
    gap: "12px",
    backgroundColor: "#080d18",
    flexWrap: "wrap",
  },
  toolbarLeft: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    flexShrink: 0,
  },
  viewTitle: {
    fontSize: "13px",
    fontWeight: "bold",
    color: "#60a5fa",
    letterSpacing: "0.5px",
  },
  dragHint: {
    fontSize: "10px",
    color: "#2d4060",
    padding: "2px 7px",
    backgroundColor: "#0f1929",
    borderRadius: "8px",
    border: "1px solid #1a2540",
  },
  viewBtns: {
    display: "flex",
    gap: "4px",
    flexShrink: 0,
  },
  viewBtn: {
    padding: "4px 12px",
    backgroundColor: "#0f1929",
    border: "1px solid #1a2540",
    borderRadius: "6px",
    color: "#4b6080",
    cursor: "pointer",
    fontSize: "11px",
    transition: "all 0.2s",
  },
  viewBtnActive: {
    backgroundColor: "rgba(59,130,246,0.15)",
    borderColor: "#3b82f6",
    color: "#60a5fa",
  },
  legend: {
    display: "flex",
    gap: "10px",
    flexWrap: "wrap",
    flex: 1,
    justifyContent: "flex-end",
  },
  legendItem: {
    display: "flex",
    alignItems: "center",
    gap: "4px",
  },
  legendDot: {
    width: "8px",
    height: "8px",
    borderRadius: "50%",
    flexShrink: 0,
  },
  legendLabel: {
    fontSize: "10px",
    color: "#4b6080",
  },
  canvasWrapper: {
    flex: 1,
    overflow: "hidden",
    display: "flex",
    alignItems: "stretch",
    justifyContent: "stretch",
    minHeight: 0,
    userSelect: "none" as const,
  },
  canvas: {
    width: "100%",
    height: "100%",
    display: "block",
  },
  infoBar: {
    display: "flex",
    gap: "8px",
    padding: "8px 14px",
    borderTop: "1px solid #1a2540",
    flexShrink: 0,
    flexWrap: "wrap",
    backgroundColor: "#080d18",
  },
};

const infoBadgeStyles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    alignItems: "center",
    gap: "5px",
    padding: "3px 9px",
    backgroundColor: "#0f1929",
    borderRadius: "12px",
    border: "1px solid #1a2540",
  },
  label: {
    fontSize: "10px",
    color: "#2d4060",
  },
  value: {
    fontSize: "11px",
    fontFamily: "monospace",
    fontWeight: "bold",
  },
};

export default GridViewer;
