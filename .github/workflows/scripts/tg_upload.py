#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import time
import argparse
import asyncio
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import RPCError
from telethon.tl.types import DocumentAttributeVideo


VIDEO_EXTS = {
    ".mp4", ".m4v", ".mov", ".webm", ".mkv", ".avi", ".3gp", ".mpeg", ".mpg", ".flv", ".wmv"
}


def jprint(obj):
    print(json.dumps(obj, ensure_ascii=False), flush=True)


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


def is_video_file(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTS


def run_cmd(cmd: list[str]) -> Tuple[int, str, str]:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def ffprobe_video_meta(video_path: Path) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    """
    Returns: (duration_sec, width, height) or (None, None, None)
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        str(video_path),
    ]
    rc, out, err = run_cmd(cmd)
    if rc != 0 or not out:
        return None, None, None

    try:
        data = json.loads(out)
        streams = data.get("streams", [])
        fmt = data.get("format", {})
        vstream = next((s for s in streams if s.get("codec_type") == "video"), None)

        width = int(vstream["width"]) if vstream and vstream.get("width") else None
        height = int(vstream["height"]) if vstream and vstream.get("height") else None

        duration = None
        if vstream and vstream.get("duration") not in (None, ""):
            duration = float(vstream["duration"])
        elif fmt.get("duration") not in (None, ""):
            duration = float(fmt["duration"])

        duration_sec = int(round(duration)) if duration is not None else None
        if duration_sec is not None and duration_sec < 0:
            duration_sec = None

        return duration_sec, width, height
    except Exception:
        return None, None, None


def make_thumbnail(video_path: Path, out_jpg: Path) -> Optional[Path]:
    """
    Build a Telegram-friendly JPEG thumbnail.
    """
    cmd = [
        "ffmpeg", "-y",
        "-ss", "00:00:01.000",
        "-i", str(video_path),
        "-frames:v", "1",
        "-vf", "scale='min(320,iw)':-2",
        "-q:v", "4",
        str(out_jpg),
    ]
    rc, _, _ = run_cmd(cmd)
    if rc != 0:
        return None
    if not out_jpg.exists() or out_jpg.stat().st_size == 0:
        return None

    # try recompress if large
    if out_jpg.stat().st_size > 200 * 1024:
        rc2, _, _ = run_cmd(["ffmpeg", "-y", "-i", str(out_jpg), "-q:v", "7", str(out_jpg)])
        if rc2 != 0:
            pass

    if out_jpg.exists() and out_jpg.stat().st_size > 0:
        return out_jpg
    return None


def make_progress_callback(prefix: str = "telegram-upload", interval_sec: int = 5):
    state = {"last_t": 0.0}

    def cb(sent: int, total: int):
        if not total:
            return
        now = time.time()
        percent = int((sent * 100) / total)
        if percent >= 100 or (now - state["last_t"] >= interval_sec):
            mb_sent = sent / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            print(f"[{prefix}] {percent:3d}% ({mb_sent:.1f}/{mb_total:.1f} MB)", flush=True)
            state["last_t"] = now

    return cb


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

    try:
        return await client.get_entity(t)
    except Exception:
        pass

    if is_numeric_target(t):
        raw = int(t)

        # Try find in dialogs first
        try:
            async for d in client.iter_dialogs():
                ent = d.entity
                ent_id = getattr(ent, "id", None)
                if ent_id is None:
                    continue

                # channel/supergroup often represented as -100 + ent.id
                if str(raw) == f"-100{ent_id}" or str(raw) == str(ent_id):
                    return ent
        except Exception:
            pass

        # Last attempt
        try:
            return await client.get_entity(raw)
        except Exception:
            fail(
                "TARGET_RESOLVE_FAILED",
                f"Could not resolve numeric target: {t}. Ensure account is member/admin and dialog is visible.",
                exit_code=4,
            )

    fail("TARGET_RESOLVE_FAILED", f"Could not resolve target: {t}", exit_code=4)


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

    is_video = is_video_file(fpath)
    duration, width, height = (None, None, None)
    thumb_attached = False

    client = TelegramClient(StringSession(string_session), api_id_int, api_hash)

    try:
        await client.connect()
        if not await client.is_user_authorized():
            fail("AUTH_REQUIRED", "Telegram session is not authorized", exit_code=8)

        entity = await resolve_target(client, args.target)

        send_kwargs = {
            "caption": args.caption or "",
            "force_document": False,
            "progress_callback": make_progress_callback("telegram-upload", interval_sec=5),
        }

        if is_video:
            duration, width, height = ffprobe_video_meta(fpath)

            attrs = [
                DocumentAttributeVideo(
                    duration=duration if isinstance(duration, int) and duration >= 0 else 0,
                    w=width if isinstance(width, int) and width and width > 0 else 0,
                    h=height if isinstance(height, int) and height and height > 0 else 0,
                    supports_streaming=True
                )
            ]
            send_kwargs["attributes"] = attrs
            send_kwargs["supports_streaming"] = True

            with tempfile.TemporaryDirectory(prefix="tgthumb_") as td:
                thumb_path = make_thumbnail(fpath, Path(td) / "thumb.jpg")
                if thumb_path:
                    send_kwargs["thumb"] = str(thumb_path)
                    thumb_attached = True

                msg = await client.send_file(entity, str(fpath), **send_kwargs)
        else:
            msg = await client.send_file(entity, str(fpath), **send_kwargs)

        jprint({
            "ok": True,
            "target": args.target,
            "file": str(fpath),
            "caption": args.caption or "",
            "message_id": getattr(msg, "id", None),
            "is_video": is_video,
            "supports_streaming": bool(is_video),
            "thumb_attached": thumb_attached,
            "duration": duration,
            "width": width,
            "height": height
        })

    except RPCError as e:
        fail("RPC_ERROR", str(e), exit_code=9)
    except Exception as e:
        fail("UPLOAD_FAILED", str(e), exit_code=10)
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
