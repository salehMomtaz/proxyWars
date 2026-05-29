#!/usr/bin/env python3
import os
import sys
import json
import argparse
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import PeerChannel, InputPeerSelf

EC_OK = 0
EC_ENV = 10
EC_AUTH = 11
EC_FILE = 12
EC_TARGET = 13
EC_UPLOAD = 14


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


async def resolve_target(client, target: str):
    t = (target or "").strip()

    if t == "me":
        return InputPeerSelf()

    # Numeric channel/supergroup id in Bot API style: -100xxxxxxxxxx
    if t.startswith("-100") and t[4:].isdigit():
        channel_id = int(t[4:])
        return PeerChannel(channel_id)

    # Other numeric ids (fallback)
    if (t.startswith("-") and t[1:].isdigit()) or t.isdigit():
        return await client.get_entity(int(t))

    # @username / t.me link / other entity references
    return await client.get_entity(t)


async def main():
    parser = argparse.ArgumentParser(description="Upload a local file to Telegram target")
    parser.add_argument("target", help='Target: "me", "@username", "-100...", etc.')
    parser.add_argument("file_path", help="Local file path to upload")
    parser.add_argument("--caption", default="", help="Optional caption")
    args = parser.parse_args()

    api_id = os.getenv("TG_API_ID", "").strip()
    api_hash = os.getenv("TG_API_HASH", "").strip()
    string_session = os.getenv("TG_STRING_SESSION", "").strip()

    if not api_id or not api_hash or not string_session:
        eprint("ENV_MISSING: TG_API_ID / TG_API_HASH / TG_STRING_SESSION are required")
        sys.exit(EC_ENV)

    file_path = args.file_path
    target = args.target.strip()
    caption = args.caption or ""

    if not os.path.isfile(file_path) or os.path.getsize(file_path) <= 0:
        eprint(f"FILE_INVALID: {file_path}")
        sys.exit(EC_FILE)

    try:
        api_id_int = int(api_id)
    except ValueError:
        eprint("ENV_INVALID: TG_API_ID must be integer")
        sys.exit(EC_ENV)

    client = TelegramClient(StringSession(string_session), api_id_int, api_hash)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            eprint("AUTH_REQUIRED: Session is not authorized")
            sys.exit(EC_AUTH)

        # Resolve target
        try:
            entity = await resolve_target(client, target)
        except Exception as ex:
            eprint(f"TARGET_RESOLVE_FAILED: {ex}")
            sys.exit(EC_TARGET)

        # Upload
        try:
            msg = await client.send_file(
                entity=entity,
                file=file_path,
                caption=caption if caption else None,
                force_document=False
            )
        except Exception as ex:
            eprint(f"UPLOAD_FAILED: {ex}")
            sys.exit(EC_UPLOAD)

        out = {
            "ok": True,
            "target": target,
            "file": file_path,
            "caption": caption,
            "message_id": getattr(msg, "id", None)
        }
        print(json.dumps(out, ensure_ascii=False))
        sys.exit(EC_OK)

    finally:
        await client.disconnect()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
