import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── 路径配置 ──────────────────────────────────────────────────
PROJECT_ROOT    = Path(__file__).parent.parent
DATA_DIR        = PROJECT_ROOT / "data"
OUTPUT_DIR      = DATA_DIR / "output"
VISUALIZATION_DIR = OUTPUT_DIR / "visualizations"
LAYER_MAP_DIR   = OUTPUT_DIR / "layer_maps"
MISSION_DIR     = OUTPUT_DIR / "missions"

# 启动时创建必要目录
for _d in [VISUALIZATION_DIR, LAYER_MAP_DIR, MISSION_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# ── 栅格空间配置 ──────────────────────────────────────────────
GRID_SIZE        = (100, 100, 20)   # X, Y, Z
INITIAL_POSITION = (50, 50, 0)      # 无人机起始位置
CELL_SIZE        = 1.0              # 每格1米

# ── 动作定义（英文名 → 方向向量）────────────────────────────────
ACTIONS = {
    "forward":        ( 0,  1,  0),
    "backward":       ( 0, -1,  0),
    "left":           (-1,  0,  0),
    "right":          ( 1,  0,  0),
    "up":             ( 0,  0,  1),
    "down":           ( 0,  0, -1),
    "hover":          ( 0,  0,  0),
    "forward_left":   (-1,  1,  0),
    "forward_right":  ( 1,  1,  0),
    "backward_left":  (-1, -1,  0),
    "backward_right": ( 1, -1,  0),
}

# ── 动作中文别名 ───────────────────────────────────────────────
ACTION_ALIASES = {
    "前进": "forward",  "向前": "forward",
    "后退": "backward", "向后": "backward",
    "左移": "left",     "向左": "left",
    "右移": "right",    "向右": "right",
    "上升": "up",       "升高": "up",   "爬升": "up",
    "下降": "down",     "降低": "down", "下落": "down",
    "悬停": "hover",
    "左前": "forward_left",   "前左": "forward_left",
    "右前": "forward_right",  "前右": "forward_right",
    "左后": "backward_left",  "后左": "backward_left",
    "右后": "backward_right", "后右": "backward_right",
}

# ── LLM配置 ───────────────────────────────────────────────────
LLM_PROVIDER    = os.getenv("LLM_PROVIDER",  "nvidia")
LLM_MODEL       = os.getenv("LLM_MODEL",     "qwen/qwen3.5-397b-a17b")
LLM_API_KEY     = os.getenv("LLM_API_KEY",   "")
LLM_BASE_URL    = os.getenv("LLM_BASE_URL",  "https://integrate.api.nvidia.com/v1")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS  = int(os.getenv("LLM_MAX_TOKENS",    "2000"))

# ── Agent配置 ─────────────────────────────────────────────────
AGENT_MAX_ITERATIONS     = 15
AGENT_MAX_REFLECT_RETRIES = 3

# ── 安全配置 ──────────────────────────────────────────────────
SAFETY_MARGIN = 1      # 安全边距（格）
MAX_SPEED     = 10.0   # 最大速度（m/s）

# ── Web服务配置 ───────────────────────────────────────────────
WEB_HOST  = "0.0.0.0"
WEB_PORT  = 5000
WEB_DEBUG = False
