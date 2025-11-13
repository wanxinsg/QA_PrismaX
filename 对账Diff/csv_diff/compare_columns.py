#!/usr/bin/env python3
import argparse
import csv
import os
from typing import Set, Optional

DEFAULT_DB_FILENAMES = {"DB_studio_result.csv", "DB_studio_results.csv"}
DEFAULT_SOLSCAN_FILENAME = "Solscan_export_transfer.csv"


def load_column_values(csv_path: str, column: str) -> Set[str]:
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        sample = f.read(4096)
        f.seek(0)
        sniffer = csv.Sniffer()
        try:
            dialect = sniffer.sniff(sample)
        except csv.Error:
            dialect = csv.excel
        try:
            has_header = sniffer.has_header(sample)
        except csv.Error:
            has_header = True

        reader = csv.reader(f, dialect)
        values: Set[str] = set()

        if has_header:
            try:
                header = next(reader)
            except StopIteration:
                return set()
            header_lower = [h.strip().lower() for h in header]
            try:
                idx = header_lower.index(column.strip().lower())
            except ValueError:
                raise ValueError(
                    f"Column '{column}' not found in {csv_path}. Available columns: {header}"
                )
            for row in reader:
                if not row or idx >= len(row):
                    continue
                v = row[idx].strip()
                if v:
                    values.add(v)
        else:
            for row in reader:
                if not row:
                    continue
                v = row[0].strip()
                if v:
                    values.add(v)
        return values


def write_diff_single_csv(out_path: str, only_in_first: Set[str], only_in_second: Set[str], first_label: str, second_label: str) -> None:
    max_len = max(len(only_in_first), len(only_in_second))
    first_list = sorted(list(only_in_first))
    second_list = sorted(list(only_in_second))
    if len(first_list) < max_len:
        first_list.extend([""] * (max_len - len(first_list)))
    if len(second_list) < max_len:
        second_list.extend([""] * (max_len - len(second_list)))

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([f"only_in_{first_label}", f"only_in_{second_label}"])
        for a, b in zip(first_list, second_list):
            writer.writerow([a, b])


def compute_default_out_path(first_csv: str, second_csv: str, base_dir: str) -> Optional[str]:
    first_base = os.path.basename(first_csv)
    second_base = os.path.basename(second_csv)
    names = {first_base, second_base}
    if (DEFAULT_SOLSCAN_FILENAME in names) and (len(names & DEFAULT_DB_FILENAMES) == 1):
        return os.path.join(base_dir, "diff_Solscan_vs_DB.csv")
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare specified columns from two CSVs and write a single diff CSV.")
    parser.add_argument("first_csv", help="Path to first CSV file")
    parser.add_argument("first_column", help="Column name in first CSV")
    parser.add_argument("second_csv", help="Path to second CSV file")
    parser.add_argument("second_column", help="Column name in second CSV")
    parser.add_argument("--out", help="Output CSV path (default: auto-named in common dir)", default=None)
    parser.add_argument("--first-label", help="Custom label for first column in output header", default=None)
    parser.add_argument("--second-label", help="Custom label for second column in output header", default=None)
    args = parser.parse_args()

    first_values = load_column_values(args.first_csv, args.first_column)
    second_values = load_column_values(args.second_csv, args.second_column)

    only_in_first = first_values - second_values
    only_in_second = second_values - first_values

    base_dir = os.path.dirname(os.path.commonprefix([os.path.abspath(args.first_csv), os.path.abspath(args.second_csv)]))

    out_path = args.out
    if not out_path:
        auto = compute_default_out_path(args.first_csv, args.second_csv, base_dir)
        if auto:
            out_path = auto
        else:
            first_label_for_path = os.path.splitext(os.path.basename(args.first_csv))[0]
            second_label_for_path = os.path.splitext(os.path.basename(args.second_csv))[0]
            out_path = os.path.join(base_dir, f"diff_{first_label_for_path}_{args.first_column}_vs_{second_label_for_path}_{args.second_column}.csv")

    first_label = args.first_label if args.first_label else args.first_column
    second_label = args.second_label if args.second_label else args.second_column

    write_diff_single_csv(out_path, only_in_first, only_in_second, first_label, second_label)

    print("Comparison complete")
    print(f"{args.first_column} total: {len(first_values)} | {args.second_column} total: {len(second_values)}")
    print(f"Only in {first_label}: {len(only_in_first)}")
    print(f"Only in {second_label}: {len(only_in_second)}")
    print(f"Diff written to: {out_path}")


if __name__ == "__main__":
    main()
