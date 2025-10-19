"""Downloader for amateurdoporn-like sites.

This module looks for .m3u8 URLs on the page or inside an iframe and downloads
the HLS stream using ffmpeg with appropriate headers. It's similar to eroleaked
but includes some refinements for filename derivation and fallback checks.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/141.0.0.0 Safari/537.36"
)
REFERER = "https://amateurdoporn.com/"


def fetch_page(url: str) -> str:
    headers = {"User-Agent": USER_AGENT, "Referer": REFERER}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.text


def extract_iframe_src(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "html.parser")
    iframe = soup.select_one("iframe")
    if iframe and iframe.has_attr("src"):
        return iframe["src"]
    return None


def extract_m3u8_from_text(text: str) -> Optional[str]:
    # look for m3u8 in any quoted context or raw
    m = re.search(r"(https?://[^\s'\"]+\.m3u8)", text)
    return m.group(1) if m else None


def derive_filename_from_url(url: str) -> str:
    path = url.rstrip("/")
    name = Path(path).name
    if not name:
        parts = [p for p in path.split("/") if p]
        name = parts[-1] if parts else "video"
    name = re.sub(r"[^A-Za-z0-9._-]", "-", name)
    return name


def download(m3u8_url: str, out_path: Optional[str] = None) -> int:
    if not m3u8_url:
        raise ValueError("m3u8_url is required")
    if out_path is None:
        out_path = derive_filename_from_url(m3u8_url) + ".mp4"

    headers = (
        "sec-ch-ua-platform: \"Windows\"\r\n"
        f"Referer: {REFERER}\r\n"
        f"User-Agent: {USER_AGENT}\r\n"
    )

    cmd = [
        "ffmpeg",
        "-headers",
        headers,
        "-i",
        m3u8_url,
        "-c",
        "copy",
        out_path,
    ]

    proc = subprocess.run(cmd)
    return proc.returncode


def full_download_from_page(url: str, out_path: Optional[str] = None) -> int:
    page_html = fetch_page(url)

    # 1) Try to find m3u8 directly on the page
    m3u8 = extract_m3u8_from_text(page_html)
    if m3u8:
        return download(m3u8, out_path=out_path)

    # 2) Try to find iframe and search inside it
    iframe_src = extract_iframe_src(page_html)
    if iframe_src:
        from urllib.parse import urljoin

        iframe_src = urljoin(url, iframe_src)
        iframe_html = fetch_page(iframe_src)
        m3u8 = extract_m3u8_from_text(iframe_html)
        if m3u8:
            return download(m3u8, out_path=out_path)

    # 3) No m3u8 found
    raise RuntimeError("No .m3u8 URL found on page or iframe")
