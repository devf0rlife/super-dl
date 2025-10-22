"""Simple CLI entrypoint for super-dl"""
from __future__ import annotations

import argparse
import sys
from typing import Dict, Optional

from . import __version__


def _site_registry() -> Dict[str, str]:
    """Return a mapping of supported site keys to module paths."""
    # Each entry maps a site key to its module path and a list of hostname patterns
    return {
        "influencersgonewild": {
            "module": "super_dl.sites.influencersgonewild",
            "hosts": ["influencersgonewild.com"],
        },
        "eroleaked": {
            "module": "super_dl.sites.eroleaked",
            "hosts": ["eroleaked.com"],
        },
        "amateurdoporn": {
            "module": "super_dl.sites.amateurdoporn",
            "hosts": ["amateurdoporn.com"],
        },
        "cumslutx": {
            "module": "super_dl.sites.cumslutx",
            "hosts": ["cumslutx.com", "girlxnude.com", "fapplay.com"],
        },
            "simpthots": {
                "module": "super_dl.sites.simpthots",
                "hosts": ["simpthots.com"],
            },
            "thothub": {
                "module": "super_dl.sites.thothub",
                "hosts": ["thothub.to", "thothub.org"],
            },
            "thotfans": {
                "module": "super_dl.sites.thotfans",
                "hosts": ["thotfans.com"],
            },
    }


def infer_site_from_url(url: str) -> Optional[str]:
    """Infer site key from the given URL by matching hostname patterns.

    Returns the site key (e.g. 'influencersgonewild') or None if not recognized.
    """
    from urllib.parse import urlparse

    if not url:
        return None
    parsed = urlparse(url)
    netloc = (parsed.netloc or "").lower()
    # strip possible credentials
    if "@" in netloc:
        netloc = netloc.split("@", 1)[-1]
    # strip leading www.
    if netloc.startswith("www."):
        netloc = netloc[4:]

    registry = _site_registry()
    for key, info in registry.items():
        hosts = info.get("hosts", []) if isinstance(info, dict) else []
        for host in hosts:
            if host and host in netloc:
                return key
    return None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="super-dl", description="super-dl CLI")
    parser.add_argument("--version", action="store_true", help="show version and exit")
    parser.add_argument("--site", help="site key (e.g. influencersgonewild)")
    parser.add_argument("url", nargs="?", help="URL of the page to download from")
    parser.add_argument("--output", "-o", help="output file path (optional)")

    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0

    if not args.url:
        parser.print_help()
        return 1

    registry = _site_registry()

    # Determine site key: prefer explicit --site, otherwise infer from URL
    site_key = args.site
    if not site_key:
        site_key = infer_site_from_url(args.url)
        if site_key:
            print(f"Inferred site: {site_key}")

    if not site_key:
        print("Could not determine site for the provided URL. Provide --site.", file=sys.stderr)
        return 2

    info = registry.get(site_key)
    module_path = info["module"] if isinstance(info, dict) else info
    if not module_path:
        print(f"Unknown site: {args.site}", file=sys.stderr)
        return 2

    # dynamic import of the site module
    try:
        module = __import__(module_path, fromlist=["*"])
    except Exception as exc:  # pragma: no cover - CLI runtime error
        print(f"Failed to import module for site {args.site}: {exc}", file=sys.stderr)
        return 3

    # Module interface handling: prefer a high-level `full_download_from_page` if present.
    try:
        # 1) high-level helper (eroleaked implements this)
        if hasattr(module, "full_download_from_page"):
            return module.full_download_from_page(args.url, out_path=args.output)

        # 2) classic mp4 extraction flow: fetch_page -> extract_mp4_url -> download
        if all(hasattr(module, name) for name in ("fetch_page", "extract_mp4_url", "download")):
            html = module.fetch_page(args.url)
            mp4_url = module.extract_mp4_url(html)
            if not mp4_url:
                print("No mp4 URL found on the page", file=sys.stderr)
                return 4
            return module.download(mp4_url, out_path=args.output)

        # 3) iframe -> m3u8 flow: fetch_page -> extract_iframe_src -> fetch iframe -> extract_m3u8_from_html -> download
        if all(hasattr(module, name) for name in ("fetch_page", "extract_iframe_src", "extract_m3u8_from_html", "download")):
            page_html = module.fetch_page(args.url)
            iframe_src = module.extract_iframe_src(page_html)
            if not iframe_src:
                print("No iframe found on page", file=sys.stderr)
                return 4

            # Resolve relative iframe URLs
            from urllib.parse import urljoin

            iframe_src = urljoin(args.url, iframe_src)

            iframe_html = module.fetch_page(iframe_src)
            m3u8 = module.extract_m3u8_from_html(iframe_html)
            if not m3u8:
                print("No .m3u8 file found on the page.", file=sys.stderr)
                return 4
            return module.download(m3u8, out_path=args.output)

        print("Site module does not expose a supported interface", file=sys.stderr)
        return 5
    except Exception as exc:  # pragma: no cover - runtime
        print(f"Error while processing: {exc}", file=sys.stderr)
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
