"""Downloader for eroleaked.com

This module fetches a page, extracts the iframe URL from the player, follows the iframe,
finds a .m3u8 playlist URL, derives a filename from the original page URL, and downloads
the stream using ffmpeg with custom headers.
"""
from __future__ import annotations

import re
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
REFERER = "https://eroleaked.com/"


def fetch_page(url: str) -> str:
    headers = {"User-Agent": USER_AGENT, "Referer": REFERER}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.text


def extract_iframe_src(html: str) -> Optional[str]:
    """Extract the src value of the iframe inside .video-player -> .responsive-player."""
    soup = BeautifulSoup(html, "html.parser")
    # try to find iframe inside the responsive-player or video-player
    iframe = soup.select_one(".video-player .responsive-player iframe")
    if iframe and iframe.has_attr("src"):
        return iframe["src"]
    # fallback: find any iframe
    iframe = soup.find("iframe")
    if iframe and iframe.has_attr("src"):
        return iframe["src"]
    return None


def extract_m3u8_from_html(html: str) -> Optional[str]:
    """Search for the first .m3u8 URL in the HTML text."""
    page_text = str(html)
    m3u8_matches = re.findall(r"(https?://[^\s'\"]+\.m3u8)", page_text)
    if m3u8_matches:
        return m3u8_matches[0]
    return None


def derive_filename_from_url(url: str) -> str:
    """Given a page URL like https://eroleaked.com/2025/08/18/<slug>/, derive a base filename."""
    # strip trailing slash
    path = url.rstrip("/")
    name = Path(path).name
    if not name:
        # fallback to last meaningful path segment
        parts = [p for p in path.split("/") if p]
        name = parts[-1] if parts else "video"
    # sanitize (keep simple chars)
    name = re.sub(r"[^A-Za-z0-9._-]", "-", name)
    return name


def download(m3u8_url: str, out_path: Optional[str] = None) -> int:
    """Download the HLS stream using ffmpeg with custom headers.

    Returns ffmpeg process return code.
    """
    if not m3u8_url:
        raise ValueError("m3u8_url is required")

    if out_path is None:
        out_path = derive_filename_from_url(REFERER) + ".mp4"

    # Build ffmpeg headers string as shown in the prompt
    headers = (
        "sec-ch-ua-platform: \"Windows\"\r\n"
        f"Referer: {REFERER}\r\n"
        f"User-Agent: {USER_AGENT}\r\n"
        "sec-ch-ua: \"Google Chrome\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"\r\n"
        "sec-ch-ua-mobile: ?0\r\n"
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

    # Note: passing headers directly (as a single argument) is fine for subprocess.
    proc = subprocess.run(cmd)
    return proc.returncode


def full_download_from_page(url: str, out_path: Optional[str] = None) -> int:
    """High-level helper: fetch page, extract iframe->m3u8, and download via ffmpeg."""
    page_html = fetch_page(url)
    iframe_src = extract_iframe_src(page_html)
    if not iframe_src:
        raise RuntimeError("No iframe found on page")

    # Resolve relative iframe URLs
    if iframe_src.startswith("//"):
        iframe_src = "https:" + iframe_src
    elif iframe_src.startswith("/"):
        iframe_src = "https://eroleaked.com" + iframe_src

    iframe_html = fetch_page(iframe_src)
    m3u8 = extract_m3u8_from_html(iframe_html)
    if not m3u8:
        raise RuntimeError("No .m3u8 found in iframe page")

    if out_path is None:
        out_base = derive_filename_from_url(url)
        out_path = f"{out_base}.mp4"

    return download(m3u8, out_path=out_path)
