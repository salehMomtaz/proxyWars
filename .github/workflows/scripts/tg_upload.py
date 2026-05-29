#!/usr/bin/env python3
import os
import sys
import json
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

EC_BAD_INPUT = 2
EC_AUTH = 4
EC_TARGET = 10
EC_UPLOAD = 11
EC_FILE = 12

async def main():
    if len(sys.argv) < 3:
        print("Usage: tg_upload.py <target> <file1> [file2 ...] [--caption TEXT]", file=sys.stderr)
        sys.exit(EC_BAD_INPUT)

    api_id = os.getenv("TG_API_ID")
    api_hash = os.getenv("TG_API_HASH")
    sess = os.getenv("TG_STRING_SESSION")

    if not api_id or not api_hash or not sess:
        print("AUTH_REQUIRED: missing TG_API_ID/TG_API_HASH/TG_STRING_SESSION", file=sys.stderr)
        sys.exit(EC_AUTH)

    args = sys.argv[1:]
    target = args[0]
    caption = ""
    files = []

    i = 1
    while i < len(args):
      if args[i] == "--caption":
          i += 1
          caption = args[i] if i < len(args) else ""
      else:
          files.append(args[i])
      i += 1

    if not files:
        print("NO_FILES_TO_UPLOAD", file=sys.stderr)
        sys.exit(EC_FILE)

    for f in files:
        if not os.path.isfile(f) or os.path.getsize(f) == 0:
            print(f"INVALID_FILE: {f}", file=sys.stderr)
            sys.exit(EC_FILE)

    client = TelegramClient(StringSession(sess), int(api_id), api_hash)
    await client.connect()
    try:
        if not await client.is_user_authorized():
            print("AUTH_REQUIRED", file=sys.stderr)
            sys.exit(EC_AUTH)

        try:
            entity = await client.get_entity("me" if target == "me" else target)
        except Exception as ex:
            print(f"TARGET_RESOLVE_FAILED: {ex}", file=sys.stderr)
            sys.exit(EC_TARGET)

        try:
            if len(files) == 1:
                await client.send_file(entity, files[0], caption=caption or None)
            else:
                await client.send_file(entity, files, caption=caption or None)
        except Exception as ex:
            print(f"UPLOAD_FAILED: {ex}", file=sys.stderr)
            sys.exit(EC_UPLOAD)

        print(json.dumps({"status": "OK", "target": target, "count": len(files)}, ensure_ascii=False))
        sys.exit(0)

    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
