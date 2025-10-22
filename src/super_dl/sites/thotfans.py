"""Downloader/extractor for thotfans.com

This module implements the same minimal interface expected by `super_dl.main`:
- fetch_page(url) -> str
- extract_mp4_url(html) -> Optional[str]
- download(mp4_url, out_path=None) -> int

It finds .mp4 URLs embedded in the HTML, for example inside a <source> or an <a>
tag, and returns the first match. The downloader streams the file to disk and
uses the last path segment as filename when no output path is provided.
"""
from __future__ import annotations

import os
import random
import re
from pathlib import Path
from typing import Optional

import requests


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/114.0.0.0 Safari/537.36"
)


def fetch_page(url: str) -> Optional[str]:
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.text


def extract_mp4_url(html: str) -> Optional[str]:
    """Extract the first .mp4 URL from the provided HTML.

    Supports patterns like:
    <source type="video/mp4" src="https://cdn.thotfans.com/.../file.mp4" />
    <a href="https://cdn.thotfans.com/.../file.mp4">...
    """
    if not html:
        return None

    # Prefer the src attribute on <source> tags
    m = re.search(r'<source[^>]+src=["\'](https?://[^"\']+?\.mp4)["\']', html, re.IGNORECASE)
    if m:
        return m.group(1)

    # Look for anchor hrefs linking to .mp4
    m2 = re.search(r'<a[^>]+href=["\'](https?://[^"\']+?\.mp4)["\']', html, re.IGNORECASE)
    if m2:
        return m2.group(1)

    # Fallback: any .mp4 URL in the document
    m3 = re.search(r'(https?://[^"\'" >]+?\.mp4)', html)
    if m3:
        return m3.group(1)

    return None


def _append_random_rnd(url: str) -> str:
    rnd = random.randrange(10**12, 10**14)
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}rnd={rnd}"


def _filename_from_url(url: str) -> str:
    from urllib.parse import urlparse
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    name = os.path.basename(path)
    return name


def download(mp4_url: str, out_path: Optional[str] = None) -> int:
    if not mp4_url:
        raise ValueError("mp4_url is empty or None")

    url_with_rnd = _append_random_rnd(mp4_url)

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": USER_AGENT,
        "DNT": "1",
    }

    if out_path:
        out_file = Path(out_path)
    else:
        filename = _filename_from_url(mp4_url)
        out_file = Path(os.getcwd()) / filename

    out_file.parent.mkdir(parents=True, exist_ok=True)

    with requests.get(url_with_rnd, headers=headers, stream=True, timeout=30) as r:
        try:
            r.raise_for_status()
        except Exception:
            raise
        with open(out_file, "wb") as fh:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    fh.write(chunk)

    return 0
