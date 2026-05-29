#!/usr/bin/env python3
import os
import re
import sys
import json
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import RPCError

EC_BAD_INPUT = 2
EC_INVALID_URL = 3
EC_AUTH = 4
EC_FETCH = 5
EC_NOT_FOUND = 6
EC_NO_MEDIA = 7
EC_DOWNLOAD_FAIL = 8
EC_WEBPAGE_ONLY = 9

def parse_tme_url(url: str):
    m = re.match(r"^https?://t\.me/([A-Za-z0-9_]+)/(\d+)(\?.*)?$", url.strip())
    if not m:
        raise ValueError("INVALID_TELEGRAM_URL")
    return m.group(1), int(m.group(2))

def safe_name(name: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9._-]+", "_", (name or "").strip())
    name = re.sub(r"_+", "_", name).strip("_.-")
    return name or "telegram_file"

async def collect_album_messages(client, entity, base_msg):
    gid = getattr(base_msg, "grouped_id", None)
    if not gid:
        return [base_msg]
    msgs = await client.get_messages(entity, limit=50, min_id=max(0, base_msg.id - 20), max_id=base_msg.id + 20)
    album = [m for m in msgs if m and getattr(m, "grouped_id", None) == gid]
    album.sort(key=lambda x: x.id)
    return album if album else [base_msg]

async def main():
    if len(sys.argv) < 3:
        print("Usage: tg_download.py <telegram_url> <output_dir> [base_filename]", file=sys.stderr)
        sys.exit(EC_BAD_INPUT)

    tg_url = sys.argv[1].strip()
    out_dir = sys.argv[2].strip()
    base_filename = sys.argv[3].strip() if len(sys.argv) >= 4 else ""

    api_id = os.getenv("TG_API_ID")
    api_hash = os.getenv("TG_API_HASH")
    sess = os.getenv("TG_STRING_SESSION")

    if not api_id or not api_hash or not sess:
        print("AUTH_REQUIRED: missing TG_API_ID/TG_API_HASH/TG_STRING_SESSION", file=sys.stderr)
        sys.exit(EC_AUTH)

    os.makedirs(out_dir, exist_ok=True)

    try:
        username, msg_id = parse_tme_url(tg_url)
    except ValueError:
        print("INVALID_TELEGRAM_URL", file=sys.stderr)
        sys.exit(EC_INVALID_URL)

    client = TelegramClient(StringSession(sess), int(api_id), api_hash)
    await client.connect()

    try:
        if not await client.is_user_authorized():
            print("AUTH_REQUIRED", file=sys.stderr)
            sys.exit(EC_AUTH)

        try:
            msg = await client.get_messages(username, ids=msg_id)
        except RPCError as ex:
            print(f"FETCH_ERROR: {ex}", file=sys.stderr)
            sys.exit(EC_FETCH)

        if not msg:
            print("MESSAGE_NOT_FOUND", file=sys.stderr)
            sys.exit(EC_NOT_FOUND)

        if not msg.media:
            print("NO_MEDIA_IN_MESSAGE", file=sys.stderr)
            sys.exit(EC_NO_MEDIA)

        mtype = type(msg.media).__name__
        if mtype == "MessageMediaWebPage":
            wp = getattr(msg.media, "webpage", None)
            ext_url = getattr(wp, "url", None) if wp else None
            print(json.dumps({
                "status": "WEBPAGE_ONLY",
                "error_code": "WEBPAGE_MEDIA_EXTERNAL",
                "external_url": ext_url or "",
                "message_id": msg.id
            }, ensure_ascii=False))
            sys.exit(EC_WEBPAGE_ONLY)

        msgs = await collect_album_messages(client, username, msg)
        downloaded = []
        base = safe_name(base_filename) if base_filename else ""

        for idx, m in enumerate(msgs, start=1):
            if not m or not m.media:
                continue
            prefix = base if base else f"tg_{m.id}"
            if len(msgs) > 1:
                prefix = f"{prefix}_{idx:02d}"
            target = os.path.join(out_dir, prefix)
            try:
                path = await client.download_media(m, file=target)
            except Exception as ex:
                print(f"MEDIA_DOWNLOAD_FAILED: message_id={m.id} err={ex}", file=sys.stderr)
                continue
            if path and os.path.isfile(path) and os.path.getsize(path) > 0:
                downloaded.append(path)

        if not downloaded:
            print("MEDIA_DOWNLOAD_FAILED", file=sys.stderr)
            sys.exit(EC_DOWNLOAD_FAIL)

        print(json.dumps({
            "status": "OK",
            "count": len(downloaded),
            "album": bool(getattr(msg, "grouped_id", None)),
            "files": downloaded,
            "message_id": msg.id
        }, ensure_ascii=False))
        sys.exit(0)

    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
