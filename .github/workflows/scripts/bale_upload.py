#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import mimetypes
import argparse
from pathlib import Path

import requests


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def bail(msg: str, code: int = 1):
    eprint(msg)
    sys.exit(code)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Upload a file to Bale via Bot API (sendDocument)"
    )
    parser.add_argument("chat_id", help="Target chat id (e.g. 1058935006)")
    parser.add_argument("file_path", help="Path to local file to upload")
    parser.add_argument("--caption", default="", help="Optional caption")
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="HTTP timeout in seconds (default: 300)"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    token = os.getenv("BALE_BOT_TOKEN", "").strip()
    if not token:
        bail("ERROR: BALE_BOT_TOKEN is not set", 2)

    file_path = Path(args.file_path).expanduser().resolve()
    if not file_path.exists() or not file_path.is_file():
        bail(f"ERROR: file not found: {file_path}", 3)
    if file_path.stat().st_size <= 0:
        bail(f"ERROR: file is empty: {file_path}", 4)

    # Bale Bot API endpoint (Telegram-compatible pattern)
    url = f"https://tapi.bale.ai/bot{token}/sendDocument"

    mime_type, _ = mimetypes.guess_type(str(file_path))
    if not mime_type:
        mime_type = "application/octet-stream"

    data = {
        "chat_id": str(args.chat_id),
    }
    if args.caption:
        data["caption"] = args.caption

    try:
        with open(file_path, "rb") as f:
            files = {
                "document": (file_path.name, f, mime_type),
            }
            resp = requests.post(url, data=data, files=files, timeout=args.timeout)
    except requests.RequestException as ex:
        bail(f"ERROR: network/request failed: {ex}", 5)
    except OSError as ex:
        bail(f"ERROR: cannot read file: {ex}", 6)

    # Try parse JSON response
    try:
        payload = resp.json()
    except ValueError:
        bail(f"ERROR: non-JSON response ({resp.status_code}): {resp.text[:500]}", 7)

    if resp.status_code != 200 or not payload.get("ok", False):
        desc = payload.get("description") or payload.get("error_code") or "unknown error"
        bail(f"ERROR: upload failed: {desc} | raw={json.dumps(payload, ensure_ascii=False)}", 8)

    result = payload.get("result", {})
    out = {
        "ok": True,
        "chat_id": args.chat_id,
        "file_path": str(file_path),
        "message_id": result.get("message_id"),
        "document": result.get("document", {}),
    }

    # stdout JSON for workflow consumption
    print(json.dumps(out, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
