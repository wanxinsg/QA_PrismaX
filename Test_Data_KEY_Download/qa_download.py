import os
import time

import requests

api_key = "pxa_9qGw9xrTz_mD4h5KuDH35ujPLozkQp_REpcihzw4xTw"
package_id = "pkg_5jp2OIxaMNK5PIhWywsElBGi"
output_dir = "./qadataset1"

CREATE_SESSION_URL = "https://data.prismaxserver.com/v1/data/download-sessions"

# Origin can be slow behind Cloudflare; short client timeouts yield empty/HTML 524 bodies.
CONNECT_TIMEOUT_S = 30
READ_TIMEOUT_S = 600
RETRYABLE_STATUS = {502, 503, 504, 524}
RETRY_BACKOFF_S = [4, 10, 25, 60]


def create_download_session():
    timeout = (CONNECT_TIMEOUT_S, READ_TIMEOUT_S)
    last_resp = None
    for attempt, delay in enumerate([0] + RETRY_BACKOFF_S):
        if delay:
            print(f"Retrying download-session create in {delay}s (attempt {attempt + 1})...")
            time.sleep(delay)
        try:
            last_resp = requests.post(
                CREATE_SESSION_URL,
                headers={"X-API-Key": api_key},
                json={"package_id": package_id},
                timeout=timeout,
            )
        except requests.Timeout as e:
            print(f"Request timed out: {e}")
            if attempt == len(RETRY_BACKOFF_S):
                raise
            continue

        if last_resp.status_code in RETRYABLE_STATUS:
            print(
                f"Server returned HTTP {last_resp.status_code}; "
                f"{last_resp.headers.get('content-type', '')!r}"
            )
            if attempt == len(RETRY_BACKOFF_S):
                last_resp.raise_for_status()
            continue

        last_resp.raise_for_status()
        try:
            body = last_resp.json()
        except requests.JSONDecodeError as e:
            snippet = (last_resp.text or "")[:400]
            raise RuntimeError(
                "download-sessions response was not JSON "
                f"(status={last_resp.status_code}, "
                f"content-type={last_resp.headers.get('content-type')!r}). "
                f"Body starts with: {snippet!r}"
            ) from e
        return body["data"]

    raise RuntimeError(
        "Failed to create download session after "
        f"{len(RETRY_BACKOFF_S) + 1} attempts "
        f"(last status={getattr(last_resp, 'status_code', None)})"
    )


def human_size(num_bytes):
    if num_bytes is None:
        return "unknown"
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.2f} {unit}"
        size /= 1024


print("Creating download session...")
download_session = create_download_session()

download_id = download_session.get("download_id")
samples = download_session["samples"]
total_samples = len(samples)
print(f"download_id={download_id!r}")
print(f"Got {total_samples} sample(s) in this session.")

grand_total_bytes = 0
for idx, sample in enumerate(samples, start=1):
    sample_cookie = sample.get("auth", {}).get("cookie_header")
    upload_id = sample.get("upload_id")
    episode_key = sample.get("episode_key")
    assets = sample.get("assets", {})

    print(
        f"\n[Sample {idx}/{total_samples}] "
        f"upload_id={upload_id!r}, episode_key={episode_key!r}, "
        f"assets={len(assets)}"
    )

    prefix = (
        os.path.join(output_dir, str(upload_id)) if upload_id is not None else output_dir
    )

    sample_total_bytes = 0
    for asset in assets.values():
        cookie = asset.get("auth", {}).get("cookie_header", sample_cookie)
        if not cookie:
            raise RuntimeError("missing Cloud CDN cookie for asset")
        target = os.path.join(prefix, asset["relative_path"])
        os.makedirs(os.path.dirname(target), exist_ok=True)
        rel = asset["relative_path"]
        print(f"  Downloading {rel!r} ...")
        bytes_written = 0
        with requests.get(
            asset["url"],
            headers={"Cookie": cookie},
            stream=True,
            timeout=(CONNECT_TIMEOUT_S, READ_TIMEOUT_S),
        ) as r:
            r.raise_for_status()
            content_length = r.headers.get("Content-Length")
            expected = int(content_length) if content_length is not None else None
            with open(target, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        bytes_written += len(chunk)
        sample_total_bytes += bytes_written
        size_str = human_size(bytes_written)
        if expected is not None and expected != bytes_written:
            size_str += f" (expected {human_size(expected)})"
        print(f"    saved {target} ({size_str})")

    grand_total_bytes += sample_total_bytes
    print(
        f"[Sample {idx}/{total_samples}] done. "
        f"upload_id={upload_id!r}, episode_key={episode_key!r}, "
        f"total size={human_size(sample_total_bytes)}"
    )

print(
    f"\nFinished {total_samples} sample(s) for download_id={download_id!r}. "
    f"Grand total downloaded: {human_size(grand_total_bytes)}"
)
