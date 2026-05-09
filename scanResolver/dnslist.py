#!/usr/bin/env python3
"""Extract, clean, sort, and split IPv4/CIDR DNS resolver lists."""

from __future__ import annotations

import argparse
import ipaddress
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator

DEFAULT_SPLIT = 100_000
WARN_EXPANDED_OVER = 1_000_000
OUTPUT_PREFIX = "dnsList"
SUMMARY_FILE = "summary.txt"

# Broad candidate finder; ipaddress performs the strict validation later.
CANDIDATE_RE = re.compile(r"(?<![0-9A-Fa-f:.])(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?(?![0-9A-Fa-f:.])")


@dataclass
class Stats:
    files_requested: int = 0
    files_read: int = 0
    files_missing: int = 0
    candidates_seen: int = 0
    invalid_skipped: int = 0
    raw_plain_ips: int = 0
    raw_cidrs: int = 0
    slash31_to_plain: int = 0
    slash32_to_plain: int = 0
    duplicate_plain_removed: int = 0
    duplicate_cidr_removed: int = 0
    plain_inside_cidr_removed: int = 0
    cidrs_before_collapse: int = 0
    cidrs_after_collapse: int = 0
    estimated_output_lines: int = 0
    output_files: int = 0


def ip_to_int(ip: ipaddress.IPv4Address) -> int:
    return int(ip)


def network_key(net: ipaddress.IPv4Network) -> tuple[int, int]:
    return int(net.network_address), net.prefixlen


def forgiving_text(path: Path) -> Iterator[str]:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            yield line


def parse_inputs(paths: list[Path], stats: Stats) -> tuple[set[ipaddress.IPv4Address], list[ipaddress.IPv4Network]]:
    plain_ips: set[ipaddress.IPv4Address] = set()
    cidrs: list[ipaddress.IPv4Network] = []
    seen_cidrs: set[ipaddress.IPv4Network] = set()

    stats.files_requested = len(paths)

    for path in paths:
        if not path.is_file():
            stats.files_missing += 1
            print(f"Warning: input file not found or not a file: {path}")
            continue

        stats.files_read += 1
        for line in forgiving_text(path):
            for match in CANDIDATE_RE.finditer(line):
                token = match.group(0)
                stats.candidates_seen += 1

                try:
                    if "/" in token:
                        net = ipaddress.ip_network(token, strict=False)
                        if net.version != 4:
                            stats.invalid_skipped += 1
                            continue

                        if net.prefixlen == 32:
                            stats.slash32_to_plain += 1
                            before = len(plain_ips)
                            plain_ips.add(net.network_address)
                            if len(plain_ips) > before:
                                stats.raw_plain_ips += 1
                            continue

                        if net.prefixlen == 31:
                            stats.slash31_to_plain += 1
                            before = len(plain_ips)
                            plain_ips.update(net)
                            stats.raw_plain_ips += len(plain_ips) - before
                            continue

                        stats.raw_cidrs += 1
                        if net not in seen_cidrs:
                            cidrs.append(net)
                            seen_cidrs.add(net)
                        else:
                            stats.duplicate_cidr_removed += 1
                    else:
                        ip = ipaddress.ip_address(token)
                        if ip.version != 4:
                            stats.invalid_skipped += 1
                            continue
                        before = len(plain_ips)
                        plain_ips.add(ip)
                        if len(plain_ips) > before:
                            stats.raw_plain_ips += 1
                        else:
                            stats.duplicate_plain_removed += 1
                except ValueError:
                    stats.invalid_skipped += 1

    stats.cidrs_before_collapse = len(cidrs)
    return plain_ips, cidrs


def collapse_cidrs(cidrs: Iterable[ipaddress.IPv4Network], stats: Stats) -> list[ipaddress.IPv4Network]:
    collapsed = list(ipaddress.collapse_addresses(cidrs))
    collapsed.sort(key=network_key)
    stats.cidrs_after_collapse = len(collapsed)
    return collapsed


def remove_plain_inside_cidrs(
    plain_ips: set[ipaddress.IPv4Address], cidrs: list[ipaddress.IPv4Network], stats: Stats
) -> list[ipaddress.IPv4Address]:
    if not plain_ips or not cidrs:
        return sorted(plain_ips, key=ip_to_int)

    kept: list[ipaddress.IPv4Address] = []
    cidr_index = 0
    sorted_ips = sorted(plain_ips, key=ip_to_int)
    sorted_cidrs = sorted(cidrs, key=lambda n: int(n.broadcast_address))

    for ip in sorted_ips:
        ip_int = int(ip)
        while cidr_index < len(sorted_cidrs) and int(sorted_cidrs[cidr_index].broadcast_address) < ip_int:
            cidr_index += 1

        covered = False
        for net in sorted_cidrs[cidr_index:]:
            if int(net.network_address) > ip_int:
                break
            if ip in net:
                covered = True
                break

        if covered:
            stats.plain_inside_cidr_removed += 1
        else:
            kept.append(ip)

    return kept


def usable_count(net: ipaddress.IPv4Network) -> int:
    # /31 and /32 are converted to plain IPs earlier, so normal CIDRs exclude endpoints.
    if net.prefixlen >= 31:
        return net.num_addresses
    return max(0, net.num_addresses - 2)


def iter_usable_hosts(net: ipaddress.IPv4Network) -> Iterator[ipaddress.IPv4Address]:
    if net.prefixlen >= 31:
        yield from net
        return
    first = int(net.network_address) + 1
    last = int(net.broadcast_address) - 1
    for value in range(first, last + 1):
        yield ipaddress.IPv4Address(value)


def estimate_lines(plain_ips: list[ipaddress.IPv4Address], cidrs: list[ipaddress.IPv4Network], cidr_mode: bool) -> int:
    if cidr_mode:
        return len(plain_ips) + len(cidrs)
    return len(plain_ips) + sum(usable_count(net) for net in cidrs)


def iter_output_items(
    plain_ips: list[ipaddress.IPv4Address], cidrs: list[ipaddress.IPv4Network], cidr_mode: bool
) -> Iterator[str]:
    if cidr_mode:
        entries: list[tuple[int, int, str]] = []
        entries.extend((int(ip), 32, str(ip)) for ip in plain_ips)
        entries.extend((int(net.network_address), net.prefixlen, str(net)) for net in cidrs)
        for _, _, item in sorted(entries):
            yield item
        return

    ip_ranges: list[tuple[int, int]] = []
    ip_ranges.extend((int(ip), int(ip)) for ip in plain_ips)
    for net in cidrs:
        if usable_count(net) <= 0:
            continue
        if net.prefixlen >= 31:
            start = int(net.network_address)
            end = int(net.broadcast_address)
        else:
            start = int(net.network_address) + 1
            end = int(net.broadcast_address) - 1
        ip_ranges.append((start, end))

    ip_ranges.sort()
    last_written: int | None = None
    for start, end in ip_ranges:
        if last_written is not None and start <= last_written:
            start = last_written + 1
        for value in range(start, end + 1):
            yield str(ipaddress.IPv4Address(value))
            last_written = value


def write_outputs(items: Iterator[str], out_dir: Path, split_size: int, stats: Stats) -> None:
    part = 1
    current: list[str] = []

    def flush(lines: list[str], part_number: int) -> None:
        filename = f"{OUTPUT_PREFIX}Part{part_number}ipSum{len(lines)}.txt"
        with (out_dir / filename).open("w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(lines))
            handle.write("\n")
        stats.output_files += 1
        print(f"Wrote {filename}")

    for item in items:
        current.append(item)
        if len(current) >= split_size:
            flush(current, part)
            part += 1
            current = []

    if current:
        flush(current, part)


def make_timestamp_dir() -> Path:
    while True:
        out_dir = Path(datetime.now().strftime("%Y%m%d%H%M%S"))
        try:
            out_dir.mkdir(exist_ok=False)
            return out_dir
        except FileExistsError:
            # Avoid a rare collision if the tool is started twice in the same second.
            time.sleep(1)


def build_summary(stats: Stats, out_dir: Path | None, cidr_mode: bool, split_size: int) -> str:
    mode = "keep CIDRs" if cidr_mode else "expanded plain IPs"
    lines = [
        "dnslist summary",
        f"Mode: {mode}",
        f"Split size: {split_size}",
        f"Output folder: {out_dir if out_dir else 'none'}",
        f"Files requested: {stats.files_requested}",
        f"Files read: {stats.files_read}",
        f"Files missing/skipped: {stats.files_missing}",
        f"Candidates seen: {stats.candidates_seen}",
        f"Invalid candidates skipped: {stats.invalid_skipped}",
        f"Unique plain IPs before CIDR coverage removal: {stats.raw_plain_ips}",
        f"Raw CIDRs seen: {stats.raw_cidrs}",
        f"/31 converted to plain IP records: {stats.slash31_to_plain}",
        f"/32 converted to plain IP records: {stats.slash32_to_plain}",
        f"Duplicate plain IPs removed while reading: {stats.duplicate_plain_removed}",
        f"Duplicate CIDRs removed while reading: {stats.duplicate_cidr_removed}",
        f"CIDRs before collapse: {stats.cidrs_before_collapse}",
        f"CIDRs after collapse/merge: {stats.cidrs_after_collapse}",
        f"Plain IPs removed because covered by CIDRs: {stats.plain_inside_cidr_removed}",
        f"Estimated output lines: {stats.estimated_output_lines}",
        f"Output files written: {stats.output_files}",
    ]
    return "\n".join(lines) + "\n"


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract IPv4/CIDR items from messy files, deduplicate, sort, optionally keep CIDRs, and split TXT output.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input", nargs="+", help="Input file(s) to read. Folders are not scanned.")
    parser.add_argument("--cidr", action="store_true", help="Keep collapsed CIDRs where possible. Default expands CIDRs to usable IPs.")
    parser.add_argument("--split", type=positive_int, default=DEFAULT_SPLIT, help="Maximum output lines per part file.")
    parser.add_argument("--yes", action="store_true", help="Do not ask confirmation when expanded output is over 1,000,000 lines.")
    return parser.parse_args(argv)


def interactive_args() -> argparse.Namespace:
    print("dnslist interactive mode")
    while True:
        raw_files = input("Input file paths separated by spaces: ").strip()
        if raw_files:
            break
        print("Please enter at least one input file.")

    print("\nOutput mode:")
    print("1. Expand CIDRs to plain IPs (default)")
    print("2. Keep CIDRs where possible")
    mode = input("Choose 1 or 2: ").strip()
    cidr_mode = mode == "2"

    split_raw = input(f"Split size, press Enter for {DEFAULT_SPLIT}: ").strip()
    split_size = DEFAULT_SPLIT if not split_raw else positive_int(split_raw)

    return argparse.Namespace(input=raw_files.split(), cidr=cidr_mode, split=split_size, yes=False)


def confirm_large_output(total: int) -> bool:
    answer = input(f"Warning: estimated expanded output is {total} lines, above {WARN_EXPANDED_OVER}. Continue? [y/N]: ")
    return answer.strip().lower() in {"y", "yes"}


def run(args: argparse.Namespace) -> int:
    stats = Stats()
    paths = [Path(p).expanduser() for p in args.input]

    plain_ips_set, raw_cidrs = parse_inputs(paths, stats)
    cidrs = collapse_cidrs(raw_cidrs, stats)
    plain_ips = remove_plain_inside_cidrs(plain_ips_set, cidrs, stats)

    stats.estimated_output_lines = estimate_lines(plain_ips, cidrs, args.cidr)
    if stats.estimated_output_lines == 0:
        print("No valid IP/CIDR found.")
        return 0

    print(f"Estimated output lines: {stats.estimated_output_lines}")
    if not args.cidr and stats.estimated_output_lines > WARN_EXPANDED_OVER and not args.yes:
        if not confirm_large_output(stats.estimated_output_lines):
            print("Operation cancelled.")
            return 1

    out_dir = make_timestamp_dir()

    write_outputs(iter_output_items(plain_ips, cidrs, args.cidr), out_dir, args.split, stats)

    summary = build_summary(stats, out_dir, args.cidr, args.split)
    (out_dir / SUMMARY_FILE).write_text(summary, encoding="utf-8")
    print("\n" + summary, end="")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    args = interactive_args() if not argv else parse_args(argv)

    if not args.input:
        print("No input files provided. Use --input file1.txt file2.json or run with no arguments for interactive mode.", file=sys.stderr)
        return 2

    try:
        return run(args)
    except KeyboardInterrupt:
        print("\nCancelled by user.")
        return 130
    except argparse.ArgumentTypeError as exc:
        print(f"Invalid value: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
