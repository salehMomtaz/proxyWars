#!/usr/bin/env python3
import os
import re
import sys
import json
import argparse
import tempfile
import subprocess
from pathlib import Path

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import InputPeerChannel
from telethon.errors import RPCError

VIDEO_EXTS = {
    ".mp4", ".m4v", ".mov", ".webm", ".mkv", ".avi", ".3gp", ".mpeg", ".mpg"
}

def jprint(obj):
    print(json.dumps(obj, ensure_ascii=False))

def fail(code, message, extra=None, exit_code=1):
    payload = {"ok": False, "error": code, "message": message}
    if extra is not None:
      payload["extra"] = extra
    jprint(payload)
    sys.exit(exit_code)

def env_required(name):
    v = os.getenv(name, "").strip()
    if not v:
        fail("MISSING_ENV", f"Environment variable {name} is required", exit_code=2)
    return v

def is_numeric_target(t: str) -> bool:
    return bool(re.fullmatch(r"-?\d+", t or ""))

async def resolve_target(client: TelegramClient, target: str):
    """
    target can be:
      - me
      - @username
      - t.me/...
      - numeric id (e.g. -1001234567890)
    """
    t = (target or "").strip()
    if not t:
        fail("BAD_TARGET", "target is empty", exit_code=3)

    if t.lower() == "me":
        return "me"

    # try direct entity first (works for @username, links, known ids sometimes)
    try:
        return await client.get_entity(t)
    except Exception:
        pass

    # numeric fallback for channel/supergroup id
    if is_numeric_target(t):
        raw = int(t)
        # Telegram channel id often starts with -100...
        # Telethon InputPeerChannel wants channel_id without -100 and access_hash.
        # We'll try to discover it from dialogs if possible.
        try:
            async for d in client.iter_dialogs():
                ent = d.entity
                if getattr(ent, "id", None) is None:
                    continue
                # reconstruct comparable peer id
                # channel/supergroup: -100 + ent.id
                cand = f"-100{ent.id}"
                if str(raw) == cand:
                    return ent
                # sometimes users pass raw ent.id (positive)
                if str(raw) == str(ent.id):
                    return ent
        except Exception:
            pass

        # last attempt: maybe it's directly resolvable as peer id through get_entity(int)
        try:
            return await client.get_entity(raw)
        except Exception:
            fail(
                "TARGET_RESOLVE_FAILED",
                f"Could not resolve numeric target: {t}. Ensure account is member/admin and dialog is visible.",
                exit_code=4,
            )

    fail("TARGET_RESOLVE_FAILED", f"Could not resolve target: {t}", exit_code=4)

def is_video_file(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTS

def run_ffmpeg_make_thumb(video_path: Path, out_jpg: Path) -> bool:
    """
    Generate a JPEG thumbnail from ~1s mark.
    """
    cmd = [
        "ffmpeg", "-y",
        "-ss", "00:00:01.000",
        "-i", str(video_path),
        "-frames:v", "1",
        "-vf", "scale='min(320,iw)':'min(320,ih)':force_original_aspect_ratio=decrease",
        "-q:v", "3",
        str(out_jpg)
    ]
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        return p.returncode == 0 and out_jpg.exists() and out_jpg.stat().st_size > 0
    except Exception:
        return False

def compress_jpeg_under_200kb(jpg_path: Path) -> bool:
    """
    Re-encode progressively lower quality until < 200KB.
    """
    max_bytes = 200 * 1024
    if not jpg_path.exists():
        return False
    if jpg_path.stat().st_size <= max_bytes:
        return True

    # Try multiple quality steps
    for q in [8, 10, 12, 15, 18, 20, 24, 28, 32]:
        tmp = jpg_path.with_suffix(".tmp.jpg")
        cmd = [
            "ffmpeg", "-y",
            "-i", str(jpg_path),
            "-q:v", str(q),
            "-vf", "scale='min(320,iw)':'min(320,ih)':force_original_aspect_ratio=decrease",
            str(tmp)
        ]
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if p.returncode == 0 and tmp.exists() and tmp.stat().st_size > 0:
            tmp.replace(jpg_path)
            if jpg_path.stat().st_size <= max_bytes:
                return True

    return jpg_path.exists() and jpg_path.stat().st_size <= max_bytes

async def main():
    parser = argparse.ArgumentParser(description="Upload file to Telegram using Telethon")
    parser.add_argument("target", help="me | @username | -100... | t.me/...")
    parser.add_argument("file_path", help="Local file path to upload")
    parser.add_argument("--caption", default="", help="Optional caption")
    args = parser.parse_args()

    api_id = env_required("TG_API_ID")
    api_hash = env_required("TG_API_HASH")
    string_session = env_required("TG_STRING_SESSION")

    fpath = Path(args.file_path).expanduser().resolve()
    if not fpath.exists() or not fpath.is_file():
        fail("FILE_NOT_FOUND", f"File not found: {fpath}", exit_code=5)
    if fpath.stat().st_size <= 0:
        fail("FILE_EMPTY", f"File is empty: {fpath}", exit_code=6)

    try:
        api_id_int = int(api_id)
    except ValueError:
        fail("BAD_API_ID", "TG_API_ID must be numeric", exit_code=7)

    client = TelegramClient(StringSession(string_session), api_id_int, api_hash)

    try:
        await client.connect()
        if not await client.is_user_authorized():
            fail("AUTH_REQUIRED", "Telegram session is not authorized", exit_code=8)

        entity = await resolve_target(client, args.target)

        send_kwargs = {
            "caption": args.caption or "",
            "force_document": False,  # important for video preview behavior
        }

        thumb_path = None
        used_thumb = False
        supports_streaming = False

        if is_video_file(fpath):
            supports_streaming = True
            send_kwargs["supports_streaming"] = True

            # create thumb best-effort
            with tempfile.TemporaryDirectory(prefix="tgthumb_") as td:
                candidate = Path(td) / "thumb.jpg"
                ok = run_ffmpeg_make_thumb(fpath, candidate)
                if ok:
                    if compress_jpeg_under_200kb(candidate):
                        # Telethon can upload local thumb path
                        thumb_path = str(candidate)
                        send_kwargs["thumb"] = thumb_path
                        used_thumb = True

                # send while temp dir still exists
                msg = await client.send_file(entity, str(fpath), **send_kwargs)

        else:
            msg = await client.send_file(entity, str(fpath), **send_kwargs)

        jprint({
            "ok": True,
            "target": args.target,
            "file": str(fpath),
            "caption": args.caption or "",
            "message_id": getattr(msg, "id", None),
            "is_video": is_video_file(fpath),
            "supports_streaming": supports_streaming,
            "thumb_attached": used_thumb
        })

    except RPCError as e:
        fail("RPC_ERROR", str(e), exit_code=9)
    except Exception as e:
        fail("UPLOAD_FAILED", str(e), exit_code=10)
    finally:
        await client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
