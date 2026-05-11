import os
import requests

api_key = "pxa_IOev_nFUdVD2jc3SfDYdnHOJ4c0cZH2uaeljdE0RLQA"
package_id = "pkg_5jp2OIxaMNK5PIhWywsElBGi"
output_dir = "./dataset"

print("this is the demo python script for downloading data from PrismaX")

session = requests.post(
    "https://app-prismax-data-pipeline-beta-1053158761087.us-west1.run.app/v1/data/download-sessions",
    headers={"X-API-Key": api_key},
    json={"package_id": package_id},
).json()["data"]

for sample in session["samples"]:
    sample_cookie = sample.get("auth", {}).get("cookie_header")
    for asset in sample["assets"].values():
        cookie = asset.get("auth", {}).get("cookie_header", sample_cookie)
        if not cookie:
            raise RuntimeError("missing Cloud CDN cookie for asset")
        target = os.path.join(output_dir, asset["relative_path"])
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with requests.get(asset["url"], headers={"Cookie": cookie}, stream=True) as r:
            r.raise_for_status()
            with open(target, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
