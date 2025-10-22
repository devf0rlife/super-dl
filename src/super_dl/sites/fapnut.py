"""Downloader/extractor for fapnut.net

This module provides the interface expected by `super_dl.main` for sites
that expose an iframe or page containing an .m3u8 playlist. The module
implements:
- fetch_page(url) -> str
- extract_iframe_src(html) -> Optional[str]
- extract_m3u8_from_html(html) -> Optional[str]
- download(m3u8_url, out_path=None) -> int

The download function shells out to ffmpeg to download an m3u8 stream and
save it as an .mp4 file when invoked from the CLI. Tests do not run ffmpeg.
"""
from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import requests


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/114.0.0.0 Safari/537.36"
)


def fetch_page(url: str) -> Optional[str]:
    headers = {"User-Agent": USER_AGENT, "Referer": "https://fapnut.net/"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.text


def extract_iframe_src(html: str) -> Optional[str]:
    """Find the first iframe src on the page."""
    if not html:
        return None
    m = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
    if m:
        return m.group(1)
    return None


def extract_m3u8_from_html(html: str) -> Optional[str]:
    """Extract an .m3u8 URL from iframe HTML or player HTML.

    Looks for direct .m3u8 links in src attributes or JS variables.
    """
    if not html:
        return None

    # look for src="https://.../playlist.m3u8"
    m = re.search(r'src=["\'](https?://[^"\']+?\.m3u8[^"\']*)["\']', html, re.IGNORECASE)
    if m:
        return m.group(1)

    # look for plain http(s) .m3u8 anywhere
    m2 = re.search(r'(https?://[^"\']+?\.m3u8\b[^"\']*)', html, re.IGNORECASE)
    if m2:
        return m2.group(1)

    return None


def _filename_from_page_url(page_url: str) -> str:
    """Derive a filename from the page URL: https://fapnut.net/<name>/ -> <name>.mp4"""
    from urllib.parse import urlparse

    parsed = urlparse(page_url)
    path = parsed.path.strip("/")
    if not path:
        return "fapnut.mp4"
    # take last segment
    name = path.split("/")[-1]
    if not name:
        name = "fapnut"
    return f"{name}.mp4"


def download(m3u8_url: str, out_path: Optional[str] = None, page_url: Optional[str] = None) -> int:
    """Download the m3u8 using ffmpeg.

    If ffmpeg is not available, raise a RuntimeError. When out_path is not
    provided, the filename is derived from page_url if given, otherwise from
    the m3u8 URL.
    """
    if not m3u8_url:
        raise ValueError("m3u8_url is empty or None")

    # Find ffmpeg
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        raise RuntimeError("ffmpeg is required to download m3u8 streams")

    if out_path:
        out_file = Path(out_path)
    else:
        if page_url:
            out_file = Path(os.getcwd()) / _filename_from_page_url(page_url)
        else:
            # fallback: use last path segment of m3u8
            from urllib.parse import urlparse

            parsed = urlparse(m3u8_url)
            name = Path(parsed.path).name or "fapnut"
            out_file = Path(os.getcwd()) / f"{name}.mp4"

    out_file.parent.mkdir(parents=True, exist_ok=True)

    # Build ffmpeg command to download HLS stream and save as mp4
    cmd = [
        ffmpeg_path,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-headers",
        f"Referer: https://fapnut.net/\r\n",
        "-i",
        m3u8_url,
        "-c",
        "copy",
        str(out_file),
    ]

    # Run ffmpeg
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {proc.stderr.decode('utf8', errors='replace')}")

    return 0
