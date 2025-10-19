"""Downloader for simpthots.com pages.

Extracts .mp4 from OpenGraph meta tags or from page contents and downloads via curl.
"""
from __future__ import annotations

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
REFERER = "https://simpthots.com/"


def fetch_page(url: str) -> str:
    headers = {"User-Agent": USER_AGENT, "Referer": url}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.text


def extract_mp4_url(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "html.parser")
    og = soup.find("meta", {"property": "og:video"})
    if og and og.has_attr("content"):
        return og["content"]
    og2 = soup.find("meta", {"property": "og:video:secure_url"})
    if og2 and og2.has_attr("content"):
        return og2["content"]

    # fallback: search for .mp4 in page
    import re

    m = re.search(r"(https?://[^\s'\"]+\.mp4)", str(html))
    return m.group(1) if m else None


def derive_filename_from_url(url: str) -> str:
    from urllib.parse import urlparse
    import re

    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    name = parts[-1] if parts else "video"
    name = re.sub(r"[^A-Za-z0-9._-]", "-", name)
    if not name.lower().endswith(".mp4"):
        name = name + ".mp4"
    return name


def download(mp4_url: str, out_path: Optional[str] = None) -> int:
    if not mp4_url:
        raise ValueError("mp4_url required")
    if out_path is None:
        out_path = derive_filename_from_url(mp4_url)

    cmd = [
        "curl",
        "-L",
        "--fail",
        "--output",
        out_path,
        "--user-agent",
        USER_AGENT,
        "--referer",
        REFERER,
        mp4_url,
    ]

    proc = subprocess.run(cmd)
    return proc.returncode


def full_download_from_page(url: str, out_path: Optional[str] = None) -> int:
    html = fetch_page(url)
    mp4 = extract_mp4_url(html)
    if not mp4:
        raise RuntimeError("No .mp4 URL found on page")
    if out_path is None:
        out_path = derive_filename_from_url(url)
    return download(mp4, out_path=out_path)
