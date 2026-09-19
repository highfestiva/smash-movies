"""Retry and backoff helpers for download scripts.

Provides `fetch_json`, `download_image` and a generic `retry` helper.
"""
from __future__ import annotations

from bs4 import BeautifulSoup
import random
import time
import os
import tempfile
from typing import Callable, Any, Optional
import requests
import logging


# logging.basicConfig(level=logging.DEBUG)
# logging.getLogger("urllib3").setLevel(logging.DEBUG)


def retry(fn: Callable[..., Any], retries: int = 3, backoff: float = 1.0, jitter: float = 0.5, on_exception: Optional[Callable[[Exception], None]] = None, *args, **kwargs):
    """Retry a callable with exponential backoff and jitter.

    - `fn` is called with *args/**kwargs
    - `retries` is number of attempts (including first)
    - `backoff` is base sleep seconds
    - `jitter` is max random jitter added/subtracted
    """
    attempt = 0
    while attempt < retries:
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            attempt += 1
            if on_exception:
                try:
                    on_exception(exc)
                except Exception:
                    pass
            if attempt >= retries:
                raise
            sleep = backoff * (2 ** (attempt - 1))
            sleep = max(0.0, sleep + random.uniform(-jitter, jitter))
            time.sleep(sleep)


def _is_server_error(resp: requests.Response) -> bool:
    return 500 <= resp.status_code < 600


def init_headers(sess, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36', accept='*/*'):
    sess.headers.update({
        "User-Agent": user_agent,
        "Accept": accept,
    })


def fetch_json(url: str, session: Optional[requests.Session] = None, timeout: int = 10, retries: int = 3, backoff: float = 1.0):
    """Fetch JSON from URL with retries. Returns parsed JSON or raises.

    If the remote server returns a 5xx status we raise requests.HTTPError so callers
    can choose to skip or retry.
    """
    sess = session or requests.Session()
    init_headers(sess)

    def _get():
        params = {"query": "The Godfather"}
        r = sess.get(url, timeout=timeout)
        if _is_server_error(r):
            # server-side problem; raise to allow caller to decide
            r.raise_for_status()
        r.raise_for_status()
        return r.json()

    return retry(_get, retries=retries, backoff=backoff)


def html_to_text(html):
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True).lower()
    return text


def download_image(url: str, dest_path: str, session: Optional[requests.Session] = None, timeout: int = 20, retries: int = 3, backoff: float = 1.0):
    """Download an image to dest_path atomically with retries.

    If the destination file already exists, it is left untouched to avoid
    unnecessary updates. Returns the final path on success.
    """
    if os.path.exists(dest_path):
        return dest_path

    sess = session or requests.Session()
    init_headers(sess)

    dest_dir = os.path.dirname(dest_path)
    os.makedirs(dest_dir, exist_ok=True)

    def _dl():
        r = sess.get(url, stream=True, timeout=timeout)
        if _is_server_error(r):
            r.raise_for_status()
        r.raise_for_status()
        # write to temp file then move
        fd, tmp = tempfile.mkstemp(dir=dest_dir)
        os.close(fd)
        try:
            with open(tmp, "wb") as fh:
                for chunk in r.iter_content(8192):
                    if chunk:
                        fh.write(chunk)
            os.replace(tmp, dest_path)
        finally:
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except Exception:
                    pass
        return dest_path

    return retry(_dl, retries=retries, backoff=backoff)
