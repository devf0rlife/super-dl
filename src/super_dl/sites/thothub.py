"""Downloader and extractor for thothub.to

This module provides the minimal interface expected by `super_dl.main`:
- fetch_page(url) -> str
- extract_mp4_url(html) -> Optional[str]
- download(mp4_url, out_path=None) -> int

Behavior notes:
- extract_mp4_url looks for a JS snippet containing "video_url: 'function/0/<mp4>'"
- download appends a random ?rnd=<int> query parameter, sends browser-like headers,
  and streams the response to disk using the last path segment of the URL as filename
  when out_path is not provided.
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
    """Extract .mp4 URL from thothub page HTML.

    The page contains a JavaScript line like:
    video_url: 'function/0/https://.../15879.mp4'

    We capture the https://... .mp4 portion.
    """
    if not html:
        return None

    # Look for video_url: 'function/0/<https...mp4>'
    pattern = re.compile(r"video_url:\s*'function/0/(https?://[^']+\.mp4)\b")
    m = pattern.search(html)
    if m:
        return m.group(1)

    # Fallback: look for any .mp4 URL in the page
    m2 = re.search(r'(https?://[^" ]+?\.mp4)', html)
    if m2:
        return m2.group(1)

    return None


def _append_random_rnd(url: str) -> str:
    rnd = random.randrange(10**12, 10**14)
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}rnd={rnd}"


def _filename_from_url(url: str) -> str:
    # Use urlparse to handle query strings and trailing slashes robustly
    from urllib.parse import urlparse
    parsed = urlparse(url)
    # parsed.path may end with a slash; strip trailing slashes first
    path = parsed.path.rstrip("/")
    name = os.path.basename(path)
    return name


def download(mp4_url: str, out_path: Optional[str] = None) -> int:
    """Download the mp4 URL by appending ?rnd=random and streaming to disk.

    Returns 0 on success, non-zero on failure.
    """
    if not mp4_url:
        raise ValueError("mp4_url is empty or None")

    url_with_rnd = _append_random_rnd(mp4_url)

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": USER_AGENT,
        "DNT": "1",
    }

    # Prepare output filename
    if out_path:
        out_file = Path(out_path)
    else:
        filename = _filename_from_url(mp4_url)
        out_file = Path(os.getcwd()) / filename

    # Ensure parent dir exists
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # Stream download
    with requests.get(url_with_rnd, headers=headers, stream=True, timeout=30) as r:
        try:
            r.raise_for_status()
        except Exception:
            # propagate same exception to caller
            raise
        with open(out_file, "wb") as fh:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    fh.write(chunk)

    return 0
