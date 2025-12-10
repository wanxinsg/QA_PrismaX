#!/usr/bin/env bash
set -euo pipefail

# Configuration
TEST_ENV_DIR="/Users/wanxin/PycharmProjects/Prismax/QA_PrismaX/Test_Env"
BACKEND_DIR="/Users/wanxin/PycharmProjects/Prismax/app-prismax-rp-backend/app_prismax_tele_op_services"
ALLURE_RESULTS_DIR="$TEST_ENV_DIR/test_report/allure-results"
BACKEND_LOG="$TEST_ENV_DIR/backend.log"
TEST_SRC_DIR="/Users/wanxin/PycharmProjects/Prismax/QA_PrismaX/QA_Test"

# Defaults (can be overridden by env)
# Hardcoded test target (requested)
TELE_HOST="localhost"
TELE_PORT="8081"
ROBOT_ID="arm1"
ROBOT_IDS="${ROBOT_IDS:-arm1,arm2,arm3}"
GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-thepinai}"
GOOGLE_APPLICATION_CREDENTIALS="${GOOGLE_APPLICATION_CREDENTIALS:-/Users/wanxin/PycharmProjects/Prismax/thepinai-compute-key.json}"

# Required credentials for tests
USER_ID="1073381"
TOKEN="bYtYp1ZAje06q2IZy6RfuVyMIOmSH2KEqT1YXjKj-64"

# Note: Values are hardcoded for convenience per request. Remove above and restore env reads for flexibility.

# Track pytest exit code but do not abort subsequent steps (report generation/serving)
PYTEST_EXIT_CODE=0

echo "==> Using Tele-Op backend: http://${TELE_HOST}:${TELE_PORT} robots=${ROBOT_IDS}"

wait_for_engineio() {
  local host="$1"
  local port="$2"
  local max_wait="${3:-60}"
  local url="http://${host}:${port}/socket.io/?EIO=4&transport=polling"
  echo "==> Waiting for Engine.IO at ${url} (timeout ${max_wait}s)..."
  local start_ts
  start_ts="$(date +%s)"
  while true; do
    if curl -s -m 2 -o /dev/null -w "%{http_code}" "$url" | grep -qE "200|204"; then
      echo "==> Engine.IO endpoint is up."
      return 0
    fi
    local now_ts
    now_ts="$(date +%s)"
    if (( now_ts - start_ts >= max_wait )); then
      echo "ERROR: Engine.IO endpoint did not become ready within ${max_wait}s."
      return 1
    fi
    sleep 1
  done
}

start_backend_if_needed() {
  if wait_for_engineio "$TELE_HOST" "$TELE_PORT" 1; then
    echo "==> Backend already running; skipping start."
    return 0
  fi

  echo "==> Starting backend in background... Logs: $BACKEND_LOG"
  # Use bash -lc to ensure 'source' is available and venv activation works
  nohup bash -lc "cd \"$BACKEND_DIR\" && \
    source .venv/bin/activate && \
    TEST_MODE=true GOOGLE_CLOUD_PROJECT=\"$GOOGLE_CLOUD_PROJECT\" \
    GOOGLE_APPLICATION_CREDENTIALS=\"$GOOGLE_APPLICATION_CREDENTIALS\" \
    PORT=\"$TELE_PORT\" python app.py" \
    > \"$BACKEND_LOG\" 2>&1 &

  # Wait up to 90s for server to become ready
  wait_for_engineio "$TELE_HOST" "$TELE_PORT" 90
}

run_tests_for_robot() {
  local robot_id="$1"
  local results_dir="$ALLURE_RESULTS_DIR/$robot_id"
  echo "==> Running pytest from: $TEST_SRC_DIR (robot: $robot_id)"
  echo "==> Collecting Allure results into: $results_dir"
  mkdir -p "$results_dir"
  # Clear previous results to ensure counts reflect only this run
  rm -rf "$results_dir"/* || true
  set +e
  TELE_HOST="$TELE_HOST" TELE_PORT="$TELE_PORT" ROBOT_ID="$robot_id" USER_ID="$USER_ID" TOKEN="$TOKEN" \
    python3 -m pytest -q "$TEST_SRC_DIR" -c "$TEST_SRC_DIR/pytest.ini" --alluredir="$results_dir"
  local code=$?
  set -e
  echo "==> Pytest finished (robot: $robot_id) with exit code: $code"
  # Track worst exit code across robots
  if [[ "$code" -ne 0 ]]; then
    PYTEST_EXIT_CODE="$code"
  fi
}

open_allure_report() {
  # In interactive terminals, default to serving; in cron/non-interactive, default to static generate.
  # Override with ALLURE_SERVE=1 (serve) or 0 (generate).
  local output_dir="${ALLURE_OUTPUT_DIR:-$TEST_ENV_DIR/test_report/allure-report}"
  local serve_default=0
  if [ -t 1 ]; then
    serve_default=1
  fi
  local use_serve="${ALLURE_SERVE:-$serve_default}"
  if [[ "$use_serve" == "1" ]]; then
    if command -v allure >/dev/null 2>&1; then
      echo "==> Launching Allure report server..."
      # Collect all robot-specific results directories; fallback to root if none
      local inputs=()
      local has_subdirs=0
      if [ -d "$ALLURE_RESULTS_DIR" ]; then
        for d in "$ALLURE_RESULTS_DIR"/*; do
          if [ -d "$d" ]; then
            inputs+=("$d")
            has_subdirs=1
          fi
        done
      fi
      if [[ "$has_subdirs" -eq 0 ]]; then
        inputs+=("$ALLURE_RESULTS_DIR")
      fi
      allure serve "${inputs[@]}"
    else
      echo "==> Allure CLI not found."
      echo "Install with one of the following and rerun this script:"
      echo "  brew install allure"
      echo "  # or"
      echo "  npm i -g allure-commandline"
      echo "Allure results are at: $ALLURE_RESULTS_DIR"
    fi
  else
    if command -v allure >/dev/null 2>&1; then
      echo "==> Generating Allure static report into: $output_dir"
      mkdir -p "$output_dir"
      # Expose for downstream steps (email, static server)
      ALLURE_REPORT_DIR="$output_dir"
      # Collect all robot-specific results directories; fallback to root if none
      local inputs=()
      local has_subdirs=0
      if [ -d "$ALLURE_RESULTS_DIR" ]; then
        for d in "$ALLURE_RESULTS_DIR"/*; do
          if [ -d "$d" ]; then
            inputs+=("$d")
            has_subdirs=1
          fi
        done
      fi
      if [[ "$has_subdirs" -eq 0 ]]; then
        inputs+=("$ALLURE_RESULTS_DIR")
      fi
      allure generate "${inputs[@]}" --clean -o "$output_dir" || {
        echo "WARN: Allure generate failed; results remain at: $ALLURE_RESULTS_DIR"
      }
      # After generation, optionally email the zipped report
      send_email_with_report "$output_dir" || true
      # In cron/non-interactive environments, optionally start a background static server
      # to provide a visual report without blocking the cron job.
      local serve_static_default=0
      if [ ! -t 1 ]; then
        serve_static_default=1
      fi
      local run_static_server="${CRON_STATIC_SERVER:-$serve_static_default}"
      if [[ "$run_static_server" == "1" ]]; then
        local port="${ALLURE_PORT:-9999}"
        local server_log="$TEST_ENV_DIR/test_report/static-server.log"
        local server_pid_file="$TEST_ENV_DIR/test_report/static-server.pid"
        mkdir -p "$(dirname "$server_log")"
        echo "==> Starting background static server for Allure at http://localhost:${port}"
        # Attempt to free port if something else is bound
        if command -v lsof >/dev/null 2>&1; then
          lsof -ti tcp:"$port" | xargs -r kill -9 || true
        fi
        # Prefer python's http.server; fallback to npx http-server if available
        if command -v python3 >/dev/null 2>&1; then
          nohup python3 -m http.server "$port" --directory "$output_dir" >> "$server_log" 2>&1 &
          echo $! > "$server_pid_file"
          echo "==> Allure report served (python) at http://localhost:${port} (pid $(cat "$server_pid_file"))"
        elif command -v npx >/dev/null 2>&1; then
          nohup npx --yes http-server "$output_dir" -p "$port" >> "$server_log" 2>&1 &
          echo $! > "$server_pid_file"
          echo "==> Allure report served (http-server) at http://localhost:${port} (pid $(cat "$server_pid_file"))"
        else
          echo "WARN: No static server found (python3/npx). Report files at: $output_dir"
          echo "      Install python3 or 'npm i -g http-server' to auto-serve in cron."
        fi
      fi
    else
      echo "==> Allure CLI not found; skipping report generation."
      echo "Allure results are at: $ALLURE_RESULTS_DIR"
    fi
  fi
}

send_email_with_report() {
  local report_dir="$1"
  local smtp_host="${SMTP_HOST:-mail.privateemail.com}"
  local smtp_port="${SMTP_PORT:-465}"
  local smtp_security="${SMTP_SECURITY:-ssl}" # ssl | starttls
  local smtp_user="${SMTP_USER:-}"
  local smtp_pass="${SMTP_PASS:-}"
  local email_to="${EMAIL_TO:-wanxin@solidcap.io}"
  local email_from="${EMAIL_FROM:-$smtp_user}"
  local subject="${EMAIL_SUBJECT:-Prismax QA Daily Report}"
  local body="${EMAIL_BODY:-Please find the attached Allure report. Local server: http://localhost:${ALLURE_PORT:-9999}}"

  if [ -z "$smtp_user" ] || [ -z "$smtp_pass" ]; then
    echo "==> SMTP_USER/SMTP_PASS not set; skipping email."
    return 0
  fi

  echo "==> Sending email report to: $email_to via $smtp_host:$smtp_port"
  RESULTS_BASE="$ALLURE_RESULTS_DIR" REPORT_URL="http://localhost:${ALLURE_PORT:-9999}" \
  python3 - <<PY || { echo "WARN: Email sending failed"; return 1; }
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
subject = os.environ.get("EMAIL_SUBJECT", "Prismax QA Daily Report")
results_base = os.environ.get("RESULTS_BASE", "")
report_url = os.environ.get("REPORT_URL", "http://localhost:9999")

if not smtp_user or not smtp_pass:
    sys.exit(0)

def summarize_results(base_dir: str):
    if not base_dir or not os.path.isdir(base_dir):
        return "No results found.", {}
    entries = [os.path.join(base_dir, d) for d in os.listdir(base_dir)]
    subdirs = [d for d in entries if os.path.isdir(d)]
    if not subdirs:
        subdirs = [base_dir]
    overall = {"passed": 0, "failed": 0, "skipped": 0, "xfailed": 0, "broken": 0}
    per_robot = {}
    failures = []
    xfails = []
    skips = []
    for d in sorted(subdirs):
        robot = os.path.basename(d) if d != base_dir else "all"
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
            # Normalize statuses, detect xfail (pytest marks as skipped with message containing XFAIL)
            is_xfail = False
            if status == "skipped":
                lm = message.lower()
                if "xfail" in lm or "expected failure" in lm:
                    is_xfail = True
            if status == "passed":
                counts["passed"] += 1
            elif status == "failed":
                counts["failed"] += 1
                failures.append(f"- [{robot}] {name}: {message or status}")
            elif status == "broken":
                counts["broken"] += 1
                failures.append(f"- [{robot}] {name}: {message or status}")
            elif status == "skipped":
                if is_xfail:
                    counts["xfailed"] += 1
                    xfails.append(f"- [{robot}] {name}: {message or 'xfail'}")
                else:
                    counts["skipped"] += 1
                    # Record skipped reason (non-xfail)
                    skips.append(f"- [{robot}] {name}: {message or 'skipped'}")
        per_robot[robot] = counts
        for k, v in counts.items():
            overall[k] = overall.get(k, 0) + v
    # Build plain text body
    text_lines = []
    text_lines.append("Prismax QA Daily Report")
    text_lines.append(f"Report: {report_url}")
    text_lines.append("")
    text_lines.append("Overall:")
    text_lines.append(f"  passed={overall.get('passed',0)} failed={overall.get('failed',0)} skipped={overall.get('skipped',0)} xfailed={overall.get('xfailed',0)} broken={overall.get('broken',0)}")
    text_lines.append("")
    text_lines.append("Per Robot:")
    for r, c in per_robot.items():
        text_lines.append(f"  {r}: passed={c.get('passed',0)} failed={c.get('failed',0)} skipped={c.get('skipped',0)} xfailed={c.get('xfailed',0)} broken={c.get('broken',0)}")
    text_lines.append("")
    if xfails:
        text_lines.append("Xfails (expected failures):")
        text_lines.extend(xfails[:50])
        text_lines.append("")
    if failures:
        text_lines.append("Failures:")
        text_lines.extend(failures[:50])
    if skips:
        text_lines.append("")
        text_lines.append("Skipped:")
        text_lines.extend(skips[:50])
    # Build HTML body (with red Xfails header)
    html = []
    html.append("<html><body style=\"font-family: -apple-system, Arial, sans-serif; font-size:14px; color:#222;\">")
    html.append("<h3 style=\"margin:0 0 8px 0;\">Prismax QA Daily Report</h3>")
    html.append(f"<div style=\"margin:4px 0 12px 0;\">Report: <a href=\"{report_url}\">{report_url}</a></div>")
    html.append("<div style=\"margin:6px 0;\"><b>Overall:</b><br/>")
    html.append(f"<code>passed={overall.get('passed',0)} failed={overall.get('failed',0)} skipped={overall.get('skipped',0)} xfailed={overall.get('xfailed',0)} broken={overall.get('broken',0)}</code></div>")
    html.append("<div style=\"margin:6px 0;\"><b>Per Robot:</b><br/><ul style=\"margin:6px 0 0 18px;\">")
    for r, c in per_robot.items():
        html.append(f"<li><code>{r}: passed={c.get('passed',0)} failed={c.get('failed',0)} skipped={c.get('skipped',0)} xfailed={c.get('xfailed',0)} broken={c.get('broken',0)}</code></li>")
    html.append("</ul></div>")
    if xfails:
        html.append("<div style=\"margin:10px 0;\"><b><span style=\"color:#d32f2f;\">Xfails (expected failures):</span></b><ul style=\"margin:6px 0 0 18px;\">")
        for x in xfails[:50]:
            html.append(f"<li><code>{x}</code></li>")
        html.append("</ul></div>")
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
    html.append("</body></html>")
    return "\n".join(text_lines), "".join(html), {"overall": overall, "per_robot": per_robot}

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
print("Email sent successfully.")
PY
}

main() {
  start_backend_if_needed
  # Iterate over configured robots (comma-separated list)
  IFS=',' read -r -a robots <<< "$ROBOT_IDS"
  for r in "${robots[@]}"; do
    r_trimmed="$(echo "$r" | xargs)"
    [ -z "$r_trimmed" ] && continue
    run_tests_for_robot "$r_trimmed"
  done
  open_allure_report
  # Propagate pytest status to caller, but only after report is prepared/served
  exit "$PYTEST_EXIT_CODE"
}

main "$@"


