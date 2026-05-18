#!/usr/bin/env python3
import argparse
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request

try:
    import certifi
except ImportError:
    certifi = None


def build_ssl_context():
    if certifi is not None:
        return ssl.create_default_context(cafile=certifi.where())
    return ssl.create_default_context()


SSL_CONTEXT = build_ssl_context()


def print_ssl_help():
    print(
        "\nSSL certificate verification failed. This is usually a local Python certificate setup issue, not a problem with the signed URL.",
        file=sys.stderr,
    )
    print("Try one of these fixes:", file=sys.stderr)
    print("  1. python3 -m pip install certifi", file=sys.stderr)
    print("  2. Re-run this script after activating a virtualenv with certifi installed", file=sys.stderr)
    print("  3. On macOS python.org builds, run the bundled 'Install Certificates.command'", file=sys.stderr)


def download_file(url, destination, retries=3):
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    if os.path.exists(destination) and os.path.getsize(destination) > 0:
        print(f"Skipping existing file: {destination}")
        return

    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(url, context=SSL_CONTEXT, timeout=60) as response, open(destination, "wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
            print(f"Downloaded: {destination}")
            return
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            if "CERTIFICATE_VERIFY_FAILED" in str(exc) or isinstance(getattr(exc, "reason", None), ssl.SSLCertVerificationError):
                print_ssl_help()
            if attempt == retries:
                raise
            print(f"Retry {attempt}/{retries} after error downloading {destination}: {exc}")
            time.sleep(min(2 ** attempt, 10))


def main():
    parser = argparse.ArgumentParser(description="Download PrismaX data from a manifest.json file.")
    parser.add_argument("--manifest", required=True, help="Path to manifest.json")
    parser.add_argument("--output", required=True, help="Output directory")
    args = parser.parse_args()

    with open(args.manifest, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)

    samples = manifest.get("samples") or []
    if not samples:
        print("No samples found in manifest.")
        return

    for sample in samples:
        upload_id = sample.get("upload_id")
        episode_key = sample.get("episode_key")
        sample_folder = os.path.join(args.output, f"upload_{upload_id}", str(episode_key))
        assets = sample.get("assets") or {}
        for asset_name, asset_data in assets.items():
            url = asset_data.get("url")
            relative_path = asset_data.get("relative_path")
            if not url or not relative_path:
                continue
            destination = os.path.join(sample_folder, relative_path)
            download_file(url, destination)


if __name__ == "__main__":
    main()
