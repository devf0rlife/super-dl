"""Downloader for cumslutx.com and girlxnude.com pages.

This module extracts a direct .mp4 URL from the page (meta itemprop or source tag)
and downloads it using curl with a browser User-Agent and proper Referer.
"""
from __future__ import annotations

import shlex
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


def fetch_page(url: str) -> str:
    headers = {"User-Agent": USER_AGENT, "Referer": url}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.text


def extract_mp4_url(html: str) -> Optional[str]:
    """Extract .mp4 URL from meta itemprop contentURL or <source> tag."""
    soup = BeautifulSoup(html, "html.parser")
    # meta itemprop contentURL
    meta = soup.find("meta", {"itemprop": "contentURL"})
    if meta and meta.has_attr("content"):
        url = meta["content"]
        if url.endswith(".mp4"):
            return url

    # <source type="video/mp4" src="...">
    source = soup.find("source", {"type": "video/mp4"})
    if source and source.has_attr("src"):
        return source["src"]

    # fallback: search for .mp4 in the page text
    import re

    m = re.search(r"(https?://[^\s'\"]+\.mp4)", str(html))
    return m.group(1) if m else None


def derive_filename_from_url(url: str) -> str:
    # url like https://cumslutx.com/<name>/ -> derive <name>
    from urllib.parse import urlparse

    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    name = parts[-1] if parts else "video"
    # sanitize
    import re

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
        "https://cumslutx.com/",
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
