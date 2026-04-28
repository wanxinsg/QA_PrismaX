#!/usr/bin/env python3
"""
Generate a human-readable Markdown summary for an MCAP file.

The report includes:
- Topic (channel) information
- Schema information
- Metadata records

By default the output is saved under the local `Reports` directory.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Any, List

from mcap.reader import make_reader


def _safe_decode_schema_data(data: bytes) -> str:
    """Best-effort decode of schema bytes to text."""
    if not data:
        return ""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        # Fallback: replace invalid bytes so that we can still show structure
        return data.decode("utf-8", errors="replace")


def build_markdown_summary(mcap_path: Path) -> str:
    """
    Build a Markdown summary string for the given MCAP file.
    """
    lines: List[str] = []

    lines.append(f"# MCAP Summary: `{mcap_path.name}`")
    lines.append("")
    lines.append(f"- **File path**: `{mcap_path}`")
    lines.append("")

    with mcap_path.open("rb") as f:
        reader = make_reader(f)
        summary = reader.get_summary()

        # ---------------------------
        # Topics / channels
        # ---------------------------
        channels: Dict[int, Any] = getattr(summary, "channels", {}) or {}
        schemas: Dict[int, Any] = getattr(summary, "schemas", {}) or {}

        statistics = getattr(summary, "statistics", None)
        channel_counts: Dict[int, int] = {}
        if statistics is not None:
            channel_counts = getattr(statistics, "channel_message_counts", {}) or {}

        lines.append("## Topics (Channels)")
        if not channels:
            lines.append("_No channels found in this MCAP summary._")
        else:
            lines.append("")
            lines.append(
                "| Channel ID | Topic | Message Encoding | Schema ID | Schema Name | Message Count |"
            )
            lines.append("| --- | --- | --- | --- | --- | --- |")

            for cid, channel in sorted(channels.items(), key=lambda kv: kv[0]):
                topic = getattr(channel, "topic", "")
                msg_enc = getattr(channel, "message_encoding", "")
                schema_id = getattr(channel, "schema_id", None)

                schema_name = ""
                if schema_id is not None and schema_id in schemas:
                    schema_obj = schemas[schema_id]
                    schema_name = getattr(schema_obj, "name", "") or ""

                msg_count = channel_counts.get(cid)

                lines.append(
                    f"| {cid} | `{topic}` | `{msg_enc}` | "
                    f"{schema_id if schema_id is not None else ''} | "
                    f"`{schema_name}` | {msg_count if msg_count is not None else ''} |"
                )

        lines.append("")

    # Re-open reader for schemas & metadata to avoid interaction with previous iteration
    with mcap_path.open("rb") as f2:
        reader2 = make_reader(f2)
        summary2 = reader2.get_summary()
        schemas2: Dict[int, Any] = getattr(summary2, "schemas", {}) or {}

        # ---------------------------
        # Schemas
        # ---------------------------
        lines.append("## Schemas")
        if not schemas2:
            lines.append("_No schemas found in this MCAP summary._")
        else:
            for sid, schema in sorted(schemas2.items(), key=lambda kv: kv[0]):
                name = getattr(schema, "name", "") or ""
                encoding = getattr(schema, "encoding", "") or ""
                data = getattr(schema, "data", b"") or b""

                lines.append("")
                lines.append(f"### Schema {sid}: `{name}`")
                lines.append("")
                lines.append(f"- **Encoding**: `{encoding}`")
                lines.append(f"- **Byte size**: {len(data)}")
                lines.append("")

                decoded = _safe_decode_schema_data(data).strip()
                if decoded:
                    lines.append("```")
                    lines.append(decoded)
                    lines.append("```")
                else:
                    lines.append("_Schema data is empty or non-text/binary._")

        lines.append("")

    # Separate reader for metadata iteration
    with mcap_path.open("rb") as f3:
        reader3 = make_reader(f3)

        lines.append("## Metadata")
        metadata_records: List[Any] = []

        try:
            for record in reader3.iter_metadata():
                metadata_records.append(record)
        except Exception as e:  # pragma: no cover - defensive
            lines.append("")
            lines.append(f"_Failed to read metadata: {e}_")
            return "\n".join(lines)

        if not metadata_records:
            lines.append("")
            lines.append("_No metadata records found in this MCAP file._")
        else:
            # Individual records
            merged: Dict[str, Any] = {}
            lines.append("")
            lines.append(f"- **Total metadata records**: {len(metadata_records)}")
            lines.append("")

            for idx, rec in enumerate(metadata_records, start=1):
                name = getattr(rec, "name", "") or ""
                md: Dict[str, Any] = getattr(rec, "metadata", {}) or {}

                # Merge for later
                merged.update(md)

                lines.append(f"### Metadata record {idx}")
                lines.append("")
                if name:
                    lines.append(f"- **Name**: `{name}`")

                if md:
                    lines.append("")
                    lines.append("| Key | Value |")
                    lines.append("| --- | --- |")
                    for k, v in sorted(md.items(), key=lambda kv: kv[0]):
                        lines.append(f"| `{k}` | `{v}` |")
                else:
                    lines.append("")
                    lines.append("_This metadata record has no key-value fields._")

                lines.append("")

            # Merged view
            if merged:
                lines.append("### Merged metadata fields")
                lines.append("")
                lines.append("| Key | Value |")
                lines.append("| --- | --- |")
                for k, v in sorted(merged.items(), key=lambda kv: kv[0]):
                    lines.append(f"| `{k}` | `{v}` |")
                lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dump MCAP topics, schemas, and metadata to a Markdown report.",
    )
    parser.add_argument(
        "mcap_path",
        help="Path to the MCAP file or a directory containing MCAP files",
    )
    parser.add_argument(
        "-o",
        "--output",
        help=(
            "Output Markdown path. "
            "If relative, it will be created under the local Reports directory."
        ),
    )

    args = parser.parse_args()
    target = Path(args.mcap_path).expanduser()

    if not target.exists():
        raise SystemExit(f"MCAP path not found: {target}")

    # Reports directory under this tool's root (QA_Mcap_Checker/Reports)
    project_root = Path(__file__).parent
    reports_dir = project_root / "Reports"
    reports_dir.mkdir(exist_ok=True, parents=True)

    # If a directory is given, process all *.mcap files inside it.
    if target.is_dir():
        mcap_files = sorted(target.glob("*.mcap"))
        if not mcap_files:
            raise SystemExit(f"No *.mcap files found in directory: {target}")

        for mcap_file in mcap_files:
            markdown = build_markdown_summary(mcap_file)
            out_path = reports_dir / f"{mcap_file.stem}_mcap_summary.md"
            out_path.write_text(markdown, encoding="utf-8")
            print(f"Markdown summary written to: {out_path}")
    else:
        mcap_path = target

        if args.output:
            out_path = Path(args.output)
            if not out_path.is_absolute():
                out_path = reports_dir / out_path
        else:
            out_path = reports_dir / f"{mcap_path.stem}_mcap_summary.md"

        markdown = build_markdown_summary(mcap_path)
        out_path.write_text(markdown, encoding="utf-8")

        print(f"Markdown summary written to: {out_path}")


if __name__ == "__main__":
    main()

