#!/usr/bin/env bash
# 稳定弹出 macOS Terminal.app 可见窗口运行 AI Daily CLI 的入口（TUI fallback）。
#
# 用法：
#   scripts/open_ai_daily_terminal.sh --root <repo-root> --date YYYY-MM-DD \
#       [--command session|choose-topic|status] [--dry-run]
#
# 纯 macOS 原生实现（/usr/bin/osascript + Terminal.app），无第三方依赖，
# 不修改任何 Python TUI/CLI 逻辑。窗口执行完成后保留 shell 提示符，
# 命令输出完整可见，之后仍可手动运行同一 CLI 恢复后续阶段。
set -euo pipefail

OSASCRIPT="/usr/bin/osascript"

usage() {
  sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
}

# 校验/用法错误：退出码 2；运行时（osascript）失败：退出码 1。
die() {
  printf '错误：%s\n' "$*" >&2
  exit 2
}

# 单引号包裹任意字符串；内部单引号转义为 '\''（POSIX shell 标准写法），
# 保证空格、单引号、$、反引号等字符在最终 shell 命令中都是字面量。
shell_quote() {
  printf "'%s'" "$(printf '%s' "$1" | sed "s/'/'\\\\''/g")"
}

ROOT=""
DATE=""
COMMAND="session"
DRY_RUN=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --root)
      [ "$#" -ge 2 ] || die "--root 缺少参数"
      ROOT="$2"
      shift 2
      ;;
    --date)
      [ "$#" -ge 2 ] || die "--date 缺少参数"
      DATE="$2"
      shift 2
      ;;
    --command)
      [ "$#" -ge 2 ] || die "--command 缺少参数"
      COMMAND="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      ;;
    *)
      die "未知参数：$1（使用 --help 查看用法）"
      ;;
  esac
done

[ -n "$ROOT" ] || die "缺少 --root <repo-root>"
[ -n "$DATE" ] || die "缺少 --date YYYY-MM-DD"

[ -d "$ROOT" ] || die "root 不是目录：$ROOT"
[ -f "$ROOT/src/ai_daily/cli.py" ] || die "root 缺少 src/ai_daily/cli.py：$ROOT"

case "$DATE" in
  [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]) ;;
  *) die "date 格式必须是 YYYY-MM-DD：$DATE" ;;
esac

# 命令白名单，避免任意命令注入；新命令需在此显式登记。
case "$COMMAND" in
  session|choose-topic|status) ;;
  *) die "不支持的 command（白名单：session、choose-topic、status）：$COMMAND" ;;
esac

Q_ROOT="$(shell_quote "$ROOT")"
Q_DATE="$(shell_quote "$DATE")"
SHELL_CMD="cd ${Q_ROOT} && export PYTHONPATH=src && python3 -m ai_daily.cli ${COMMAND} --root ${Q_ROOT} --date ${Q_DATE}"

if [ "$DRY_RUN" -eq 1 ]; then
  printf '%s\n' "$SHELL_CMD"
  exit 0
fi

if [ "$(uname -s)" != "Darwin" ]; then
  printf '错误：仅支持 macOS（当前系统：%s）\n' "$(uname -s)" >&2
  exit 1
fi
[ -x "$OSASCRIPT" ] || die "找不到 $OSASCRIPT"

# 命令经 argv 传给 osascript，避免 AppleScript 字符串二次转义；
# do script 默认在新窗口执行（命令结束后保留提示符），activate 让窗口置前。
OSA='on run argv
  set shellCmd to item 1 of argv
  tell application "Terminal"
    do script shellCmd
    activate
  end tell
end run'

if ! ERR="$("$OSASCRIPT" -e "$OSA" "$SHELL_CMD" 2>&1 >/dev/null)"; then
  printf '错误：osascript 启动 Terminal.app 失败\n' >&2
  [ -n "$ERR" ] && printf '%s\n' "$ERR" >&2
  exit 1
fi

printf '已弹出 Terminal.app 窗口，正在运行：%s\n' "$SHELL_CMD"
