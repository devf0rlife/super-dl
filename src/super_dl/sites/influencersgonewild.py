"""Downloader and extractor for influencersgonewild.com

This module provides:
- extract_mp4_url(html): parse HTML and return .mp4 URL (or None)
- download(url, out_path=None): download the mp4 using wget with required headers
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
    "Chrome/91.0.4472.124 Safari/537.36"
)
REFERER = "https://influencersgonewild.com/"


def extract_mp4_url(html: str) -> Optional[str]:
    """Extract .mp4 video URL from HTML content.

    Returns the first <source type="video/mp4" src="..."> value found, or None.
    """
    soup = BeautifulSoup(html, "html.parser")
    source_tag = soup.find("source", {"type": "video/mp4"})
    if source_tag and source_tag.has_attr("src"):
        return source_tag["src"]
    return None


def download(mp4_url: str, out_path: Optional[str] = None) -> int:
    """Download the mp4 URL using wget with the required UA and referer.

    - mp4_url: direct URL to the .mp4 file
    - out_path: optional file path to save to; if None, wget chooses filename

    Returns subprocess exit code (0 on success).
    """
    if not mp4_url:
        raise ValueError("mp4_url is empty or None")

    cmd = [
        "wget",
        "--user-agent",
        USER_AGENT,
        "--referer",
        REFERER,
    ]

    if out_path:
        out_dir = Path(out_path).parent
        if out_dir and not out_dir.exists():
            out_dir.mkdir(parents=True, exist_ok=True)
        cmd += ["-O", str(out_path)]

    cmd.append(mp4_url)

    # Use subprocess to run wget
    proc = subprocess.run(cmd)
    return proc.returncode


def fetch_page(url: str) -> Optional[str]:
    """Fetch page HTML with a browser-like user-agent and referer set to the site root."""
    headers = {"User-Agent": USER_AGENT, "Referer": REFERER}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.text
