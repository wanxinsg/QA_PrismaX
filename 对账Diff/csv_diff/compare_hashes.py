#!/usr/bin/env python3
import argparse
import csv
import os
from typing import Set, Optional, List
import time; time.sleep(2)
import sys; print(sys.gettrace())
print("烦躁 first Reached before breakpoint")
import sys, pydevd
print("Before patch:", sys.gettrace())
pydevd.settrace(suspend=True)
print("After patch:", sys.gettrace())


def detect_hash_column(fieldnames: List[str]) -> int:
    if not fieldnames:
        raise ValueError("CSV has no header/columns")
    # No auto-detection: default to first column
    return 0


def load_hashes(csv_path: str, column: Optional[str] = None) -> Set[str]:
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        sniffer = csv.Sniffer()
        sample = f.read(2048)
        f.seek(0)
        try:
            has_header = sniffer.has_header(sample)
        except csv.Error:
            has_header = False
        # If a specific column name is requested, force header-based parsing even if sniffer fails
        if column is not None:
            has_header = True
        try:
            dialect = sniffer.sniff(sample)
        except csv.Error:
            dialect = csv.excel

        reader = csv.reader(f, dialect)
        hashes: Set[str] = set()

        if has_header:
            try:
                header = next(reader)
            except StopIteration:
                return set()
            if column is not None:
                try:
                    normalized_header = [h.strip().lstrip("\ufeff").lower() for h in header]
                    col_index = normalized_header.index(column.strip().lower())
                except ValueError:
                    raise ValueError(
                        f"Column '{column}' not found in {csv_path}. Available: {header}"
                    )
            else:
                col_index = detect_hash_column(header)
            for row in reader:
                if not row:
                    continue
                if col_index >= len(row):
                    continue
                value = row[col_index].strip()
                if value:
                    hashes.add(value)
        else:
            # No header: assume single-column of hashes, or use first column
            for row in reader:
                if not row:
                    continue
                value = row[0].strip()
                if value:
                    hashes.add(value)

        return hashes


def write_list(csv_path: str, values: Set[str]) -> None:
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["hash"])  # header
        for v in sorted(values):
            writer.writerow([v])


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two CSVs of transaction hashes and output diffs.")
    parser.add_argument("db_csv", help="Path to DB CSV file (list of hashes)")
    parser.add_argument("onchain_csv", help="Path to on-chain CSV file (list of hashes)")
    parser.add_argument(
        "-D", "--db-column",
        help="DB CSV column name to read key from (case-insensitive). If omitted, use the first column.",
        default=None,
    )
    parser.add_argument(
        "-O", "--onchain-column",
        help="On-chain CSV column name to read key from (case-insensitive). If omitted, use the first column.",
        default=None,
    )
    parser.add_argument("--out-prefix", help="Output file prefix (default: diff_)\nCreates '<prefix>db_minus_onchain.csv' and '<prefix>onchain_minus_db.csv'", default="diff_")
    args = parser.parse_args()
    print("烦躁Reached before breakpoint")
    db_hashes = load_hashes(args.db_csv, args.db_column)
    onchain_hashes = load_hashes(args.onchain_csv, args.onchain_column)

    only_in_db = db_hashes - onchain_hashes
    only_onchain = onchain_hashes - db_hashes
    in_both = db_hashes & onchain_hashes

    base_dir = os.path.dirname(os.path.commonprefix([os.path.abspath(args.db_csv), os.path.abspath(args.onchain_csv)]))
    out_db_minus_onchain = os.path.join(base_dir, f"{args.out_prefix}db_minus_onchain.csv")
    out_onchain_minus_db = os.path.join(base_dir, f"{args.out_prefix}onchain_minus_db.csv")

    write_list(out_db_minus_onchain, only_in_db)
    write_list(out_onchain_minus_db, only_onchain)

    print("Comparison complete")
    print(f"DB total: {len(db_hashes)} | On-chain total: {len(onchain_hashes)}")
    print(f"In both: {len(in_both)}")
    print(f"Only in DB: {len(only_in_db)} -> {out_db_minus_onchain}")
    print(f"Only on-chain: {len(only_onchain)} -> {out_onchain_minus_db}")


if __name__ == "__main__":
    main()
