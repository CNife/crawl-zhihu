#!/bin/bash

set -euo pipefail

# ========== 配置参数 ==========
DEBUG_PORT=9222
DEBUG_URL="http://localhost:${DEBUG_PORT}/json/version"
USER_DATA_DIR="./browser_profiles/zhihu_profile"
CHROME_PATH="chromium"

# ========== 颜色输出 ==========
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# ========== 检查并安装 agent-browser ==========
check_agent_browser() {
    if command -v agent-browser &> /dev/null; then
        log_info "agent-browser 已全局安装，跳过安装步骤"
        return 0
    fi

    log_info "agent-browser 未安装，开始安装流程..."

    # 检查并安装 Node.js
    if ! command -v node &> /dev/null; then
        log_info "Node.js 未安装，开始安装..."

        # 检测 Linux 发行版并安装
        if command -v apt &> /dev/null; then
            curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
            sudo apt-get install -y nodejs
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y nodejs
        elif command -v yum &> /dev/null; then
            sudo yum install -y nodejs
        elif command -v pacman &> /dev/null; then
            sudo pacman -S --noconfirm nodejs npm
        else
            log_error "未找到支持的包管理器，请手动安装 Node.js"
            exit 1
        fi

        log_info "Node.js 安装成功：$(node --version)"
    else
        log_info "Node.js 已安装：$(node --version)"
    fi

    # 安装 agent-browser
    log_info "开始安装 agent-browser..."
    npm install -g agent-browser --registry=https://registry.npmmirror.com
    log_info "agent-browser 安装成功"
}

# ========== Chrome Debug 模式 ==========
check_chrome_debug() {
    curl -s --connect-timeout 2 "${DEBUG_URL}" > /dev/null 2>&1
}

start_chrome_debug() {
    log_info "正在启动 Chrome Debug 模式..."

    if ! type "$CHROME_PATH" >/dev/null 2>&1; then
        log_error "未找到 Chrome 浏览器：$CHROME_PATH"
        exit 1
    fi

    mkdir -p "$USER_DATA_DIR"
    "$CHROME_PATH" \
        --remote-debugging-port=${DEBUG_PORT} \
        --no-first-run \
        --no-default-browser-check \
        --user-data-dir="$USER_DATA_DIR" \
        > /dev/null 2>&1 &

    log_info "Chrome 启动命令已执行，等待服务就绪..."

    # 等待 Debug 端口可用
    for attempt in $(seq 1 10); do
        sleep 1
        if check_chrome_debug; then
            log_info "Chrome Debug 模式已成功启动！"
            return 0
        fi
        log_info "等待中... (${attempt}/10)"
    done

    log_error "Chrome Debug 模式启动超时"
    return 1
}

show_connection_info() {
    log_info "=========================================="
    log_info "Chrome Debug 模式运行中"
    log_info "调试端口：${DEBUG_PORT}"
    log_info "端点地址：${DEBUG_URL}"
    log_info "=========================================="
}

# ========== 主流程 ==========
echo ""
log_info "Chrome Debug 模式检查脚本"
echo ""

# 检查并安装 agent-browser
check_agent_browser

# 检查并启动 Chrome Debug 模式
if check_chrome_debug; then
    log_info "Chrome Debug 模式已在运行"
    show_connection_info
    exit 0
fi

log_warn "Chrome Debug 模式未启动"

if start_chrome_debug; then
    show_connection_info
    exit 0
else
    log_error "无法启动 Chrome Debug 模式"
    log_error "提示：如果端口被占用，可能需要手动关闭占用端口的进程"
    exit 1
fi
