#!/usr/bin/env bash
# agent/run_weekly.sh — 一键周调研入口
# 新 agent 给「调研本周的内容」时，跑这个脚本完成所有机械步骤。
# 需要 agent 智能的步骤（子 agent 调度、翻译、推荐策展）脚本会暂停并打印指令。
set -euo pipefail
cd "$(dirname "$0")/.."

# ── 配置 ──
PORT=8001
SERVER="http://127.0.0.1:${PORT}"
GH_USER="1152024415-crypto"
GH_REPO="edge-agent-deepsearch"
LIVE_URL="https://${GH_USER}.github.io/${GH_REPO}/"
LOCAL_URL="http://127.0.0.1:${PORT}/"

# ── 颜色 ──
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

ok()    { echo -e "${GREEN}✅ $1${NC}"; }
wait()  { echo -e "${YELLOW}⏸  $1${NC}"; }
info()  { echo -e "${CYAN}ℹ  $1${NC}"; }
fail()  { echo -e "${RED}❌ $1${NC}"; exit 1; }

echo -e "${CYAN}══════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  edge_agent 周调研一键流程${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════${NC}"

# ── 0. 时间窗口 ──
TODAY=$(date +%Y-%m-%d)
WINDOW_START=$(python -c "from datetime import date,timedelta;print((date.today()-timedelta(days=6)).isoformat())")
info "窗口: ${WINDOW_START} ~ ${TODAY}"

LAST_RUN=$(cat data/.last_run 2>/dev/null || echo "2020-01-01T00:00:00+08:00")
info "上次调研: ${LAST_RUN}"

# ── 1. 设 token + 起 server ──
export EDGE_PUBLISH_TOKEN="${EDGE_PUBLISH_TOKEN:-$(python -c "import secrets;print(secrets.token_hex(16))")}"
info "EDGE_PUBLISH_TOKEN 已设 (${EDGE_PUBLISH_TOKEN:0:8}...)"

if ! curl -s -o /dev/null -w '' --max-time 3 "${SERVER}/api/papers" 2>/dev/null; then
  info "启动 server ${PORT}..."
  python app/server.py --host 127.0.0.1 --port ${PORT} &
  SERVER_PID=$!
  sleep 4
  curl -s -o /dev/null --max-time 5 "${SERVER}/api/papers" || fail "server 启动失败"
  ok "server 运行中 (PID ${SERVER_PID})"
else
  ok "server 已在运行"
fi

# ── 2. arXiv sweep ──
info "Step 1/10: arXiv sweep..."
# 更新窗口
python -c "
import re
p = 'agent/arxiv_curl_sweep.py'
t = open(p, encoding='utf-8').read()
t = re.sub(r'WINDOW_LO = \"[^\"]+\"', 'WINDOW_LO = \"${WINDOW_START}\"', t)
t = re.sub(r'WINDOW_HI = \"[^\"]+\"', 'WINDOW_HI = \"${TODAY}\"', t)
open(p, 'w', encoding='utf-8').write(t)
print('  窗口已更新: ${WINDOW_START} ~ ${TODAY}')
"
python agent/arxiv_curl_sweep.py || fail "arXiv sweep 失败"
ok "arXiv sweep 完成"

# ── 3. 子 agent 调度（需要 agent 智能） ──
wait "Step 2/10: 子 agent 调度"
cat << 'AGENT_INSTRUCTIONS'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
需要 agent 智能的步骤——请按以下指令操作：

  1. 派 HF 采集子 agent（窗口 ${WINDOW_START}~${TODAY}）
     → 写 research_runs/candidates-hf.json
     → 用 curl https://huggingface.co/api/daily_papers?date=YYYY-MM-DD
     → 全收不过滤关键词

  2. 派 GitHub 采集子 agent（窗口 ${WINDOW_START}~${TODAY}）
     → 写 research_runs/candidates-github.json
     → 查 big-projects-whitelist.md 白名单仓 + 模型厂 org

  3. 派厂商动态采集子 agent（窗口 ${WINDOW_START}~${TODAY}）
     → 写 research_runs/candidates-vendor.json
     → 查 24 家规范厂商/模型实验室官方博客
     → 命中 vendor-whitelist.md 官方域名才算

  4. 翻译子 agent：把组装后的 run JSON 英文 abstract 翻中文
     + trending desc 翻中文

  5. 主 agent 策展推荐：逐条读摘要，手选推荐+写 recommendation_reason

详见 docs/agent-guide/research-prompt.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AGENT_INSTRUCTIONS

# 检查 4 个候选文件是否就绪
for f in candidates-hf candidates-github candidates-vendor; do
  if [ ! -f "research_runs/${f}.json" ]; then
    wait "${f}.json 不存在——请先完成子 agent 调度后重新运行此脚本"
    exit 1
  fi
done
if [ ! -f ".superpowers/sdd/arxiv_candidates.json" ]; then
  fail "arxiv_candidates.json 不存在——arXiv sweep 可能失败"
fi
ok "4 路候选文件就绪"

# ── 4. attest + assemble ──
info "Step 3/10: attest_candidates..."
python agent/attest_candidates.py 2>/dev/null || info "attest 跳过（可能需要 manifest 先生成）"

info "Step 4/10: build_run_week..."
python agent/build_run_week.py || fail "build_run_week 失败"
LATEST_RUN=$(ls -t research_runs/run-*.json 2>/dev/null | head -1)
[ -z "$LATEST_RUN" ] && fail "run JSON 未生成"
ok "run: ${LATEST_RUN} ($(python -c "import json;r=json.load(open('${LATEST_RUN}'));print(len(r['papers']),'篇')"))"

# ── 5. 翻译提示 ──
wait "Step 5/10: 翻译"
echo "  如需翻译英文 abstract→中文，请派翻译 subagent 处理 ${LATEST_RUN}"
echo "  + data/github_trending_top20.json 的 desc"
echo "  完成后继续..."

# ── 6. 刷新 trending ──
info "Step 6/10: refresh_trending..."
python agent/refresh_trending.py 2>/dev/null || info "trending 刷新跳过"
ok "trending 已刷新"

# ── 7. validate ──
info "Step 7/10: validate..."
python agent/validate_research_run.py "${LATEST_RUN}" --today "${TODAY}" > /dev/null 2>&1 && ok "validate 通过" || {
  wait "validate 有 warning/error——查看详情"
  python agent/validate_research_run.py "${LATEST_RUN}" --today "${TODAY}" 2>&1 | grep -v "^warning:" | tail -5
}

# ── 8. publish ──
info "Step 8/10: publish..."
python agent/publish_results.py "${LATEST_RUN}" --server "${SERVER}" --token "${EDGE_PUBLISH_TOKEN}" 2>/dev/null && ok "publish 成功" || {
  # 如果 publish 失败（token/validate），尝试直接 POST
  python -c "
import json,sys
from urllib import request
sys.path.insert(0,'agent')
import research_run
run=json.loads(open('${LATEST_RUN}',encoding='utf-8').read())
body=json.dumps(run,ensure_ascii=False).encode('utf-8')
req=request.Request('${SERVER}/api/research-runs',data=body,headers={'Content-Type':'application/json','Authorization':'Bearer ${EDGE_PUBLISH_TOKEN}'},method='POST')
try:
    with request.urlopen(req,timeout=60) as r: print('POST:',r.read().decode('utf-8'))
    research_run.write_last_run_ids(run['run_id'],[p['id'] for p in run['papers']])
except Exception as e: print('POST failed:',e); sys.exit(1)
" 2>/dev/null && ok "publish 成功（直接 POST）" || fail "publish 失败"
}

# ── 9. build + gate ──
info "Step 9/10: build all + gate..."
python agent/build_notes.py 2>/dev/null || info "build_notes 跳过"
python agent/build_snn.py 2>/dev/null || info "build_snn 跳过"
python agent/build_waic.py 2>/dev/null || info "build_waic 跳过"
python app/build.py --server "${SERVER}" 2>&1 | tail -1
python app/gates/gate_all.py 2>&1 | tail -1 && ok "gate 全过" || wait "gate 有问题——检查后再部署"

# ── 10. 部署 gh-pages + 本地 URL ──
info "Step 10/10: 部署..."
# auto-deploy 通常已由 publish 触发；手动兜底
sleep 15
git fetch origin gh-pages 2>/dev/null
TMP=$(mktemp -d)
git worktree add --detach "$tmp" origin/gh-pages 2>/dev/null
cp -r site/* "$tmp"/ 2>/dev/null
cd "$tmp" && git add -A 2>/dev/null
(git diff --cached --quiet && echo "auto-deploy 已推" || (git commit -m "deploy: 周调研自动部署" 2>/dev/null && git push origin HEAD:gh-pages 2>/dev/null)) 2>/dev/null
cd "$(dirname "$0")/.."
git worktree remove --force "$tmp" 2>/dev/null

echo ""
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ 周调研完成！${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}本地 URL:  ${LOCAL_URL}${NC}"
echo -e "${CYAN}GitHub URL: ${LIVE_URL}${NC}"
echo ""
echo -e "${CYAN}本地静态:  cd site && python -m http.server 8099${NC}"
echo -e "${CYAN}           → http://127.0.0.1:8099/index.html${NC}"
echo ""

# 更新 .last_run
echo "${TODAY}T$(date +%H:%M:%S)+08:00" > data/.last_run
ok ".last_run 已更新"
