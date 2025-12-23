#!/usr/bin/env bash
set -euo pipefail

##############################################
# Tele-Op Backend Regression Test Runner
# - 启动/检测 Tele-Op 本地服务
# - 创建并使用本目录的测试虚拟环境
# - 运行 pytest + 生成 Allure 报告
##############################################

# 兼容 cron/sh：BASH_SOURCE 可能没有定义
if [[ -n "${BASH_SOURCE-}" ]]; then
  SCRIPT_PATH="${BASH_SOURCE[0]}"
else
  SCRIPT_PATH="$0"
fi
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
BACKEND_DIR="/Users/wanxin/PycharmProjects/Prismax/app-prismax-rp-backend/app_prismax_tele_op_services"
TEST_DIR="$SCRIPT_DIR"
ALLURE_RESULTS_DIR="$TEST_DIR/test_report/allure-results"
ALLURE_REPORT_DIR="$TEST_DIR/test_report/allure-report"
BACKEND_LOG="$TEST_DIR/backend.log"

# 默认环境变量（可在外部覆盖）
TELE_HOST="${TELE_HOST:-localhost}"
TELE_PORT="${TELE_PORT:-8081}"
TELE_SCHEME="${TELE_SCHEME:-http}"
TELE_BASE="${TELE_BASE:-}"

ROBOT_ID="${ROBOT_ID:-arm1}"
# 默认使用经过验证的 Tele-Op 队列用户，用于日常回归
USER_ID="${USER_ID:-1073381}"
TOKEN="${TOKEN:-HZjIrBDYYlDZ2p2hyzj6P4B9HeMKyIGl5lwp3sdorDg}"

PYTEST_EXIT_CODE=0

print_info() { echo "[INFO]  $1"; }
print_warn() { echo "[WARN]  $1"; }
print_err()  { echo "[ERROR] $1" >&2; }

wait_for_backend() {
  local host="$1"
  local port="$2"
  local max_wait="${3:-60}"
  local url="http://${host}:${port}/robots/status"
  print_info "Waiting for Tele-Op backend at ${url} (timeout ${max_wait}s)..."
  local start_ts
  start_ts="$(date +%s)"
  while true; do
    # 只要能连通就认为服务已就绪（不强制 200）
    local code
    code="$(curl -s -m 2 -o /dev/null -w "%{http_code}" "$url" || echo "000")"
    if [[ "$code" != "000" ]]; then
      print_info "Backend is up (HTTP $code)."
      return 0
    fi
    local now_ts
    now_ts="$(date +%s)"
    if (( now_ts - start_ts >= max_wait )); then
      print_err "Backend did not become ready within ${max_wait}s."
      return 1
    fi
    sleep 1
  done
}

start_backend_if_needed() {
  # 每次运行前强制从后端目录启动一次服务
  print_info "Forcing Tele-Op backend restart on port ${TELE_PORT}..."

  # 如果有进程占用该端口，先尝试杀掉（需要 lsof）
  if command -v lsof >/dev/null 2>&1; then
    local pids
    pids="$(lsof -ti tcp:\"$TELE_PORT\" || true)"
    if [ -n "$pids" ]; then
      print_warn "Killing existing process(es) on port ${TELE_PORT}: $pids"
      echo "$pids" | xargs -r kill -9 || true
    fi
  fi

  print_info "Starting Tele-Op backend in background... (logs: $BACKEND_LOG)"
  mkdir -p "$(dirname "$BACKEND_LOG")"

  # 使用后端自己的虚拟环境启动 app.py
  nohup bash -lc "cd \"$BACKEND_DIR\" && \
    source .venv/bin/activate && \
    TEST_MODE=true GOOGLE_CLOUD_PROJECT=thepinai \
    GOOGLE_APPLICATION_CREDENTIALS=/Users/wanxin/PycharmProjects/Prismax/thepinai-compute-key.json \
    PORT=\"$TELE_PORT\" python app.py" \
    >"$BACKEND_LOG" 2>&1 &

  # 等待最多 90 秒让服务起来
  set +e
  wait_for_backend "$TELE_HOST" "$TELE_PORT" 90
  local rc=$?
  set -e
  if (( rc != 0 )); then
    print_warn "Backend may not be ready; tests might fail to connect."
  fi
}

ensure_test_venv() {
  if ! command -v python3 >/dev/null 2>&1; then
    print_err "python3 not found. Please install Python 3 first."
    exit 1
  fi

  if [ ! -d "$TEST_DIR/.venv" ]; then
    print_info "Creating test virtualenv at $TEST_DIR/.venv"
    python3 -m venv "$TEST_DIR/.venv"
  fi

  # shellcheck disable=SC1091
  source "$TEST_DIR/.venv/bin/activate"

  if [ ! -f "$TEST_DIR/.venv/.deps_installed" ]; then
    print_info "Installing test dependencies from requirements.txt ..."
    pip install -r "$TEST_DIR/requirements.txt"
    touch "$TEST_DIR/.venv/.deps_installed"
  fi
}

run_pytest() {
  print_info "Running pytest for Tele-Op regression tests..."
  print_info "Tele-Op target: ${TELE_SCHEME}://${TELE_HOST}:${TELE_PORT}${TELE_BASE} (robot_id=$ROBOT_ID user_id=$USER_ID)"

  # 每次运行前清理旧的 allure-results，避免历史用例（例如已删除的 test_tele_op）残留在报告中
  rm -rf "$ALLURE_RESULTS_DIR"/*
  mkdir -p "$ALLURE_RESULTS_DIR"

  set +e
  TELE_HOST="$TELE_HOST" TELE_PORT="$TELE_PORT" TELE_SCHEME="$TELE_SCHEME" TELE_BASE="$TELE_BASE" \
  ROBOT_ID="$ROBOT_ID" USER_ID="$USER_ID" TOKEN="$TOKEN" \
    pytest -q "$TEST_DIR/test_cases"
  PYTEST_EXIT_CODE=$?
  set -e

  if [ "$PYTEST_EXIT_CODE" -eq 0 ]; then
    print_info "Pytest finished successfully."
  else
    print_warn "Pytest finished with exit code: $PYTEST_EXIT_CODE"
  fi
}

generate_allure_report() {
  if ! command -v allure >/dev/null 2>&1; then
    print_warn "allure CLI not found; skip report generation. Results at: $ALLURE_RESULTS_DIR"
    return 0
  fi

  mkdir -p "$ALLURE_REPORT_DIR"
  print_info "Generating Allure report into: $ALLURE_REPORT_DIR"
  allure generate "$ALLURE_RESULTS_DIR" --clean -o "$ALLURE_REPORT_DIR" || {
    print_warn "Allure generate failed; please check raw results at: $ALLURE_RESULTS_DIR"
    return 0
  }
  print_info "Allure report generated at: $ALLURE_REPORT_DIR/index.html"

  # 启动一个本地 HTTP 服务来托管报告，然后在浏览器中打开 http://localhost:PORT
  local port="${ALLURE_PORT:-9999}"

  # 如果端口已被占用，尝试释放
  if command -v lsof >/dev/null 2>&1; then
    local pids
    pids="$(lsof -ti tcp:\"$port\" || true)"
    if [ -n "$pids" ]; then
      print_warn "Killing existing process(es) on port ${port}: $pids"
      echo "$pids" | xargs -r kill -9 || true
    fi
  fi

  if command -v python3 >/dev/null 2>&1; then
    print_info "Starting local HTTP server for Allure report on port ${port}..."
    nohup python3 -m http.server "$port" --directory "$ALLURE_REPORT_DIR" >/tmp/allure_http_${port}.log 2>&1 &
  else
    print_warn "python3 not found; cannot start local HTTP server. Please open the report via file:// manually."
    return 0
  fi

  # 自动在浏览器中打开 HTTP 报告地址（macOS 使用 open）
  local url="http://localhost:${port}/"
  if command -v open >/dev/null 2>&1; then
    print_info "Opening Allure report in default browser at ${url} ..."
    open "$url" || print_warn "Failed to open browser automatically; please open ${url} manually."
  else
    print_warn "Could not find 'open' command. Please open ${url} manually in your browser."
  fi
}

send_email_summary() {
  # 使用 SMTP_* 环境变量发送一封包含测试汇总和 xfail 高亮的邮件
  local results_base="$ALLURE_RESULTS_DIR"
  local smtp_host="${SMTP_HOST:-mail.privateemail.com}"
  local smtp_port="${SMTP_PORT:-465}"
  local smtp_security="${SMTP_SECURITY:-ssl}" # ssl | starttls
  local smtp_user="${SMTP_USER:-}"
  local smtp_pass="${SMTP_PASS:-}"
  local email_to="${EMAIL_TO:-wanxin@solidcap.io}"
  local email_from="${EMAIL_FROM:-$smtp_user}"
  local subject="${EMAIL_SUBJECT:-Tele-Op Daily Regression Summary}"
  local report_url="http://localhost:${ALLURE_PORT:-9999}"

  if [ -z "$smtp_user" ] || [ -z "$smtp_pass" ]; then
    print_warn "SMTP_USER/SMTP_PASS not set; skipping email summary."
    return 0
  fi

  print_info "Sending Tele-Op test summary email to: $email_to via $smtp_host:$smtp_port"

  RESULTS_BASE="$results_base" REPORT_URL="$report_url" \
  SMTP_HOST="$smtp_host" SMTP_PORT="$smtp_port" SMTP_SECURITY="$smtp_security" \
  SMTP_USER="$smtp_user" SMTP_PASS="$smtp_pass" \
  EMAIL_TO="$email_to" EMAIL_FROM="$email_from" EMAIL_SUBJECT="$subject" \
  python3 - <<'PY' || echo "WARN: Email sending failed"
import os, smtplib, ssl, sys, json, glob
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
smtp_port = int(os.environ.get("SMTP_PORT", "465"))
smtp_security = os.environ.get("SMTP_SECURITY", "ssl").lower()
smtp_user = os.environ.get("SMTP_USER", "")
smtp_pass = os.environ.get("SMTP_PASS", "")
email_to = os.environ.get("EMAIL_TO", "wanxin@solidcap.io")
email_from = os.environ.get("EMAIL_FROM", smtp_user)
subject = os.environ.get("EMAIL_SUBJECT", "Tele-Op Daily Regression Summary")
results_base = os.environ.get("RESULTS_BASE", "")
report_url = os.environ.get("REPORT_URL", "http://localhost:9999")

if not smtp_user or not smtp_pass:
    sys.exit(0)

def summarize_results(base_dir: str):
    if not base_dir or not os.path.isdir(base_dir):
        return "No results found.", {}

    def _extract_queue_mismatch(result_dir: str, data: dict):
        """Extract expected/actual queue sequences from Allure attachment for test_queue_positions xfail."""
        name = (data.get("name") or data.get("fullName") or "").lower()
        if "test_queue_positions" not in name:
            return None

        # Collect attachments from both top-level and step-level, because Allure
        # stores our "positions_mismatch" attachment under the step.
        attachments = list(data.get("attachments") or [])
        for step in data.get("steps") or []:
            for att in step.get("attachments") or []:
                attachments.append(att)
        for att in attachments:
            if att.get("name") != "positions_mismatch":
                continue
            source = att.get("source")
            if not source:
                continue
            path = os.path.join(result_dir, source)
            try:
                txt = open(path, "r", encoding="utf-8").read().strip()
            except Exception:
                continue
            exp = act = None
            for line in txt.splitlines():
                l = line.strip()
                if l.startswith("expected="):
                    exp = l[len("expected=") :]
                elif l.startswith("actual="):
                    act = l[len("actual=") :]
            lines = ["[queue_positions] MISMATCH"]
            if exp is not None and act is not None:
                lines.append(f"[queue_positions] expected queue: {exp}")
                lines.append(f"[queue_positions] actual   queue: {act}")
            else:
                lines.append("[queue_positions] raw attachment:")
                lines.extend(txt.splitlines())
            return "\n".join(lines)
        return None
    entries = [os.path.join(base_dir, d) for d in os.listdir(base_dir)]
    subdirs = [d for d in entries if os.path.isdir(d)]
    if not subdirs:
        subdirs = [base_dir]
    overall = {"passed": 0, "failed": 0, "skipped": 0, "xfailed": 0, "broken": 0}
    per_suite = {}
    failures = []
    xfails = []
    skips = []
    queue_position_xfails = []
    all_cases = []  # track every test case: name + status + message
    for d in sorted(subdirs):
        suite = os.path.basename(d) if d != base_dir else "all"
        counts = {"passed": 0, "failed": 0, "skipped": 0, "xfailed": 0, "broken": 0}
        for p in glob.glob(os.path.join(d, "*-result.json")):
            try:
                data = json.load(open(p, "r", encoding="utf-8"))
            except Exception:
                continue
            status = (data.get("status") or "").lower()
            name = data.get("name") or data.get("fullName") or "unknown"
            details = data.get("statusDetails") or {}
            message = (details.get("message") or "").strip()
            is_xfail = False
            if status == "skipped":
                lm = message.lower()
                if "xfail" in lm or "expected failure" in lm:
                    is_xfail = True
            normalized_status = status
            if status == "passed":
                counts["passed"] += 1
            elif status == "failed":
                counts["failed"] += 1
                failures.append(f"- {name}: {message or status}")
            elif status == "broken":
                counts["broken"] += 1
                failures.append(f"- {name}: {message or status}")
            elif status == "skipped":
                if is_xfail:
                    counts["xfailed"] += 1
                    xfails.append(f"- {name}: {message or 'xfail'}")
                    normalized_status = "xfailed"
                else:
                    counts["skipped"] += 1
                    skips.append(f"- {name}: {message or 'skipped'}")
            # 如果是队列位置相关的 xfail，用附件中的 positions_mismatch 补充 expected/actual 序列
            if normalized_status == "xfailed":
                detail = _extract_queue_mismatch(d, data)
                if detail:
                    queue_position_xfails.append(detail)
            # record every case for detailed section
            all_cases.append(
                {
                    "suite": suite,
                    "name": name,
                    "status": normalized_status,
                    "message": message,
                }
            )
        per_suite[suite] = counts
        for k, v in counts.items():
            overall[k] = overall.get(k, 0) + v
    text_lines = []
    text_lines.append("Tele-Op Regression Summary")
    text_lines.append(f"Report: {report_url}")
    text_lines.append("")
    text_lines.append("Overall:")
    text_lines.append(f"  passed={overall.get('passed',0)} failed={overall.get('failed',0)} skipped={overall.get('skipped',0)} xfailed={overall.get('xfailed',0)} broken={overall.get('broken',0)}")
    text_lines.append("")
    text_lines.append("Per Suite:")
    for r, c in per_suite.items():
        text_lines.append(f"  {r}: passed={c.get('passed',0)} failed={c.get('failed',0)} skipped={c.get('skipped',0)} xfailed={c.get('xfailed',0)} broken={c.get('broken',0)}")
    text_lines.append("")
    if xfails:
        text_lines.append("Xfails (expected failures):")
        text_lines.extend(xfails[:50])
        text_lines.append("")
    if queue_position_xfails:
        text_lines.append("Queue position xfail details:")
        for q in queue_position_xfails:
            text_lines.append(q)
            text_lines.append("")
    if failures:
        text_lines.append("Failures:")
        text_lines.extend(failures[:50])
    if skips:
        text_lines.append("")
        text_lines.append("Skipped:")
        text_lines.extend(skips[:50])

    # Detailed per-case section
    text_lines.append("")
    text_lines.append("Detailed cases:")
    for c in all_cases:
        line = f"- [{c['status']}] {c['name']}"
        if c["message"]:
            line += f": {c['message']}"
        text_lines.append(line)
    html = []
    html.append("<html><body style=\"font-family: -apple-system, Arial, sans-serif; font-size:14px; color:#222;\">")
    html.append("<h3 style=\"margin:0 0 8px 0;\">Tele-Op Regression Summary</h3>")
    html.append(f"<div style=\"margin:4px 0 12px 0;\">Report: <a href=\"{report_url}\">{report_url}</a></div>")
    html.append("<div style=\"margin:6px 0;\"><b>Overall:</b><br/>")
    html.append(f"<code>passed={overall.get('passed',0)} failed={overall.get('failed',0)} skipped={overall.get('skipped',0)} xfailed={overall.get('xfailed',0)} broken={overall.get('broken',0)}</code></div>")
    html.append("<div style=\"margin:6px 0;\"><b>Per Suite:</b><br/><ul style=\"margin:6px 0 0 18px;\">")
    for r, c in per_suite.items():
        html.append(f"<li><code>{r}: passed={c.get('passed',0)} failed={c.get('failed',0)} skipped={c.get('skipped',0)} xfailed={c.get('xfailed',0)} broken={c.get('broken',0)}</code></li>")
    html.append("</ul></div>")
    if xfails:
        html.append("<div style=\"margin:10px 0;\"><b><span style=\"color:#d32f2f;\">Xfails (expected failures):</span></b><ul style=\"margin:6px 0 0 18px;\">")
        for x in xfails[:50]:
            html.append(f"<li><code>{x}</code></li>")
        html.append("</ul></div>")
    if queue_position_xfails:
        html.append("<div style=\"margin:10px 0;\"><b>Queue position xfail details:</b>")
        for q in queue_position_xfails:
            esc = q.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            html.append("<pre style=\"margin:4px 0 0 0; padding:6px 8px; background:#f5f5f5; border-radius:4px;\">")
            html.append(esc)
            html.append("</pre>")
        html.append("</div>")
    if failures:
        html.append("<div style=\"margin:10px 0;\"><b>Failures:</b><ul style=\"margin:6px 0 0 18px;\">")
        for f in failures[:50]:
            html.append(f"<li><code>{f}</code></li>")
        html.append("</ul></div>")
    if skips:
        html.append("<div style=\"margin:10px 0;\"><b>Skipped:</b><ul style=\"margin:6px 0 0 18px;\">")
        for s in skips[:50]:
            html.append(f"<li><code>{s}</code></li>")
        html.append("</ul></div>")

    # Detailed per-case HTML section
    html.append("<div style=\"margin:10px 0;\"><b>All cases:</b><ul style=\"margin:6px 0 0 18px;\">")
    for c in all_cases:
        status = c["status"]
        color = "#2e7d32"  # green for passed
        if status == "failed" or status == "broken":
            color = "#c62828"
        elif status == "xfailed":
            color = "#d32f2f"
        elif status == "skipped":
            color = "#757575"
        msg = f": {c['message']}" if c["message"] else ""
        html.append(
            f"<li><code><span style=\"color:{color};\">[{status}]</span> {c['name']}{msg}</code></li>"
        )
    html.append("</ul></div>")
    html.append("</body></html>")
    return "\n".join(text_lines), "".join(html), {"overall": overall, "per_suite": per_suite}

text_body, html_body, _ = summarize_results(results_base)

msg = MIMEMultipart('alternative')
msg["From"] = email_from
msg["To"] = email_to
msg["Subject"] = subject
msg.attach(MIMEText(text_body, "plain", "utf-8"))
msg.attach(MIMEText(html_body, "html", "utf-8"))

context = ssl.create_default_context()
if smtp_security == "ssl" or smtp_port == 465:
    with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
        server.login(smtp_user, smtp_pass)
        server.sendmail(email_from, [email_to], msg.as_string())
else:
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls(context=context)
        server.login(smtp_user, smtp_pass)
        server.sendmail(email_from, [email_to], msg.as_string())
print("Email summary sent successfully.")
PY
}

main() {
  print_info "== Tele-Op Backend Regression Test Runner =="
  start_backend_if_needed
  ensure_test_venv
  run_pytest
  generate_allure_report
  # 发送基于 allure-results 的测试摘要邮件（包含 xfail 高亮）
  send_email_summary || true
  exit "$PYTEST_EXIT_CODE"
}

main "$@"
