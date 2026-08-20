#!/usr/bin/env bash
# 墙内抓取车道探针（只读）：直连 HTTP 车道的一次性探测。
#
# Usage:
#   scripts/fetch_probe.sh <url> [out_dir]   # 打印状态/标题/摘要/正文标记
#
# 这是三车道验证中的第 1 档（确定性、无凭据）。第 2 档 tavily_extract
# 与第 3 档本地 Chrome 的操作步骤见
# docs/verification/results/2026-08-14-walled-fetch-lane-validation.md。
set -euo pipefail

URL="${1:?usage: scripts/fetch_probe.sh <url> [out_dir]}"
OUT_DIR="${2:-}"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
BODY="$(mktemp)"
trap 'rm -f "$BODY"' EXIT

CODE="$(curl -sL -A "$UA" -w '%{http_code}' -o "$BODY" "$URL")"
SIZE="$(wc -c < "$BODY" | tr -d ' ')"

echo "URL:     $URL"
echo "HTTP:    $CODE   SIZE: $SIZE bytes"

case "$URL" in
  *mp.weixin.qq.com*)
    echo "og:title: $(grep -o '<meta property="og:title" content="[^"]*"' "$BODY" | head -1 | sed 's/.*content="//;s/"$//')"
    DESC="$(grep -o '<meta property="og:description" content="[^"]*"' "$BODY" | head -1 | sed 's/.*content="//;s/"$//')"
    printf 'og:desc 前 400 字: %s\n' "${DESC:0:400}"
    echo "js_content 容器: $([ "$(grep -c 'id="js_content"' "$BODY" || true)" -gt 0 ] && echo 存在 || echo 不存在（分享页壳，正文未入静态 HTML）)"
    ;;
  *zhihu.com*)
    echo "响应前 200 字节:"
    head -c 200 "$BODY" | tr -d '\n'
    echo
    ;;
  *)
    echo "未识别的站点类型：仅报告状态码与大小。"
    ;;
esac

if [ -n "$OUT_DIR" ]; then
  mkdir -p "$OUT_DIR"
  SAFE="$(basename "$URL" | tr -c 'A-Za-z0-9._-' '_' | cut -c1-60)"
  cp "$BODY" "$OUT_DIR/$SAFE.html"
  echo "SAVED:   $OUT_DIR/$SAFE.html"
fi
