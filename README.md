# UavAgent — 无人机智能飞行认知代理系统

## 项目简介

**UavAgent** 是一个基于认知代理架构（Cognitive Agent）的无人机智能飞行系统。系统采用类似自动驾驶的 **感知-思考-行动-安全检查-反思** 五阶段认知循环，通过大语言模型（LLM）理解自然语言飞行指令，自动完成指令翻译、路径规划、碰撞检测、避障重规划和飞行代码生成。

用户只需输入自然语言指令（如"飞一个边长3米的正方形"），系统即可自动完成从理解到执行的完整流程，并通过 Web 界面实时展示认知循环的全过程。

## 核心架构

```
用户输入自然语言指令
        │
        ▼
┌──────────────────────────────────────────────────┐
│              Orchestrator 编排器                   │
│                                                    │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐      │
│   │ OBSERVE  │───▶│  THINK  │───▶│   ACT   │      │
│   │  感知    │    │  思考    │    │  行动   │      │
│   └─────────┘    └─────────┘    └────┬────┘      │
│                                       │            │
│                                       ▼            │
│                               ┌──────────────┐    │
│                               │ SAFETY_CHECK  │    │
│                               │  安全检查     │    │
│                               └──────┬───────┘    │
│                                      │             │
│                          ┌──安全──────┤──危险──┐   │
│                          ▼                     ▼   │
│                      下一轮循环           ┌────────┐ │
│                                           │ REFLECT│ │
│                                           │  反思   │ │
│                                           └───┬────┘ │
│                                               │      │
│                                               ▼      │
│                                          避障重规划  │
└──────────────────────────────────────────────────┘
        │
        ▼
   任务完成 / 飞行代码输出
```

### 五阶段认知循环

| 阶段 | 职责 | 说明 |
|------|------|------|
| **OBSERVE** (感知) | 收集环境信息 | 获取当前无人机位置、障碍物分布、栅格空间状态、历史循环记录 |
| **THINK** (思考) | LLM 决策 | 调用 LLM 分析用户意图，通过 Function Calling 选择下一个要执行的工具 |
| **ACT** (行动) | 执行工具 | 执行 LLM 选中的飞行工具（翻译、解析、规划、可视化等） |
| **SAFETY_CHECK** (安全检查) | 碰撞检测 | 对规划路径进行碰撞检测，判断是否安全 |
| **REFLECT** (反思) | 避障策略 | 安全检查失败时，分析障碍物密度，推荐避障重规划策略 |

### 标准工作流

对于飞行任务，Agent 会按以下顺序自动执行工具：

```
ai_translate_flight → parse_command → plan_flight → visualize_flight → generate_uav_code → task_complete
```

如果路径规划遇到障碍物碰撞，会自动触发：

```
ai_replan_with_obstacles (使用推荐策略) → 重新进行安全检查
```

## 项目结构

```
UavAgent/
├── main.py                  # 主入口，6步初始化流程
├── requirements.txt         # Python 依赖
├── .env                     # 环境变量配置（LLM API Key 等）
│
├── config/
│   └── settings.py          # 全局配置：栅格空间、动作定义、LLM、Agent、安全、Web
│
├── core/                    # 核心功能模块
│   ├── grid_space.py        # 三维栅格空间 (100x100x20)，位置管理、障碍物管理
│   ├── command_parser.py    # 动作序列解析器，将文本解析为三维航点
│   ├── flight_planner.py    # 路径规划器，支持 A*/BFS/直线算法
│   ├── visualizer.py        # 3D可视化 + 2D分层切片图生成
│   └── code_generator.py    # 飞行代码生成器，输出 DroneKit/仿真版本
│
├── agent/                   # 认知代理模块
│   ├── orchestrator.py      # 认知循环编排器，驱动 OBSERVE→THINK→ACT→SAFETY→REFLECT
│   ├── llm_client.py        # LLM 客户端，封装 OpenAI 兼容 API + Function Calling
│   ├── safety_guard.py      # 安全守卫，路径碰撞检测
│   └── reflector.py         # 反思器，碰撞后推荐避障策略
│
├── tools/                   # 工具系统
│   ├── registry.py          # 工具注册中心，管理飞行工具和认知工具
│   ├── flight_tools.py      # 13个飞行工具（LLM 通过 Function Calling 选择调用）
│   └── cognitive_tools.py   # 4个认知工具（编排器在各阶段自动调用）
│
├── memory/
│   └── memory.py            # 记忆系统，跨任务持久化经验
│
├── server/                  # Web 服务
│   ├── app.py               # Flask + SocketIO 应用创建与启动
│   ├── api.py               # REST API 路由（状态查询、障碍物管理、文件资源）
│   └── events.py            # WebSocket 事件处理（实时双向通信）
│
├── frontend/web/            # React 前端
│   ├── package.json
│   └── src/
│       ├── App.tsx           # 三栏布局：聊天面板 | 栅格视图 | 右侧面板
│       ├── types.ts          # TypeScript 类型定义
│       ├── index.tsx         # 入口
│       ├── store/
│       │   └── agentStore.ts # Zustand 全局状态管理
│       ├── hooks/
│       │   └── useWebSocket.ts # WebSocket 实时通信 Hook
│       └── components/
│           ├── ChatPanel/    # 聊天面板：消息气泡、快捷指令菜单
│           ├── GridViewer/   # Canvas 2D 栅格可视化：等轴测3D/俯视XY/侧视XZ
│           ├── StatusBar/    # 认知阶段管线：5节点流水线 + 统计信息
│           └── RightPanel/   # 右侧面板：认知日志/工具调用/任务结果/环境控制
│
└── data/                    # 数据输出目录
    └── output/
        ├── visualizations/   # 3D可视化图片
        ├── layer_maps/       # 2D分层切片图
        └── missions/         # 生成的飞行代码
```

## 工具系统

系统包含 **13 个飞行工具** + **4 个认知工具**，通过 `ToolRegistry` 统一管理。

### 飞行工具（LLM 通过 Function Calling 选择）

| 工具名称 | 分类 | 说明 |
|----------|------|------|
| `ai_translate_flight` | 输入 | 将自然语言飞行指令翻译为标准动作序列（如"飞一个边长3米的正方形" → "上升3米,右移3米,前进3米,..."） |
| `parse_command` | 解析 | 将动作序列字符串解析为三维坐标航点列表 |
| `plan_flight` | 规划 | 对航点列表进行路径规划，支持 A*/BFS/直线三种算法 |
| `ai_replan_with_obstacles` | 重规划 | 碰撞后使用5种避障策略（上升绕过/下降绕过/水平绕行/AI智能规划/组合策略）重新规划路径 |
| `add_obstacles` | 空间 | 添加障碍物到栅格空间 |
| `clear_obstacles` | 空间 | 清除所有障碍物 |
| `get_obstacles` | 空间 | 获取当前所有障碍物坐标 |
| `visualize_flight` | 可视化 | 生成3D飞行路径可视化图片（PNG） |
| `generate_layer_maps` | 可视化 | 生成栅格空间的2D分层俯视切片图 |
| `get_flight_info` | 状态 | 获取当前无人机飞行状态和环境信息 |
| `reset_position` | 状态 | 重置无人机位置 |
| `generate_uav_code` | 输出 | 生成 DroneKit 和仿真版本的可执行飞行代码（Python） |
| `task_complete` | 控制 | 标记任务完成（虚拟工具） |

### 认知工具（编排器自动调用）

| 工具名称 | 阶段 | 说明 |
|----------|------|------|
| `agent_observe` | OBSERVE | 收集环境观察信息，生成观察指南 |
| `agent_think` | THINK | 分析用户意图，推荐下一步工具，生成决策指南 |
| `agent_safety_check` | SAFETY_CHECK | 生成安全检查指南，记录碰撞检测信息 |
| `agent_reflect` | REFLECT | 生成反思指南，根据障碍物密度和重试次数推荐避障策略 |

## 栅格空间

系统使用三维离散化栅格空间模拟飞行环境：

- **空间大小**: 100 x 100 x 20（X x Y x Z），每格 1 米
- **初始位置**: (50, 50, 0)
- **支持动作**: 前进、后退、左移、右移、上升、下降、悬停、以及对角线方向（共 11 个方向）
- **中文别名**: 每个动作支持多种中文说法（如"前进"/"向前" = forward）

## 前端界面

前端基于 React + TypeScript 构建，采用三栏布局：

```
┌──────────┬──────────────────────┬──────────┐
│          │                      │          │
│  聊天面板  │     栅格可视化视图     │  右侧面板  │
│  320px   │      (自适应)         │  360px   │
│          │                      │          │
│ 消息气泡  │  ┌────────────────┐  │ 4个Tab:  │
│ 快捷指令  │  │  等轴测3D/俯视  │  │ 认知日志  │
│          │  │  XY/侧视XZ     │  │ 工具调用  │
│          │  └────────────────┘  │ 任务结果  │
│          │                      │ 环境控制  │
│          │  ┌────────────────┐  │          │
│          │  │ 认知阶段管线    │  │          │
│          │  └────────────────┘  │          │
└──────────┴──────────────────────┴──────────┘
```

### 主要组件

- **ChatPanel**: 消息气泡（用户/Agent/系统）、快捷指令菜单（+）、空状态引导、自动滚动
- **GridViewer**: Canvas 2D 渲染，支持等轴测3D（鼠标拖拽旋转）、俯视XY、侧视XZ三种视角；渲染网格线、障碍物（3D方块）、飞行路径（发光效果）、航点、无人机图标
- **StatusBar**: 认知阶段5节点流水线（发光效果）、迭代次数/反思次数/障碍物数统计、连接状态
- **RightPanel**: 4个标签页
  - 认知日志：按级别过滤、自动滚动、可展开数据详情
  - 工具调用：按时间倒序、可展开参数和结果
  - 任务结果：状态卡片、安全检查结果、可视化图片、分层地图、代码文件
  - 环境控制：环境信息、位置重置、预设障碍物、自定义障碍物、快捷飞行指令

## 环境要求

- **Python**: 3.9+
- **Node.js**: 18+（推荐 20+）
- **LLM API**: 需要兼容 OpenAI API 格式的大语言模型服务

## 安装与配置

### 1. 克隆项目

```bash
git clone <repository-url>
cd UavAgent
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

依赖包括：
- `flask` + `flask-socketio` + `flask-cors` — Web 服务
- `openai` — LLM 调用（兼容 OpenAI API 格式）
- `python-dotenv` — 环境变量加载
- `numpy` — 数值计算
- `matplotlib` + `Pillow` — 可视化
- `eventlet` — WebSocket 异步支持

### 3. 配置环境变量

编辑项目根目录下的 `.env` 文件：

```env
# LLM 提供商（默认使用 NVIDIA API）
LLM_PROVIDER=nvidia

# 模型名称（默认使用通义千问大模型）
LLM_MODEL=qwen/qwen3.5-397b-a17b

# API Key（必须配置）
LLM_API_KEY=your-api-key-here

# API 基础 URL（兼容 OpenAI API 格式的任意服务）
LLM_BASE_URL=https://integrate.api.nvidia.com/v1

# 生成参数
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
```

> **说明**: 系统使用 OpenAI 兼容 API，因此可以对接任意支持该格式的服务（如 OpenAI、NVIDIA NIM、本地 Ollama、vLLM 等），只需修改 `LLM_BASE_URL` 和 `LLM_MODEL` 即可。

### 4. 安装前端依赖

```bash
cd frontend/web
npm install
```

## 使用方法

### 方式一：前后端分别启动（推荐开发时使用）

**终端 1 — 启动后端：**

```bash
python main.py
```

后端启动后会在 `http://localhost:5000` 运行，控制台输出 6 步初始化日志。

**终端 2 — 启动前端开发服务器：**

```bash
cd frontend/web
npm start
```

前端开发服务器启动在 `http://localhost:3000`，自动连接到后端 WebSocket。

### 方式二：构建前端后统一启动

```bash
cd frontend/web
npm run build
```

构建产物输出到 `frontend/web/build/`，之后只需启动后端：

```bash
python main.py
```

访问 `http://localhost:5000` 即可同时使用前后端。

### 使用示例

1. 打开 Web 界面后，在聊天面板中输入自然语言飞行指令
2. 观察 StatusBar 中的认知阶段管线实时变化
3. 在 GridViewer 中查看飞行路径和障碍物
4. 在 RightPanel 的各个标签页中查看详细日志、工具调用和任务结果

**示例指令：**

| 指令 | 说明 |
|------|------|
| `飞一个边长3米的正方形` | 规划正方形路径 |
| `前进10米然后左转飞5米` | 连续动作 |
| `添加一些障碍物到(60,60,0)附近` | 添加障碍物 |
| `查看当前环境信息` | 查询状态 |
| `生成飞行动画的分层地图` | 可视化 |
| `生成飞行代码` | 输出 DroneKit 代码 |

## REST API

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/status` | GET | 系统整体状态 |
| `/api/health` | GET | 健康检查 |
| `/api/agent/state` | GET | Agent 运行状态 |
| `/api/grid-state` | GET | 栅格空间完整状态 |
| `/api/obstacles` | GET/POST/DELETE | 障碍物查询/添加/清除 |
| `/api/layer-maps` | GET | 分层切片图文件列表 |
| `/api/code-files` | GET | 生成的飞行代码文件列表 |
| `/api/visualizations` | GET | 可视化图片文件列表 |
| `/api/files/<path>` | GET | 下载 data/output/ 下的文件 |
| `/api/history` | GET | 任务历史 |

## WebSocket 事件

### 客户端 → 服务器

| 事件 | 说明 |
|------|------|
| `user_message` | 发送飞行指令 `{"message": "..."}` |
| `add_obstacles` | 添加障碍物 `{"obstacles": [[x,y,z],...]}` |
| `clear_obstacles` | 清除所有障碍物 |
| `reset_position` | 重置无人机位置 |
| `request_state` | 请求完整状态同步 |
| `ping` | 心跳检测 |

### 服务器 → 客户端

| 事件 | 说明 |
|------|------|
| `connected` | 连接成功，包含初始状态 |
| `message_received` | 指令已收到 |
| `agent_observe` / `agent_observe_done` | OBSERVE 阶段开始/完成 |
| `agent_think` / `agent_think_done` | THINK 阶段开始/完成（含 LLM 决策） |
| `agent_act` / `agent_act_done` | ACT 阶段开始/完成（含工具执行结果） |
| `agent_safety_check_done` | SAFETY_CHECK 完成（含碰撞检测结果） |
| `agent_reflect_done` | REFLECT 完成（含避障策略推荐） |
| `task_result` | 任务最终结果 |
| `task_completed` / `task_failed` | 任务完成/失败 |
| `grid_update` | 栅格空间状态更新 |
| `obstacles_updated` | 障碍物更新 |
| `agent_error` | Agent 执行错误 |

## 配置项说明

在 `config/settings.py` 中可调整以下配置：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `GRID_SIZE` | (100, 100, 20) | 栅格空间大小（米） |
| `INITIAL_POSITION` | (50, 50, 0) | 无人机初始位置 |
| `CELL_SIZE` | 1.0 | 每格边长（米） |
| `AGENT_MAX_ITERATIONS` | 15 | 最大认知循环迭代次数 |
| `AGENT_MAX_REFLECT_RETRIES` | 3 | 最大反思重试次数 |
| `SAFETY_MARGIN` | 1 | 安全边距（格） |
| `MAX_SPEED` | 10.0 | 最大速度（m/s） |
| `WEB_HOST` | "0.0.0.0" | Web 服务监听地址 |
| `WEB_PORT` | 5000 | Web 服务端口 |

## 技术栈

### 后端
- **Python 3.9+**
- **Flask** + **Flask-SocketIO** — Web 服务 + WebSocket 实时通信
- **OpenAI SDK** — LLM 调用 + Function Calling
- **NumPy** — 数值计算
- **Matplotlib** — 路径可视化
- **eventlet** — 异步 WebSocket 支持

### 前端
- **React 18** + **TypeScript 5**
- **Zustand** — 轻量状态管理
- **Socket.IO Client** — WebSocket 实时通信
- **Canvas 2D** — 栅格空间可视化（等轴测3D、俯视、侧视）
- **Axios** — HTTP 请求

## 工作原理

1. 用户在聊天面板输入自然语言指令（如"飞一个边长3米的正方形"）
2. WebSocket 将指令发送到后端，触发 `Orchestrator.run()`
3. Orchestrator 进入认知循环：
   - **OBSERVE**: 收集环境信息（当前位置、障碍物、历史）
   - **THINK**: 调用认知工具生成决策指南，再调用 LLM 通过 Function Calling 选择工具
   - **ACT**: 执行 LLM 选择的飞行工具（如 `ai_translate_flight`）
   - **SAFETY_CHECK**: SafetyGuard 检测路径碰撞
   - **REFLECT**: 碰撞时推荐避障策略，引导 LLM 使用 `ai_replan_with_obstacles`
4. 每个阶段的事件通过 WebSocket 实时推送到前端
5. 前端更新认知管线、日志、工具调用记录和栅格视图
6. 循环持续直到任务完成（`task_complete`）或达到最大迭代次数

## License

MIT
